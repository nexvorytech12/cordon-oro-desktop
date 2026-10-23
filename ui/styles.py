from __future__ import annotations


def stylesheet(theme: str = "light") -> str:
    dark = theme == "dark"
    bg = "#203247" if dark else "#F7F8FA"
    card = "#2A4057" if dark else "#FFFFFF"
    text = "#F5F6F8" if dark else "#0B1F35"
    muted = "#C2CCD6" if dark else "#6B7886"
    border = "#41566B" if dark else "#E2E7EC"
    sidebar = "#25394D" if dark else "#FFFDF8"
    sidebar_text = "#EEF2F5" if dark else "#23384C"
    nav_hover = "#344D64" if dark else "#F7EFD9"
    nav_active = "#3B5369" if dark else "#F1E2BD"
    header_bg = "#31495F" if dark else "#EAF0F5"
    header_text = "#FFFFFF" if dark else "#17334D"
    return f"""
    * {{ font-family: 'Segoe UI'; font-size: 10pt; color: {text}; }}
    QMainWindow, QDialog, QWidget#page {{ background: {bg}; }}
    QFrame#card {{ background: {card}; border: 1px solid {border}; border-radius: 12px; }}
    QFrame#topbar {{ background: {card}; border: none; border-bottom: 1px solid {border}; }}
    QFrame#logoPanel {{ background: #102A43; border: 1px solid #294762; border-radius: 12px; }}
    QFrame#loginHero {{ background: {sidebar}; border: none; border-right: 1px solid {border}; }}
    QLabel#brand {{ color: #B28A36; font-size: 17pt; font-weight: 700; }}
    QLabel#heading {{ font-size: 20pt; font-weight: 700; }}
    QLabel#sectionHeading {{ font-size: 13pt; font-weight: 700; }}
    QLabel#muted {{ color: {muted}; }}
    QLabel#metric {{ color: #A77D28; font-size: 23pt; font-weight: 700; }}
    QLabel#statusOnline {{ color: #23835A; font-weight: 700; }}
    QLabel#statusOffline {{ color: #A63D40; font-weight: 700; }}
    QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QTextEdit {{
        background: {card}; border: 1px solid {border}; border-radius: 8px; padding: 9px;
        selection-background-color: #C5A052;
    }}
    QLineEdit:focus, QComboBox:focus, QDateEdit:focus {{ border: 1px solid #C5A052; }}
    QPushButton {{ background: #244A68; color: white; border: none; border-radius: 8px; padding: 9px 15px; font-weight: 600; }}
    QPushButton:hover {{ background: #315F82; }}
    QPushButton#gold {{ background: #D4B46A; color: #132D43; }}
    QPushButton#gold:hover {{ background: #E0C680; }}
    QPushButton#danger {{ background: #A63D40; }}
    QCheckBox {{ spacing: 8px; }}
    QCheckBox::indicator {{ width: 18px; height: 18px; }}
    QPushButton#nav {{ background: transparent; text-align: left; padding: 11px; color: {sidebar_text}; border-radius: 8px; }}
    QPushButton#nav:hover {{ background: {nav_hover}; color: {sidebar_text}; }}
    QPushButton#nav:checked {{ background: {nav_active}; color: {sidebar_text}; border-left: 3px solid #C5A052; }}
    QFrame#sidebar {{ background: {sidebar}; border: none; border-right: 1px solid {border}; }}
    QTableWidget {{ background: {card}; alternate-background-color: {bg}; border: 1px solid {border}; border-radius: 8px; gridline-color: {border}; }}
    QHeaderView::section {{ background: {header_bg}; color: {header_text}; border: none; border-right: 1px solid {border}; padding: 9px; font-weight: 600; }}
    QTableWidget::item {{ padding: 6px; }}
    QStatusBar {{ background: {card}; border-top: 1px solid {border}; }}
    QScrollBar:vertical {{ width: 10px; background: transparent; }}
    QScrollBar::handle:vertical {{ background: #91A0B0; border-radius: 5px; min-height: 24px; }}
    """

