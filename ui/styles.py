from __future__ import annotations


def stylesheet(theme: str = "light") -> str:
    dark = theme == "dark"
    bg = "#111B27" if dark else "#F5F6F8"
    card = "#172536" if dark else "#FFFFFF"
    text = "#F5F6F8" if dark else "#0B1F35"
    muted = "#AEB9C5" if dark else "#627184"
    border = "#2C3D50" if dark else "#DDE2E8"
    return f"""
    * {{ font-family: 'Segoe UI'; font-size: 10pt; color: {text}; }}
    QMainWindow, QDialog, QWidget#page {{ background: {bg}; }}
    QFrame#card {{ background: {card}; border: 1px solid {border}; border-radius: 10px; }}
    QLabel#brand {{ color: #C5A052; font-size: 18pt; font-weight: 700; }}
    QLabel#heading {{ font-size: 20pt; font-weight: 700; }}
    QLabel#muted {{ color: {muted}; }}
    QLabel#metric {{ color: #C5A052; font-size: 23pt; font-weight: 700; }}
    QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QTextEdit {{
        background: {card}; border: 1px solid {border}; border-radius: 6px; padding: 8px;
        selection-background-color: #C5A052;
    }}
    QLineEdit:focus, QComboBox:focus, QDateEdit:focus {{ border: 1px solid #C5A052; }}
    QPushButton {{ background: #0B1F35; color: white; border: none; border-radius: 6px; padding: 9px 15px; font-weight: 600; }}
    QPushButton:hover {{ background: #173B61; }}
    QPushButton#gold {{ background: #C5A052; color: #0B1F35; }}
    QPushButton#danger {{ background: #A63D40; }}
    QPushButton#nav {{ background: transparent; text-align: left; padding: 12px; color: #DDE5ED; border-radius: 6px; }}
    QPushButton#nav:hover, QPushButton#nav:checked {{ background: #1B3854; color: #FFFFFF; border-left: 3px solid #C5A052; }}
    QFrame#sidebar {{ background: #0B1F35; border: none; }}
    QTableWidget {{ background: {card}; alternate-background-color: {bg}; border: 1px solid {border}; border-radius: 8px; gridline-color: {border}; }}
    QHeaderView::section {{ background: #0B1F35; color: white; border: none; padding: 9px; font-weight: 600; }}
    QTableWidget::item {{ padding: 6px; }}
    QStatusBar {{ background: {card}; border-top: 1px solid {border}; }}
    QScrollBar:vertical {{ width: 10px; background: transparent; }}
    QScrollBar::handle:vertical {{ background: #91A0B0; border-radius: 5px; min-height: 24px; }}
    """

