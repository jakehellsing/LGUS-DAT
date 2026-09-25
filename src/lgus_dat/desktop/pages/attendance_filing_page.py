"""Attendance filing page for holidays, leave types, and employee status."""

from __future__ import annotations

from datetime import date

from PySide6.QtCore import Qt, QDate
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from lgus_dat.desktop.desktop_controller import DesktopController
from lgus_dat.domain.attendance_filing import AttendanceFiling
from lgus_dat.domain.holiday import Holiday


class AttendanceFilingPage(QWidget):
    """Page for configuring holidays, status types, and employee filings."""

    def __init__(self, controller: DesktopController, parent=None) -> None:
        super().__init__(parent)
        self.controller = controller
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        header = QLabel("Attendance Filing")
        header.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(header)

        self.tabs = QTabWidget()

        self.holidays_tab = QWidget()
        self._build_holidays_tab()
        self.tabs.addTab(self.holidays_tab, "Holidays")

        self.leave_types_tab = QWidget()
        self._build_leave_types_tab()
        self.tabs.addTab(self.leave_types_tab, "Leave Types")

        self.filings_tab = QWidget()
        self._build_filings_tab()
        self.tabs.addTab(self.filings_tab, "File Leave/Status")

        layout.addWidget(self.tabs)

    # ------------------------------------------------------------------
    # Holidays tab
    # ------------------------------------------------------------------

    def _build_holidays_tab(self) -> None:
        layout = QVBoxLayout(self.holidays_tab)

        controls = QHBoxLayout()
        controls.setSpacing(12)

        self.holiday_date = QDateEdit()
        self.holiday_date.setCalendarPopup(True)
        self.holiday_date.setDisplayFormat("yyyy-MM-dd")
        self.holiday_date.setDate(QDate.currentDate())
        controls.addWidget(QLabel("Date:"))
        controls.addWidget(self.holiday_date)

        self.holiday_name = QLineEdit()
        self.holiday_name.setPlaceholderText("Holiday Name")
        controls.addWidget(self.holiday_name)

        add_holiday_btn = QPushButton("Add Holiday")
        add_holiday_btn.clicked.connect(self._add_holiday)
        controls.addWidget(add_holiday_btn)

        del_holiday_btn = QPushButton("Delete Selected")
        del_holiday_btn.clicked.connect(self._delete_holiday)
        controls.addWidget(del_holiday_btn)

        controls.addStretch()
        layout.addLayout(controls)

        self.holidays_table = QTableWidget()
        self.holidays_table.setColumnCount(2)
        self.holidays_table.setHorizontalHeaderLabels(["Date", "Name"])
        self.holidays_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.holidays_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.holidays_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.holidays_table.setSortingEnabled(True)
        layout.addWidget(self.holidays_table)

    def _refresh_holidays(self) -> None:
        self.holidays_table.horizontalHeader().setSortIndicator(-1, Qt.AscendingOrder)
        self.holidays_table.setRowCount(0)
        holidays = self.controller.registry.all_holidays()
        self.holidays_table.setRowCount(len(holidays))
        for row, holiday in enumerate(holidays):
            self.holidays_table.setItem(row, 0, QTableWidgetItem(holiday.holiday_date.isoformat()))
            self.holidays_table.setItem(row, 1, QTableWidgetItem(holiday.name))

    def _add_holiday(self) -> None:
        name = self.holiday_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Missing Data", "Holiday name is required.")
            return

        qdate = self.holiday_date.date()
        holiday = Holiday(
            holiday_date=date(qdate.year(), qdate.month(), qdate.day()),
            name=name,
        )
        self.controller.registry.upsert_holiday(holiday)
        self.holiday_name.clear()
        self._refresh_holidays()

    def _delete_holiday(self) -> None:
        selected = self.holidays_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select a holiday to delete.")
            return

        row = selected[0].row()
        date_text = self.holidays_table.item(row, 0).text()
        self.controller.registry.delete_holiday(date.fromisoformat(date_text))
        self._refresh_holidays()

    # ------------------------------------------------------------------
    # Leave types tab
    # ------------------------------------------------------------------

    def _build_leave_types_tab(self) -> None:
        layout = QVBoxLayout(self.leave_types_tab)

        controls = QHBoxLayout()
        controls.setSpacing(12)

        self.leave_type_input = QLineEdit()
        self.leave_type_input.setPlaceholderText("Leave / Status Type")
        controls.addWidget(self.leave_type_input)

        add_type_btn = QPushButton("Add")
        add_type_btn.clicked.connect(self._add_leave_type)
        controls.addWidget(add_type_btn)

        edit_type_btn = QPushButton("Edit")
        edit_type_btn.clicked.connect(self._edit_leave_type)
        controls.addWidget(edit_type_btn)

        del_type_btn = QPushButton("Delete")
        del_type_btn.clicked.connect(self._delete_leave_type)
        controls.addWidget(del_type_btn)

        controls.addStretch()
        layout.addLayout(controls)

        self.leave_types_table = QTableWidget()
        self.leave_types_table.setColumnCount(1)
        self.leave_types_table.setHorizontalHeaderLabels(["Leave / Status Type"])
        self.leave_types_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.leave_types_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.leave_types_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.leave_types_table.setSortingEnabled(True)
        layout.addWidget(self.leave_types_table)

    def _refresh_leave_types(self) -> None:
        self.leave_types_table.horizontalHeader().setSortIndicator(-1, Qt.AscendingOrder)
        self.leave_types_table.setRowCount(0)
        leave_types = self.controller.registry.all_leave_types()
        self.leave_types_table.setRowCount(len(leave_types))
        for row, name in enumerate(leave_types):
            self.leave_types_table.setItem(row, 0, QTableWidgetItem(name))

    def _add_leave_type(self) -> None:
        name = self.leave_type_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Missing Data", "Leave/Status type name is required.")
            return
        self.controller.registry.add_leave_type(name)
        self.leave_type_input.clear()
        self._refresh_leave_types()
        self._refresh_status_combos()

    def _edit_leave_type(self) -> None:
        selected = self.leave_types_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select a type to edit.")
            return

        row = selected[0].row()
        old_name = self.leave_types_table.item(row, 0).text()
        new_name, ok = QInputDialog.getText(
            self, "Edit Type", f"Rename '{old_name}' to:", text=old_name
        )
        if not ok or not new_name.strip() or new_name.strip() == old_name:
            return

        self.controller.registry.rename_leave_type(old_name, new_name.strip())
        self._refresh_leave_types()
        self._refresh_status_combos()

    def _delete_leave_type(self) -> None:
        selected = self.leave_types_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select a type to delete.")
            return

        row = selected[0].row()
        name = self.leave_types_table.item(row, 0).text()
        self.controller.registry.delete_leave_type(name)
        self._refresh_leave_types()
        self._refresh_status_combos()

    # ------------------------------------------------------------------
    # Employee filings tab
    # ------------------------------------------------------------------

    def _build_filings_tab(self) -> None:
        layout = QVBoxLayout(self.filings_tab)

        controls = QVBoxLayout()
        controls.setSpacing(8)

        top = QHBoxLayout()
        top.setSpacing(12)

        left_panel = QVBoxLayout()
        self.employee_filter = QLineEdit()
        self.employee_filter.setPlaceholderText("Filter employees...")
        self.employee_filter.setMinimumWidth(160)
        self.employee_filter.textChanged.connect(self._refresh_employee_list)
        left_panel.addWidget(self.employee_filter)

        list_layout = QVBoxLayout()
        list_layout.addWidget(QLabel("Employees (check to file):"))
        self.employee_list = QListWidget()
        self.employee_list.setMinimumHeight(140)
        self.employee_list.itemChanged.connect(self._update_selected_employees)
        self.employee_list.itemPressed.connect(self._on_employee_pressed)
        self.employee_list.itemClicked.connect(self._on_employee_clicked)
        self._last_pressed_check_state = None
        list_layout.addWidget(self.employee_list)

        list_btn_layout = QHBoxLayout()
        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(self._select_all_employees)
        list_btn_layout.addWidget(select_all_btn)
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self._clear_employee_selection)
        list_btn_layout.addWidget(clear_btn)
        list_btn_layout.addStretch()
        list_layout.addLayout(list_btn_layout)

        left_panel.addLayout(list_layout)
        top.addLayout(left_panel, stretch=1)

        selected_layout = QVBoxLayout()
        selected_layout.addWidget(QLabel("Selected employees:"))
        self.selected_employees_list = QListWidget()
        self.selected_employees_list.setMinimumHeight(140)
        selected_layout.addWidget(self.selected_employees_list)
        top.addLayout(selected_layout, stretch=1)

        controls.addLayout(top)

        bottom = QHBoxLayout()
        bottom.setSpacing(12)

        bottom.addWidget(QLabel("Start:"))
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDisplayFormat("yyyy-MM-dd")
        self.start_date.setDate(QDate.currentDate())
        bottom.addWidget(self.start_date)

        bottom.addWidget(QLabel("End:"))
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDisplayFormat("yyyy-MM-dd")
        self.end_date.setDate(QDate.currentDate())
        bottom.addWidget(self.end_date)

        bottom.addWidget(QLabel("Status:"))
        self.status_combo = QComboBox()
        self.status_combo.setMinimumWidth(140)
        bottom.addWidget(self.status_combo)

        add_filing_btn = QPushButton("File")
        add_filing_btn.clicked.connect(self._add_filing)
        bottom.addWidget(add_filing_btn)

        del_filing_btn = QPushButton("Delete Selected")
        del_filing_btn.clicked.connect(self._delete_filing)
        bottom.addWidget(del_filing_btn)

        bottom.addStretch()
        controls.addLayout(bottom)

        layout.addLayout(controls)

        self.filings_table = QTableWidget()
        self.filings_table.setColumnCount(6)
        self.filings_table.setHorizontalHeaderLabels(["Employee ID", "Employee Name", "Start", "End", "Status", "Filing ID"])
        self.filings_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.filings_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.filings_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.filings_table.setColumnHidden(5, True)
        self.filings_table.setSortingEnabled(True)
        layout.addWidget(self.filings_table)

    def _refresh_employee_list(self) -> None:
        filter_text = self.employee_filter.text().strip().lower()
        checked = set()
        for i in range(self.employee_list.count()):
            item = self.employee_list.item(i)
            if item.checkState() == Qt.Checked:
                checked.add(item.data(Qt.UserRole))
        self.employee_list.blockSignals(True)
        self.employee_list.clear()
        for emp in self.controller.registry.all_employees():
            display = emp.full_name or emp.name
            if filter_text and filter_text not in display.lower():
                continue
            item = QListWidgetItem(display)
            item.setData(Qt.UserRole, emp.device_user_id)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if emp.device_user_id in checked else Qt.Unchecked)
            self.employee_list.addItem(item)
        self.employee_list.blockSignals(False)
        self._update_selected_employees()

    def _update_selected_employees(self) -> None:
        self.selected_employees_list.clear()
        for i in range(self.employee_list.count()):
            item = self.employee_list.item(i)
            if item.checkState() == Qt.Checked:
                QListWidgetItem(item.text(), self.selected_employees_list)

    def _on_employee_pressed(self, item: QListWidgetItem) -> None:
        self._last_pressed_check_state = item.checkState()

    def _on_employee_clicked(self, item: QListWidgetItem) -> None:
        if item.checkState() == self._last_pressed_check_state:
            item.setCheckState(Qt.Unchecked if item.checkState() == Qt.Checked else Qt.Checked)

    def _select_all_employees(self) -> None:
        self.employee_list.blockSignals(True)
        for i in range(self.employee_list.count()):
            self.employee_list.item(i).setCheckState(Qt.Checked)
        self.employee_list.blockSignals(False)
        self._update_selected_employees()

    def _clear_employee_selection(self) -> None:
        self.employee_list.blockSignals(True)
        for i in range(self.employee_list.count()):
            self.employee_list.item(i).setCheckState(Qt.Unchecked)
        self.employee_list.blockSignals(False)
        self._update_selected_employees()

    def _refresh_status_combos(self) -> None:
        current = self.status_combo.currentData()
        self.status_combo.clear()
        for name in self.controller.registry.all_leave_types():
            self.status_combo.addItem(name, name)

        for i in range(self.status_combo.count()):
            if self.status_combo.itemData(i) == current:
                self.status_combo.setCurrentIndex(i)
                break

    def _refresh_filings(self) -> None:
        self.filings_table.horizontalHeader().setSortIndicator(-1, Qt.AscendingOrder)
        self.filings_table.setRowCount(0)
        filings = self.controller.registry.all_employee_status_filings()
        self.filings_table.setRowCount(len(filings))

        for row, filing in enumerate(filings):
            emp = self.controller.registry.get_employee(filing.employee_id)
            emp_name = emp.name if emp else ""
            self.filings_table.setItem(row, 0, QTableWidgetItem(filing.employee_id))
            self.filings_table.setItem(row, 1, QTableWidgetItem(emp_name))
            self.filings_table.setItem(row, 2, QTableWidgetItem(filing.start_date.isoformat()))
            self.filings_table.setItem(row, 3, QTableWidgetItem(filing.end_date.isoformat()))
            self.filings_table.setItem(row, 4, QTableWidgetItem(filing.status))
            id_item = QTableWidgetItem(str(filing.filing_id) if filing.filing_id else "")
            id_item.setData(Qt.UserRole, filing.filing_id)
            self.filings_table.setItem(row, 5, id_item)

    def _add_filing(self) -> None:
        selected_ids = []
        for i in range(self.employee_list.count()):
            item = self.employee_list.item(i)
            if item.checkState() == Qt.Checked:
                selected_ids.append(item.data(Qt.UserRole))
        if not selected_ids:
            QMessageBox.warning(self, "Missing Data", "Please check at least one employee by clicking the checkbox next to their name.")
            return

        status = self.status_combo.currentData()
        if not status:
            QMessageBox.warning(self, "Missing Data", "Please select a status.")
            return

        qstart = self.start_date.date()
        qend = self.end_date.date()
        start = date(qstart.year(), qstart.month(), qstart.day())
        end = date(qend.year(), qend.month(), qend.day())

        if end < start:
            QMessageBox.warning(self, "Validation", "End date cannot be earlier than start date.")
            return

        try:
            for employee_id in selected_ids:
                filing = AttendanceFiling(
                    employee_id=employee_id,
                    start_date=start,
                    end_date=end,
                    status=status,
                )
                self.controller.registry.file_employee_status(filing)
            self._refresh_filings()
        except Exception as exc:
            QMessageBox.critical(self, "Filing Error", str(exc))

    def _delete_filing(self) -> None:
        selected = self.filings_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select a filing to delete.")
            return

        row = selected[0].row()
        filing_id = self.filings_table.item(row, 5).data(Qt.UserRole)
        if filing_id is None:
            return

        self.controller.registry.delete_employee_status_filing(filing_id)
        self._refresh_filings()

    # ------------------------------------------------------------------
    # Page refresh
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """Refresh all tables and combo boxes from the registry."""
        self._refresh_holidays()
        self._refresh_leave_types()
        self._refresh_employee_list()
        self._refresh_status_combos()
        self._refresh_filings()
