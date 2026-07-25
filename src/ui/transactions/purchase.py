
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QLabel, QComboBox, QDoubleSpinBox,
    QMessageBox, QDateEdit, QTextEdit, QFrame, QFormLayout,
    QGroupBox, QAbstractItemView, QTabWidget,
)
from PySide6.QtCore import Qt, Slot, QDate
from PySide6.QtGui import QFont

from src.services.party_service import PartyService
from src.services.item_service import ItemService
from src.services.godown_service import GodownService
from src.services.purchase_service import PurchaseService
from src.services.company_service import CompanyService
from src.utils.gst_utils import calculate_gst


class PurchaseBillWidget(QWidget):
    def __init__(self, session_factory, current_user, parent=None):
        super().__init__(parent)
        self.session_factory = session_factory
        self.current_user = current_user
        self._items_data: list[dict] = []
        self._company_state_code: str | None = None

        self.tabs = QTabWidget()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.tabs)

        self._setup_form()
        self.tabs.addTab(self.form_tab, "New Bill")

        self._setup_list()
        self.tabs.addTab(self.list_tab, "Bill History")

    def _setup_form(self):
        self.form_tab = QWidget()
        layout = QVBoxLayout(self.form_tab)
        layout.setContentsMargins(16, 16, 16, 16)

        header = QLabel("New Purchase Bill")
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setBold(True)
        header.setFont(header_font)
        layout.addWidget(header)

        session = self.session_factory()
        try:
            company_svc = CompanyService(session)
            company = company_svc.get_company()
            self._company_state_code = company.state_code if company else None

            form = QFormLayout()
            form.setSpacing(6)

            self.date_edit = QDateEdit(QDate.currentDate())
            self.date_edit.setCalendarPopup(True)
            form.addRow("Date:", self.date_edit)

            party_svc = PartyService(session)
            self.vendor_combo = QComboBox()
            self.vendor_combo.addItem("-- Select Vendor --", None)
            for p in party_svc.get_all_parties("vendor"):
                self.vendor_combo.addItem(f"{p.code} - {p.name}", p.id)
            self.vendor_combo.currentIndexChanged.connect(self._recalc_totals)
            form.addRow("Vendor:", self.vendor_combo)

            godown_svc = GodownService(session)
            self.godown_combo = QComboBox()
            for g in godown_svc.get_all_godowns():
                self.godown_combo.addItem(f"{g.code} - {g.name}", g.id)
            form.addRow("Godown:", self.godown_combo)

            item_svc = ItemService(session)
            self.item_combo = QComboBox()
            self.item_combo.addItem("-- Select Item --", None)
            self._items_map: dict[int, dict] = {}
            for it in item_svc.get_all_items():
                self.item_combo.addItem(f"{it.code} - {it.name} [{it.unit}]", it.id)
                self._items_map[it.id] = {"name": f"{it.code} - {it.name}", "gst_rate": it.gst_rate}
            form.addRow("Item:", self.item_combo)
        finally:
            session.close()

        layout.addLayout(form)

        qty_rate_layout = QHBoxLayout()
        self.qty_spin = QDoubleSpinBox()
        self.qty_spin.setRange(0.001, 999999)
        self.qty_spin.setDecimals(3)
        self.qty_spin.setValue(1)
        qty_rate_layout.addWidget(QLabel("Qty:"))
        qty_rate_layout.addWidget(self.qty_spin)

        self.rate_spin = QDoubleSpinBox()
        self.rate_spin.setRange(0, 999999)
        self.rate_spin.setDecimals(2)
        self.rate_spin.setPrefix("₹ ")
        qty_rate_layout.addWidget(QLabel("Rate:"))
        qty_rate_layout.addWidget(self.rate_spin)

        self.btn_add_row = QPushButton("Add Item")
        qty_rate_layout.addWidget(self.btn_add_row)
        qty_rate_layout.addStretch()
        layout.addLayout(qty_rate_layout)

        self.items_table = QTableWidget()
        self.items_table.setColumnCount(6)
        self.items_table.setHorizontalHeaderLabels(
            ["Item", "Qty", "Rate", "Amount", "GST%", "Remove"]
        )
        self.items_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.items_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.items_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.items_table, 1)

        totals_group = QGroupBox()
        totals_layout = QFormLayout(totals_group)

        self.lbl_gross = QLabel("0.00")
        totals_layout.addRow("Gross Amount:", self.lbl_gross)
        self.discount_spin = QDoubleSpinBox()
        self.discount_spin.setRange(0, 999999)
        self.discount_spin.setDecimals(2)
        self.discount_spin.setPrefix("₹ ")
        self.discount_spin.valueChanged.connect(self._recalc_totals)
        totals_layout.addRow("Discount:", self.discount_spin)
        self.lbl_taxable = QLabel("0.00")
        totals_layout.addRow("Taxable:", self.lbl_taxable)
        self.lbl_cgst = QLabel("0.00")
        totals_layout.addRow("CGST:", self.lbl_cgst)
        self.lbl_sgst = QLabel("0.00")
        totals_layout.addRow("SGST:", self.lbl_sgst)
        self.lbl_igst = QLabel("0.00")
        totals_layout.addRow("IGST:", self.lbl_igst)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        totals_layout.addRow(sep)
        self.lbl_grand = QLabel("₹ 0.00")
        gf = QFont()
        gf.setBold(True)
        gf.setPointSize(12)
        self.lbl_grand.setFont(gf)
        totals_layout.addRow("Grand Total:", self.lbl_grand)
        layout.addWidget(totals_group)

        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Notes...")
        self.notes_edit.setMaximumHeight(60)
        layout.addWidget(self.notes_edit)

        self.btn_save = QPushButton("Save Purchase Bill")
        self.btn_save.setMinimumHeight(36)
        layout.addWidget(self.btn_save, alignment=Qt.AlignmentFlag.AlignRight)

        self.btn_add_row.clicked.connect(self._add_row)
        self.btn_save.clicked.connect(self._save)

    def _setup_list(self):
        self.list_tab = QWidget()
        layout = QVBoxLayout(self.list_tab)
        layout.setContentsMargins(16, 16, 16, 16)
        header = QLabel("Purchase Bills")
        hf = QFont()
        hf.setPointSize(14)
        hf.setBold(True)
        header.setFont(hf)
        layout.addWidget(header)
        self.lv_table = QTableWidget()
        self.lv_table.setColumnCount(5)
        self.lv_table.setHorizontalHeaderLabels(["Bill No", "Date", "Vendor", "Amount", "Status"])
        self.lv_table.horizontalHeader().setStretchLastSection(True)
        self.lv_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.lv_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.lv_table.setAlternatingRowColors(True)
        layout.addWidget(self.lv_table)
        self._load_list()

    def _load_list(self):
        session = self.session_factory()
        try:
            svc = PurchaseService(session)
            bills = svc.get_all_bills()
            self.lv_table.setRowCount(len(bills))
            for row, b in enumerate(bills):
                self.lv_table.setItem(row, 0, QTableWidgetItem(b.bill_no))
                self.lv_table.setItem(row, 1, QTableWidgetItem(b.bill_date))
                self.lv_table.setItem(row, 2, QTableWidgetItem(b.party.name if b.party else ""))
                self.lv_table.setItem(row, 3, QTableWidgetItem(f"₹{b.grand_total:,.2f}"))
                self.lv_table.setItem(row, 4, QTableWidgetItem(b.status))
        finally:
            session.close()

    @Slot()
    def _add_row(self):
        item_id = self.item_combo.currentData()
        if item_id is None:
            QMessageBox.warning(self, "Error", "Please select an item.")
            return
        info = self._items_map.get(item_id)
        if info is None:
            return
        self._items_data.append({
            "item_id": item_id,
            "item_name": info["name"],
            "quantity": self.qty_spin.value(),
            "rate": self.rate_spin.value(),
            "gst_rate": info["gst_rate"],
        })
        self._refresh_table()

    def _refresh_table(self):
        self.items_table.setRowCount(len(self._items_data))
        for row, d in enumerate(self._items_data):
            self.items_table.setItem(row, 0, QTableWidgetItem(d["item_name"]))
            self.items_table.setItem(row, 1, QTableWidgetItem(str(d["quantity"])))
            self.items_table.setItem(row, 2, QTableWidgetItem(f"{d['rate']:.2f}"))
            amt = round(d["quantity"] * d["rate"], 2)
            self.items_table.setItem(row, 3, QTableWidgetItem(f"{amt:.2f}"))
            self.items_table.setItem(row, 4, QTableWidgetItem(f"{d['gst_rate']}%"))
            btn = QPushButton("✕")
            btn.clicked.connect(lambda checked, r=row: self._remove_row(r))
            self.items_table.setCellWidget(row, 5, btn)
        self._recalc_totals()

    def _remove_row(self, row):
        if 0 <= row < len(self._items_data):
            self._items_data.pop(row)
            self._refresh_table()

    def _get_vendor_state_code(self) -> str | None:
        idx = self.vendor_combo.currentIndex()
        if idx <= 0:
            return None
        session = self.session_factory()
        try:
            svc = PartyService(session)
            party = svc.get_party_by_id(self.vendor_combo.currentData())
            return party.state_code if party else None
        finally:
            session.close()

    def _recalc_totals(self):
        gross = sum(d["quantity"] * d["rate"] for d in self._items_data)
        discount = self.discount_spin.value()
        taxable = round(gross - discount, 2)
        self.lbl_gross.setText(f"{gross:,.2f}")
        self.lbl_taxable.setText(f"{taxable:,.2f}")

        vendor_state = self._get_vendor_state_code()
        cgst = sgst = igst = 0.0
        for d in self._items_data:
            amt = round(d["quantity"] * d["rate"], 2)
            item_taxable = amt
            tax = calculate_gst(item_taxable, d["gst_rate"], self._company_state_code, vendor_state)
            cgst += tax["cgst"]
            sgst += tax["sgst"]
            igst += tax["igst"]

        self.lbl_cgst.setText(f"{cgst:,.2f}")
        self.lbl_sgst.setText(f"{sgst:,.2f}")
        self.lbl_igst.setText(f"{igst:,.2f}")
        grand = round(taxable + cgst + sgst + igst, 2)
        self.lbl_grand.setText(f"₹ {grand:,.2f}")

    def _save(self):
        vendor_id = self.vendor_combo.currentData()
        godown_id = self.godown_combo.currentData()
        if vendor_id is None:
            QMessageBox.warning(self, "Error", "Please select a vendor.")
            return
        if godown_id is None:
            QMessageBox.warning(self, "Error", "Please select a godown.")
            return
        if not self._items_data:
            QMessageBox.warning(self, "Error", "Please add at least one item.")
            return

        session = self.session_factory()
        try:
            svc = PurchaseService(session)
            svc.create_purchase_bill(
                party_id=vendor_id,
                godown_id=godown_id,
                items=self._items_data,
                bill_date=self.date_edit.date().toString("yyyy-MM-dd"),
                discount_amount=self.discount_spin.value(),
                notes=self.notes_edit.toPlainText().strip(),
                created_by=self.current_user.id,
            )
            QMessageBox.information(self, "Success", "Purchase bill saved!")
            self._items_data.clear()
            self._refresh_table()
            self.discount_spin.setValue(0)
            self.notes_edit.clear()
            self._load_list()
            self.tabs.setCurrentIndex(1)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed: {e}")
            session.rollback()
        finally:
            session.close()
