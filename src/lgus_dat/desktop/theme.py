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
DARK_PALETTE.setColor(QPalette.Button, _DARK_WINDOW)
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
