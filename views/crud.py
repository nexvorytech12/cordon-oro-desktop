from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Literal

from PySide6.QtCore import QDate, Qt, QTimer
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDateEdit, QDialog, QDialogButtonBox, QDoubleSpinBox,
    QFileDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QMessageBox,
    QPushButton, QSpinBox, QTableWidget, QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget,
)

from repositories.base_repository import BaseRepository
from services.report_service import export_excel, export_pdf
from services.supabase_service import SupabaseService
from utils.formatters import display

logger = logging.getLogger(__name__)
FieldKind = Literal["text", "password", "longtext", "integer", "decimal", "date", "bool", "choice"]


@dataclass(frozen=True, slots=True)
class Field:
    key: str
    label: str
    kind: FieldKind = "text"
    required: bool = False
    choices: tuple[str, ...] = ()


class RecordDialog(QDialog):
    def __init__(self, title: str, fields: list[Field], values: dict[str, Any] | None = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(480)
        self.fields, self.inputs = fields, {}
        values = values or {}
        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(12)
        for field in fields:
            widget = self._widget(field, values.get(field.key))
            self.inputs[field.key] = widget
            form.addRow(field.label + (" *" if field.required else ""), widget)
        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("Guardar")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        buttons.accepted.connect(self._validate)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _widget(self, field: Field, value: Any):
        if field.kind == "longtext":
            widget = QTextEdit(str(value or "")); widget.setMaximumHeight(90)
        elif field.kind == "integer":
            widget = QSpinBox(); widget.setRange(0, 10_000_000); widget.setValue(int(value or 0))
        elif field.kind == "decimal":
            widget = QDoubleSpinBox(); widget.setRange(0, 100_000_000); widget.setDecimals(2); widget.setValue(float(value or 0))
        elif field.kind == "date":
            widget = QDateEdit(); widget.setCalendarPopup(True); widget.setDisplayFormat("dd/MM/yyyy")
            widget.setDate(QDate.fromString(str(value)[:10], "yyyy-MM-dd") if value else QDate.currentDate())
        elif field.kind == "bool":
            widget = QCheckBox(); widget.setChecked(bool(value) if value is not None else field.key == "is_active")
        elif field.kind == "choice":
            widget = QComboBox(); widget.addItems(field.choices)
            if value in field.choices: widget.setCurrentText(str(value))
        else:
            widget = QLineEdit(str(value or "")); widget.setClearButtonEnabled(True)
            if field.kind == "password": widget.setEchoMode(QLineEdit.EchoMode.Password)
        return widget

    def _validate(self) -> None:
        data = self.data()
        missing = [f.label for f in self.fields if f.required and not str(data.get(f.key, "")).strip()]
        if missing:
            QMessageBox.warning(self, "Datos incompletos", "Complete: " + ", ".join(missing))
            return
        self.accept()

    def data(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for field in self.fields:
            widget = self.inputs[field.key]
            if isinstance(widget, QLineEdit): value = widget.text().strip()
            elif isinstance(widget, QTextEdit): value = widget.toPlainText().strip()
            elif isinstance(widget, (QSpinBox, QDoubleSpinBox)): value = widget.value()
            elif isinstance(widget, QDateEdit): value = widget.date().toString("yyyy-MM-dd")
            elif isinstance(widget, QCheckBox): value = widget.isChecked()
            elif isinstance(widget, QComboBox): value = widget.currentText()
            else: value = None
            result[field.key] = value if value != "" else None
        return result


class CrudView(QWidget):
    def __init__(self, service: SupabaseService, *, title: str, table: str,
                 columns: list[tuple[str, str]], fields: list[Field],
                 permission: str, select: str = "*", parent=None):
        super().__init__(parent, objectName="page")
        self.service, self.title, self.table_name = service, title, table
        self.columns, self.fields, self.permission, self.select = columns, fields, permission, select
        self.repo = BaseRepository(service, table)
        self.rows: list[dict[str, Any]] = []
        self._build()
        QTimer.singleShot(0, self.refresh)

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 22, 26, 22)
        header = QHBoxLayout()
        heading = QLabel(self.title); heading.setObjectName("heading")
        header.addWidget(heading)
        header.addStretch()
        self.search = QLineEdit(); self.search.setPlaceholderText("Buscar en resultados…"); self.search.setMaximumWidth(300)
        self.search.textChanged.connect(self._filter)
        header.addWidget(self.search)
        refresh = QPushButton("Actualizar"); refresh.clicked.connect(self.refresh); header.addWidget(refresh)
        self.new_button = QPushButton("+ Nuevo", objectName="gold"); self.new_button.clicked.connect(self.create); header.addWidget(self.new_button)
        layout.addLayout(header)
        tools = QHBoxLayout()
        self.edit_button = QPushButton("Editar"); self.edit_button.clicked.connect(self.edit); tools.addWidget(self.edit_button)
        self.deactivate_button = QPushButton("Desactivar", objectName="danger"); self.deactivate_button.clicked.connect(self.deactivate); tools.addWidget(self.deactivate_button)
        tools.addStretch()
        xlsx = QPushButton("Exportar Excel"); xlsx.clicked.connect(lambda: self.export("xlsx")); tools.addWidget(xlsx)
        pdf = QPushButton("Exportar PDF"); pdf.clicked.connect(lambda: self.export("pdf")); tools.addWidget(pdf)
        layout.addLayout(tools)
        self.grid = QTableWidget(0, len(self.columns))
        self.grid.setHorizontalHeaderLabels([label for _, label in self.columns])
        self.grid.setAlternatingRowColors(True)
        self.grid.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.grid.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.grid.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.grid.horizontalHeader().setStretchLastSection(True)
        self.grid.doubleClicked.connect(self.edit)
        layout.addWidget(self.grid)
        allowed = bool(self.service.session and self.service.session.can(self.permission))
        for button in (self.new_button, self.edit_button, self.deactivate_button): button.setEnabled(allowed)

    def refresh(self) -> None:
        try:
            self.rows = self.repo.list(self.select)
            self._render(self.rows)
        except Exception as exc:
            logger.exception("Error consultando %s", self.table_name)
            QMessageBox.critical(self, "No se pudieron cargar los datos", str(exc))

    def _render(self, rows: list[dict[str, Any]]) -> None:
        self.grid.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, (key, _) in enumerate(self.columns):
                value: Any = row
                for part in key.split("."):
                    value = value.get(part) if isinstance(value, dict) else None
                item = QTableWidgetItem(display(value)); item.setData(Qt.ItemDataRole.UserRole, row.get("id"))
                self.grid.setItem(r, c, item)
        self.grid.resizeColumnsToContents()

    def _filter(self, text: str) -> None:
        term = text.casefold().strip()
        self._render([row for row in self.rows if term in " ".join(display(v) for v in row.values()).casefold()])

    def _selected(self) -> dict[str, Any] | None:
        idx = self.grid.currentRow()
        if idx < 0: return None
        record_id = self.grid.item(idx, 0).data(Qt.ItemDataRole.UserRole)
        return next((row for row in self.rows if row.get("id") == record_id), None)

    def create(self) -> None:
        dialog = RecordDialog(f"Nuevo — {self.title}", self.fields, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                self.repo.create(dialog.data()); self.refresh()
            except Exception as exc: QMessageBox.critical(self, "No se pudo guardar", str(exc))

    def edit(self) -> None:
        row = self._selected()
        if not row:
            QMessageBox.information(self, "Seleccione un registro", "Seleccione una fila para editar."); return
        dialog = RecordDialog(f"Editar — {self.title}", self.fields, row, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                self.repo.update(str(row["id"]), dialog.data()); self.refresh()
            except Exception as exc: QMessageBox.critical(self, "No se pudo actualizar", str(exc))

    def deactivate(self) -> None:
        row = self._selected()
        if not row: QMessageBox.information(self, "Seleccione un registro", "Seleccione una fila."); return
        if QMessageBox.question(self, "Confirmar", "¿Desactivar el registro seleccionado?") == QMessageBox.StandardButton.Yes:
            try: self.repo.deactivate(str(row["id"])); self.refresh()
            except Exception as exc: QMessageBox.critical(self, "No se pudo desactivar", str(exc))

    def export(self, kind: str) -> None:
        ext, label = ("xlsx", "Excel") if kind == "xlsx" else ("pdf", "PDF")
        path, _ = QFileDialog.getSaveFileName(self, f"Exportar {label}", f"{self.table_name}.{ext}", f"{label} (*.{ext})")
        if not path: return
        try:
            (export_excel if kind == "xlsx" else export_pdf)(path, self.title, self.columns, self.rows)
            QMessageBox.information(self, "Exportación completa", f"Archivo creado en:\n{path}")
        except Exception as exc: QMessageBox.critical(self, "No se pudo exportar", str(exc))

