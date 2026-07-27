from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.services.item_service import ItemService
from src.services.report_service import ReportService
from src.ui.helpers import export_dialog, make_header


class StockMovementReportWidget(QWidget):
    def __init__(self, session_factory, parent=None):
        super().__init__(parent)
        self.session_factory = session_factory
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        layout.addWidget(make_header("Stock Movement Report"))

        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("Item:"))
        self.item_combo = QComboBox()
        self.item_combo.addItem("-- All Items --", None)
        session = self.session_factory()
        try:
            svc = ItemService(session)
            for it in svc.get_all_items():
                self.item_combo.addItem(f"{it.code} - {it.name}", it.id)
        finally:
            session.close()
        toolbar.addWidget(self.item_combo)

        self.btn_refresh = QPushButton("Refresh")
        self.btn_export = QPushButton("Export Excel")
        toolbar.addStretch()
        toolbar.addWidget(self.btn_export)
        toolbar.addWidget(self.btn_refresh)
        layout.addLayout(toolbar)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(
            ["Date", "Type", "Item", "Godown", "Qty", "Rate", "Amount", "Party"]
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table, 1)

        self.btn_refresh.clicked.connect(self._load)
        self.btn_export.clicked.connect(self._export)
        self.item_combo.currentIndexChanged.connect(self._load)
        self._load()

    @Slot()
    def _export(self):
        export_dialog(self, self.table, "stock_movement.xlsx")

    @Slot()
    def _load(self):
        session = self.session_factory()
        try:
            svc = ReportService(session)
            data = svc.stock_movement(item_id=self.item_combo.currentData())
            self.table.setRowCount(len(data))
            for row, d in enumerate(data):
                self.table.setItem(row, 0, QTableWidgetItem(d["date"]))
                self.table.setItem(row, 1, QTableWidgetItem(d["type"]))
                self.table.setItem(row, 2, QTableWidgetItem(d["item"]))
                self.table.setItem(row, 3, QTableWidgetItem(d["godown"]))
                qty = d["qty"]
                qty_item = QTableWidgetItem(f"{qty:.3f}")
                qty_item.setForeground(Qt.GlobalColor.darkGreen if qty > 0 else Qt.GlobalColor.red)
                self.table.setItem(row, 4, qty_item)
                self.table.setItem(row, 5, QTableWidgetItem(f"{d['rate']:.2f}"))
                self.table.setItem(row, 6, QTableWidgetItem(f"{d['amount']:,.2f}"))
                self.table.setItem(row, 7, QTableWidgetItem(d["party"]))
        finally:
            session.close()
