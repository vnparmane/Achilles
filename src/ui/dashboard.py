from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from src.services.report_service import ReportService
from src.ui.helpers import make_header


class SummaryCard(QFrame):
    clicked = Signal()

    def __init__(self, title: str, value: str, color: str = "#2c3e50", parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(f"""
            SummaryCard {{
                background: {color};
                border-radius: 10px;
                padding: 16px;
            }}
        """)
        self.setMinimumHeight(130)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(8)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("color: rgba(255,255,255,0.8); font-size: 12px; font-weight: 600;")
        layout.addWidget(self.title_label)

        self.value_label = QLabel(value)
        self.value_label.setStyleSheet("color: white; font-size: 28px; font-weight: bold;")
        layout.addWidget(self.value_label)

        layout.addStretch()

    def set_value(self, value: str):
        self.value_label.setText(value)

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)


class ActivityCard(QFrame):
    clicked = Signal(str)

    def __init__(self, label: str, party: str, amount: float, nav_id: str, parent=None):
        super().__init__(parent)
        self.nav_id = nav_id
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            ActivityCard {
                background: white;
                border: 1px solid #ecf0f1;
                border-radius: 6px;
            }
            ActivityCard:hover {
                border-color: #3498db;
                background: #f8f9fa;
            }
        """)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(44)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        lbl = QLabel(label)
        lbl.setStyleSheet("font-size: 13px; font-weight: 600;")
        layout.addWidget(lbl)

        party_lbl = QLabel(party)
        party_lbl.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        layout.addWidget(party_lbl)

        layout.addStretch()

        amt_lbl = QLabel(f"₹{amount:,.2f}")
        amt_lbl.setStyleSheet("color: #2c3e50; font-size: 13px; font-weight: bold;")
        layout.addWidget(amt_lbl)

    def mousePressEvent(self, event):
        self.clicked.emit(self.nav_id)
        super().mousePressEvent(event)


class DashboardWidget(QWidget):
    navigate_to = Signal(str)

    def __init__(self, session_factory, parent=None):
        super().__init__(parent)
        self.session_factory = session_factory
        self._chart_view = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        layout.addWidget(make_header("Dashboard", 18))

        subtitle = QLabel("Welcome to TextileERP")
        subtitle.setStyleSheet("color: #7f8c8d; margin-bottom: 4px;")
        layout.addWidget(subtitle)

        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(16)

        self.today_sales_card = SummaryCard("Today's Sales", "₹ 0.00", "#27ae60")
        cards_layout.addWidget(self.today_sales_card)

        self.today_purchases_card = SummaryCard("Today's Purchases", "₹ 0.00", "#e67e22")
        cards_layout.addWidget(self.today_purchases_card)

        self.receivables_card = SummaryCard("Outstanding Receivables", "₹ 0.00", "#2980b9")
        cards_layout.addWidget(self.receivables_card)

        self.payables_card = SummaryCard("Outstanding Payables", "₹ 0.00", "#8e44ad")
        cards_layout.addWidget(self.payables_card)

        self.low_stock_card = SummaryCard("Low Stock Items", "0", "#e74c3c")
        cards_layout.addWidget(self.low_stock_card)

        layout.addLayout(cards_layout)

        chart_mid = QHBoxLayout()
        chart_mid.setSpacing(16)

        chart_container = QWidget()
        chart_layout = QVBoxLayout(chart_container)
        chart_layout.setContentsMargins(0, 0, 0, 0)
        chart_layout.setSpacing(8)
        chart_layout.addWidget(make_header("Sales Trend"))
        self.chart_view = QWidget()
        self.chart_view.setMinimumHeight(200)
        chart_layout.addWidget(self.chart_view, 1)
        chart_mid.addWidget(chart_container, 1)

        layout.addLayout(chart_mid)

        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(16)

        activity_container = QWidget()
        activity_layout = QVBoxLayout(activity_container)
        activity_layout.setContentsMargins(0, 0, 0, 0)
        activity_layout.setSpacing(8)

        activity_layout.addWidget(make_header("Recent Activity"))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setMinimumHeight(200)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        self.activity_inner = QWidget()
        self.activity_inner_layout = QVBoxLayout(self.activity_inner)
        self.activity_inner_layout.setContentsMargins(0, 0, 0, 0)
        self.activity_inner_layout.setSpacing(4)
        self.activity_inner_layout.addStretch()
        scroll.setWidget(self.activity_inner)
        activity_layout.addWidget(scroll, 1)
        bottom_row.addWidget(activity_container, 1)

        actions_container = QWidget()
        actions_layout = QVBoxLayout(actions_container)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(8)

        actions_layout.addWidget(make_header("Quick Actions"))

        self.btn_new_invoice = QPushButton("🧾  + New Invoice")
        self.btn_new_purchase = QPushButton("🚚  + New Purchase")
        self.btn_new_party = QPushButton("👤  + New Party")
        self.btn_new_item = QPushButton("📦  + New Item")

        for btn in [self.btn_new_invoice, self.btn_new_purchase, self.btn_new_party, self.btn_new_item]:
            btn.setMinimumHeight(44)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background: white;
                    border: 1px solid #dcdde1;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-size: 13px;
                    text-align: left;
                }
                QPushButton:hover {
                    background: #f0f3f8;
                    border-color: #3498db;
                }
            """)
            actions_layout.addWidget(btn)

        actions_layout.addStretch()
        bottom_row.addWidget(actions_container, 1)

        layout.addLayout(bottom_row, 1)

        self._load()

    def _load(self):
        session = self.session_factory()
        try:
            svc = ReportService(session)
            data = svc.dashboard_summary()

            chart_data = [
                ("Mon", 0), ("Tue", 0), ("Wed", 0), ("Thu", 0),
                ("Fri", 0), ("Sat", 0), ("Sun", 0),
            ]
            today_sales = data.get("today_sales", 0)
            if today_sales:
                chart_data[-1] = ("Today", today_sales)
            raw_data = session.execute(
                "SELECT invoice_date, SUM(grand_total) FROM sales_invoice "
                "WHERE status='confirmed' AND invoice_date >= date('now', '-7 days') "
                "GROUP BY invoice_date ORDER BY invoice_date"
            ).fetchall()
            if raw_data:
                chart_data = [(str(r[0]), float(r[1])) for r in raw_data]

            from src.ui.charts import mini_sales_chart
            new_chart = mini_sales_chart(chart_data)
            parent_layout = self.chart_view.parent().layout()
            if parent_layout:
                idx = parent_layout.indexOf(self.chart_view)
                parent_layout.insertWidget(idx, new_chart)
                self.chart_view.deleteLater()
                self.chart_view = new_chart
            self.today_sales_card.set_value(f"₹ {data['today_sales']:,.2f}")
            self.today_purchases_card.set_value(f"₹ {data['today_purchases']:,.2f}")
            self.receivables_card.set_value(f"₹ {data['total_receivables']:,.2f}")
            self.payables_card.set_value(f"₹ {data['total_payables']:,.2f}")
            self.low_stock_card.set_value(str(len(data["low_stock_items"])))

            for item in self.activity_inner.findChildren(ActivityCard):
                item.deleteLater()

            for act in data["recent_activity"]:
                card = ActivityCard(
                    act["label"], act["party"], act["amount"], act["nav_id"]
                )
                card.clicked.connect(self.navigate_to.emit)
                self.activity_inner_layout.insertWidget(
                    self.activity_inner_layout.count() - 1, card
                )
        finally:
            session.close()

        self.btn_new_invoice.clicked.connect(lambda: self.navigate_to.emit("invoice"))
        self.btn_new_purchase.clicked.connect(lambda: self.navigate_to.emit("purchase"))
        self.btn_new_party.clicked.connect(lambda: self.navigate_to.emit("party"))
        self.btn_new_item.clicked.connect(lambda: self.navigate_to.emit("item"))
