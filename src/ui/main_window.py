from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QListWidget, QListWidgetItem, QStackedWidget, QLabel,
    QFrame,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

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
    ("", None, None),
    ("REPORTS", None, None),
    ("Stock Report", "stock_report", None),
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


class MainWindow(QMainWindow):
    def __init__(self, session_factory, current_user: User, parent=None):
        super().__init__(parent)
        self.session_factory = session_factory
        self.current_user = current_user
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.resize(1200, 800)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.sidebar = SidebarWidget(current_user)
        layout.addWidget(self.sidebar)

        self.content_stack = QStackedWidget()
        self.content_stack.setObjectName("contentArea")
        layout.addWidget(self.content_stack, 1)

        from src.ui.dashboard import DashboardWidget
        self.dashboard = DashboardWidget(session_factory)
        self.dashboard.navigate_to.connect(self._on_navigate)
        self.dashboard.nav_id = "dashboard"
        self.content_stack.addWidget(self.dashboard)
        self.content_stack.setCurrentWidget(self.dashboard)

        self.sidebar.navigation_changed.connect(self._on_navigate)

    def _on_navigate(self, nav_id: str):
        for i in range(self.content_stack.count()):
            widget = self.content_stack.widget(i)
            if hasattr(widget, "nav_id") and widget.nav_id == nav_id:
                self.content_stack.setCurrentWidget(widget)
                return

        widget = self._create_widget(nav_id)
        if widget is not None:
            widget.nav_id = nav_id
            self.content_stack.addWidget(widget)
            self.content_stack.setCurrentWidget(widget)

    def _create_widget(self, nav_id: str):
        from src.ui.masters.party_master import PartyMasterWidget
        from src.ui.masters.item_master import ItemMasterWidget
        from src.ui.masters.godown_master import GodownMasterWidget
        from src.ui.transactions.purchase import PurchaseBillWidget
        from src.ui.transactions.invoice import SalesInvoiceWidget
        from src.ui.transactions.payment import PaymentEntryWidget
        from src.ui.reports.stock_report import StockReportWidget
        from src.ui.reports.ledger_report import LedgerReportWidget
        from src.ui.reports.gst_report import GSTReportWidget
        from src.ui.reports.register_report import RegisterReportWidget

        factories = {
            "party": PartyMasterWidget,
            "item": ItemMasterWidget,
            "godown": GodownMasterWidget,
            "purchase": lambda sf: PurchaseBillWidget(sf, self.current_user),
            "invoice": lambda sf: SalesInvoiceWidget(sf, self.current_user),
            "payment": lambda sf: PaymentEntryWidget(sf, self.current_user),
            "stock_report": StockReportWidget,
            "ledger": LedgerReportWidget,
            "gst_report": GSTReportWidget,
            "purchase_register": RegisterReportWidget,
            "sales_register": RegisterReportWidget,
        }
        cls = factories.get(nav_id)
        if cls is not None:
            return cls(self.session_factory)
        return None
