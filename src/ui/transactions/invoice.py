import os
import tempfile

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QLabel, QComboBox, QDoubleSpinBox,
    QLineEdit, QMessageBox, QDateEdit, QTextEdit, QFrame, QFormLayout,
    QGroupBox, QAbstractItemView, QTabWidget,
)
from PySide6.QtCore import Qt, Slot, QDate
from PySide6.QtGui import QFont

from src.services.party_service import PartyService
from src.services.item_service import ItemService
from src.services.godown_service import GodownService
from src.services.invoice_service import InvoiceService
from src.services.company_service import CompanyService
from src.reports.pdf_generator import generate_invoice_pdf
from src.utils.gst_utils import calculate_gst


class SalesInvoiceWidget(QWidget):
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
        self.tabs.addTab(self.form_tab, "New Invoice")

        self._setup_list()
        self.tabs.addTab(self.list_tab, "Invoice History")

    def _setup_form(self):
        self.form_tab = QWidget()
        layout = QVBoxLayout(self.form_tab)
        layout.setContentsMargins(16, 16, 16, 16)

        header = QLabel("New Sales Invoice")
        hf = QFont()
        hf.setPointSize(14)
        hf.setBold(True)
        header.setFont(hf)
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
            self.customer_combo = QComboBox()
            self.customer_combo.addItem("-- Select Customer --", None)
            for p in party_svc.get_all_parties("customer"):
                self.customer_combo.addItem(f"{p.code} - {p.name}", p.id)
            self.customer_combo.currentIndexChanged.connect(self._recalc_totals)
            form.addRow("Customer:", self.customer_combo)

            godown_svc = GodownService(session)
            self.godown_combo = QComboBox()
            for g in godown_svc.get_all_godowns():
                self.godown_combo.addItem(f"{g.code} - {g.name}", g.id)
            form.addRow("Godown:", self.godown_combo)

            self.transport_edit = QLineEdit()
            self.transport_edit.setPlaceholderText("Transport name / vehicle no")
            form.addRow("Transport:", self.transport_edit)

            item_svc = ItemService(session)
            self.item_combo = QComboBox()
            self.item_combo.addItem("-- Select Item --", None)
            self._items_map: dict[int, dict] = {}
            for it in item_svc.get_all_items():
                self.item_combo.addItem(f"{it.code} - {it.name} [{it.unit}]", it.id)
                self._items_map[it.id] = {
                    "name": f"{it.code} - {it.name}",
                    "gst_rate": it.gst_rate,
                    "hsn_code": it.hsn_code or "",
                }
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
        self.notes_edit.setPlaceholderText("Terms / notes...")
        self.notes_edit.setMaximumHeight(60)
        layout.addWidget(self.notes_edit)

        self.btn_save = QPushButton("Save Invoice")
        self.btn_save.setMinimumHeight(36)
        layout.addWidget(self.btn_save, alignment=Qt.AlignmentFlag.AlignRight)

        self.btn_add_row.clicked.connect(self._add_row)
        self.btn_save.clicked.connect(self._save)

    def _generate_and_open_pdf(self, invoice_id: int):
        session = self.session_factory()
        try:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            generate_invoice_pdf(session, invoice_id, tmp.name)
            tmp.close()
            os.startfile(tmp.name)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate PDF: {e}")
        finally:
            session.close()

    @Slot()
    def _print_pdf(self):
        row = self.lv_table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Select", "Please select an invoice.")
            return
        invoice_id = self.lv_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        self._generate_and_open_pdf(invoice_id)

    def _setup_list(self):
        self.list_tab = QWidget()
        layout = QVBoxLayout(self.list_tab)
        layout.setContentsMargins(16, 16, 16, 16)
        header = QLabel("Sales Invoices")
        hf = QFont()
        hf.setPointSize(14)
        hf.setBold(True)
        header.setFont(hf)
        layout.addWidget(header)

        toolbar = QHBoxLayout()
        self.btn_print = QPushButton("Print PDF")
        self.btn_refresh_list = QPushButton("Refresh")
        toolbar.addWidget(self.btn_print)
        toolbar.addStretch()
        toolbar.addWidget(self.btn_refresh_list)
        layout.addLayout(toolbar)

        self.lv_table = QTableWidget()
        self.lv_table.setColumnCount(5)
        self.lv_table.setHorizontalHeaderLabels(["Invoice No", "Date", "Customer", "Amount", "Status"])
        self.lv_table.horizontalHeader().setStretchLastSection(True)
        self.lv_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.lv_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.lv_table.setAlternatingRowColors(True)
        layout.addWidget(self.lv_table)

        self.btn_print.clicked.connect(self._print_pdf)
        self.btn_refresh_list.clicked.connect(self._load_list)
        self._load_list()

    def _load_list(self):
        session = self.session_factory()
        try:
            svc = InvoiceService(session)
            invoices = svc.get_all_invoices()
            self.lv_table.setRowCount(len(invoices))
            for row, inv in enumerate(invoices):
                item = QTableWidgetItem(inv.invoice_no)
                item.setData(Qt.ItemDataRole.UserRole, inv.id)
                self.lv_table.setItem(row, 0, item)
                self.lv_table.setItem(row, 1, QTableWidgetItem(inv.invoice_date))
                self.lv_table.setItem(row, 2, QTableWidgetItem(inv.party.name if inv.party else ""))
                self.lv_table.setItem(row, 3, QTableWidgetItem(f"₹{inv.grand_total:,.2f}"))
                self.lv_table.setItem(row, 4, QTableWidgetItem(inv.status))
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
            "hsn_code": info["hsn_code"],
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

    def _get_customer_state_code(self) -> str | None:
        idx = self.customer_combo.currentIndex()
        if idx <= 0:
            return None
        session = self.session_factory()
        try:
            svc = PartyService(session)
            party = svc.get_party_by_id(self.customer_combo.currentData())
            return party.state_code if party else None
        finally:
            session.close()

    def _recalc_totals(self):
        gross = sum(d["quantity"] * d["rate"] for d in self._items_data)
        discount = self.discount_spin.value()
        taxable = round(gross - discount, 2)
        self.lbl_gross.setText(f"{gross:,.2f}")
        self.lbl_taxable.setText(f"{taxable:,.2f}")

        customer_state = self._get_customer_state_code()
        cgst = sgst = igst = 0.0
        for d in self._items_data:
            amt = round(d["quantity"] * d["rate"], 2)
            tax = calculate_gst(amt, d["gst_rate"], self._company_state_code, customer_state)
            cgst += tax["cgst"]
            sgst += tax["sgst"]
            igst += tax["igst"]

        self.lbl_cgst.setText(f"{cgst:,.2f}")
        self.lbl_sgst.setText(f"{sgst:,.2f}")
        self.lbl_igst.setText(f"{igst:,.2f}")
        grand = round(taxable + cgst + sgst + igst, 2)
        self.lbl_grand.setText(f"₹ {grand:,.2f}")

    def _save(self):
        customer_id = self.customer_combo.currentData()
        godown_id = self.godown_combo.currentData()
        if customer_id is None:
            QMessageBox.warning(self, "Error", "Please select a customer.")
            return
        if godown_id is None:
            QMessageBox.warning(self, "Error", "Please select a godown.")
            return
        if not self._items_data:
            QMessageBox.warning(self, "Error", "Please add at least one item.")
            return

        session = self.session_factory()
        try:
            svc = InvoiceService(session)
            invoice = svc.create_invoice(
                party_id=customer_id,
                godown_id=godown_id,
                items=self._items_data,
                invoice_date=self.date_edit.date().toString("yyyy-MM-dd"),
                discount_amount=self.discount_spin.value(),
                transport=self.transport_edit.text().strip() or None,
                notes=self.notes_edit.toPlainText().strip() or None,
                created_by=self.current_user.id,
            )
            self._load_list()
            reply = QMessageBox.question(
                self, "Print", "Invoice saved. Print PDF?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._generate_and_open_pdf(invoice.id)
            self._items_data.clear()
            self._refresh_table()
            self.discount_spin.setValue(0)
            self.notes_edit.clear()
            self.tabs.setCurrentIndex(1)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed: {e}")
            session.rollback()
        finally:
            session.close()
