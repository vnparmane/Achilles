from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QFormLayout, QLineEdit, QComboBox,
    QMessageBox, QLabel, QDoubleSpinBox,
)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QFont

from src.database.models.party import Party
from src.services.party_service import PartyService

INDIAN_STATES = [
    ("", "-- Select --"),
    ("AP", "Andhra Pradesh"), ("AR", "Arunachal Pradesh"), ("AS", "Assam"),
    ("BR", "Bihar"), ("CG", "Chhattisgarh"), ("GA", "Goa"),
    ("GJ", "Gujarat"), ("HR", "Haryana"), ("HP", "Himachal Pradesh"),
    ("JK", "Jammu and Kashmir"), ("JH", "Jharkhand"), ("KA", "Karnataka"),
    ("KL", "Kerala"), ("MP", "Madhya Pradesh"), ("MH", "Maharashtra"),
    ("MN", "Manipur"), ("ML", "Meghalaya"), ("MZ", "Mizoram"),
    ("NL", "Nagaland"), ("OD", "Odisha"), ("PB", "Punjab"),
    ("RJ", "Rajasthan"), ("SK", "Sikkim"), ("TN", "Tamil Nadu"),
    ("TS", "Telangana"), ("TR", "Tripura"), ("UP", "Uttar Pradesh"),
    ("UK", "Uttarakhand"), ("WB", "West Bengal"),
    ("DL", "Delhi"),
]


class PartyDialog(QDialog):
    def __init__(self, service: PartyService, party: Party | None = None, parent=None):
        super().__init__(parent)
        self.service = service
        self.party = party
        self.setWindowTitle("Add Party" if party is None else "Edit Party")
        self.setMinimumWidth(450)
        self.setModal(True)

        layout = QFormLayout(self)
        layout.setSpacing(8)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Party name *")
        if party:
            self.name_edit.setText(party.name)
        layout.addRow("Name *:", self.name_edit)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["customer", "vendor", "both"])
        if party:
            self.type_combo.setCurrentText(party.party_type)
        layout.addRow("Type:", self.type_combo)

        self.gstin_edit = QLineEdit()
        self.gstin_edit.setPlaceholderText("GSTIN (15 characters)")
        self.gstin_edit.setMaxLength(15)
        if party and party.gstin:
            self.gstin_edit.setText(party.gstin)
        layout.addRow("GSTIN:", self.gstin_edit)

        self.reg_combo = QComboBox()
        self.reg_combo.addItems(["regular", "composition", "unregistered"])
        if party:
            self.reg_combo.setCurrentText(party.registration_type)
        layout.addRow("Registration:", self.reg_combo)

        self.state_combo = QComboBox()
        for code, name in INDIAN_STATES:
            self.state_combo.addItem(name, code)
        if party and party.state:
            idx = self.state_combo.findText(party.state)
            if idx >= 0:
                self.state_combo.setCurrentIndex(idx)
        layout.addRow("State:", self.state_combo)

        self.address_edit = QLineEdit()
        self.address_edit.setPlaceholderText("Address")
        if party and party.address:
            self.address_edit.setText(party.address)
        layout.addRow("Address:", self.address_edit)

        self.phone_edit = QLineEdit()
        if party and party.phone:
            self.phone_edit.setText(party.phone)
        layout.addRow("Phone:", self.phone_edit)

        self.email_edit = QLineEdit()
        if party and party.email:
            self.email_edit.setText(party.email)
        layout.addRow("Email:", self.email_edit)

        self.balance_spin = QDoubleSpinBox()
        self.balance_spin.setRange(-999999, 999999)
        self.balance_spin.setDecimals(2)
        if party:
            self.balance_spin.setValue(party.opening_balance)
        layout.addRow("Opening Bal:", self.balance_spin)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)

        save_btn.clicked.connect(self._save)
        cancel_btn.clicked.connect(self.reject)

    def _save(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Party name is required.")
            return
        data = {
            "name": name,
            "party_type": self.type_combo.currentText(),
            "gstin": self.gstin_edit.text().strip().upper(),
            "registration_type": self.reg_combo.currentText(),
            "state": self.state_combo.currentText(),
            "state_code": self.state_combo.currentData() or "",
            "address": self.address_edit.text().strip(),
            "phone": self.phone_edit.text().strip(),
            "email": self.email_edit.text().strip(),
            "opening_balance": self.balance_spin.value(),
        }
        if self.party:
            self.service.update_party(self.party.id, **data)
        else:
            self.service.create_party(**data)
        self.accept()


class PartyMasterWidget(QWidget):
    def __init__(self, session_factory, parent=None):
        super().__init__(parent)
        self.session_factory = session_factory
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        header = QLabel("Parties (Customers & Vendors)")
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setBold(True)
        header.setFont(header_font)
        layout.addWidget(header)

        toolbar = QHBoxLayout()
        self.btn_add = QPushButton("+ New Party")
        self.btn_edit = QPushButton("Edit")
        self.btn_refresh = QPushButton("Refresh")
        toolbar.addWidget(self.btn_add)
        toolbar.addWidget(self.btn_edit)
        toolbar.addStretch()
        toolbar.addWidget(self.btn_refresh)
        layout.addLayout(toolbar)

        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels(
            ["Code", "Name", "Type", "GSTIN", "State", "Phone", "Email", "Balance", "Status"]
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

        self.btn_add.clicked.connect(self._add)
        self.btn_edit.clicked.connect(self._edit)
        self.btn_refresh.clicked.connect(self._load)
        self.table.doubleClicked.connect(self._edit)
        self._load()

    def _get_session_and_service(self):
        session = self.session_factory()
        return session, PartyService(session)

    @Slot()
    def _load(self):
        session, svc = self._get_session_and_service()
        try:
            parties = svc.get_all_parties()
            self.table.setRowCount(len(parties))
            for row, p in enumerate(parties):
                self.table.setItem(row, 0, QTableWidgetItem(p.code))
                self.table.setItem(row, 1, QTableWidgetItem(p.name))
                self.table.setItem(row, 2, QTableWidgetItem(p.party_type))
                self.table.setItem(row, 3, QTableWidgetItem(p.gstin or ""))
                self.table.setItem(row, 4, QTableWidgetItem(p.state or ""))
                self.table.setItem(row, 5, QTableWidgetItem(p.phone or ""))
                self.table.setItem(row, 6, QTableWidgetItem(p.email or ""))
                self.table.setItem(row, 7, QTableWidgetItem(f"{p.opening_balance:.2f}"))
                self.table.setItem(row, 8, QTableWidgetItem("Active" if p.is_active else "Inactive"))
                self.table.item(row, 0).setData(Qt.ItemDataRole.UserRole, p.id)
        finally:
            session.close()

    @Slot()
    def _add(self):
        session, svc = self._get_session_and_service()
        try:
            dialog = PartyDialog(svc, parent=self)
            if dialog.exec():
                self._load()
        finally:
            session.close()

    @Slot()
    def _edit(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Select", "Please select a party to edit.")
            return
        party_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        session, svc = self._get_session_and_service()
        try:
            party = svc.get_party_by_id(party_id)
            if party is None:
                return
            dialog = PartyDialog(svc, party, self)
            if dialog.exec():
                self._load()
        finally:
            session.close()
