from __future__ import annotations

import os
import sys
import base64
import json
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


class SettingsError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class Settings:
    supabase_url: str
    supabase_anon_key: str
    app_env: str = "production"
    app_version: str = "0.1.4"
    github_repository: str = ""
    update_enabled: bool = True

    @classmethod
    def load(cls) -> "Settings":
        candidates = [Path(__file__).resolve().parent.parent / ".env"]
        if getattr(sys, "frozen", False):
            candidates.insert(0, Path(sys.executable).resolve().parent / ".env")
        if os.getenv("LOCALAPPDATA"):
            candidates.append(Path(os.environ["LOCALAPPDATA"]) / "Cordón de Oro" / ".env")
        for candidate in candidates:
            if candidate.exists():
                load_dotenv(candidate)
                break
        url = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
        key = os.getenv("SUPABASE_ANON_KEY", "").strip()
        if not url or not key:
            raise SettingsError(
                "Falta configurar Supabase. Copie .env.example como .env y complete "
                "SUPABASE_URL y SUPABASE_ANON_KEY. Nunca use service_role en la aplicación."
            )
        privileged = "service_role" in key.lower()
        if key.count(".") == 2:
            try:
                payload = key.split(".")[1]
                payload += "=" * (-len(payload) % 4)
                privileged = privileged or json.loads(base64.urlsafe_b64decode(payload)).get("role") == "service_role"
            except Exception:
                pass
        if privileged:
            raise SettingsError("La clave service_role no puede usarse en el cliente de escritorio.")
        return cls(
            url,
            key,
            os.getenv("APP_ENV", "production"),
            os.getenv("APP_VERSION", "0.1.4"),
            os.getenv("GITHUB_REPOSITORY", "").strip(),
            os.getenv("UPDATE_ENABLED", "true").strip().lower() in {"1", "true", "yes", "si", "sí"},
        )

