from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
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
                border-radius: 8px;
                padding: 16px;
            }}
        """)
        self.setMinimumHeight(120)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("color: rgba(255,255,255,0.8); font-size: 12px;")
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


class DashboardWidget(QWidget):
    navigate_to = Signal(str)

    def __init__(self, session_factory, parent=None):
        super().__init__(parent)
        self.session_factory = session_factory
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)

        layout.addWidget(make_header("Dashboard", 18))

        subtitle = QLabel("Welcome to TextileERP")
        subtitle.setStyleSheet("color: #666; margin-bottom: 12px;")
        layout.addWidget(subtitle)

        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(16)

        self.today_sales_card = SummaryCard("Today's Sales", "₹ 0.00", "#27ae60")
        cards_layout.addWidget(self.today_sales_card)

        self.receivables_card = SummaryCard("Total Receivables", "₹ 0.00", "#2980b9")
        cards_layout.addWidget(self.receivables_card)

        self.payables_card = SummaryCard("Total Payables", "₹ 0.00", "#e67e22")
        cards_layout.addWidget(self.payables_card)

        self.low_stock_card = SummaryCard("Low Stock Items", "0", "#c0392b")
        cards_layout.addWidget(self.low_stock_card)

        layout.addLayout(cards_layout)

        layout.addWidget(make_header("Quick Actions"))

        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(12)

        self.btn_new_invoice = QPushButton("+ New Invoice")
        self.btn_new_purchase = QPushButton("+ New Purchase")
        self.btn_new_party = QPushButton("+ New Party")
        self.btn_new_item = QPushButton("+ New Item")

        for btn in [self.btn_new_invoice, self.btn_new_purchase, self.btn_new_party, self.btn_new_item]:
            btn.setMinimumHeight(40)
            btn.setStyleSheet("""
                QPushButton {
                    background: #ecf0f1;
                    border: 1px solid #bdc3c7;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background: #dfe6e9;
                }
            """)
            actions_layout.addWidget(btn)

        layout.addLayout(actions_layout)
        layout.addStretch()

        self._load()

    def _load(self):
        session = self.session_factory()
        try:
            svc = ReportService(session)
            data = svc.dashboard_summary()
            self.today_sales_card.set_value(f"₹ {data['today_sales']:,.2f}")
            self.receivables_card.set_value(f"₹ {data['total_receivables']:,.2f}")
            self.payables_card.set_value(f"₹ {data['total_payables']:,.2f}")
            self.low_stock_card.set_value(str(len(data["low_stock_items"])))
        finally:
            session.close()

        self.btn_new_invoice.clicked.connect(lambda: self.navigate_to.emit("invoice"))
        self.btn_new_purchase.clicked.connect(lambda: self.navigate_to.emit("purchase"))
        self.btn_new_party.clicked.connect(lambda: self.navigate_to.emit("party"))
        self.btn_new_item.clicked.connect(lambda: self.navigate_to.emit("item"))
