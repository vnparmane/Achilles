from PySide6.QtCore import QDate, Slot
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDateEdit,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.services.party_service import PartyService
from src.services.report_service import ReportService
from src.ui.helpers import export_dialog, make_header


class LedgerReportWidget(QWidget):
    def __init__(self, session_factory, parent=None):
        super().__init__(parent)
        self.session_factory = session_factory
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        layout.addWidget(make_header("Party Ledger"))

        top = QHBoxLayout()
        top.addWidget(QLabel("Party:"))
        self.party_combo = QComboBox()
        self.party_combo.addItem("-- Select --", None)
        top.addWidget(self.party_combo, 1)

        top.addWidget(QLabel("From:"))
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addYears(-1))
        top.addWidget(self.date_from)
        top.addWidget(QLabel("To:"))
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        top.addWidget(self.date_to)

        self.btn_show = QPushButton("Show Ledger")
        top.addWidget(self.btn_show)
        self.btn_export = QPushButton("Export Excel")
        top.addWidget(self.btn_export)
        layout.addLayout(top)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Date", "Description", "Debit", "Credit", "Balance"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table, 1)

        self.lbl_balance = QLabel("")
        lbf = QFont()
        lbf.setBold(True)
        self.lbl_balance.setFont(lbf)
        layout.addWidget(self.lbl_balance)

        self.btn_show.clicked.connect(self._load)
        self.btn_export.clicked.connect(self._export)
        self._populate_parties()

    @Slot()
    def _export(self):
        export_dialog(self, self.table, "party_ledger.xlsx")

    def _populate_parties(self):
        session = self.session_factory()
        try:
            svc = PartyService(session)
            for p in svc.get_all_parties():
                self.party_combo.addItem(f"{p.code} - {p.name} [{p.party_type}]", p.id)
        finally:
            session.close()

    @Slot()
    def _load(self):
        party_id = self.party_combo.currentData()
        if party_id is None:
            return
        session = self.session_factory()
        try:
            svc = ReportService(session)
            entries = svc.party_ledger(
                party_id,
                date_from=self.date_from.date().toString("yyyy-MM-dd"),
                date_to=self.date_to.date().toString("yyyy-MM-dd"),
            )
            self.table.setRowCount(len(entries))
            balance = 0.0
            for row, e in enumerate(entries):
                self.table.setItem(row, 0, QTableWidgetItem(e["date"]))
                self.table.setItem(row, 1, QTableWidgetItem(e["description"]))
                self.table.setItem(row, 2, QTableWidgetItem(f"{e['debit']:,.2f}" if e["debit"] else ""))
                self.table.setItem(row, 3, QTableWidgetItem(f"{e['credit']:,.2f}" if e["credit"] else ""))
                self.table.setItem(row, 4, QTableWidgetItem(f"{e['balance']:,.2f}"))
                balance = e["balance"]
            label = f"Closing Balance: ₹{balance:,.2f}"
            if balance > 0:
                label += " (Dr)"
            elif balance < 0:
                label += " (Cr)"
            self.lbl_balance.setText(label)
        finally:
            session.close()
