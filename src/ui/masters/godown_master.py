from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QFormLayout, QLineEdit,
    QMessageBox, QLabel,
)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QFont

from src.database.models.godown import Godown
from src.services.godown_service import GodownService


class GodownDialog(QDialog):
    def __init__(self, service: GodownService, godown: Godown | None = None, parent=None):
        super().__init__(parent)
        self.service = service
        self.godown = godown
        self.setWindowTitle("Add Godown" if godown is None else "Edit Godown")
        self.setMinimumWidth(400)
        self.setModal(True)

        layout = QFormLayout(self)
        layout.setSpacing(8)

        self.code_edit = QLineEdit()
        self.code_edit.setPlaceholderText("Godown code *")
        if godown:
            self.code_edit.setText(godown.code)
        layout.addRow("Code *:", self.code_edit)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Godown name *")
        if godown:
            self.name_edit.setText(godown.name)
        layout.addRow("Name *:", self.name_edit)

        self.address_edit = QLineEdit()
        self.address_edit.setPlaceholderText("Address (optional)")
        if godown and godown.address:
            self.address_edit.setText(godown.address)
        layout.addRow("Address:", self.address_edit)

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
        code = self.code_edit.text().strip()
        name = self.name_edit.text().strip()
        if not code:
            QMessageBox.warning(self, "Error", "Godown code is required.")
            return
        if not name:
            QMessageBox.warning(self, "Error", "Godown name is required.")
            return
        address = self.address_edit.text().strip() or None
        if self.godown:
            self.service.update_godown(self.godown.id, code=code, name=name, address=address)
        else:
            self.service.create_godown(code=code, name=name, address=address)
        self.accept()


class GodownMasterWidget(QWidget):
    def __init__(self, session_factory, parent=None):
        super().__init__(parent)
        self.session_factory = session_factory
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        header = QLabel("Godowns (Storage Locations)")
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setBold(True)
        header.setFont(header_font)
        layout.addWidget(header)

        toolbar = QHBoxLayout()
        self.btn_add = QPushButton("+ New Godown")
        self.btn_edit = QPushButton("Edit")
        self.btn_refresh = QPushButton("Refresh")
        toolbar.addWidget(self.btn_add)
        toolbar.addWidget(self.btn_edit)
        toolbar.addStretch()
        toolbar.addWidget(self.btn_refresh)
        layout.addLayout(toolbar)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Code", "Name", "Address", "Status"])
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
        return session, GodownService(session)

    @Slot()
    def _load(self):
        session, svc = self._get_session_and_service()
        try:
            godowns = svc.get_all_godowns()
            self.table.setRowCount(len(godowns))
            for row, g in enumerate(godowns):
                self.table.setItem(row, 0, QTableWidgetItem(g.code))
                self.table.setItem(row, 1, QTableWidgetItem(g.name))
                self.table.setItem(row, 2, QTableWidgetItem(g.address or ""))
                self.table.setItem(row, 3, QTableWidgetItem("Active" if g.is_active else "Inactive"))
                self.table.item(row, 0).setData(Qt.ItemDataRole.UserRole, g.id)
        finally:
            session.close()

    @Slot()
    def _add(self):
        session, svc = self._get_session_and_service()
        try:
            dialog = GodownDialog(svc, parent=self)
            if dialog.exec():
                self._load()
        finally:
            session.close()

    @Slot()
    def _edit(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Select", "Please select a godown to edit.")
            return
        godown_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        session, svc = self._get_session_and_service()
        try:
            godown = svc.get_godown_by_id(godown_id)
            if godown is None:
                return
            dialog = GodownDialog(svc, godown, self)
            if dialog.exec():
                self._load()
        finally:
            session.close()
