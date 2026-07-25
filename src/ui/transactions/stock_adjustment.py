from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QPushButton,
    QComboBox, QDoubleSpinBox, QMessageBox, QLabel,
    QLineEdit, QDateEdit,
)
from PySide6.QtCore import Qt, Slot, QDate
from PySide6.QtGui import QFont

from src.services.item_service import ItemService
from src.services.godown_service import GodownService
from src.services.stock_service import StockService


class StockAdjustmentWidget(QWidget):
    def __init__(self, session_factory, current_user, parent=None):
        super().__init__(parent)
        self.session_factory = session_factory
        self.current_user = current_user
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        header = QLabel("Stock Adjustment")
        hf = QFont()
        hf.setPointSize(14)
        hf.setBold(True)
        header.setFont(hf)
        layout.addWidget(header)

        form = QFormLayout()
        form.setSpacing(8)

        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        form.addRow("Date:", self.date_edit)

        session = self.session_factory()
        try:
            item_svc = ItemService(session)
            self.item_combo = QComboBox()
            self.item_combo.addItem("-- Select Item --", None)
            for it in item_svc.get_all_items():
                self.item_combo.addItem(f"{it.code} - {it.name} [{it.unit}]", it.id)
            form.addRow("Item *:", self.item_combo)

            godown_svc = GodownService(session)
            self.godown_combo = QComboBox()
            for g in godown_svc.get_all_godowns():
                self.godown_combo.addItem(f"{g.code} - {g.name}", g.id)
            form.addRow("Godown *:", self.godown_combo)
        finally:
            session.close()

        self.type_combo = QComboBox()
        self.type_combo.addItem("Plus (Add Stock)", "adjustment_plus")
        self.type_combo.addItem("Minus (Remove Stock)", "adjustment_minus")
        form.addRow("Type:", self.type_combo)

        self.qty_spin = QDoubleSpinBox()
        self.qty_spin.setRange(0.001, 999999)
        self.qty_spin.setDecimals(3)
        self.qty_spin.setValue(1)
        form.addRow("Quantity *:", self.qty_spin)

        self.rate_spin = QDoubleSpinBox()
        self.rate_spin.setRange(0, 999999)
        self.rate_spin.setDecimals(2)
        self.rate_spin.setPrefix("₹ ")
        form.addRow("Rate:", self.rate_spin)

        self.notes_edit = QLineEdit()
        self.notes_edit.setPlaceholderText("Reason for adjustment *")
        form.addRow("Reason *:", self.notes_edit)

        layout.addLayout(form)

        self.btn_save = QPushButton("Record Adjustment")
        self.btn_save.setMinimumHeight(36)
        layout.addWidget(self.btn_save, alignment=Qt.AlignmentFlag.AlignRight)
        layout.addStretch()

        self.btn_save.clicked.connect(self._save)

    @Slot()
    def _save(self):
        item_id = self.item_combo.currentData()
        godown_id = self.godown_combo.currentData()
        reason = self.notes_edit.text().strip()
        if item_id is None:
            QMessageBox.warning(self, "Error", "Please select an item.")
            return
        if godown_id is None:
            QMessageBox.warning(self, "Error", "Please select a godown.")
            return
        if not reason:
            QMessageBox.warning(self, "Error", "Please enter a reason.")
            return

        txn_type = self.type_combo.currentData()
        qty = self.qty_spin.value()
        if txn_type == "adjustment_minus":
            qty = -qty

        session = self.session_factory()
        try:
            svc = StockService(session)
            svc.record_transaction(
                transaction_type=txn_type,
                item_id=item_id,
                godown_id=godown_id,
                quantity=qty,
                rate=self.rate_spin.value(),
                amount=round(qty * self.rate_spin.value(), 2),
                transaction_date=self.date_edit.date().toString("yyyy-MM-dd"),
                notes=reason,
                created_by=self.current_user.id,
            )
            session.commit()
            QMessageBox.information(self, "Success", "Stock adjustment recorded.")
            self.qty_spin.setValue(1)
            self.rate_spin.setValue(0)
            self.notes_edit.clear()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed: {e}")
            session.rollback()
        finally:
            session.close()
