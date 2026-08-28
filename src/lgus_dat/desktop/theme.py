"""Theme definitions for the PySide6 desktop UI."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette


LIGHT_PALETTE = QPalette()
DARK_PALETTE = QPalette()

_DARK_WINDOW = QColor("#1e1e1e")
_DARK_BASE = QColor("#252526")
_DARK_TEXT = QColor("#f0f0f0")
_DARK_DISABLED = QColor("#6e6e6e")

DARK_PALETTE.setColor(QPalette.Window, _DARK_WINDOW)
DARK_PALETTE.setColor(QPalette.WindowText, _DARK_TEXT)
DARK_PALETTE.setColor(QPalette.Base, _DARK_BASE)
DARK_PALETTE.setColor(QPalette.AlternateBase, _DARK_WINDOW)
DARK_PALETTE.setColor(QPalette.Text, _DARK_TEXT)
DARK_PALETTE.setColor(QPalette.Button, _DARK_BASE)
DARK_PALETTE.setColor(QPalette.ButtonText, _DARK_TEXT)
DARK_PALETTE.setColor(QPalette.Disabled, QPalette.Text, _DARK_DISABLED)
DARK_PALETTE.setColor(QPalette.Highlight, QColor("#0078d4"))
DARK_PALETTE.setColor(QPalette.HighlightedText, _DARK_TEXT)
DARK_PALETTE.setColor(QPalette.PlaceholderText, _DARK_DISABLED)


LIGHT_PALETTE.setColor(QPalette.Window, QColor("#f8f9fa"))
LIGHT_PALETTE.setColor(QPalette.WindowText, QColor("#1e1e1e"))
LIGHT_PALETTE.setColor(QPalette.Base, QColor("#ffffff"))
LIGHT_PALETTE.setColor(QPalette.AlternateBase, QColor("#f8f9fa"))
LIGHT_PALETTE.setColor(QPalette.Text, QColor("#1e1e1e"))
LIGHT_PALETTE.setColor(QPalette.Button, QColor("#e9ecef"))
LIGHT_PALETTE.setColor(QPalette.ButtonText, QColor("#1e1e1e"))
LIGHT_PALETTE.setColor(QPalette.Highlight, QColor("#0078d4"))
LIGHT_PALETTE.setColor(QPalette.HighlightedText, QColor("#ffffff"))
LIGHT_PALETTE.setColor(QPalette.PlaceholderText, QColor("#6c757d"))


def apply_theme(app, dark: bool) -> None:
    """Apply light or dark theme to the QApplication."""
    app.setPalette(DARK_PALETTE if dark else LIGHT_PALETTE)
    app.setStyleSheet(_DARK_STYLESHEET if dark else _LIGHT_STYLESHEET)


_LIGHT_STYLESHEET = """
QPushButton {
    padding: 6px 14px;
    border-radius: 4px;
    border: 1px solid #ced4da;
    background-color: #f8f9fa;
}
QPushButton:hover {
    background-color: #e9ecef;
}
QPushButton:checked {
    background-color: #0078d4;
    color: white;
    border: 1px solid #0078d4;
}
QLineEdit, QSpinBox, QDateEdit {
    padding: 4px 8px;
    border: 1px solid #ced4da;
    border-radius: 4px;
}
QTableWidget {
    border: 1px solid #dee2e6;
    border-radius: 4px;
}
QHeaderView::section {
    padding: 6px;
    background-color: #e9ecef;
    border: 1px solid #dee2e6;
}
"""

_DARK_STYLESHEET = """
QPushButton {
    padding: 6px 14px;
    border-radius: 4px;
    border: 1px solid #3e3e3e;
    background-color: #2d2d30;
    color: #f0f0f0;
}
QPushButton:hover {
    background-color: #3e3e3e;
}
QPushButton:checked {
    background-color: #0078d4;
    color: white;
    border: 1px solid #0078d4;
}
QLineEdit, QSpinBox, QDateEdit {
    padding: 4px 8px;
    border: 1px solid #3e3e3e;
    border-radius: 4px;
    background-color: #2d2d30;
    color: #f0f0f0;
}
QTableWidget {
    border: 1px solid #3e3e3e;
    border-radius: 4px;
    background-color: #252526;
}
QHeaderView::section {
    padding: 6px;
    background-color: #2d2d30;
    border: 1px solid #3e3e3e;
    color: #f0f0f0;
}
"""
