from __future__ import annotations

from urllib.parse import urlparse

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from models.session import UserSession
from services.preferences_service import PreferencesService
from services.supabase_service import SupabaseService


class SettingsView(QWidget):
    preferences_changed = Signal(str, bool)
    check_updates_requested = Signal()

    def __init__(
        self,
        service: SupabaseService,
        session: UserSession,
        preferences: PreferencesService,
    ):
        super().__init__(objectName="page")
        self.service = service
        self.session = session
        self.preferences = preferences
        self._build()
        self.sync_from_preferences()
        self.refresh_connection()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 28)
        root.setSpacing(18)

        title = QLabel("Configuración", objectName="heading")
        subtitle = QLabel(
            "Administre en un solo lugar la apariencia, las actualizaciones, la conexión y su cuenta.",
            objectName="muted",
        )
        root.addWidget(title)
        root.addWidget(subtitle)

        grid = QGridLayout()
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(18)
        root.addLayout(grid)

        appearance, appearance_layout = self._card("Apariencia", "Personalice cómo se muestra el sistema.")
        appearance_form = QFormLayout()
        appearance_form.setSpacing(12)
        self.theme = QComboBox()
        self.theme.addItem("Claro", "light")
        self.theme.addItem("Oscuro", "dark")
        appearance_form.addRow("Tema", self.theme)
        self.compact_sidebar = QCheckBox("Usar menú lateral compacto")
        appearance_form.addRow("Navegación", self.compact_sidebar)
        appearance_layout.addLayout(appearance_form)
        appearance_layout.addStretch()
        grid.addWidget(appearance, 0, 0)

        updates, updates_layout = self._card("Actualizaciones", "Control de nuevas versiones publicadas en GitHub.")
        self.automatic_updates = QCheckBox("Buscar actualizaciones al iniciar")
        updates_layout.addWidget(self.automatic_updates)
        updates_layout.addWidget(QLabel(f"Versión instalada: {self.service.settings.app_version}", objectName="muted"))
        repository = self.service.settings.github_repository or "No configurado"
        updates_layout.addWidget(QLabel(f"Repositorio: {repository}", objectName="muted"))
        self.update_status = QLabel("Listo para buscar actualizaciones.", objectName="muted")
        self.update_status.setWordWrap(True)
        updates_layout.addWidget(self.update_status)
        check_button = QPushButton("Buscar actualización ahora", objectName="gold")
        check_button.clicked.connect(self._request_update_check)
        updates_layout.addWidget(check_button)
        updates_layout.addStretch()
        grid.addWidget(updates, 0, 1)

        connection, connection_layout = self._card("Conexión", "Información de la conexión segura con Supabase.")
        connection_form = QFormLayout()
        connection_form.setSpacing(12)
        project = urlparse(self.service.settings.supabase_url).hostname or self.service.settings.supabase_url
        self.connection_status = QLabel()
        connection_form.addRow("Estado", self.connection_status)
        connection_form.addRow("Proyecto", QLabel(project))
        connection_form.addRow("Entorno", QLabel(self.service.settings.app_env.title()))
        connection_layout.addLayout(connection_form)
        refresh_button = QPushButton("Comprobar estado")
        refresh_button.clicked.connect(self.refresh_connection)
        connection_layout.addWidget(refresh_button)
        connection_layout.addWidget(
            QLabel("Las credenciales no se muestran ni se guardan en esta pantalla por seguridad.", objectName="muted")
        )
        connection_layout.addStretch()
        grid.addWidget(connection, 1, 0)

        account, account_layout = self._card("Cuenta y permisos", "Datos de la sesión activa.")
        account_form = QFormLayout()
        account_form.setSpacing(12)
        account_form.addRow("Usuario", QLabel(self.session.full_name))
        account_form.addRow("Correo", QLabel(self.session.email))
        account_form.addRow("Rol", QLabel(self.session.role.replace("_", " ").title()))
        permissions = "Acceso total" if self.session.role == "administrador" else f"{len(self.session.permissions)} permisos asignados"
        account_form.addRow("Permisos", QLabel(permissions))
        account_layout.addLayout(account_form)
        account_layout.addWidget(
            QLabel("Los usuarios, roles y permisos se administran desde el módulo Usuarios.", objectName="muted")
        )
        account_layout.addStretch()
        grid.addWidget(account, 1, 1)

        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        grid.setRowStretch(0, 1)
        grid.setRowStretch(1, 1)

        actions = QHBoxLayout()
        actions.addStretch()
        save_button = QPushButton("Guardar configuración", objectName="gold")
        save_button.clicked.connect(self.save)
        actions.addWidget(save_button)
        root.addLayout(actions)

    @staticmethod
    def _card(title: str, description: str) -> tuple[QFrame, QVBoxLayout]:
        card = QFrame(objectName="card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(10)
        heading = QLabel(title, objectName="sectionHeading")
        helper = QLabel(description, objectName="muted")
        helper.setWordWrap(True)
        layout.addWidget(heading)
        layout.addWidget(helper)
        return card, layout

    def sync_from_preferences(self) -> None:
        index = self.theme.findData(self.preferences.theme)
        self.theme.setCurrentIndex(max(index, 0))
        self.compact_sidebar.setChecked(self.preferences.compact_sidebar)
        self.automatic_updates.setChecked(self.preferences.automatic_updates)

    def save(self) -> None:
        theme = str(self.theme.currentData())
        compact = self.compact_sidebar.isChecked()
        self.preferences.save(
            theme=theme,
            compact_sidebar=compact,
            automatic_updates=self.automatic_updates.isChecked(),
        )
        self.preferences_changed.emit(theme, compact)
        self.update_status.setText("Configuración guardada correctamente.")

    def refresh_connection(self) -> None:
        if self.service.online:
            self.connection_status.setText("● Conectado")
            self.connection_status.setObjectName("statusOnline")
        else:
            self.connection_status.setText("● Sin conexión")
            self.connection_status.setObjectName("statusOffline")
        self.connection_status.style().unpolish(self.connection_status)
        self.connection_status.style().polish(self.connection_status)

    def set_update_status(self, message: str) -> None:
        self.update_status.setText(message)

    def _request_update_check(self) -> None:
        self.update_status.setText("Buscando actualizaciones…")
        self.check_updates_requested.emit()
