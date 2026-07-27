from PySide6.QtCore import QDate, Slot
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDateEdit,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.services.report_service import ReportService
from src.ui.helpers import make_header, export_dialog


class RegisterReportWidget(QWidget):
    def __init__(self, session_factory, parent=None):
        super().__init__(parent)
        self.session_factory = session_factory
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self._setup_purchase()
        self._setup_sales()
        self.tabs.addTab(self.purchase_tab, "Purchase Register")
        self.tabs.addTab(self.sales_tab, "Sales Register")

    def _setup_purchase(self):
        self.purchase_tab = QWidget()
        layout = QVBoxLayout(self.purchase_tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.addWidget(make_header("Purchase Register"))

        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("From:"))
        self.pur_date_from = QDateEdit()
        self.pur_date_from.setCalendarPopup(True)
        self.pur_date_from.setDate(QDate.currentDate().addYears(-1))
        toolbar.addWidget(self.pur_date_from)
        toolbar.addWidget(QLabel("To:"))
        self.pur_date_to = QDateEdit()
        self.pur_date_to.setCalendarPopup(True)
        self.pur_date_to.setDate(QDate.currentDate())
        toolbar.addWidget(self.pur_date_to)
        self.btn_refresh_pur = QPushButton("Refresh")
        self.btn_export_pur = QPushButton("Export Excel")
        toolbar.addStretch()
        toolbar.addWidget(self.btn_export_pur)
        toolbar.addWidget(self.btn_refresh_pur)
        layout.addLayout(toolbar)

        self.pur_table = QTableWidget()
        self.pur_table.setColumnCount(6)
        self.pur_table.setHorizontalHeaderLabels(
            ["Bill No", "Date", "Vendor", "Gross", "Taxable", "Grand Total"]
        )
        self.pur_table.horizontalHeader().setStretchLastSection(True)
        self.pur_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.pur_table.setAlternatingRowColors(True)
        layout.addWidget(self.pur_table, 1)
        self.btn_refresh_pur.clicked.connect(self._load_purchase)
        self.btn_export_pur.clicked.connect(self._export_purchase)

    def _setup_sales(self):
        self.sales_tab = QWidget()
        layout = QVBoxLayout(self.sales_tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.addWidget(make_header("Sales Register"))

        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("From:"))
        self.sal_date_from = QDateEdit()
        self.sal_date_from.setCalendarPopup(True)
        self.sal_date_from.setDate(QDate.currentDate().addYears(-1))
        toolbar.addWidget(self.sal_date_from)
        toolbar.addWidget(QLabel("To:"))
        self.sal_date_to = QDateEdit()
        self.sal_date_to.setCalendarPopup(True)
        self.sal_date_to.setDate(QDate.currentDate())
        toolbar.addWidget(self.sal_date_to)
        self.btn_refresh_sal = QPushButton("Refresh")
        self.btn_export_sal = QPushButton("Export Excel")
        toolbar.addStretch()
        toolbar.addWidget(self.btn_export_sal)
        toolbar.addWidget(self.btn_refresh_sal)
        layout.addLayout(toolbar)

        self.sal_table = QTableWidget()
        self.sal_table.setColumnCount(6)
        self.sal_table.setHorizontalHeaderLabels(
            ["Invoice No", "Date", "Customer", "Gross", "Taxable", "Grand Total"]
        )
        self.sal_table.horizontalHeader().setStretchLastSection(True)
        self.sal_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.sal_table.setAlternatingRowColors(True)
        layout.addWidget(self.sal_table, 1)
        self.btn_refresh_sal.clicked.connect(self._load_sales)
        self.btn_export_sal.clicked.connect(self._export_sales)

        self._load_purchase()
        self._load_sales()

    @Slot()
    def _export_purchase(self):
        export_dialog(self, self.pur_table, "purchase_register.xlsx")

    @Slot()
    def _export_sales(self):
        export_dialog(self, self.sal_table, "sales_register.xlsx")

    def _load_purchase(self):
        session = self.session_factory()
        try:
            svc = ReportService(session)
            data = svc.purchase_register(
                date_from=self.pur_date_from.date().toString("yyyy-MM-dd"),
                date_to=self.pur_date_to.date().toString("yyyy-MM-dd"),
            )
            self.pur_table.setRowCount(len(data))
            for row, d in enumerate(data):
                self.pur_table.setItem(row, 0, QTableWidgetItem(d["bill_no"]))
                self.pur_table.setItem(row, 1, QTableWidgetItem(d["date"]))
                self.pur_table.setItem(row, 2, QTableWidgetItem(d["party"]))
                self.pur_table.setItem(row, 3, QTableWidgetItem(f"{d['gross']:,.2f}"))
                self.pur_table.setItem(row, 4, QTableWidgetItem(f"{d['taxable']:,.2f}"))
                self.pur_table.setItem(row, 5, QTableWidgetItem(f"{d['grand']:,.2f}"))
        finally:
            session.close()

    def _load_sales(self):
        session = self.session_factory()
        try:
            svc = ReportService(session)
            data = svc.sales_register(
                date_from=self.sal_date_from.date().toString("yyyy-MM-dd"),
                date_to=self.sal_date_to.date().toString("yyyy-MM-dd"),
            )
            self.sal_table.setRowCount(len(data))
            for row, d in enumerate(data):
                self.sal_table.setItem(row, 0, QTableWidgetItem(d["invoice_no"]))
                self.sal_table.setItem(row, 1, QTableWidgetItem(d["date"]))
                self.sal_table.setItem(row, 2, QTableWidgetItem(d["party"]))
                self.sal_table.setItem(row, 3, QTableWidgetItem(f"{d['gross']:,.2f}"))
                self.sal_table.setItem(row, 4, QTableWidgetItem(f"{d['taxable']:,.2f}"))
                self.sal_table.setItem(row, 5, QTableWidgetItem(f"{d['grand']:,.2f}"))
        finally:
            session.close()
