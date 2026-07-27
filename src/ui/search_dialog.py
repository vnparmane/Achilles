from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
)

from src.services.item_service import ItemService
from src.services.party_service import PartyService


class SearchDialog(QDialog):
    def __init__(self, session_factory, parent=None):
        super().__init__(parent)
        self.session_factory = session_factory
        self.setWindowTitle("Search")
        self.setMinimumWidth(500)
        self.setMaximumWidth(500)
        self.setModal(True)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Dialog)
        self.setStyleSheet("""
            QDialog { background: white; border-radius: 8px; }
            QLineEdit {
                border: 2px solid #3498db;
                border-radius: 6px;
                padding: 10px 14px;
                font-size: 15px;
                background: #f8f9fa;
            }
            QListWidget {
                border: none;
                font-size: 13px;
                outline: none;
            }
            QListWidget::item {
                padding: 10px 14px;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background: #eef2f7;
                color: #2c3e50;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search customers, invoices, items, parties...")
        self.search_input.textChanged.connect(self._search)
        layout.addWidget(self.search_input)

        self.results_list = QListWidget()
        self.results_list.setMinimumHeight(300)
        self.results_list.itemClicked.connect(self._on_select)
        layout.addWidget(self.results_list)

        hint = QLabel("Enter to select · Esc to close")
        hint.setStyleSheet("color: #95a5a6; font-size: 11px;")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint)

        self._all_results: list[tuple[str, str]] = []

        QTimer.singleShot(100, self.search_input.setFocus)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
        elif event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            item = self.results_list.currentItem()
            if item:
                self._on_select(item)
        elif event.key() == Qt.Key.Key_Down:
            row = self.results_list.currentRow()
            self.results_list.setCurrentRow(min(row + 1, self.results_list.count() - 1))
        elif event.key() == Qt.Key.Key_Up:
            row = self.results_list.currentRow()
            self.results_list.setCurrentRow(max(row - 1, 0))
        else:
            super().keyPressEvent(event)

    def _search(self, text: str):
        self.results_list.clear()
        self._all_results = []
        if len(text.strip()) < 2:
            return

        q = text.lower()
        session = self.session_factory()
        try:
            party_svc = PartyService(session)
            for p in party_svc.get_all_parties():
                if q in p.name.lower() or q in (p.gstin or "").lower():
                    self._all_results.append(("party", p.id))

            item_svc = ItemService(session)
            for it in item_svc.get_all_items():
                if q in it.name.lower() or q in (it.code or "").lower():
                    self._all_results.append(("item", it.id))

            from src.services.godown_service import GodownService
            gdn_svc = GodownService(session)
            for g in gdn_svc.get_all_godowns():
                if q in g.name.lower():
                    self._all_results.append(("godown", g.id))
        finally:
            session.close()

        seen = set()
        for entry_type, eid in self._all_results:
            key = (entry_type, eid)
            if key in seen:
                continue
            seen.add(key)
            icons = {"party": "👤", "item": "📦", "godown": "🏪"}
            icon = icons.get(entry_type, "📄")
            label = f"{icon}  {entry_type.title()} #{eid}"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, (entry_type, eid))
            self.results_list.addItem(item)

    def _on_select(self, item):
        entry_type, _ = item.data(Qt.ItemDataRole.UserRole)
        nav_map = {"party": "party", "item": "item", "godown": "godown"}
        nav_id = nav_map.get(entry_type, entry_type)
        self.accept()
        parent = self.parent()
        if parent and hasattr(parent, "_on_navigate"):
            parent._on_navigate(nav_id)
