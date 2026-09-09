"""Daily DTR review page with employee list, calendar preview, and punch editor."""

from __future__ import annotations

import calendar
from collections import defaultdict
from datetime import date

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from lgus_dat.desktop.desktop_controller import DesktopController
from lgus_dat.domain.attendance_record import AttendanceRecord, PunchStatus
from lgus_dat.output.pdf_writer import (
    DailyPunches,
    _calculate_undertime,
    _format_time,
    _map_punches_to_daily_slots,
    _remark,
)


class DailyDTRReviewPage(QWidget):
    """Three-pane page: employees, DTR-style month preview, daily punch editor."""

    def __init__(self, controller: DesktopController, parent=None) -> None:
        super().__init__(parent)
        self.controller = controller
        self._current_month = date.today().replace(day=1)
        self._employee_records: dict[str, list[AttendanceRecord]] = {}
        self._records_by_day: dict[int, list[AttendanceRecord]] = {}
        self._daily_punches: dict[int, DailyPunches] = {}
        self._holidays_by_day: dict[int, str] = {}
        self._employee_status_by_day: dict[int, list[str]] = {}
        self._punch_records: list[AttendanceRecord] = []
        self._current_employee_id: str | None = None
        self._current_day: int | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        self.splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(self.splitter)

        # Left: employee list
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(QLabel("Employees"))

        self.employee_filter = QLineEdit()
        self.employee_filter.setPlaceholderText("Filter employee ID or name...")
        left_layout.addWidget(self.employee_filter)

        self.employee_list = QListWidget()
        self.employee_list.setSelectionMode(QListWidget.SingleSelection)
        left_layout.addWidget(self.employee_list)

        self.splitter.addWidget(left)

        # Center: month DTR preview
        center = QWidget()
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(0, 0, 0, 0)

        controls = QHBoxLayout()
        controls.addWidget(QLabel("Month:"))

        self.month_edit = QComboBox()
        today = date.today()
        for year in range(today.year - 2, today.year + 3):
            for month in range(1, 13):
                month_date = date(year, month, 1)
                display = month_date.strftime("%Y-%m")
                self.month_edit.addItem(display, month_date)
                if month_date == self._current_month:
                    self.month_edit.setCurrentIndex(self.month_edit.count() - 1)
        controls.addWidget(self.month_edit)

        load_btn = QPushButton("Load")
        load_btn.clicked.connect(self._on_load_month)
        controls.addWidget(load_btn)

        controls.addStretch()
        center_layout.addLayout(controls)

        self.dtr_table = QTableWidget()
        self.dtr_table.setColumnCount(8)
        self.dtr_table.setHorizontalHeaderLabels(
            ["Day", "IN AM", "OUT AM", "IN PM", "OUT PM", "Und Hr", "Und Min", "Remarks"]
        )
        self.dtr_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.dtr_table.setSelectionMode(QTableWidget.SingleSelection)
        self.dtr_table.setAlternatingRowColors(True)
        self.dtr_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.dtr_table.setEditTriggers(QTableWidget.NoEditTriggers)
        center_layout.addWidget(self.dtr_table)

        self.splitter.addWidget(center)

        # Right: punches for selected day
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self.punch_header = QLabel("Punches for selected day")
        right_layout.addWidget(self.punch_header)

        self.punch_table = QTableWidget()
        self.punch_table.setColumnCount(2)
        self.punch_table.setHorizontalHeaderLabels(["Time", "Status"])
        self.punch_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.punch_table.setSelectionMode(QTableWidget.SingleSelection)
        self.punch_table.setAlternatingRowColors(True)
        self.punch_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.punch_table.setEditTriggers(QTableWidget.NoEditTriggers)
        right_layout.addWidget(self.punch_table)

        edit_btn = QPushButton("Edit Status")
        edit_btn.clicked.connect(self._edit_punch_status)
        right_layout.addWidget(edit_btn)

        override_layout = QHBoxLayout()
        for slot, label in [
            ("out_am", "Use as DTR AM OUT"),
            ("in_pm", "Use as DTR PM IN"),
            ("out_pm", "Use as DTR PM OUT"),
        ]:
            btn = QPushButton(label)
            btn.clicked.connect(lambda checked, s=slot: self._set_dtr_override(s))
            override_layout.addWidget(btn)
        right_layout.addLayout(override_layout)

        save_btn = QPushButton("Save Overrides")
        save_btn.clicked.connect(self._save_dtr_overrides)
        right_layout.addWidget(save_btn)

        self.splitter.addWidget(right)

        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 3)
        self.splitter.setStretchFactor(2, 2)

        # Connections
        self.employee_filter.textChanged.connect(self._refresh_employee_list)
        self.employee_list.currentRowChanged.connect(self._on_employee_changed)
        self.dtr_table.itemSelectionChanged.connect(self._on_day_selected)

    def refresh(self) -> None:
        """Refresh the employee list and load the current month."""
        self._refresh_employee_list()
        self._on_load_month()

    def _refresh_employee_list(self) -> None:
        filter_text = self.employee_filter.text().strip().lower()
        current_id: str | None = None
        current_item = self.employee_list.currentItem()
        if current_item is not None:
            current_id = current_item.data(Qt.UserRole)

        self.employee_list.clear()
        employees = sorted(
            self.controller.registry.all_employees(),
            key=lambda e: (e.name or "").lower(),
        )

        for emp in employees:
            display = f"{emp.device_user_id} - {emp.name or ''}"
            if filter_text and filter_text not in display.lower():
                continue
            item = QListWidgetItem(display)
            item.setData(Qt.UserRole, emp.device_user_id)
            self.employee_list.addItem(item)

        if current_id is not None:
            for i in range(self.employee_list.count()):
                if self.employee_list.item(i).data(Qt.UserRole) == current_id:
                    self.employee_list.setCurrentRow(i)
                    break

    def _on_employee_changed(self, row: int) -> None:
        if row < 0:
            self._current_employee_id = None
            self._clear_panels()
            return

        item = self.employee_list.item(row)
        if item is None:
            return

        self._current_employee_id = item.data(Qt.UserRole)
        self._refresh_employee_dtr()

    def _on_load_month(self) -> None:
        selected = self.month_edit.currentData()
        if isinstance(selected, date):
            self._current_month = selected
        else:
            self._current_month = date.today().replace(day=1)
        self._current_day = None

        records = self.controller.ui.state.all_processed_records
        if not records:
            records = self.controller.ui.ensure_processed()

        month_records = [
            rec
            for rec in records
            if rec.punch_date.year == self._current_month.year
            and rec.punch_date.month == self._current_month.month
        ]

        self._employee_records = defaultdict(list)
        for rec in month_records:
            self._employee_records[rec.employee_id].append(rec)

        for emp_id in self._employee_records:
            self._employee_records[emp_id].sort(key=lambda r: (r.timestamp, r.original_record))

        self._refresh_employee_list()

        if self._current_employee_id is not None:
            self._refresh_employee_dtr()
        else:
            self._clear_panels()

    def _refresh_employee_dtr(self) -> None:
        if not self._current_employee_id:
            self._clear_panels()
            return

        records = self._employee_records.get(self._current_employee_id, [])
        dtr_overrides = self.controller.ui.get_dtr_overrides_for_employee(
            self._current_employee_id
        )
        self._daily_punches = _map_punches_to_daily_slots(
            records, self._current_month, dtr_overrides
        )

        self._holidays_by_day = self.controller.registry.get_holidays_for_month(
            self._current_month.year, self._current_month.month
        )
        self._employee_status_by_day = self.controller.registry.get_employee_status_for_month(
            self._current_employee_id, self._current_month.year, self._current_month.month
        )

        self._records_by_day = defaultdict(list)
        for rec in records:
            self._records_by_day[rec.punch_date.day].append(rec)

        num_days = calendar.monthrange(self._current_month.year, self._current_month.month)[1]
        self.dtr_table.setRowCount(num_days)

        for day in range(1, num_days + 1):
            punches = self._daily_punches.get(day, DailyPunches(day=day))
            status_labels = self._employee_status_by_day.get(day, [])
            undertime_hr, undertime_min = _calculate_undertime(
                self._current_month.year,
                self._current_month.month,
                day,
                punches,
                status_labels,
                self._holidays_by_day,
            )
            remark = _remark(
                self._current_month.year,
                self._current_month.month,
                day,
                self._holidays_by_day,
                self._employee_status_by_day,
            )

            self.dtr_table.setItem(day - 1, 0, QTableWidgetItem(str(day)))
            self.dtr_table.setItem(day - 1, 1, QTableWidgetItem(_format_time(punches.in_am)))
            self.dtr_table.setItem(day - 1, 2, QTableWidgetItem(_format_time(punches.out_am)))
            self.dtr_table.setItem(day - 1, 3, QTableWidgetItem(_format_time(punches.in_pm)))
            self.dtr_table.setItem(day - 1, 4, QTableWidgetItem(_format_time(punches.out_pm)))
            self.dtr_table.setItem(
                day - 1, 5, QTableWidgetItem(str(undertime_hr) if undertime_hr else "")
            )
            self.dtr_table.setItem(
                day - 1, 6, QTableWidgetItem(str(undertime_min) if undertime_min or undertime_hr else "")
            )
            self.dtr_table.setItem(day - 1, 7, QTableWidgetItem(remark))

        if self._current_day is not None and 1 <= self._current_day <= num_days:
            self.dtr_table.selectRow(self._current_day - 1)
        else:
            self._clear_punch_table()

    def _on_day_selected(self) -> None:
        row = self.dtr_table.currentRow()
        if row < 0:
            self._current_day = None
            self._clear_punch_table()
            return

        num_days = calendar.monthrange(self._current_month.year, self._current_month.month)[1]
        day = row + 1
        if day > num_days:
            self._current_day = None
            self._clear_punch_table()
            return

        self._current_day = day
        self._refresh_punch_table(day)

    def _refresh_punch_table(self, day: int) -> None:
        records = self._records_by_day.get(day, [])
        self._punch_records = records

        self.punch_table.setRowCount(len(records))
        for row, rec in enumerate(records):
            self.punch_table.setItem(row, 0, QTableWidgetItem(rec.punch_time))
            self.punch_table.setItem(row, 1, QTableWidgetItem(rec.status.value))

        display_name = self._current_employee_id or ""
        emp = self.controller.registry.get_employee(display_name)
        if emp is not None:
            display_name = f"{emp.device_user_id} - {emp.name or ''}"

        self.punch_header.setText(
            f"Punches for {display_name} on {self._current_month:%Y-%m}-{day:02d}"
        )

    def _edit_punch_status(self) -> None:
        selected = self.punch_table.selectedItems()
        if not selected:
            return

        row = selected[0].row()
        if row >= len(self._punch_records):
            return

        record = self._punch_records[row]
        items = [PunchStatus.IN.value, PunchStatus.OUT.value]
        status_text, ok = QInputDialog.getItem(
            self,
            "Edit Status",
            "Select the new status:",
            items,
            items.index(record.status.value),
            False,
        )
        if not ok:
            return

        new_status = PunchStatus(status_text)
        self.controller.ui.edit_record_status(record, new_status)

        # Reload from the now-edited state and refresh both panels
        selected_day = self._current_day
        self._on_load_month()
        if self._current_employee_id is not None and selected_day is not None:
            self.dtr_table.selectRow(selected_day - 1)

    def _set_dtr_override(self, slot: str) -> None:
        if self._current_employee_id is None or self._current_day is None:
            return

        selected = self.punch_table.selectedItems()
        if not selected:
            return

        row = selected[0].row()
        if row >= len(self._punch_records):
            return

        record = self._punch_records[row]
        punch_date = date(
            self._current_month.year,
            self._current_month.month,
            self._current_day,
        )
        self.controller.ui.set_dtr_override(
            self._current_employee_id,
            punch_date,
            slot,
            record.punch_time,
        )
        self._refresh_employee_dtr()
        if self._current_day is not None:
            self.dtr_table.selectRow(self._current_day - 1)

    def _save_dtr_overrides(self) -> None:
        if self._current_employee_id is None:
            return
        self.controller.ui.save_dtr_overrides_for_employee(self._current_employee_id)

    def _clear_panels(self) -> None:
        self.dtr_table.setRowCount(0)
        self._clear_punch_table()

    def _clear_punch_table(self) -> None:
        self._punch_records = []
        self.punch_table.setRowCount(0)
        self.punch_header.setText("Punches for selected day")
