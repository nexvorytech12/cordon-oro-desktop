from __future__ import annotations

from typing import Any

from services.supabase_service import SupabaseService


class BaseRepository:
    def __init__(self, service: SupabaseService, table: str):
        self.service = service
        self.table = table

    def list(self, columns: str = "*", *, order: str = "created_at", limit: int = 500) -> list[dict[str, Any]]:
        try:
            query = self.service.client.table(self.table).select(columns).limit(limit)
            if order:
                query = query.order(order, desc=True)
            rows = query.execute().data or []
            self.service.online = True
            try: self.service.cache.save(self.table, rows)
            except Exception: pass  # La caché es una mejora; nunca invalida una consulta correcta.
            return rows
        except Exception:
            self.service.online = False
            try: cached = self.service.cache.load(self.table)
            except Exception: cached = None
            if cached is not None: return cached
            raise

    def get(self, record_id: str, columns: str = "*") -> dict[str, Any] | None:
        rows = self.service.client.table(self.table).select(columns).eq("id", record_id).limit(1).execute().data
        return rows[0] if rows else None

    def create(self, payload: dict[str, Any]) -> dict[str, Any]:
        rows = self.service.client.table(self.table).insert(payload).execute().data
        return rows[0] if rows else payload

    def update(self, record_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        rows = self.service.client.table(self.table).update(payload).eq("id", record_id).execute().data
        return rows[0] if rows else payload

    def deactivate(self, record_id: str) -> None:
        self.update(record_id, {"is_active": False})

