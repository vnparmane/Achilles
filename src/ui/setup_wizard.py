from PySide6.QtWidgets import QMessageBox, QWizard

from src.services.company_service import CompanyService
from src.services.godown_service import GodownService
from src.services.user_service import UserService
from src.ui.wizard_pages import AdminUserPage, BankInfoPage, CompanyInfoPage
from src.utils.constants import APP_NAME


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
            QMessageBox.critical(self, "Error", f"Setup failed: {e}")
            session.rollback()
        finally:
            session.close()
