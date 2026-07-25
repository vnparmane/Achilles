from pathlib import Path

from PySide6.QtWidgets import QApplication

from src.database.engine import create_db_engine, create_session_factory
from src.database.models.base import Base
from src.services.company_service import CompanyService
from src.ui.login_dialog import LoginDialog
from src.ui.main_window import MainWindow
from src.ui.setup_wizard import SetupWizard
from src.utils.constants import APP_NAME


def run_app():
    app = QApplication([])
    app.setApplicationName(APP_NAME)

    qss_path = Path(__file__).resolve().parent.parent / "resources" / "styles" / "app.qss"
    if qss_path.exists():
        with open(qss_path, encoding="utf-8") as f:
            app.setStyleSheet(f.read())

    engine = create_db_engine()
    session_factory = create_session_factory(engine)
    Base.metadata.create_all(engine)

    session = session_factory()
    try:
        company_svc = CompanyService(session)
        if not company_svc.has_company():
            wizard = SetupWizard(session_factory)
            if wizard.exec() != SetupWizard.DialogCode.Accepted:
                return 1
    finally:
        session.close()

    login = LoginDialog(session_factory)
    if login.exec() != LoginDialog.DialogCode.Accepted:
        return 1

    window = MainWindow(session_factory, login.authenticated_user)
    window.show()

    return app.exec()
