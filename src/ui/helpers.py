import os

from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDateEdit, QFileDialog, QHBoxLayout, QLabel,
    QMessageBox, QPushButton, QVBoxLayout, QWidget,
)

from src.reports.excel_generator import export_table_widget_to_excel


def make_header(text: str, size: int = 14) -> QLabel:
    lbl = QLabel(text)
    f = QFont()
    f.setPointSize(size)
    f.setBold(True)
    lbl.setFont(f)
    return lbl


def export_dialog(parent, table, default_name: str):
    path, _ = QFileDialog.getSaveFileName(parent, "Export Excel", default_name, "Excel (*.xlsx)")
    if not path:
        return
    try:
        export_table_widget_to_excel(table, path)
        QMessageBox.information(parent, "Exported", f"Saved to {path}")
        os.startfile(path)
    except Exception as e:
        QMessageBox.critical(parent, "Error", f"Export failed: {e}")


def make_date_range(default_months_back: int = 12):
    date_from = QDateEdit()
    date_from.setCalendarPopup(True)
    date_from.setDate(QDate.currentDate().addMonths(-default_months_back))
    date_to = QDateEdit()
    date_to.setCalendarPopup(True)
    date_to.setDate(QDate.currentDate())
    return date_from, date_to


def form_section(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(
        "font-weight: bold; font-size: 12px; color: #3498db; "
        "padding: 4px 0; margin-top: 8px; border-bottom: 1px solid #ecf0f1;"
    )
    lbl.setMinimumHeight(28)
    return lbl


def setup_table_sort(table):
    table.setSortingEnabled(True)


def make_table_filter(table, search_input):
    def on_filter(text):
        q = text.lower()
        for row in range(table.rowCount()):
            visible = False
            for col in range(table.columnCount()):
                item = table.item(row, col)
                if item and q in item.text().lower():
                    visible = True
                    break
            table.setRowHidden(row, not visible)

    search_input.textChanged.connect(on_filter)


STATUS_COLORS = {
    "paid": "#27ae60",
    "active": "#27ae60",
    "pending": "#e67e22",
    "overdue": "#e74c3c",
    "cancelled": "#95a5a6",
    "inactive": "#95a5a6",
    "draft": "#95a5a6",
}


def status_badge(text: str) -> QLabel:
    color = STATUS_COLORS.get(text.lower(), "#3498db")
    lbl = QLabel(text)
    lbl.setStyleSheet(
        f"background: {color}20; color: {color}; "
        f"padding: 2px 10px; border-radius: 8px; "
        f"font-weight: bold; font-size: 11px;"
    )
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return lbl


class EmptyState(QWidget):
    def __init__(self, message: str, action_text: str = "", on_action=None, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(12)

        icon = QLabel("📋")
        icon.setStyleSheet("font-size: 48px;")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon)

        msg = QLabel(message)
        msg.setStyleSheet("font-size: 14px; color: #95a5a6;")
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg.setWordWrap(True)
        layout.addWidget(msg)

        if action_text and on_action:
            btn = QPushButton(action_text)
            btn.setFixedWidth(200)
            btn.clicked.connect(on_action)
            btn_layout = QHBoxLayout()
            btn_layout.addStretch()
            btn_layout.addWidget(btn)
            btn_layout.addStretch()
            layout.addLayout(btn_layout)

        self.setMinimumHeight(200)
