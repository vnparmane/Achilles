from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QLabel, QComboBox, QDoubleSpinBox,
    QMessageBox, QDateEdit, QLineEdit, QFormLayout,
    QAbstractItemView, QTabWidget, QGroupBox,
)
from PySide6.QtCore import Qt, Slot, QDate
from PySide6.QtGui import QFont

from src.services.party_service import PartyService
from src.services.payment_service import PaymentService
from src.utils.constants import PaymentMode


class PaymentEntryWidget(QWidget):
    def __init__(self, session_factory, current_user, parent=None):
        super().__init__(parent)
        self.session_factory = session_factory
        self.current_user = current_user

        self.tabs = QTabWidget()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.tabs)

        self._setup_form()
        self.tabs.addTab(self.form_tab, "New Payment")
        self._setup_list()
        self.tabs.addTab(self.list_tab, "Payment History")

    def _setup_form(self):
        self.form_tab = QWidget()
        layout = QVBoxLayout(self.form_tab)
        layout.setContentsMargins(16, 16, 16, 16)

        header = QLabel("Record Payment")
        hf = QFont()
        hf.setPointSize(14)
        hf.setBold(True)
        header.setFont(hf)
        layout.addWidget(header)

        form = QFormLayout()
        form.setSpacing(6)

        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        form.addRow("Date:", self.date_edit)

        self.type_combo = QComboBox()
        self.type_combo.addItem("Receipt (from Customer)", "receipt")
        self.type_combo.addItem("Payment (to Vendor)", "payment")
        self.type_combo.currentIndexChanged.connect(self._on_type_change)
        form.addRow("Type:", self.type_combo)

        session = self.session_factory()
        try:
            party_svc = PartyService(session)
            self.party_combo = QComboBox()
            self.party_combo.addItem("-- Select --", None)
            self._parties_data: dict[int, str] = {}
            for p in party_svc.get_all_parties():
                self.party_combo.addItem(f"{p.code} - {p.name} [{p.party_type}]", p.id)
                self._parties_data[p.id] = p.party_type
            self.party_combo.currentIndexChanged.connect(self._on_party_change)
            form.addRow("Party:", self.party_combo)
        finally:
            session.close()

        self.mode_combo = QComboBox()
        for m in PaymentMode:
            self.mode_combo.addItem(m.value.capitalize(), m.value)
        form.addRow("Mode:", self.mode_combo)

        self.ref_edit = QLineEdit()
        self.ref_edit.setPlaceholderText("Cheque/UPI/Ref No")
        form.addRow("Ref No:", self.ref_edit)

        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0, 999999)
        self.amount_spin.setDecimals(2)
        self.amount_spin.setPrefix("₹ ")
        form.addRow("Amount:", self.amount_spin)

        self.notes_edit = QLineEdit()
        self.notes_edit.setPlaceholderText("Optional notes")
        form.addRow("Notes:", self.notes_edit)

        layout.addLayout(form)

        self.outstanding_group = QGroupBox("Outstanding Bills")
        olayout = QVBoxLayout(self.outstanding_group)
        self.outstanding_table = QTableWidget()
        self.outstanding_table.setColumnCount(5)
        self.outstanding_table.setHorizontalHeaderLabels(
            ["Ref No", "Date", "Total", "Paid", "Outstanding"]
        )
        self.outstanding_table.horizontalHeader().setStretchLastSection(True)
        self.outstanding_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.outstanding_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        olayout.addWidget(self.outstanding_table)

        self.lbl_total_outstanding = QLabel("Total Outstanding: ₹ 0.00")
        to_font = QFont()
        to_font.setBold(True)
        self.lbl_total_outstanding.setFont(to_font)
        olayout.addWidget(self.lbl_total_outstanding)
        layout.addWidget(self.outstanding_group)

        self.btn_save = QPushButton("Record Payment")
        self.btn_save.setMinimumHeight(36)
        layout.addWidget(self.btn_save, alignment=Qt.AlignmentFlag.AlignRight)

        self.btn_save.clicked.connect(self._save)

    def _setup_list(self):
        self.list_tab = QWidget()
        layout = QVBoxLayout(self.list_tab)
        layout.setContentsMargins(16, 16, 16, 16)
        header = QLabel("Payment History")
        hf = QFont()
        hf.setPointSize(14)
        hf.setBold(True)
        header.setFont(hf)
        layout.addWidget(header)
        self.lv_table = QTableWidget()
        self.lv_table.setColumnCount(6)
        self.lv_table.setHorizontalHeaderLabels(["Date", "Type", "Party", "Mode", "Amount", "Ref No"])
        self.lv_table.horizontalHeader().setStretchLastSection(True)
        self.lv_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.lv_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.lv_table.setAlternatingRowColors(True)
        layout.addWidget(self.lv_table)
        self._load_list()

    def _load_list(self):
        session = self.session_factory()
        try:
            svc = PaymentService(session)
            payments = svc.get_all_payments()
            self.lv_table.setRowCount(len(payments))
            for row, p in enumerate(payments):
                self.lv_table.setItem(row, 0, QTableWidgetItem(p.payment_date))
                self.lv_table.setItem(row, 1, QTableWidgetItem(p.payment_type.capitalize()))
                self.lv_table.setItem(row, 2, QTableWidgetItem(p.party.name if p.party else ""))
                self.lv_table.setItem(row, 3, QTableWidgetItem(p.mode.capitalize()))
                self.lv_table.setItem(row, 4, QTableWidgetItem(f"₹{p.amount:,.2f}"))
                self.lv_table.setItem(row, 5, QTableWidgetItem(p.reference_no or ""))
        finally:
            session.close()

    @Slot()
    def _on_type_change(self):
        ptype = self.type_combo.currentData()
        self.party_combo.clear()
        self.party_combo.addItem("-- Select --", None)
        session = self.session_factory()
        try:
            party_svc = PartyService(session)
            filter_type = "customer" if ptype == "receipt" else "vendor"
            for p in party_svc.get_all_parties(filter_type):
                self.party_combo.addItem(f"{p.code} - {p.name}", p.id)
                self._parties_data[p.id] = p.party_type
        finally:
            session.close()

    @Slot()
    def _on_party_change(self):
        party_id = self.party_combo.currentData()
        if party_id is None:
            self.outstanding_table.setRowCount(0)
            self.lbl_total_outstanding.setText("Total Outstanding: ₹ 0.00")
            return
        session = self.session_factory()
        try:
            svc = PaymentService(session)
            invoices = svc.get_outstanding_invoices(party_id)
            self.outstanding_table.setRowCount(len(invoices))
            total_outstanding = 0.0
            for row, inv in enumerate(invoices):
                self.outstanding_table.setItem(row, 0, QTableWidgetItem(inv["ref_no"]))
                self.outstanding_table.setItem(row, 1, QTableWidgetItem(inv["date"]))
                self.outstanding_table.setItem(row, 2, QTableWidgetItem(f"₹{inv['total']:,.2f}"))
                self.outstanding_table.setItem(row, 3, QTableWidgetItem(f"₹{inv['paid']:,.2f}"))
                self.outstanding_table.setItem(row, 4, QTableWidgetItem(f"₹{inv['outstanding']:,.2f}"))
                total_outstanding += inv["outstanding"]
            self.lbl_total_outstanding.setText(f"Total Outstanding: ₹ {total_outstanding:,.2f}")
        finally:
            session.close()

    def _save(self):
        party_id = self.party_combo.currentData()
        amount = self.amount_spin.value()
        if party_id is None:
            QMessageBox.warning(self, "Error", "Please select a party.")
            return
        if amount <= 0:
            QMessageBox.warning(self, "Error", "Amount must be greater than zero.")
            return

        session = self.session_factory()
        try:
            svc = PaymentService(session)
            svc.record_payment(
                payment_type=self.type_combo.currentData(),
                party_id=party_id,
                amount=amount,
                payment_date=self.date_edit.date().toString("yyyy-MM-dd"),
                mode=self.mode_combo.currentData(),
                reference_no=self.ref_edit.text().strip() or None,
                notes=self.notes_edit.text().strip() or None,
            )
            QMessageBox.information(self, "Success", "Payment recorded!")
            self.amount_spin.setValue(0)
            self.ref_edit.clear()
            self.notes_edit.clear()
            self._on_party_change()
            self._load_list()
            self.tabs.setCurrentIndex(1)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed: {e}")
            session.rollback()
        finally:
            session.close()
