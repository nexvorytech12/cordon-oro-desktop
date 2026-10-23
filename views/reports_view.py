from __future__ import annotations

from PySide6.QtWidgets import QFileDialog, QGridLayout, QLabel, QMessageBox, QPushButton, QVBoxLayout, QWidget

from services.report_service import export_excel, export_pdf
from services.supabase_service import SupabaseService


REPORTS = {
    "Inventario actual": ("inventory_report", [("sku", "SKU"), ("name", "Producto"), ("size", "Talla"), ("color", "Color"), ("stock", "Stock"), ("value", "Valor")]),
    "Kardex": ("kardex_report", [("created_at", "Fecha"), ("sku", "SKU"), ("movement_type", "Tipo"), ("quantity", "Cantidad"), ("balance", "Saldo"), ("reason", "Motivo")]),
    "Ventas": ("sales_report", [("sale_date", "Fecha"), ("number", "Venta"), ("customer", "Cliente"), ("total", "Total"), ("paid", "Pagado"), ("balance", "Saldo")]),
    "Pedidos pendientes": ("pending_orders_report", [("number", "Pedido"), ("customer", "Cliente"), ("status", "Estado"), ("delivery_date", "Entrega"), ("balance", "Saldo")]),
    "Producción": ("production_report", [("number", "Orden"), ("operator", "Operador"), ("status", "Estado"), ("quantity", "Cantidad"), ("approved", "Aprobadas"), ("defective", "Defectuosas")]),
    "Compras": ("purchases_report", [("purchase_date", "Fecha"), ("number", "Compra"), ("supplier", "Proveedor"), ("total", "Total"), ("paid", "Pagado")]),
}


class ReportsView(QWidget):
    def __init__(self, service: SupabaseService):
        super().__init__(objectName="page"); self.service = service
        layout = QVBoxLayout(self); layout.setContentsMargins(26, 22, 26, 22)
        title = QLabel("Centro de reportes"); title.setObjectName("heading"); layout.addWidget(title)
        info = QLabel("Los reportes consultan información autorizada por RLS y pueden exportarse a PDF o Excel."); info.setObjectName("muted"); layout.addWidget(info)
        grid = QGridLayout()
        for i, name in enumerate(REPORTS):
            button = QPushButton(name); button.setMinimumHeight(55); button.clicked.connect(lambda _=False, n=name: self._export(n)); grid.addWidget(button, i // 3, i % 3)
        layout.addLayout(grid); layout.addStretch()

    def _export(self, name: str) -> None:
        rpc, columns = REPORTS[name]
        path, selected = QFileDialog.getSaveFileName(self, f"Exportar {name}", name.replace(" ", "_") + ".xlsx", "Excel (*.xlsx);;PDF (*.pdf)")
        if not path: return
        try:
            rows = self.service.rpc(rpc, {}) or []
            if path.lower().endswith(".pdf"): export_pdf(path, name, columns, rows)
            else: export_excel(path, name, columns, rows)
            QMessageBox.information(self, "Reporte generado", path)
        except Exception as exc: QMessageBox.critical(self, "No se pudo generar", str(exc))

