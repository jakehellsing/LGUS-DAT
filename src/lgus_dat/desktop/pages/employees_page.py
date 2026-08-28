"""Employees and departments management page."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class EmployeesPage(QWidget):
    """Page for managing employees and departments."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        header = QLabel("Employees & Departments")
        header.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(header)

        info = QLabel("Manage employees, departments, and mappings here.")
        layout.addWidget(info)

        layout.addStretch()
