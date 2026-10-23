from __future__ import annotations

import ctypes
import json
from ctypes import wintypes
from pathlib import Path
from typing import Any

from PySide6.QtCore import QStandardPaths


class _Blob(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_byte))]


class SecureCache:
    """Caché de solo lectura cifrada con Windows DPAPI para el usuario actual."""

    def __init__(self):
        self.directory = Path(QStandardPaths.writableLocation(QStandardPaths.AppLocalDataLocation)) / "cache"
        self.directory.mkdir(parents=True, exist_ok=True)

    def save(self, key: str, value: Any) -> None:
        raw = json.dumps(value, ensure_ascii=False, default=str).encode("utf-8")
        source_buffer = ctypes.create_string_buffer(raw)
        source = _Blob(len(raw), ctypes.cast(source_buffer, ctypes.POINTER(ctypes.c_byte)))
        target = _Blob()
        if not ctypes.windll.crypt32.CryptProtectData(ctypes.byref(source), ctypes.c_wchar_p("Cordón de Oro"), None, None, None, 0, ctypes.byref(target)):
            return
        try:
            encrypted = ctypes.string_at(target.pbData, target.cbData)
            (self.directory / f"{key}.bin").write_bytes(encrypted)
        finally:
            ctypes.windll.kernel32.LocalFree(target.pbData)

    def load(self, key: str) -> Any | None:
        path = self.directory / f"{key}.bin"
        if not path.exists(): return None
        encrypted = path.read_bytes()
        source_buffer = ctypes.create_string_buffer(encrypted)
        source = _Blob(len(encrypted), ctypes.cast(source_buffer, ctypes.POINTER(ctypes.c_byte)))
        target = _Blob()
        if not ctypes.windll.crypt32.CryptUnprotectData(ctypes.byref(source), None, None, None, None, 0, ctypes.byref(target)):
            return None
        try: return json.loads(ctypes.string_at(target.pbData, target.cbData).decode("utf-8"))
        finally: ctypes.windll.kernel32.LocalFree(target.pbData)

