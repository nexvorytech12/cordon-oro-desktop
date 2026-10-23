from __future__ import annotations

import logging
import sys
from pathlib import Path

from PySide6.QtCore import QLockFile, QStandardPaths
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox

from config.settings import Settings, SettingsError
from services.supabase_service import SupabaseService
from ui.login_window import LoginWindow
from ui.styles import stylesheet


def configure_logging() -> None:
    log_dir = Path(QStandardPaths.writableLocation(QStandardPaths.AppLocalDataLocation))
    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=log_dir / "cordon_de_oro.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Cordón de Oro")
    app.setOrganizationName("Cordón de Oro E.I.R.L.")
    app.setApplicationVersion("0.1.0")
    app.setStyle("Fusion")
    app.setStyleSheet(stylesheet("light"))

    icon_path = Path(__file__).parent / "assets" / "icon.ico"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    configure_logging()
    lock_path = Path(QStandardPaths.writableLocation(QStandardPaths.TempLocation)) / "cordon_de_oro.lock"
    lock = QLockFile(str(lock_path))
    lock.setStaleLockTime(0)
    if not lock.tryLock(100):
        QMessageBox.warning(None, "Aplicación en ejecución", "Cordón de Oro ya está abierto en este equipo.")
        return 1

    try:
        settings = Settings.load()
        app.setApplicationVersion(settings.app_version)
        service = SupabaseService(settings)
    except SettingsError as exc:
        QMessageBox.critical(None, "Configuración incompleta", str(exc))
        return 2
    except Exception as exc:
        logging.exception("No fue posible inicializar Supabase")
        QMessageBox.critical(None, "Error de conexión", f"No fue posible iniciar el cliente de Supabase.\n\n{exc}")
        return 3

    window = LoginWindow(service)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

