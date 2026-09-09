"""Dashboard page with KPI cards and quick actions."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from lgus_dat.desktop.desktop_controller import DesktopController
from lgus_dat.desktop.widgets.kpi_card import KpiCard


class DashboardPage(QWidget):
    """Dashboard with summary metrics and quick actions."""

    quick_action = Signal(str)

    def __init__(self, controller: DesktopController, parent=None) -> None:
        super().__init__(parent)
        self.controller = controller
        self._build_ui()
        self.refresh()

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
        self.kpi_imported = KpiCard("Imported Logs", "0")

        kpi_layout.addWidget(self.kpi_total_employees)
        kpi_layout.addWidget(self.kpi_total_records)
        kpi_layout.addWidget(self.kpi_processed)
        kpi_layout.addWidget(self.kpi_unpaired)
        kpi_layout.addWidget(self.kpi_imported)
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
            btn.clicked.connect(lambda _checked=False, action=label: self.quick_action.emit(action))
            actions_layout.addWidget(btn)

        actions_layout.addStretch()
        layout.addLayout(actions_layout)

        layout.addStretch()

    def refresh(self) -> None:
        """Refresh dashboard metrics from the controller."""
        state = self.controller.ui.state
        registry = self.controller.registry

        employee_count = len(registry.all_employees())
        total_records = len(state.parsed_records)
        processed_count = len(state.all_processed_records)
        unpaired_count = sum(
            1 for rec in state.all_processed_records
            if rec.exception_flag == "UNPAIRED_FINAL_IN"
        )
        imported_logs = registry.count_attendance_logs()

        self.kpi_total_employees.set_value(str(employee_count))
        self.kpi_total_records.set_value(str(total_records))
        self.kpi_processed.set_value(str(processed_count))
        self.kpi_unpaired.set_value(str(unpaired_count))
        self.kpi_imported.set_value(str(imported_logs))
