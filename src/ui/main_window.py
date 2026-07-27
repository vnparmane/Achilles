from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QStackedWidget,
    QWidget,
)

from src.database.models.user import User
from src.ui.sidebar import SidebarWidget
from src.utils.constants import APP_NAME, APP_VERSION


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
        from src.ui.masters.company_master import CompanyMasterWidget
        from src.ui.masters.godown_master import GodownMasterWidget
        from src.ui.masters.item_master import ItemMasterWidget
        from src.ui.masters.party_master import PartyMasterWidget
        from src.ui.masters.user_master import UserMasterWidget
        from src.ui.reports.gst_report import GSTReportWidget
        from src.ui.reports.ledger_report import LedgerReportWidget
        from src.ui.reports.movement_report import StockMovementReportWidget
        from src.ui.reports.register_report import RegisterReportWidget
        from src.ui.reports.stock_report import StockReportWidget
        from src.ui.transactions.invoice import SalesInvoiceWidget
        from src.ui.transactions.payment import PaymentEntryWidget
        from src.ui.transactions.purchase import PurchaseBillWidget
        from src.ui.transactions.stock_adjustment import StockAdjustmentWidget

        factories = {
            "party": PartyMasterWidget,
            "item": ItemMasterWidget,
            "godown": GodownMasterWidget,
            "company": CompanyMasterWidget,
            "users": UserMasterWidget,
            "purchase": lambda sf: PurchaseBillWidget(sf, self.current_user),
            "invoice": lambda sf: SalesInvoiceWidget(sf, self.current_user),
            "payment": lambda sf: PaymentEntryWidget(sf, self.current_user),
            "stock_adjustment": lambda sf: StockAdjustmentWidget(sf, self.current_user),
            "stock_report": StockReportWidget,
            "stock_movement": StockMovementReportWidget,
            "ledger": LedgerReportWidget,
            "gst_report": GSTReportWidget,
            "purchase_register": RegisterReportWidget,
            "sales_register": RegisterReportWidget,
        }
        cls = factories.get(nav_id)
        if cls is not None:
            return cls(self.session_factory)
        return None
