from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from src.database.models.user import User
from src.services.user_service import UserService
from src.utils.constants import APP_NAME


class LoginDialog(QDialog):
    login_successful = Signal(User)

    def __init__(self, session_factory, parent=None):
        super().__init__(parent)
        self.session_factory = session_factory
        self.authenticated_user: User | None = None
        self.setWindowTitle(f"{APP_NAME} — Login")
        self.setFixedSize(380, 280)
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(40, 30, 40, 30)

        title = QLabel(f"{APP_NAME}")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("Sign in to your account")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        form = QFormLayout()
        form.setSpacing(8)

        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Username")
        self.username_edit.setMinimumHeight(32)
        form.addRow("Username:", self.username_edit)

        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText("Password")
        self.password_edit.setMinimumHeight(32)
        form.addRow("Password:", self.password_edit)

        layout.addLayout(form)

        self.login_btn = QPushButton("Sign In")
        self.login_btn.setMinimumHeight(36)
        self.login_btn.setDefault(True)
        layout.addWidget(self.login_btn)

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: red;")
        layout.addWidget(self.status_label)

        self.login_btn.clicked.connect(self._do_login)
        self.password_edit.returnPressed.connect(self._do_login)
        self.username_edit.returnPressed.connect(lambda: self.password_edit.setFocus())

    def _do_login(self):
        username = self.username_edit.text().strip()
        password = self.password_edit.text()

        if not username or not password:
            self.status_label.setText("Please enter username and password.")
            return

        session = self.session_factory()
        try:
            svc = UserService(session)
            user = svc.authenticate(username, password)
            if user is None:
                self.status_label.setText("Invalid username or password.")
                return
            self.authenticated_user = user
            self.accept()
        finally:
            session.close()
