"""Import page for .DAT files."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from lgus_dat.desktop.desktop_controller import DesktopController
from lgus_dat.desktop.widgets.progress_dialog import ProgressDialog


class ImportPage(QWidget):
    """Page for importing attendance .dat, user.dat, and department.dat files."""

    process_requested = Signal()

    def __init__(self, controller: DesktopController, parent=None) -> None:
        super().__init__(parent)
        self.controller = controller
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        header = QLabel("Import Data")
        header.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(header)

        info = QLabel("Open attendance .dat, user.dat, or department.dat files.")
        layout.addWidget(info)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        open_btn = QPushButton("Open attendance.dat")
        open_btn.clicked.connect(self._open_attendance)
        btn_layout.addWidget(open_btn)

        user_btn = QPushButton("Import user.dat")
        user_btn.clicked.connect(self._open_user_dat)
        btn_layout.addWidget(user_btn)

        dept_btn = QPushButton("Import department.dat")
        dept_btn.clicked.connect(self._open_department_dat)
        btn_layout.addWidget(dept_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Process action
        process_layout = QHBoxLayout()
        process_layout.setSpacing(12)

        process_label = QLabel("Process for month:")
        process_layout.addWidget(process_label)

        self.month_edit = QLineEdit()
        self.month_edit.setPlaceholderText("YYYY-MM")
        self.month_edit.setMaximumWidth(100)
        process_layout.addWidget(self.month_edit)

        process_btn = QPushButton("Process")
        process_btn.setStyleSheet("font-weight: bold;")
        process_btn.clicked.connect(self._process)
        process_layout.addWidget(process_btn)

        process_all_btn = QPushButton("Process All")
        process_all_btn.clicked.connect(self._process_all)
        process_layout.addWidget(process_all_btn)

        process_layout.addStretch()
        layout.addLayout(process_layout)

        # Results table
        table_label = QLabel("Raw Input Preview")
        table_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(table_label)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Employee ID", "Employee Name", "Timestamp", "Original Record"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

    def _open_attendance(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select MB10-VL .DAT export",
            "",
            "DAT files (*.dat);;All files (*.*)",
        )
        if not path:
            return

        result = ProgressDialog("Importing", "Loading attendance .dat file...", self).run_task(
            lambda: self.controller.load_attendance(Path(path))
        )
        if result is None:
            return

        loaded_path, records, errors, new_count = result

        self.table.setRowCount(len(records))
        for row, rec in enumerate(records):
            name = self.controller.ui.get_employee_name(rec.employee_id) or ""
            self.table.setItem(row, 0, QTableWidgetItem(rec.employee_id))
            self.table.setItem(row, 1, QTableWidgetItem(name))
            self.table.setItem(row, 2, QTableWidgetItem(rec.timestamp.strftime("%Y-%m-%d %H:%M:%S")))
            self.table.setItem(row, 3, QTableWidgetItem(rec.original_line))

    def _open_user_dat(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select user.dat",
            "",
            "DAT files (*.dat);;All files (*.*)",
        )
        if not path:
            return
        ProgressDialog("Importing", "Loading user.dat...", self).run_task(
            lambda: self.controller.ui.import_user_dat(Path(path))
        )

    def _open_department_dat(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select department.dat",
            "",
            "DAT files (*.dat);;All files (*.*)",
        )
        if not path:
            return
        ProgressDialog("Importing", "Loading department.dat...", self).run_task(
            lambda: self.controller.ui.import_department_dat(Path(path))
        )

    def _process(self) -> None:
        if not self.controller.ui.state.parsed_records:
            QMessageBox.warning(self, "No Data", "Import an attendance .dat file first.")
            return

        month_text = self.month_edit.text().strip()
        try:
            year, month = map(int, month_text.split("-"))
        except ValueError:
            QMessageBox.warning(self, "Invalid Month", "Enter month as YYYY-MM.")
            return

        filtered = [
            rec for rec in self.controller.ui.state.parsed_records
            if rec.timestamp.year == year and rec.timestamp.month == month
        ]

        if not filtered:
            QMessageBox.information(self, "No Records", f"No records found for {month_text}.")
            return

        ProgressDialog("Processing", f"Processing records for {month_text}...", self).run_task(
            lambda: self.controller.ui.process_records(filtered)
        )
        self.process_requested.emit()

    def _process_all(self) -> None:
        if not self.controller.ui.state.parsed_records:
            QMessageBox.warning(self, "No Data", "Import an attendance .dat file first.")
            return
        ProgressDialog("Processing", "Processing all records...", self).run_task(
            lambda: self.controller.ui.process_records()
        )
        self.process_requested.emit()
