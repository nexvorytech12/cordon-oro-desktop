from __future__ import annotations

from PySide6.QtCore import QSettings


class PreferencesService:
    """Preferencias locales de la interfaz; nunca almacena credenciales."""

    def __init__(self, settings: QSettings | None = None):
        self._settings = settings or QSettings("CordonDeOro", "SistemaGestion")

    @property
    def theme(self) -> str:
        value = str(self._settings.value("appearance/theme", "light")).lower()
        return value if value in {"light", "dark"} else "light"

    @property
    def compact_sidebar(self) -> bool:
        return self._as_bool(self._settings.value("appearance/compact_sidebar", False))

    @property
    def automatic_updates(self) -> bool:
        return self._as_bool(self._settings.value("updates/check_automatically", True))

    def save(self, *, theme: str, compact_sidebar: bool, automatic_updates: bool) -> None:
        self._settings.setValue("appearance/theme", theme if theme in {"light", "dark"} else "light")
        self._settings.setValue("appearance/compact_sidebar", compact_sidebar)
        self._settings.setValue("updates/check_automatically", automatic_updates)
        self._settings.sync()

    def set_compact_sidebar(self, compact: bool) -> None:
        self._settings.setValue("appearance/compact_sidebar", compact)
        self._settings.sync()

    @staticmethod
    def _as_bool(value: object) -> bool:
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {"1", "true", "yes", "si", "sí"}
