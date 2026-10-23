from __future__ import annotations

from datetime import date, datetime
from typing import Any

import pyqtgraph as pg
from PySide6.QtCore import QTimer
from PySide6.QtGui import QFont
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


class DateAxisItem(pg.AxisItem):
    def __init__(self):
        super().__init__(orientation="bottom")
        self.labels: list[str] = []

    def tickStrings(self, values: list[float], scale: float, spacing: float) -> list[str]:
        result = []
        for value in values:
            index = int(round(value))
            result.append(self.labels[index] if 0 <= index < len(self.labels) else "")
        return result


class MoneyAxisItem(pg.AxisItem):
    def tickStrings(self, values: list[float], scale: float, spacing: float) -> list[str]:
        return [_compact_money(value) for value in values]


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
        chart_card = QFrame(objectName="chartCard"); chart_layout = QVBoxLayout(chart_card)
        chart_layout.setContentsMargins(18, 14, 18, 16)
        chart_title = QLabel("Ventas de los últimos 30 días", objectName="chartTitle")
        chart_layout.addWidget(chart_title)
        self.date_axis = DateAxisItem()
        money_axis = MoneyAxisItem(orientation="left")
        self.chart = pg.PlotWidget(
            background="#FFFFFF",
            axisItems={"bottom": self.date_axis, "left": money_axis},
        )
        self.chart.setMinimumHeight(260)
        self.chart.showGrid(x=True, y=True, alpha=0.16)
        self.chart.setMouseEnabled(x=False, y=False)
        self.chart.setMenuEnabled(False)
        self.chart.hideButtons()
        for axis_name in ("left", "bottom"):
            axis = self.chart.getAxis(axis_name)
            axis.setPen(pg.mkPen("#CBD5E1"))
            axis.setTextPen(pg.mkPen("#64748B"))
            axis.setTickFont(QFont("Segoe UI", 9))
        self.chart.getAxis("left").setWidth(72)
        self.chart.getAxis("bottom").setHeight(34)
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
            self.date_axis.labels = [_short_date(p.get("day")) for p in points]
            if values:
                last_index = len(values) - 1
                self.chart.setLimits(xMin=-0.5, xMax=last_index + 0.5, yMin=0)
                self.chart.setXRange(-0.5, last_index + 0.5, padding=0)
                maximum = max(values)
                if maximum > 0:
                    self.chart.setYRange(0, maximum * 1.18, padding=0)
                    self.chart.plot(
                        range(len(values)),
                        values,
                        pen=pg.mkPen("#C5A052", width=3),
                        brush=pg.mkBrush(197, 160, 82, 42),
                        fillLevel=0,
                        symbol="o",
                        symbolSize=7,
                        symbolBrush="#C5A052",
                        symbolPen=pg.mkPen("#FFFFFF", width=1),
                    )
                else:
                    self.chart.setYRange(0, 1, padding=0)
                    message = pg.TextItem(
                        "Aún no hay ventas registradas en los últimos 30 días",
                        color="#64748B",
                        anchor=(0.5, 0.5),
                    )
                    message.setFont(QFont("Segoe UI", 10))
                    message.setPos(last_index / 2, 0.52)
                    self.chart.addItem(message)
        except Exception as exc:
            # El dashboard no bloquea el resto del sistema ante una caída de red.
            self.setToolTip(f"Última actualización fallida: {exc}")


def _short_date(value: object) -> str:
    if isinstance(value, (date, datetime)):
        return value.strftime("%d/%m")
    text = str(value or "")
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).strftime("%d/%m")
    except ValueError:
        return text[:5]


def _compact_money(value: float) -> str:
    absolute = abs(value)
    if absolute >= 1_000_000:
        return f"S/ {value / 1_000_000:.1f} M"
    if absolute >= 1_000:
        return f"S/ {value / 1_000:.1f} mil"
    return f"S/ {value:,.0f}"

