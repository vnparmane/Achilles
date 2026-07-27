from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.database.models.user import User
from src.utils.constants import APP_NAME, APP_VERSION, UserRole

NAV_ITEMS = [
    ("MASTERS", None, None),
    ("Party", "party", None),
    ("Item", "item", None),
    ("Godown", "godown", None),
    ("Company", "company", None),
    ("", None, None),
    ("TRANSACTIONS", None, None),
    ("Purchase Bill", "purchase", None),
    ("Sales Invoice", "invoice", None),
    ("Payment", "payment", None),
    ("Stock Adjustment", "stock_adjustment", None),
    ("", None, None),
    ("REPORTS", None, None),
    ("Stock Report", "stock_report", None),
    ("Stock Movement", "stock_movement", None),
    ("Party Ledger", "ledger", None),
    ("GST Report", "gst_report", None),
    ("Purchase Register", "purchase_register", None),
    ("Sales Register", "sales_register", None),
    ("", None, None),
    ("ADMIN", None, None),
    ("Users", "users", UserRole.ADMIN),
]


class SidebarWidget(QWidget):
    navigation_changed = Signal(str)

    def __init__(self, current_user: User, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self.setFixedWidth(220)
        self.setObjectName("sidebar")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        app_label = QLabel(f"{APP_NAME}")
        app_label.setObjectName("appTitle")
        app_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        app_label.setFixedHeight(56)
        app_font = QFont()
        app_font.setPointSize(14)
        app_font.setBold(True)
        app_label.setFont(app_font)
        layout.addWidget(app_label)

        version_label = QLabel(f"v{APP_VERSION}")
        version_label.setObjectName("versionLabel")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setFixedHeight(20)
        layout.addWidget(version_label)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setObjectName("sidebarSeparator")
        sep.setFixedHeight(1)
        layout.addWidget(sep)

        self.list_widget = QListWidget()
        self.list_widget.setObjectName("navList")
        self.list_widget.setFrameShape(QFrame.Shape.NoFrame)
        self.list_widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._populate()
        self.list_widget.currentRowChanged.connect(self._on_row_changed)
        layout.addWidget(self.list_widget, 1)

        bottom_sep = QFrame()
        bottom_sep.setFrameShape(QFrame.Shape.HLine)
        bottom_sep.setObjectName("sidebarSeparator")
        layout.addWidget(bottom_sep)

        user_label = QLabel(current_user.display_name)
        user_label.setObjectName("userLabel")
        user_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        user_label.setFixedHeight(44)
        layout.addWidget(user_label)

    def _populate(self):
        for text, nav_id, min_role in NAV_ITEMS:
            if min_role is not None and self.current_user.role != min_role:
                continue
            item = QListWidgetItem()
            if nav_id is None:
                if text == "":
                    item.setFlags(Qt.ItemFlag.NoItemFlags)
                else:
                    item.setText(f"  {text}")
                    item.setFlags(Qt.ItemFlag.NoItemFlags)
                    font = QFont()
                    font.setPointSize(9)
                    font.setBold(True)
                    item.setFont(font)
            else:
                item.setText(f"    {text}")
                item.setData(Qt.ItemDataRole.UserRole, nav_id)
            self.list_widget.addItem(item)

    def _on_row_changed(self, row):
        item = self.list_widget.item(row)
        if item is None:
            return
        nav_id = item.data(Qt.ItemDataRole.UserRole)
        if nav_id is not None:
            self.navigation_changed.emit(nav_id)
