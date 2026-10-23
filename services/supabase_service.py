from __future__ import annotations

import logging
from typing import Any, Callable

from supabase import Client, create_client

from config.settings import Settings
from models.session import UserSession
from services.cache_service import SecureCache

logger = logging.getLogger(__name__)


class SupabaseService:
    """Único punto de acceso al SDK; la autorización efectiva siempre depende de RLS."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.client: Client = create_client(settings.supabase_url, settings.supabase_anon_key)
        self.session: UserSession | None = None
        self._channels: list[Any] = []
        self.online = True
        self.cache = SecureCache()

    def sign_in(self, email: str, password: str) -> UserSession:
        response = self.client.auth.sign_in_with_password({"email": email, "password": password})
        user = response.user
        if not user:
            raise RuntimeError("Supabase no devolvió un usuario válido.")
        return self._load_profile(user, response.session)

    def _load_profile(self, user: Any, raw_session: Any) -> UserSession:
        profile_rows = (
            self.client.table("profiles")
            .select("full_name,is_active,roles(name,role_permissions(permissions(code)))")
            .eq("id", str(user.id))
            .limit(1)
            .execute()
            .data
        )
        if not profile_rows:
            self.client.auth.sign_out()
            raise PermissionError("La cuenta no tiene un perfil empresarial asignado.")
        profile = profile_rows[0]
        if not profile.get("is_active", False):
            self.client.auth.sign_out()
            raise PermissionError("La cuenta está desactivada. Contacte al administrador.")
        role_data = profile.get("roles") or {}
        permissions = {
            item.get("permissions", {}).get("code")
            for item in role_data.get("role_permissions") or []
            if item.get("permissions")
        }
        self.session = UserSession(
            user_id=str(user.id),
            email=user.email or "",
            full_name=profile.get("full_name") or user.email or "Usuario",
            role=role_data.get("name", "sin_rol"),
            permissions={p for p in permissions if p},
            raw=raw_session,
        )
        return self.session

    def restore_session(self) -> UserSession | None:
        try:
            current = self.client.auth.get_session()
            if not current:
                return None
            user = self.client.auth.get_user().user
            if user:
                return self._load_profile(user, current)
        except Exception:
            logger.info("No se restauró una sesión previa", exc_info=True)
        return None

    def sign_out(self) -> None:
        for channel in self._channels:
            try:
                self.client.remove_channel(channel)
            except Exception:
                logger.debug("No se pudo retirar canal", exc_info=True)
        self._channels.clear()
        self.client.auth.sign_out()
        self.session = None

    def reset_password(self, email: str) -> None:
        self.client.auth.reset_password_email(email)

    def rpc(self, name: str, params: dict[str, Any]) -> Any:
        try:
            data = self.client.rpc(name, params).execute().data
            self.online = True
            return data
        except Exception:
            self.online = False
            raise

    def subscribe(self, table: str, callback: Callable[[Any], None]) -> Any:
        channel = self.client.channel(f"desktop:{table}")
        channel.on_postgres_changes("*", schema="public", table=table, callback=callback).subscribe()
        self._channels.append(channel)
        return channel

