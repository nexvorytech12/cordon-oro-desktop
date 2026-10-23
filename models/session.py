from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class UserSession:
    user_id: str
    email: str
    full_name: str
    role: str
    permissions: set[str] = field(default_factory=set)
    raw: Any = None

    def can(self, permission: str) -> bool:
        return self.role == "administrador" or permission in self.permissions

