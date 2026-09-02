"""KPI summary card widget for the dashboard."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


class KpiCard(QFrame):
    """A card showing a metric label and value."""

    def __init__(self, title: str, value: str = "0", parent=None) -> None:
        super().__init__(parent)

        self.setFrameShape(QFrame.StyledPanel)
        self.setMinimumWidth(160)
        self.setMinimumHeight(90)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)

        self.value_label = QLabel(value)
        self.value_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        self.value_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("font-size: 12px; color: gray;")

        layout.addWidget(self.value_label)
        layout.addWidget(self.title_label)
        layout.addStretch()

    def set_value(self, value: str) -> None:
        """Update the displayed value."""
        self.value_label.setText(value)
