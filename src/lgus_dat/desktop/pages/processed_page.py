"""Processed records page with filters and output table."""

from __future__ import annotations

from datetime import datetime, time

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QCheckBox,
    QDateEdit,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from lgus_dat.desktop.desktop_controller import DesktopController
from lgus_dat.domain.attendance_record import PunchStatus


class ProcessedPage(QWidget):
    """Page for viewing processed attendance records and applying filters."""

    def __init__(self, controller: DesktopController, parent=None) -> None:
        super().__init__(parent)
        self.controller = controller
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        header = QLabel("Processed Records")
        header.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(header)

        # Filter controls
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

        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Edit control
        edit_layout = QHBoxLayout()
        edit_btn = QPushButton("Edit Selected Status")
        edit_btn.clicked.connect(self._edit_status)
        edit_layout.addWidget(edit_btn)
        edit_layout.addStretch()
        layout.addLayout(edit_layout)

        # Results table
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

    def refresh(self) -> None:
        """Refresh the table from the controller's processed records."""
        records = self.controller.ui.state.processed_records
        self._populate(records)

    def _populate(self, records) -> None:
        self.table.setRowCount(len(records))
        for row, rec in enumerate(records):
            name = rec.employee_name or self.controller.ui.get_employee_name(rec.employee_id) or ""
            self.table.setItem(row, 0, QTableWidgetItem(rec.employee_id))
            self.table.setItem(row, 1, QTableWidgetItem(name))
            self.table.setItem(row, 2, QTableWidgetItem(str(rec.punch_date)))
            self.table.setItem(row, 3, QTableWidgetItem(rec.punch_time))
            self.table.setItem(row, 4, QTableWidgetItem(rec.status.value))
            self.table.setItem(row, 5, QTableWidgetItem(rec.exception_flag or ""))
            self.table.setItem(row, 6, QTableWidgetItem(rec.original_record))

    def _apply_filters(self) -> None:
        query = self.search_field.text().strip()

        if self.start_date_check.isChecked() or self.end_date_check.isChecked():
            start = None
            end = None

            if self.start_date_check.isChecked():
                qdate = self.start_date.date().toPython()
                start = datetime.combine(qdate, time.min)

            if self.end_date_check.isChecked():
                qdate = self.end_date.date().toPython()
                end = datetime.combine(qdate, time.max)

            self.controller.ui.apply_date_filter(start, end)

        self.controller.ui.apply_search_filter(query)
        self._populate(self.controller.ui.state.processed_records)

    def _clear_filters(self) -> None:
        self.search_field.clear()
        self.start_date_check.setChecked(False)
        self.end_date_check.setChecked(False)
        self.controller.ui.clear_filters()
        self._populate(self.controller.ui.state.processed_records)

    def _edit_status(self) -> None:
        selected = self.table.selectedItems()
        if not selected:
            return

        row = selected[0].row()
        records = self.controller.ui.state.processed_records
        if row >= len(records):
            return

        record = records[row]
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
        self._populate(self.controller.ui.state.processed_records)
