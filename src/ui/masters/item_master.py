from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDoubleSpinBox,
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

from src.database.models.item import Item
from src.services.item_service import ItemService
from src.ui.helpers import form_section, make_header, make_table_filter, setup_table_sort
from src.utils.constants import GST_RATES, ItemUnit


class ItemDialog(QDialog):
    def __init__(self, service: ItemService, item: Item | None = None, parent=None):
        super().__init__(parent)
        self.service = service
        self.item = item
        self.setWindowTitle("Add Item" if item is None else "Edit Item")
        self.setMinimumWidth(400)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(6)

        layout.addWidget(form_section("Basic Info"))
        basic = QFormLayout()
        basic.setSpacing(6)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Item name *")
        if item:
            self.name_edit.setText(item.name)
        basic.addRow("Name *:", self.name_edit)

        self.unit_combo = QComboBox()
        for u in ItemUnit:
            self.unit_combo.addItem(u.value)
        if item:
            self.unit_combo.setCurrentText(item.unit)
        basic.addRow("Unit:", self.unit_combo)
        layout.addLayout(basic)

        layout.addWidget(form_section("Tax & Inventory"))
        tax = QFormLayout()
        tax.setSpacing(6)
        self.hsn_edit = QLineEdit()
        self.hsn_edit.setPlaceholderText("HSN code (e.g., 5205)")
        if item and item.hsn_code:
            self.hsn_edit.setText(item.hsn_code)
        tax.addRow("HSN Code:", self.hsn_edit)

        self.gst_combo = QComboBox()
        for rate in GST_RATES:
            self.gst_combo.addItem(f"{rate}%", rate)
        if item:
            idx = self.gst_combo.findData(item.gst_rate)
            if idx >= 0:
                self.gst_combo.setCurrentIndex(idx)
        tax.addRow("GST Rate:", self.gst_combo)

        self.balance_spin = QDoubleSpinBox()
        self.balance_spin.setRange(0, 999999)
        self.balance_spin.setDecimals(2)
        if item:
            self.balance_spin.setValue(item.opening_balance)
        tax.addRow("Opening:", self.balance_spin)
        layout.addLayout(tax)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        save_btn.clicked.connect(self._save)
        cancel_btn.clicked.connect(self.reject)

    def _save(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Item name is required.")
            return
        data = {
            "name": name,
            "unit": self.unit_combo.currentText(),
            "hsn_code": self.hsn_edit.text().strip(),
            "gst_rate": self.gst_combo.currentData(),
            "opening_balance": self.balance_spin.value(),
        }
        if self.item:
            self.service.update_item(self.item.id, **data)
        else:
            self.service.create_item(**data)
        self.accept()


class ItemMasterWidget(QWidget):
    def __init__(self, session_factory, parent=None):
        super().__init__(parent)
        self.session_factory = session_factory
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        layout.addWidget(make_header("Items"))

        toolbar = QHBoxLayout()
        self.btn_add = QPushButton("+ New Item")
        self.btn_edit = QPushButton("Edit")
        self.btn_delete = QPushButton("Delete")
        self.btn_delete.setObjectName("dangerButton")
        self.btn_refresh = QPushButton("Refresh")
        toolbar.addWidget(self.btn_add)
        toolbar.addWidget(self.btn_edit)
        toolbar.addWidget(self.btn_delete)
        toolbar.addStretch()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍  Search items...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setFixedWidth(250)
        toolbar.addWidget(self.search_input)
        toolbar.addWidget(self.btn_refresh)
        layout.addLayout(toolbar)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["Code", "Name", "Unit", "HSN", "GST Rate", "Opening", "Status"]
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        setup_table_sort(self.table)
        make_table_filter(self.table, self.search_input)
        layout.addWidget(self.table)

        self.btn_add.clicked.connect(self._add)
        self.btn_edit.clicked.connect(self._edit)
        self.btn_delete.clicked.connect(self._delete)
        self.btn_refresh.clicked.connect(self._load)
        self.table.doubleClicked.connect(self._edit)
        self._load()

    def _get_session_and_service(self):
        session = self.session_factory()
        return session, ItemService(session)

    @Slot()
    def _load(self):
        session, svc = self._get_session_and_service()
        try:
            items = svc.get_all_items()
            self.table.setRowCount(len(items))
            for row, it in enumerate(items):
                self.table.setItem(row, 0, QTableWidgetItem(it.code))
                self.table.setItem(row, 1, QTableWidgetItem(it.name))
                self.table.setItem(row, 2, QTableWidgetItem(it.unit))
                self.table.setItem(row, 3, QTableWidgetItem(it.hsn_code or ""))
                self.table.setItem(row, 4, QTableWidgetItem(f"{it.gst_rate}%"))
                self.table.setItem(row, 5, QTableWidgetItem(str(it.opening_balance)))
                self.table.setItem(row, 6, QTableWidgetItem("Active" if it.is_active else "Inactive"))
                self.table.item(row, 0).setData(Qt.ItemDataRole.UserRole, it.id)
        finally:
            session.close()

    @Slot()
    def _add(self):
        session, svc = self._get_session_and_service()
        try:
            if ItemDialog(svc, parent=self).exec():
                self._load()
        finally:
            session.close()

    @Slot()
    def _edit(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Select", "Please select an item to edit.")
            return
        item_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        session, svc = self._get_session_and_service()
        try:
            item = svc.get_item_by_id(item_id)
            if item is None:
                return
            if ItemDialog(svc, item, self).exec():
                self._load()
        finally:
            session.close()

    @Slot()
    def _delete(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Select", "Please select an item to delete.")
            return
        item_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        reply = QMessageBox.question(
            self, "Confirm Delete",
            "Delete this item? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        session, svc = self._get_session_and_service()
        try:
            svc.delete_item(item_id)
            self._load()
        except Exception as e:
            QMessageBox.warning(self, "Cannot Delete", f"Item has existing transactions: {e}")
        finally:
            session.close()
