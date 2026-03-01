from PySide6.QtGui import QFont
from PySide6.QtCore import Qt

COLORS = {
    "bg_white": "#FAFAFA",
    "bg_soft": "#F2F4F7",
    "bg_card": "#FFFFFF",
    "accent_yellow": "#F5C842",
    "accent_orange": "#F0842C",
    "accent_blue": "#3B82F6",
    "accent_green": "#22C55E",
    "accent_red": "#EF4444",
    "accent_purple": "#8B5CF6",
    "text_dark": "#0F172A",
    "text_mid": "#475569",
    "text_soft": "#94A3B8",
    "border": "#E2E8F0",
    "border_focus": "#F5C842",
}

def get_font_regular(size=12):
    font = QFont("Segoe UI", size)
    return font

def get_font_bold(size=14):
    font = QFont("Segoe UI", size, QFont.Bold)
    return font

def get_font_large(size=24):
    font = QFont("Segoe UI", size, QFont.Bold)
    return font

BUTTON_PRIMARY = f"""
    QPushButton {{
        background-color: {COLORS['accent_yellow']};
        color: {COLORS['text_dark']};
        border: none;
        border-radius: 12px;
        padding: 12px 28px;
        font-size: 16px;
        padding: 14px 32px;
        font-weight: bold;
        font-family: 'Segoe UI';
    }}
    QPushButton:hover {{
        background-color: {COLORS['accent_orange']};
        color: white;
    }}
    QPushButton:pressed {{
        background-color: #d97706;
    }}
"""

BUTTON_SECONDARY = f"""
    QPushButton {{
        background-color: {COLORS['bg_soft']};
        color: {COLORS['text_dark']};
        border: 1.5px solid {COLORS['border']};
        border-radius: 12px;
        padding: 10px 22px;
        font-size: 13px;
        font-weight: bold;
        font-family: 'Segoe UI';
    }}
    QPushButton:hover {{
        background-color: {COLORS['border']};
        border-color: {COLORS['accent_yellow']};
    }}
"""

BUTTON_DANGER = f"""
    QPushButton {{
        background-color: #FEF2F2;
        color: {COLORS['accent_red']};
        border: 1.5px solid #FECACA;
        border-radius: 12px;
        padding: 10px 22px;
        font-size: 13px;
        font-weight: bold;
        font-family: 'Segoe UI';
    }}
    QPushButton:hover {{
        background-color: {COLORS['accent_red']};
        color: white;
        border-color: {COLORS['accent_red']};
    }}
"""

BUTTON_SUCCESS = f"""
    QPushButton {{
        background-color: #F0FDF4;
        color: {COLORS['accent_green']};
        border: 1.5px solid #BBF7D0;
        border-radius: 12px;
        padding: 10px 22px;
        font-size: 13px;
        font-weight: bold;
        font-family: 'Segoe UI';
    }}
    QPushButton:hover {{
        background-color: {COLORS['accent_green']};
        color: white;
        border-color: {COLORS['accent_green']};
    }}
"""

CARD_STYLE = f"""
    QFrame {{
        background-color: {COLORS['bg_card']};
        border-radius: 16px;
        border: 1.5px solid {COLORS['border']};
    }}
"""

INPUT_STYLE = f"""
    QLineEdit {{
        padding: 11px 14px;
        border: 1.5px solid {COLORS['border']};
        border-radius: 10px;
        font-size: 14px;
        font-family: 'Segoe UI';
        background-color: white;
        color: {COLORS['text_dark']};
    }}
    QLineEdit:focus {{
        border: 1.5px solid {COLORS['accent_yellow']};
        background-color: #FFFDF0;
    }}
    QLineEdit:hover {{
        border: 1.5px solid {COLORS['text_soft']};
    }}
"""

NAV_BUTTON_ACTIVE = f"""
    QPushButton {{
        background-color: {COLORS['accent_yellow']};
        color: {COLORS['text_dark']};
        border: none;
        border-radius: 10px;
        padding: 8px 18px;
        font-size: 13px;
        font-weight: bold;
        font-family: 'Segoe UI';
    }}
"""

NAV_BUTTON_INACTIVE = f"""
    QPushButton {{
        background-color: transparent;
        color: {COLORS['text_mid']};
        border: none;
        border-radius: 10px;
        padding: 8px 18px;
        font-size: 13px;
        font-family: 'Segoe UI';
    }}
    QPushButton:hover {{
        background-color: {COLORS['bg_soft']};
        color: {COLORS['text_dark']};
    }}
"""

def apply_global_style(app):
    app.setStyle('Fusion')
    app.setStyleSheet(f"""
        QMainWindow, QWidget {{
            background-color: {COLORS['bg_white']};
            font-family: 'Segoe UI';
        }}
        QScrollBar:vertical {{
            background: {COLORS['bg_soft']};
            width: 6px;
            border-radius: 3px;
        }}
        QScrollBar::handle:vertical {{
            background: {COLORS['text_soft']};
            border-radius: 3px;
            min-height: 30px;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0;
        }}
        QToolTip {{
            background: {COLORS['text_dark']};
            color: white;
            border: none;
            padding: 6px 10px;
            border-radius: 6px;
            font-size: 12px;
        }}
    """)
