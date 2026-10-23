from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation


def money(value: object) -> str:
    try:
        return f"S/ {Decimal(str(value or 0)):,.2f}"
    except InvalidOperation:
        return "S/ 0.00"


def display(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "Sí" if value else "No"
    if isinstance(value, (date, datetime)):
        return value.strftime("%d/%m/%Y")
    if isinstance(value, dict):
        return str(value.get("name") or value.get("full_name") or "")
    return str(value)

