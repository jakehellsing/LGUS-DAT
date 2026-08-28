"""Dashboard page with KPI cards and quick actions."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from lgus_dat.desktop.widgets.kpi_card import KpiCard


class DashboardPage(QWidget):
    """Dashboard with summary metrics and quick actions."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        header = QLabel("Dashboard")
        header.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(header)

        # KPI cards
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(16)

        self.kpi_total_employees = KpiCard("Total Employees", "0")
        self.kpi_total_records = KpiCard("Total Records", "0")
        self.kpi_processed = KpiCard("Processed Records", "0")
        self.kpi_unpaired = KpiCard("Unpaired IN", "0")
        self.kpi_errors = KpiCard("Import Errors", "0")

        kpi_layout.addWidget(self.kpi_total_employees)
        kpi_layout.addWidget(self.kpi_total_records)
        kpi_layout.addWidget(self.kpi_processed)
        kpi_layout.addWidget(self.kpi_unpaired)
        kpi_layout.addWidget(self.kpi_errors)
        kpi_layout.addStretch()

        layout.addLayout(kpi_layout)

        # Quick actions
        actions_label = QLabel("Quick Actions")
        actions_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(actions_label)

        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(12)

        for label in ["Open .DAT File", "Process Records", "Generate DTR PDF", "Export CSV"]:
            btn = QPushButton(label)
            btn.setEnabled(False)
            actions_layout.addWidget(btn)

        actions_layout.addStretch()
        layout.addLayout(actions_layout)

        layout.addStretch()
