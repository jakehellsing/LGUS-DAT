"""Theme definitions for the PySide6 desktop UI."""

from __future__ import annotations

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
#sidebar {
    background-color: #f1f3f5;
    border-right: 1px solid #dee2e6;
}
QLabel#sidebarTitle {
    color: #1e1e1e;
    font-size: 20px;
    font-weight: bold;
}
QLabel#sidebarSubtitle {
    color: #6c757d;
    font-size: 11px;
}
QPushButton {
    padding: 8px 14px;
    border-radius: 6px;
    border: 1px solid #ced4da;
    background-color: #f8f9fa;
    color: #1e1e1e;
}
QPushButton:hover {
    background-color: #e9ecef;
    border-color: #adb5bd;
}
QPushButton:pressed {
    background-color: #d0d0d0;
}
QPushButton:checked {
    background-color: #0078d4;
    color: #ffffff;
    border: 1px solid #0078d4;
    font-weight: 600;
}
#sidebar QPushButton {
    text-align: left;
    background-color: transparent;
    border: 1px solid transparent;
}
#sidebar QPushButton:hover {
    background-color: #e9ecef;
    border-color: #adb5bd;
}
#sidebar QPushButton:pressed {
    background-color: #d0d0d0;
}
#sidebar QPushButton:checked {
    background-color: #0078d4;
    color: #ffffff;
    border: 1px solid #0078d4;
}
QLineEdit, QSpinBox, QDateEdit, QComboBox {
    padding: 6px 10px;
    border: 1px solid #ced4da;
    border-radius: 6px;
    background-color: #ffffff;
    selection-background-color: #0078d4;
}
QLineEdit:focus, QSpinBox:focus, QDateEdit:focus, QComboBox:focus {
    border-color: #0078d4;
}
QTableWidget {
    border: 1px solid #dee2e6;
    border-radius: 8px;
    background-color: #ffffff;
    gridline-color: #e9ecef;
}
QTableWidget::item:selected {
    background-color: #d0ebff;
    color: #1e1e1e;
}
QHeaderView::section {
    padding: 8px;
    background-color: #e9ecef;
    border: none;
    border-bottom: 2px solid #dee2e6;
    font-weight: 600;
    color: #1e1e1e;
}
QFrame#kpiCard {
    background-color: #ffffff;
    border: 1px solid #dee2e6;
    border-radius: 10px;
}
QFrame#kpiCard QLabel#kpiValue {
    color: #1e1e1e;
    font-size: 26px;
    font-weight: bold;
}
QFrame#kpiCard QLabel#kpiTitle {
    color: #6c757d;
    font-size: 12px;
}
QGroupBox {
    border: 1px solid #dee2e6;
    border-radius: 8px;
    margin-top: 12px;
    font-weight: 600;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
}
QTabWidget::pane {
    border: 1px solid #dee2e6;
    border-radius: 0 0 8px 8px;
    border-top: none;
    background-color: #ffffff;
}
QTabBar::tab {
    padding: 8px 16px;
    background-color: #f8f9fa;
    border: 1px solid #dee2e6;
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background-color: #ffffff;
    color: #0078d4;
    font-weight: 600;
}
QTabBar::tab:!selected {
    margin-top: 2px;
}
"""

_DARK_STYLESHEET = """
#sidebar {
    background-color: #2d2d30;
    border-right: 1px solid #3e3e3e;
}
QLabel#sidebarTitle {
    color: #f0f0f0;
    font-size: 20px;
    font-weight: bold;
}
QLabel#sidebarSubtitle {
    color: #a0a0a0;
    font-size: 11px;
}
QPushButton {
    padding: 8px 14px;
    border-radius: 6px;
    border: 1px solid #3e3e3e;
    background-color: #2d2d30;
    color: #f0f0f0;
}
QPushButton:hover {
    background-color: #3e3e3e;
    border-color: #4e4e4e;
}
QPushButton:pressed {
    background-color: #1e1e1e;
}
QPushButton:checked {
    background-color: #0078d4;
    color: #ffffff;
    border: 1px solid #0078d4;
    font-weight: 600;
}
#sidebar QPushButton {
    text-align: left;
    background-color: transparent;
    border: 1px solid transparent;
}
#sidebar QPushButton:hover {
    background-color: #3e3e3e;
    border-color: #4e4e4e;
}
#sidebar QPushButton:pressed {
    background-color: #1e1e1e;
}
#sidebar QPushButton:checked {
    background-color: #0078d4;
    color: #ffffff;
    border: 1px solid #0078d4;
}
QLineEdit, QSpinBox, QDateEdit, QComboBox {
    padding: 6px 10px;
    border: 1px solid #3e3e3e;
    border-radius: 6px;
    background-color: #252526;
    color: #f0f0f0;
    selection-background-color: #0078d4;
}
QLineEdit:focus, QSpinBox:focus, QDateEdit:focus, QComboBox:focus {
    border-color: #0078d4;
}
QTableWidget {
    border: 1px solid #3e3e3e;
    border-radius: 8px;
    background-color: #252526;
    gridline-color: #3e3e3e;
}
QTableWidget::item:selected {
    background-color: #094771;
    color: #f0f0f0;
}
QHeaderView::section {
    padding: 8px;
    background-color: #2d2d30;
    border: none;
    border-bottom: 2px solid #3e3e3e;
    font-weight: 600;
    color: #f0f0f0;
}
QFrame#kpiCard {
    background-color: #252526;
    border: 1px solid #3e3e3e;
    border-radius: 10px;
}
QFrame#kpiCard QLabel#kpiValue {
    color: #f0f0f0;
    font-size: 26px;
    font-weight: bold;
}
QFrame#kpiCard QLabel#kpiTitle {
    color: #a0a0a0;
    font-size: 12px;
}
QGroupBox {
    border: 1px solid #3e3e3e;
    border-radius: 8px;
    margin-top: 12px;
    font-weight: 600;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
}
QTabWidget::pane {
    border: 1px solid #3e3e3e;
    border-radius: 0 0 8px 8px;
    border-top: none;
    background-color: #252526;
}
QTabBar::tab {
    padding: 8px 16px;
    background-color: #2d2d30;
    border: 1px solid #3e3e3e;
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
    color: #f0f0f0;
}
QTabBar::tab:selected {
    background-color: #252526;
    color: #0078d4;
    font-weight: 600;
}
QTabBar::tab:!selected {
    margin-top: 2px;
}
"""
