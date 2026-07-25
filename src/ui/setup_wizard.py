from PySide6.QtWidgets import (
    QWizard, QWizardPage, QFormLayout,
    QLineEdit, QComboBox,
)

from src.services.company_service import CompanyService
from src.services.user_service import UserService
from src.services.godown_service import GodownService
from src.utils.constants import APP_NAME

INDIAN_STATES = [
    ("", "-- Select State --"),
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
    ("AN", "Andaman and Nicobar"), ("CH", "Chandigarh"),
    ("DN", "Dadra and Nagar Haveli"), ("DD", "Daman and Diu"),
    ("DL", "Delhi"), ("LD", "Lakshadweep"), ("PY", "Puducherry"),
]


class CompanyInfoPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Company Information")
        self.setSubTitle("Enter your company details as they should appear on invoices.")

        layout = QFormLayout(self)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g., ABC Textiles Pvt. Ltd.")
        layout.addRow("Company Name *:", self.name_edit)

        self.gstin_edit = QLineEdit()
        self.gstin_edit.setPlaceholderText("e.g., 27AAAAA0000A1Z5")
        self.gstin_edit.setMaxLength(15)
        layout.addRow("GSTIN:", self.gstin_edit)

        self.address_edit = QLineEdit()
        self.address_edit.setPlaceholderText("Full address")
        layout.addRow("Address:", self.address_edit)

        self.state_combo = QComboBox()
        for code, name in INDIAN_STATES:
            self.state_combo.addItem(name, code)
        layout.addRow("State:", self.state_combo)

        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("Phone number")
        layout.addRow("Phone:", self.phone_edit)

        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("Email address")
        layout.addRow("Email:", self.email_edit)

        self.registerField("company_name*", self.name_edit)

    def get_company_data(self) -> dict:
        return {
            "name": self.name_edit.text().strip(),
            "gstin": self.gstin_edit.text().strip().upper(),
            "address": self.address_edit.text().strip(),
            "state": self.state_combo.currentText(),
            "state_code": self.state_combo.currentData() or "",
            "phone": self.phone_edit.text().strip(),
            "email": self.email_edit.text().strip(),
        }


class BankInfoPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Bank Details")
        self.setSubTitle("Bank information for invoice payment details.")

        layout = QFormLayout(self)

        self.bank_name_edit = QLineEdit()
        self.bank_name_edit.setPlaceholderText("e.g., State Bank of India")
        layout.addRow("Bank Name:", self.bank_name_edit)

        self.branch_edit = QLineEdit()
        self.branch_edit.setPlaceholderText("Branch name")
        layout.addRow("Branch:", self.branch_edit)

        self.account_edit = QLineEdit()
        self.account_edit.setPlaceholderText("Account number")
        layout.addRow("Account No:", self.account_edit)

        self.ifsc_edit = QLineEdit()
        self.ifsc_edit.setPlaceholderText("e.g., SBIN0001234")
        self.ifsc_edit.setMaxLength(11)
        layout.addRow("IFSC Code:", self.ifsc_edit)

    def get_bank_data(self) -> dict:
        return {
            "bank_name": self.bank_name_edit.text().strip(),
            "bank_branch": self.branch_edit.text().strip(),
            "bank_account_no": self.account_edit.text().strip(),
            "bank_ifsc": self.ifsc_edit.text().strip().upper(),
        }


class AdminUserPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Admin User")
        self.setSubTitle("Create the administrator account for this software.")

        layout = QFormLayout(self)

        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("admin")
        layout.addRow("Username *:", self.username_edit)

        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText("Minimum 4 characters")
        layout.addRow("Password *:", self.password_edit)

        self.confirm_edit = QLineEdit()
        self.confirm_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_edit.setPlaceholderText("Re-enter password")
        layout.addRow("Confirm *:", self.confirm_edit)

        self.registerField("admin_username*", self.username_edit)
        self.registerField("admin_password*", self.password_edit)

    def validatePage(self) -> bool:
        if self.password_edit.text() != self.confirm_edit.text():
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Error", "Passwords do not match.")
            return False
        if len(self.password_edit.text()) < 4:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Error", "Password must be at least 4 characters.")
            return False
        return True

    def get_user_data(self) -> dict:
        return {
            "username": self.username_edit.text().strip(),
            "password": self.password_edit.text(),
        }


class SetupWizard(QWizard):
    def __init__(self, session_factory, parent=None):
        super().__init__(parent)
        self.session_factory = session_factory
        self.setWindowTitle(f"{APP_NAME} — Setup")
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.setMinimumSize(550, 450)

        self.company_page = CompanyInfoPage()
        self.bank_page = BankInfoPage()
        self.admin_page = AdminUserPage()

        self.addPage(self.company_page)
        self.addPage(self.bank_page)
        self.addPage(self.admin_page)

    def accept(self):
        session = self.session_factory()
        try:
            company_data = self.company_page.get_company_data()
            bank_data = self.bank_page.get_bank_data()
            user_data = self.admin_page.get_user_data()

            company_svc = CompanyService(session)
            company_svc.create_company(**company_data, **bank_data)

            user_svc = UserService(session)
            user_svc.create_user(
                username=user_data["username"],
                password=user_data["password"],
                display_name="Admin",
                role="admin",
            )

            godown_svc = GodownService(session)
            godown_svc.create_godown(code="MAIN", name="Main Godown")

            super().accept()
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error", f"Setup failed: {e}")
            session.rollback()
        finally:
            session.close()
