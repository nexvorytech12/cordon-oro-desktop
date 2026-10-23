from datetime import date

from views.dashboard import _compact_money, _short_date


def test_dashboard_dates_use_short_day_month_format():
    assert _short_date(date(2026, 10, 23)) == "23/10"
    assert _short_date("2026-01-07") == "07/01"


def test_dashboard_money_axis_uses_compact_labels():
    assert _compact_money(850) == "S/ 850"
    assert _compact_money(12_500) == "S/ 12.5 mil"
    assert _compact_money(2_000_000) == "S/ 2.0 M"
