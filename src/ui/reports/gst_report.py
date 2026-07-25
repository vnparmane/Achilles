import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QLabel,
    QAbstractItemView, QFileDialog, QMessageBox, QDateEdit,
)
from PySide6.QtCore import Slot, QDate
from PySide6.QtGui import QFont

from src.services.report_service import ReportService
from src.reports.excel_generator import export_table_widget_to_excel


class GSTReportWidget(QWidget):
    def __init__(self, session_factory, parent=None):
        super().__init__(parent)
        self.session_factory = session_factory
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        header = QLabel("GST Summary")
        hf = QFont()
        hf.setPointSize(14)
        hf.setBold(True)
        header.setFont(hf)
        layout.addWidget(header)

        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("From:"))
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addYears(-1))
        toolbar.addWidget(self.date_from)
        toolbar.addWidget(QLabel("To:"))
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        toolbar.addWidget(self.date_to)
        self.btn_refresh = QPushButton("Refresh")
        self.btn_export = QPushButton("Export Excel")
        toolbar.addStretch()
        toolbar.addWidget(self.btn_export)
        toolbar.addWidget(self.btn_refresh)
        layout.addLayout(toolbar)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["GST Rate", "Taxable", "CGST", "SGST", "IGST"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table, 1)

        self.btn_refresh.clicked.connect(self._load)
        self.btn_export.clicked.connect(self._export)
        self._load()

    @Slot()
    def _export(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Excel", "gst_summary.xlsx", "Excel (*.xlsx)")
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
            data = svc.gst_summary(
                date_from=self.date_from.date().toString("yyyy-MM-dd"),
                date_to=self.date_to.date().toString("yyyy-MM-dd"),
            )
            self.table.setRowCount(len(data))
            cgst_t = sgst_t = igst_t = 0.0
            for row, d in enumerate(data):
                self.table.setItem(row, 0, QTableWidgetItem(f"{d['rate']}%"))
                self.table.setItem(row, 1, QTableWidgetItem(f"{d['taxable']:,.2f}"))
                self.table.setItem(row, 2, QTableWidgetItem(f"{d['cgst']:,.2f}"))
                self.table.setItem(row, 3, QTableWidgetItem(f"{d['sgst']:,.2f}"))
                self.table.setItem(row, 4, QTableWidgetItem(f"{d['igst']:,.2f}"))
                cgst_t += d["cgst"]
                sgst_t += d["sgst"]
                igst_t += d["igst"]

            row = self.table.rowCount()
            self.table.setRowCount(row + 1)
            self.table.setItem(row, 0, QTableWidgetItem("Total"))
            self.table.setItem(row, 1, QTableWidgetItem(""))
            self.table.setItem(row, 2, QTableWidgetItem(f"{cgst_t:,.2f}"))
            self.table.setItem(row, 3, QTableWidgetItem(f"{sgst_t:,.2f}"))
            self.table.setItem(row, 4, QTableWidgetItem(f"{igst_t:,.2f}"))
            for col in range(5):
                item = self.table.item(row, col)
                if item:
                    f = QFont()
                    f.setBold(True)
                    item.setFont(f)
        finally:
            session.close()
