from PySide6.QtGui import QFont
from PySide6.QtCore import Qt

COLORS = {
    "bg_white": "#FDFFFC",
    "bg_soft": "#F0F7F4",
    "accent_yellow": "#FFD166",
    "accent_orange": "#FF9F1C",
    "accent_blue": "#70D6FF",
    "accent_green": "#06D6A0",
    "accent_red": "#EF476F",
    "text_dark": "#011627",
    "text_soft": "#2C3E4F"
}

def get_font_regular(size=12):
    font = QFont("Segoe UI", size)
    return font

def get_font_bold(size=14):
    font = QFont("Segoe UI", size)
    font.setBold(True)
    return font

def get_font_large(size=24):
    font = QFont("Segoe UI", size)
    font.setBold(True)
    return font

BUTTON_STYLE = f"""
    QPushButton {{
        background-color: {COLORS['accent_yellow']};
        color: {COLORS['text_dark']};
        border: none;
        border-radius: 15px;
        padding: 12px 25px;
        font-size: 14px;
        font-weight: bold;
    }}
    QPushButton:hover {{
        background-color: {COLORS['accent_orange']};
    }}
"""

CARD_STYLE = f"""
    QFrame {{
        background-color: white;
        border-radius: 20px;
        border: 2px solid {COLORS['accent_yellow']};
        padding: 15px;
    }}
"""

def apply_global_style(app):
    app.setStyle('Fusion')