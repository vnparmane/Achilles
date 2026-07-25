from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QPushButton,
    QLineEdit, QComboBox, QMessageBox, QLabel,
    QScrollArea, QGroupBox,
)
from PySide6.QtCore import Slot
from PySide6.QtGui import QFont

from src.services.company_service import CompanyService
from src.ui.setup_wizard import INDIAN_STATES


class CompanyMasterWidget(QWidget):
    def __init__(self, session_factory, parent=None):
        super().__init__(parent)
        self.session_factory = session_factory

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        header = QLabel("Company Settings")
        hf = QFont()
        hf.setPointSize(14)
        hf.setBold(True)
        header.setFont(hf)
        layout.addWidget(header)

        company_group = QGroupBox("Company Information")
        company_form = QFormLayout(company_group)
        company_form.setSpacing(8)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Company name *")
        company_form.addRow("Name *:", self.name_edit)

        self.gstin_edit = QLineEdit()
        self.gstin_edit.setPlaceholderText("e.g., 27AAAAA0000A1Z5")
        self.gstin_edit.setMaxLength(15)
        company_form.addRow("GSTIN:", self.gstin_edit)

        self.address_edit = QLineEdit()
        self.address_edit.setPlaceholderText("Full address")
        company_form.addRow("Address:", self.address_edit)

        self.state_combo = QComboBox()
        for code, name in INDIAN_STATES:
            self.state_combo.addItem(name, code)
        company_form.addRow("State:", self.state_combo)

        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("Phone number")
        company_form.addRow("Phone:", self.phone_edit)

        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("Email address")
        company_form.addRow("Email:", self.email_edit)

        layout.addWidget(company_group)

        bank_group = QGroupBox("Bank Details")
        bank_form = QFormLayout(bank_group)
        bank_form.setSpacing(8)

        self.bank_name_edit = QLineEdit()
        self.bank_name_edit.setPlaceholderText("e.g., State Bank of India")
        bank_form.addRow("Bank Name:", self.bank_name_edit)

        self.branch_edit = QLineEdit()
        self.branch_edit.setPlaceholderText("Branch name")
        bank_form.addRow("Branch:", self.branch_edit)

        self.account_edit = QLineEdit()
        self.account_edit.setPlaceholderText("Account number")
        bank_form.addRow("Account No:", self.account_edit)

        self.ifsc_edit = QLineEdit()
        self.ifsc_edit.setPlaceholderText("e.g., SBIN0001234")
        self.ifsc_edit.setMaxLength(11)
        bank_form.addRow("IFSC Code:", self.ifsc_edit)

        layout.addWidget(bank_group)

        self.btn_save = QPushButton("Save Changes")
        self.btn_save.setObjectName("primaryButton")
        self.btn_save.setFixedWidth(160)
        layout.addWidget(self.btn_save)
        layout.addStretch()

        scroll.setWidget(inner)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

        self.btn_save.clicked.connect(self._save)
        self._load()

    def _load(self):
        session = self.session_factory()
        try:
            svc = CompanyService(session)
            company = svc.get_company()
            if company is None:
                return
            self.name_edit.setText(company.name)
            self.gstin_edit.setText(company.gstin or "")
            self.address_edit.setText(company.address or "")
            self.phone_edit.setText(company.phone or "")
            self.email_edit.setText(company.email or "")
            if company.state_code:
                idx = self.state_combo.findData(company.state_code)
                if idx >= 0:
                    self.state_combo.setCurrentIndex(idx)
            self.bank_name_edit.setText(company.bank_name or "")
            self.branch_edit.setText(company.bank_branch or "")
            self.account_edit.setText(company.bank_account_no or "")
            self.ifsc_edit.setText(company.bank_ifsc or "")
        finally:
            session.close()

    @Slot()
    def _save(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Company name is required.")
            return
        session = self.session_factory()
        try:
            svc = CompanyService(session)
            company = svc.get_company()
            if company is None:
                QMessageBox.warning(self, "Error", "No company found. Run setup first.")
                return
            svc.update_company(
                company.id,
                name=name,
                gstin=self.gstin_edit.text().strip().upper(),
                address=self.address_edit.text().strip(),
                state=self.state_combo.currentText(),
                state_code=self.state_combo.currentData() or "",
                phone=self.phone_edit.text().strip(),
                email=self.email_edit.text().strip(),
                bank_name=self.bank_name_edit.text().strip(),
                bank_branch=self.branch_edit.text().strip(),
                bank_account_no=self.account_edit.text().strip(),
                bank_ifsc=self.ifsc_edit.text().strip().upper(),
            )
            session.commit()
            QMessageBox.information(self, "Saved", "Company details updated.")
        finally:
            session.close()
