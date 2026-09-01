"""Standalone window showing all accumulated attendance records."""

from __future__ import annotations

from datetime import datetime, time

from PySide6.QtCore import Qt, QDate
from PySide6.QtWidgets import (
    QCheckBox,
    QDateEdit,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from lgus_dat.desktop.desktop_controller import DesktopController
from lgus_dat.desktop.widgets.progress_dialog import ProgressDialog
from lgus_dat.processing.sequence_processor import process_records
from lgus_dat.ui.date_filter import filter_by_date
from lgus_dat.ui.search_filter import filter_by_search


class AllRecordsWindow(QWidget):
    """Non-modal window that loads and displays every stored attendance log."""

    def __init__(self, controller: DesktopController, parent=None) -> None:
        super().__init__(parent, Qt.Window)
        self.controller = controller
        self.all_records = []
        self._build_ui()
        self.load_data()

    def _build_ui(self) -> None:
        self.setWindowTitle("All Accumulated Attendance Records")
        self.resize(1200, 700)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        header = QLabel("All Accumulated Records")
        header.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(header)

        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(12)

        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("Search employee ID or name...")
        self.search_field.setMinimumWidth(220)
        filter_layout.addWidget(self.search_field)

        search_btn = QPushButton("Search")
        search_btn.clicked.connect(self._apply_filters)
        filter_layout.addWidget(search_btn)

        filter_layout.addSpacing(20)

        self.start_date_check = QCheckBox("From:")
        filter_layout.addWidget(self.start_date_check)

        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDisplayFormat("yyyy-MM-dd")
        self.start_date.setDate(QDate.currentDate())
        self.start_date.setMinimumWidth(120)
        filter_layout.addWidget(self.start_date)

        self.end_date_check = QCheckBox("To:")
        filter_layout.addWidget(self.end_date_check)

        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDisplayFormat("yyyy-MM-dd")
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setMinimumWidth(120)
        filter_layout.addWidget(self.end_date)

        apply_btn = QPushButton("Apply Filter")
        apply_btn.clicked.connect(self._apply_filters)
        filter_layout.addWidget(apply_btn)

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self._clear_filters)
        filter_layout.addWidget(clear_btn)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_data)
        filter_layout.addWidget(refresh_btn)

        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        self.count_label = QLabel("0 records")
        layout.addWidget(self.count_label)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["Employee ID", "Employee Name", "Date", "Time", "Status", "Exception", "Original Record"]
        )
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

    def _load_and_process(self) -> list:
        raw_records = self.controller.registry.get_attendance_logs()
        if not raw_records:
            return []

        employees = {
            emp.device_user_id: emp.name
            for emp in self.controller.registry.all_employees()
        }
        return process_records(raw_records, name_lookup=employees.get)

    def load_data(self) -> None:
        records = ProgressDialog(
            "Loading",
            "Loading and processing all attendance records...",
            self,
        ).run_task(lambda: self._load_and_process())

        self.all_records = records if records is not None else []
        self._apply_filters()

    def _apply_filters(self) -> None:
        records = self.all_records

        if self.start_date_check.isChecked() or self.end_date_check.isChecked():
            start = None
            end = None
            if self.start_date_check.isChecked():
                qdate = self.start_date.date().toPython()
                start = datetime.combine(qdate, time.min)
            if self.end_date_check.isChecked():
                qdate = self.end_date.date().toPython()
                end = datetime.combine(qdate, time.max)
            records = filter_by_date(records, lambda rec: rec.timestamp, start, end)

        query = self.search_field.text().strip()
        if query:
            records = filter_by_search(
                records,
                query,
                [
                    lambda rec: rec.employee_id,
                    lambda rec: rec.employee_name or "",
                ],
            )

        self._populate(records)

    def _clear_filters(self) -> None:
        self.search_field.clear()
        self.start_date_check.setChecked(False)
        self.end_date_check.setChecked(False)
        self._apply_filters()

    def _populate(self, records) -> None:
        self.count_label.setText(f"{len(records)} records")
        self.table.setRowCount(len(records))
        for row, rec in enumerate(records):
            self.table.setItem(row, 0, QTableWidgetItem(rec.employee_id))
            self.table.setItem(row, 1, QTableWidgetItem(rec.employee_name or ""))
            self.table.setItem(row, 2, QTableWidgetItem(str(rec.punch_date)))
            self.table.setItem(row, 3, QTableWidgetItem(rec.punch_time))
            self.table.setItem(row, 4, QTableWidgetItem(rec.status.value))
            self.table.setItem(row, 5, QTableWidgetItem(rec.exception_flag or ""))
            self.table.setItem(row, 6, QTableWidgetItem(rec.original_record))
