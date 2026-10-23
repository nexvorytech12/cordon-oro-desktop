from __future__ import annotations

from typing import Any

import pyqtgraph as pg
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QMessageBox, QVBoxLayout, QWidget

from services.supabase_service import SupabaseService
from utils.formatters import money


class MetricCard(QFrame):
    def __init__(self, label: str):
        super().__init__(objectName="card")
        layout = QVBoxLayout(self)
        title = QLabel(label); title.setObjectName("muted")
        self.value = QLabel("—"); self.value.setObjectName("metric")
        layout.addWidget(title); layout.addWidget(self.value)


class DashboardView(QWidget):
    metrics = [
        ("products", "Productos"), ("total_stock", "Stock total"),
        ("low_stock", "Stock bajo"), ("active_customers", "Clientes activos"),
        ("pending_quotes", "Cotizaciones pendientes"), ("production_orders", "En producción"),
        ("delivered_orders", "Entregados"), ("daily_sales", "Ventas de hoy"),
        ("monthly_sales", "Ventas del mes"), ("total_income", "Ingresos acumulados"),
    ]

    def __init__(self, service: SupabaseService, parent=None):
        super().__init__(parent, objectName="page")
        self.service, self.cards = service, {}
        layout = QVBoxLayout(self); layout.setContentsMargins(26, 22, 26, 22)
        title = QLabel("Resumen empresarial"); title.setObjectName("heading"); layout.addWidget(title)
        grid = QGridLayout(); grid.setSpacing(14)
        for i, (key, label) in enumerate(self.metrics):
            card = MetricCard(label); self.cards[key] = card
            grid.addWidget(card, i // 5, i % 5)
        layout.addLayout(grid)
        chart_card = QFrame(objectName="card"); chart_layout = QVBoxLayout(chart_card)
        chart_layout.addWidget(QLabel("Ventas de los últimos 30 días"))
        self.chart = pg.PlotWidget(background="transparent")
        self.chart.showGrid(x=False, y=True, alpha=0.15)
        self.chart.getAxis("left").setTextPen("#627184")
        self.chart.getAxis("bottom").setTextPen("#627184")
        chart_layout.addWidget(self.chart)
        layout.addWidget(chart_card, 1)
        self.timer = QTimer(self); self.timer.timeout.connect(self.refresh); self.timer.start(60_000)
        QTimer.singleShot(0, self.refresh)

    def refresh(self) -> None:
        try:
            data = self.service.rpc("dashboard_metrics", {}) or {}
            if isinstance(data, list): data = data[0] if data else {}
            for key, _ in self.metrics:
                value = data.get(key, 0)
                self.cards[key].value.setText(money(value) if key.endswith("sales") or key == "total_income" else f"{value:,}")
            points = self.service.rpc("sales_last_30_days", {}) or []
            self.chart.clear()
            values = [float(p.get("total", 0)) for p in points]
            if values:
                self.chart.plot(range(len(values)), values, pen=pg.mkPen("#C5A052", width=3), symbol="o", symbolBrush="#C5A052")
        except Exception as exc:
            # El dashboard no bloquea el resto del sistema ante una caída de red.
            self.setToolTip(f"Última actualización fallida: {exc}")

