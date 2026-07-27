from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.database.models.user import User
from src.services.user_service import UserService
from src.ui.helpers import make_header
from src.utils.constants import UserRole


class UserDialog(QDialog):
    def __init__(self, service: UserService, user: User | None = None, parent=None):
        super().__init__(parent)
        self.service = service
        self.user = user
        self.setWindowTitle("Add User" if user is None else "Edit User")
        self.setMinimumWidth(400)
        self.setModal(True)

        layout = QFormLayout(self)
        layout.setSpacing(8)

        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Username *")
        if user:
            self.username_edit.setText(user.username)
            self.username_edit.setEnabled(False)
        layout.addRow("Username *:", self.username_edit)

        self.display_edit = QLineEdit()
        self.display_edit.setPlaceholderText("Display name *")
        if user:
            self.display_edit.setText(user.display_name)
        layout.addRow("Display Name *:", self.display_edit)

        self.role_combo = QComboBox()
        for role in UserRole:
            self.role_combo.addItem(role.value.capitalize(), role.value)
        if user:
            self.role_combo.setCurrentIndex(
                self.role_combo.findData(user.role)
            )
        layout.addRow("Role:", self.role_combo)

        self.change_pwd_cb = QCheckBox("Change password")
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText("Min 4 characters")
        self.password_edit.setEnabled(False)

        if user is None:
            self.password_edit.setEnabled(True)
            self.change_pwd_cb.setChecked(True)
            self.change_pwd_cb.hide()
        else:
            self.change_pwd_cb.toggled.connect(self.password_edit.setEnabled)

        layout.addRow("", self.change_pwd_cb)
        layout.addRow("Password:", self.password_edit)

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
        username = self.username_edit.text().strip()
        display_name = self.display_edit.text().strip()
        if not username:
            QMessageBox.warning(self, "Error", "Username is required.")
            return
        if not display_name:
            QMessageBox.warning(self, "Error", "Display name is required.")
            return
        role = self.role_combo.currentData()
        if self.user:
            kwargs = {"display_name": display_name, "role": role}
            if self.change_pwd_cb.isChecked():
                pwd = self.password_edit.text()
                if len(pwd) < 4:
                    QMessageBox.warning(self, "Error", "Password must be at least 4 characters.")
                    return
                kwargs["password"] = pwd
            self.service.update_user(self.user.id, **kwargs)
        else:
            pwd = self.password_edit.text()
            if len(pwd) < 4:
                QMessageBox.warning(self, "Error", "Password must be at least 4 characters.")
                return
            self.service.create_user(
                username=username,
                password=pwd,
                display_name=display_name,
                role=role,
            )
        self.accept()


class UserMasterWidget(QWidget):
    def __init__(self, session_factory, parent=None):
        super().__init__(parent)
        self.session_factory = session_factory
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        layout.addWidget(make_header("User Management"))

        toolbar = QHBoxLayout()
        self.btn_add = QPushButton("+ New User")
        self.btn_edit = QPushButton("Edit")
        self.btn_toggle = QPushButton("Deactivate")
        self.btn_refresh = QPushButton("Refresh")
        toolbar.addWidget(self.btn_add)
        toolbar.addWidget(self.btn_edit)
        toolbar.addWidget(self.btn_toggle)
        toolbar.addStretch()
        toolbar.addWidget(self.btn_refresh)
        layout.addLayout(toolbar)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Username", "Display Name", "Role", "Status", ""])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

        self.btn_add.clicked.connect(self._add)
        self.btn_edit.clicked.connect(self._edit)
        self.btn_toggle.clicked.connect(self._toggle_active)
        self.btn_refresh.clicked.connect(self._load)
        self.table.doubleClicked.connect(self._edit)
        self._load()

    def _get_session_and_service(self):
        session = self.session_factory()
        return session, UserService(session)

    @Slot()
    def _load(self):
        session, svc = self._get_session_and_service()
        try:
            users = svc.get_all_users()
            self.table.setRowCount(len(users))
            for row, u in enumerate(users):
                self.table.setItem(row, 0, QTableWidgetItem(u.username))
                self.table.setItem(row, 1, QTableWidgetItem(u.display_name))
                self.table.setItem(row, 2, QTableWidgetItem(u.role.capitalize()))
                self.table.setItem(row, 3, QTableWidgetItem("Active" if u.is_active else "Inactive"))
                self.table.item(row, 0).setData(Qt.ItemDataRole.UserRole, u.id)
        finally:
            session.close()

    @Slot()
    def _add(self):
        session, svc = self._get_session_and_service()
        try:
            dialog = UserDialog(svc, parent=self)
            if dialog.exec():
                self._load()
        finally:
            session.close()

    @Slot()
    def _edit(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Select", "Please select a user to edit.")
            return
        user_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        session, svc = self._get_session_and_service()
        try:
            user = svc.get_user_by_id(user_id)
            if user is None:
                return
            dialog = UserDialog(svc, user, self)
            if dialog.exec():
                self._load()
        finally:
            session.close()

    @Slot()
    def _toggle_active(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Select", "Please select a user.")
            return
        user_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        session, svc = self._get_session_and_service()
        try:
            user = svc.get_user_by_id(user_id)
            if user is None:
                return
            new_state = not user.is_active
            svc.update_user(user.id, is_active=new_state)
            self._load()
        finally:
            session.close()
