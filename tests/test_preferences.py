from pathlib import Path

from PySide6.QtCore import QSettings

from services.preferences_service import PreferencesService


def test_preferences_are_persisted(tmp_path):
    path = tmp_path / "preferences.ini"
    store = QSettings(str(path), QSettings.Format.IniFormat)
    preferences = PreferencesService(store)

    preferences.save(theme="dark", compact_sidebar=True, automatic_updates=False)

    reloaded = PreferencesService(QSettings(str(path), QSettings.Format.IniFormat))
    assert reloaded.theme == "dark"
    assert reloaded.compact_sidebar is True
    assert reloaded.automatic_updates is False


def test_installer_shortcuts_use_the_brand_icon():
    installer = (Path(__file__).resolve().parents[1] / "installer" / "CordonDeOro.iss").read_text(encoding="utf-8")
    assert 'DestName: "icon.ico"' in installer
    assert installer.count('IconFilename: "{app}\\icon.ico"') == 2
