from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

import httpx
from packaging.version import InvalidVersion, Version
from PySide6.QtCore import QStandardPaths

from config.settings import Settings


@dataclass(frozen=True, slots=True)
class ReleaseInfo:
    version: str
    title: str
    notes: str
    installer_url: str
    checksum_url: str
    page_url: str


class UpdateService:
    """Actualizaciones firmadas por checksum desde GitHub Releases."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = httpx.Client(
            timeout=30,
            follow_redirects=True,
            headers={"Accept": "application/vnd.github+json", "User-Agent": "CordonDeOro-Updater"},
        )

    @property
    def configured(self) -> bool:
        return self.settings.update_enabled and bool(re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", self.settings.github_repository))

    def check(self) -> ReleaseInfo | None:
        if not self.configured:
            return None
        response = self.client.get(f"https://api.github.com/repos/{self.settings.github_repository}/releases/latest")
        if response.status_code == 404:
            return None
        response.raise_for_status()
        release = response.json()
        tag = str(release.get("tag_name", "")).removeprefix("v")
        try:
            if Version(tag) <= Version(self.settings.app_version):
                return None
        except InvalidVersion as exc:
            raise RuntimeError(f"La versión publicada no es válida: {tag}") from exc
        assets = release.get("assets") or []
        installer = next((a for a in assets if str(a.get("name", "")).lower().endswith(".exe")), None)
        checksum = next((a for a in assets if str(a.get("name", "")).lower().endswith(".sha256")), None)
        if not installer or not checksum:
            raise RuntimeError("La versión publicada debe incluir el instalador .exe y su archivo .sha256.")
        return ReleaseInfo(
            tag,
            release.get("name") or f"Versión {tag}",
            release.get("body") or "",
            installer["browser_download_url"],
            checksum["browser_download_url"],
            release.get("html_url") or "",
        )

    def download(self, release: ReleaseInfo) -> Path:
        update_dir = Path(QStandardPaths.writableLocation(QStandardPaths.DownloadLocation)) / "CordonDeOro-Updates"
        update_dir.mkdir(parents=True, exist_ok=True)
        destination = update_dir / f"CordonDeOro-Setup-{release.version}.exe"
        expected_response = self.client.get(release.checksum_url)
        expected_response.raise_for_status()
        match = re.search(r"\b[0-9a-fA-F]{64}\b", expected_response.text)
        if not match:
            raise RuntimeError("El archivo de integridad de la actualización es inválido.")
        expected = match.group(0).lower()
        digest = hashlib.sha256()
        with self.client.stream("GET", release.installer_url, timeout=300) as response:
            response.raise_for_status()
            with destination.open("wb") as output:
                for chunk in response.iter_bytes():
                    output.write(chunk)
                    digest.update(chunk)
        if digest.hexdigest().lower() != expected:
            destination.unlink(missing_ok=True)
            raise RuntimeError("La actualización descargada no superó la verificación SHA-256.")
        return destination

