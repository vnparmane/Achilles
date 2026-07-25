import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QLabel,
    QAbstractItemView, QFileDialog, QMessageBox,
)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QFont

from src.services.report_service import ReportService
from src.reports.excel_generator import export_table_widget_to_excel


class StockReportWidget(QWidget):
    def __init__(self, session_factory, parent=None):
        super().__init__(parent)
        self.session_factory = session_factory
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        header = QLabel("Stock Balance Report")
        hf = QFont()
        hf.setPointSize(14)
        hf.setBold(True)
        header.setFont(hf)
        layout.addWidget(header)

        toolbar = QHBoxLayout()
        self.btn_refresh = QPushButton("Refresh")
        self.btn_export = QPushButton("Export Excel")
        toolbar.addStretch()
        toolbar.addWidget(self.btn_export)
        toolbar.addWidget(self.btn_refresh)
        layout.addLayout(toolbar)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Code", "Item", "Unit", "Opening", "Balance"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table, 1)

        self.btn_refresh.clicked.connect(self._load)
        self.btn_export.clicked.connect(self._export)
        self._load()

    @Slot()
    def _export(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Excel", "stock_balance.xlsx", "Excel (*.xlsx)")
        if path:
            try:
                export_table_widget_to_excel(self.table, path)
                QMessageBox.information(self, "Exported", f"Saved to {path}")
                os.startfile(path)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Export failed: {e}")

    @Slot()
    def _load(self):
        session = self.session_factory()
        try:
            svc = ReportService(session)
            data = svc.stock_balance()
            self.table.setRowCount(len(data))
            for row, d in enumerate(data):
                self.table.setItem(row, 0, QTableWidgetItem(d["code"]))
                self.table.setItem(row, 1, QTableWidgetItem(d["name"]))
                self.table.setItem(row, 2, QTableWidgetItem(d["unit"]))
                self.table.setItem(row, 3, QTableWidgetItem(str(d["opening"])))
                bal = d["balance"]
                item = QTableWidgetItem(f"{bal:.3f}")
                item.setForeground(Qt.GlobalColor.darkGreen if bal > 0 else Qt.GlobalColor.red)
                self.table.setItem(row, 4, item)
        finally:
            session.close()
