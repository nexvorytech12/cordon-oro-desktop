from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox, QDoubleSpinBox, QFormLayout, QHBoxLayout, QLabel, QLineEdit,
    QMessageBox, QPushButton, QSpinBox, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from services.supabase_service import SupabaseService
from utils.formatters import money


class SalesView(QWidget):
    def __init__(self, service: SupabaseService):
        super().__init__(objectName="page")
        self.service, self.items = service, []
        layout = QVBoxLayout(self); layout.setContentsMargins(26, 22, 26, 22)
        title = QLabel("Punto de venta y caja"); title.setObjectName("heading"); layout.addWidget(title)
        form = QHBoxLayout()
        self.customer = QLineEdit(); self.customer.setPlaceholderText("ID cliente (opcional)"); form.addWidget(self.customer)
        self.cash_register = QLineEdit(); self.cash_register.setPlaceholderText("ID caja abierta"); form.addWidget(self.cash_register)
        self.variant = QLineEdit(); self.variant.setPlaceholderText("ID variante / código"); form.addWidget(self.variant)
        self.quantity = QSpinBox(); self.quantity.setRange(1, 100000); form.addWidget(self.quantity)
        self.price = QDoubleSpinBox(); self.price.setRange(0, 1000000); self.price.setPrefix("S/ "); form.addWidget(self.price)
        add = QPushButton("Agregar", objectName="gold"); add.clicked.connect(self._add); form.addWidget(add)
        layout.addLayout(form)
        self.grid = QTableWidget(0, 5); self.grid.setHorizontalHeaderLabels(["Variante", "Descripción", "Cantidad", "Precio", "Importe"])
        self.grid.horizontalHeader().setStretchLastSection(True); layout.addWidget(self.grid)
        footer = QHBoxLayout()
        remove = QPushButton("Quitar línea", objectName="danger"); remove.clicked.connect(self._remove); footer.addWidget(remove)
        footer.addStretch()
        footer.addWidget(QLabel("Descuento")); self.discount = QDoubleSpinBox(); self.discount.setPrefix("S/ "); self.discount.setMaximum(1000000); self.discount.valueChanged.connect(self._totals); footer.addWidget(self.discount)
        footer.addWidget(QLabel("Forma de pago")); self.method = QComboBox(); self.method.addItems(["efectivo", "yape", "plin", "transferencia", "tarjeta"]); footer.addWidget(self.method)
        footer.addWidget(QLabel("Pago")); self.payment = QDoubleSpinBox(); self.payment.setPrefix("S/ "); self.payment.setMaximum(10000000); footer.addWidget(self.payment)
        self.total = QLabel("S/ 0.00"); self.total.setObjectName("metric"); footer.addWidget(self.total)
        checkout = QPushButton("COBRAR", objectName="gold"); checkout.clicked.connect(self._checkout); footer.addWidget(checkout)
        layout.addLayout(footer)

    def _add(self) -> None:
        variant = self.variant.text().strip()
        if not variant: QMessageBox.warning(self, "Falta producto", "Ingrese el ID de la variante."); return
        self.items.append({"variant_id": variant, "description": variant, "quantity": self.quantity.value(), "unit_price": self.price.value()})
        self.variant.clear(); self._render()

    def _remove(self) -> None:
        row = self.grid.currentRow()
        if row >= 0: self.items.pop(row); self._render()

    def _render(self) -> None:
        self.grid.setRowCount(len(self.items))
        for r, item in enumerate(self.items):
            values = [item["variant_id"], item["description"], item["quantity"], money(item["unit_price"]), money(Decimal(str(item["quantity"])) * Decimal(str(item["unit_price"])))]
            for c, value in enumerate(values): self.grid.setItem(r, c, QTableWidgetItem(str(value)))
        self._totals()

    def _totals(self) -> None:
        subtotal = sum(Decimal(str(i["quantity"])) * Decimal(str(i["unit_price"])) for i in self.items)
        total = max(Decimal("0"), subtotal - Decimal(str(self.discount.value())))
        self.total.setText(money(total))

    def _checkout(self) -> None:
        if not self.items: QMessageBox.warning(self, "Venta vacía", "Agregue al menos un producto."); return
        if not self.cash_register.text().strip(): QMessageBox.warning(self, "Caja requerida", "Indique una caja abierta."); return
        try:
            result = self.service.rpc("register_sale", {
                "p_customer_id": self.customer.text().strip() or None,
                "p_cash_register_id": self.cash_register.text().strip(),
                "p_items": self.items,
                "p_discount": self.discount.value(),
                "p_payment_amount": self.payment.value(),
                "p_payment_method": self.method.currentText(),
                "p_idempotency_key": str(uuid4()),
            })
            QMessageBox.information(self, "Venta registrada", f"La venta, pago y salida de stock se confirmaron.\nID: {result}")
            self.items.clear(); self.discount.setValue(0); self.payment.setValue(0); self._render()
        except Exception as exc: QMessageBox.critical(self, "Venta rechazada", str(exc))


class CashView(QWidget):
    def __init__(self, service: SupabaseService):
        super().__init__(objectName="page")
        self.service = service
        layout = QVBoxLayout(self); layout.setContentsMargins(26, 22, 26, 22)
        title = QLabel("Apertura y cierre de caja"); title.setObjectName("heading"); layout.addWidget(title)
        form = QFormLayout(); self.opening = QDoubleSpinBox(); self.opening.setMaximum(1000000); self.opening.setPrefix("S/ ")
        self.register_id = QLineEdit(); self.register_id.setPlaceholderText("ID de caja para cerrar")
        self.closing = QDoubleSpinBox(); self.closing.setMaximum(1000000); self.closing.setPrefix("S/ ")
        form.addRow("Monto inicial", self.opening); form.addRow("Caja abierta", self.register_id); form.addRow("Efectivo contado", self.closing); layout.addLayout(form)
        buttons = QHBoxLayout(); op = QPushButton("Abrir caja", objectName="gold"); op.clicked.connect(self._open); buttons.addWidget(op)
        close = QPushButton("Cerrar caja"); close.clicked.connect(self._close); buttons.addWidget(close); buttons.addStretch(); layout.addLayout(buttons); layout.addStretch()

    def _open(self) -> None:
        try:
            result = self.service.rpc("open_cash_register", {"p_opening_amount": self.opening.value()})
            self.register_id.setText(str(result)); QMessageBox.information(self, "Caja abierta", f"ID: {result}")
        except Exception as exc: QMessageBox.critical(self, "No fue posible abrir", str(exc))

    def _close(self) -> None:
        try:
            result = self.service.rpc("close_cash_register", {"p_register_id": self.register_id.text().strip(), "p_counted_amount": self.closing.value()})
            QMessageBox.information(self, "Caja cerrada", f"Resumen: {result}")
        except Exception as exc: QMessageBox.critical(self, "No fue posible cerrar", str(exc))

