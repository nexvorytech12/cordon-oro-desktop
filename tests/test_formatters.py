from utils.formatters import display, money


def test_money_formats_peruvian_currency():
    assert money("1250.5") == "S/ 1,250.50"


def test_display_nested_friendly_values():
    assert display(True) == "Sí"
    assert display({"name": "Telas"}) == "Telas"

