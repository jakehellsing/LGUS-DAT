"""Employees and departments management page."""

from __future__ import annotations

from collections import Counter
from dataclasses import replace

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from lgus_dat.desktop.desktop_controller import DesktopController
from lgus_dat.domain.department import Department
from lgus_dat.domain.employee import Employee


def _employee_id_key(emp: Employee):
    """Sort key for employee ID that prefers numeric order."""
    try:
        return (0, int(emp.device_user_id))
    except ValueError:
        return (1, emp.device_user_id)


def _department_id_key(dept: Department):
    """Sort key for department ID."""
    return dept.department_id


class NumericTableItem(QTableWidgetItem):
    """QTableWidgetItem that sorts numbers numerically and falls back to string sort."""

    def __lt__(self, other: QTableWidgetItem) -> bool:
        try:
            return int(self.text()) < int(other.text())
        except ValueError:
            return super().__lt__(other)


class EmployeeEditDialog(QDialog):
    """Modal dialog for editing an employee."""

    def __init__(self, controller: DesktopController, employee: Employee, parent=None) -> None:
        super().__init__(parent)
        self.controller = controller
        self.employee = employee
        self.setWindowTitle("Edit Employee")
        self.setModal(True)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QFormLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        self.id_edit = QLineEdit(self.employee.device_user_id)
        self.id_edit.setReadOnly(True)
        layout.addRow("Employee ID:", self.id_edit)

        self.name_edit = QLineEdit(self.employee.name)
        layout.addRow("Name:", self.name_edit)

        self.full_name_edit = QLineEdit(self.employee.full_name or "")
        layout.addRow("Full Name (DTR only):", self.full_name_edit)

        self.position_combo = QComboBox()
        self.position_combo.addItem("None", None)
        for pos in self.controller.registry.all_positions():
            self.position_combo.addItem(pos, pos)
        for i in range(self.position_combo.count()):
            if self.position_combo.itemData(i, Qt.UserRole) == self.employee.position:
                self.position_combo.setCurrentIndex(i)
                break
        layout.addRow("Position (DTR only):", self.position_combo)

        self.dept_combo = QComboBox()
        self.dept_combo.addItem("None", None)
        for dept in self.controller.registry.all_departments():
            self.dept_combo.addItem(f"{dept.department_id} - {dept.name}", dept.department_id)
        for i in range(self.dept_combo.count()):
            if self.dept_combo.itemData(i, Qt.UserRole) == self.employee.department_id:
                self.dept_combo.setCurrentIndex(i)
                break
        layout.addRow("Department:", self.dept_combo)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _save(self) -> None:
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Missing Data", "Employee name is required.")
            return

        full_name = self.full_name_edit.text().strip() or None
        position = self.position_combo.currentData()
        dept_id = self.dept_combo.currentData()

        updated = replace(
            self.employee,
            name=name,
            full_name=full_name,
            position=position,
            department_id=dept_id,
        )
        self.controller.registry.upsert_employee(updated)
        self.accept()


class DepartmentEditDialog(QDialog):
    """Modal dialog for editing a department."""

    def __init__(self, controller: DesktopController, department: Department, parent=None) -> None:
        super().__init__(parent)
        self.controller = controller
        self.department = department
        self.setWindowTitle("Edit Department")
        self.setModal(True)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QFormLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        self.id_edit = QLineEdit(str(self.department.department_id))
        self.id_edit.setReadOnly(True)
        layout.addRow("Department ID:", self.id_edit)

        self.name_edit = QLineEdit(self.department.name)
        layout.addRow("Name:", self.name_edit)

        self.head_edit = QLineEdit(self.department.head_name or "")
        layout.addRow("Head Name (DTR only):", self.head_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _save(self) -> None:
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Missing Data", "Department name is required.")
            return

        head_name = self.head_edit.text().strip() or None
        updated = replace(self.department, name=name, head_name=head_name)
        self.controller.registry.upsert_department(updated)
        self.accept()


class EmployeeAddDialog(QDialog):
    """Modal dialog for adding a new employee."""

    def __init__(self, controller: DesktopController, parent=None) -> None:
        super().__init__(parent)
        self.controller = controller
        self.setWindowTitle("Add Employee")
        self.setModal(True)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QFormLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        self.id_edit = QLineEdit()
        layout.addRow("Employee ID:", self.id_edit)

        self.name_edit = QLineEdit()
        layout.addRow("Name:", self.name_edit)

        self.full_name_edit = QLineEdit()
        layout.addRow("Full Name (DTR only):", self.full_name_edit)

        self.position_combo = QComboBox()
        self.position_combo.addItem("None", None)
        for pos in self.controller.registry.all_positions():
            self.position_combo.addItem(pos, pos)
        layout.addRow("Position (DTR only):", self.position_combo)

        self.dept_combo = QComboBox()
        self.dept_combo.addItem("None", None)
        for dept in self.controller.registry.all_departments():
            self.dept_combo.addItem(f"{dept.department_id} - {dept.name}", dept.department_id)
        layout.addRow("Department:", self.dept_combo)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _save(self) -> None:
        emp_id = self.id_edit.text().strip()
        name = self.name_edit.text().strip()
        if not emp_id or not name:
            QMessageBox.warning(self, "Missing Data", "Employee ID and name are required.")
            return

        if self.controller.registry.get_employee(emp_id):
            QMessageBox.warning(self, "Validation", f"Employee {emp_id} already exists.")
            return

        full_name = self.full_name_edit.text().strip() or None
        position = self.position_combo.currentData()
        dept_id = self.dept_combo.currentData()

        employee = Employee(
            device_user_id=emp_id,
            name=name,
            full_name=full_name,
            position=position,
            department_id=dept_id,
        )
        self.controller.registry.upsert_employee(employee)
        self.accept()


class EmployeesPage(QWidget):
    """Page for managing employees and departments."""

    def __init__(self, controller: DesktopController, parent=None) -> None:
        super().__init__(parent)
        self.controller = controller
        self._build_ui()
        self._refresh()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        header = QLabel("Employees & Departments")
        header.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(header)

        self.tabs = QTabWidget()

        # Employees tab
        self.employees_tab = QWidget()
        emp_layout = QVBoxLayout(self.employees_tab)

        # Filter controls
        emp_filter_controls = QHBoxLayout()
        emp_filter_controls.setSpacing(12)

        self.emp_id_input = QLineEdit()
        self.emp_id_input.setPlaceholderText("Filter by ID")
        self.emp_id_input.setMaximumWidth(120)
        emp_filter_controls.addWidget(self.emp_id_input)

        self.emp_name_input = QLineEdit()
        self.emp_name_input.setPlaceholderText("Filter by Name")
        emp_filter_controls.addWidget(self.emp_name_input)

        self.emp_full_name_input = QLineEdit()
        self.emp_full_name_input.setPlaceholderText("Filter by Full Name")
        emp_filter_controls.addWidget(self.emp_full_name_input)

        self.emp_position_combo = QComboBox()
        self.emp_position_combo.setMinimumWidth(140)
        emp_filter_controls.addWidget(self.emp_position_combo)

        self.emp_dept_filter = QComboBox()
        self.emp_dept_filter.setMinimumWidth(160)
        emp_filter_controls.addWidget(self.emp_dept_filter)

        filter_btn = QPushButton("Filter")
        filter_btn.clicked.connect(self._filter_employees)
        emp_filter_controls.addWidget(filter_btn)

        clear_filter_btn = QPushButton("Clear")
        clear_filter_btn.clicked.connect(self._clear_employee_filters)
        emp_filter_controls.addWidget(clear_filter_btn)

        emp_filter_controls.addStretch()
        emp_layout.addLayout(emp_filter_controls)

        # Action controls
        emp_action_controls = QHBoxLayout()
        emp_action_controls.setSpacing(12)

        self.add_emp_btn = QPushButton("Add Employee")
        self.add_emp_btn.clicked.connect(self._open_add_employee_dialog)
        emp_action_controls.addWidget(self.add_emp_btn)

        edit_emp_btn = QPushButton("Edit Selected")
        edit_emp_btn.clicked.connect(self._edit_employee)
        emp_action_controls.addWidget(edit_emp_btn)

        del_emp_btn = QPushButton("Delete Selected")
        del_emp_btn.clicked.connect(self._delete_employee)
        emp_action_controls.addWidget(del_emp_btn)

        refresh_emp_btn = QPushButton("Refresh")
        refresh_emp_btn.clicked.connect(self._refresh)
        emp_action_controls.addWidget(refresh_emp_btn)

        emp_action_controls.addStretch()

        emp_action_controls.addWidget(QLabel("Sort by:"))
        self.emp_sort_combo = QComboBox()
        self.emp_sort_combo.addItems(["ID", "Name"])
        self.emp_sort_combo.currentIndexChanged.connect(self._refresh_employees)
        emp_action_controls.addWidget(self.emp_sort_combo)

        emp_layout.addLayout(emp_action_controls)

        self.emp_table = QTableWidget()
        self.emp_table.setColumnCount(5)
        self.emp_table.setHorizontalHeaderLabels(["Employee ID", "Name", "Full Name", "Position", "Department ID"])
        self.emp_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.emp_table.horizontalHeader().setStretchLastSection(True)
        self.emp_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.emp_table.setSortingEnabled(True)
        emp_layout.addWidget(self.emp_table)

        self.tabs.addTab(self.employees_tab, "Employees")

        # Departments tab
        self.departments_tab = QWidget()
        dept_layout = QVBoxLayout(self.departments_tab)

        dept_controls = QHBoxLayout()
        dept_controls.setSpacing(12)

        self.dept_id_input = QSpinBox()
        self.dept_id_input.setMinimum(1)
        self.dept_id_input.setMaximum(999999)
        self.dept_id_input.setPrefix("ID: ")
        dept_controls.addWidget(self.dept_id_input)

        self.dept_name_input = QLineEdit()
        self.dept_name_input.setPlaceholderText("Department Name")
        dept_controls.addWidget(self.dept_name_input)

        self.dept_head_input = QLineEdit()
        self.dept_head_input.setPlaceholderText("Department Head Name")
        dept_controls.addWidget(self.dept_head_input)

        add_dept_btn = QPushButton("Add Department")
        add_dept_btn.clicked.connect(self._add_department)
        dept_controls.addWidget(add_dept_btn)

        edit_dept_btn = QPushButton("Edit Selected")
        edit_dept_btn.clicked.connect(self._edit_department)
        dept_controls.addWidget(edit_dept_btn)

        del_dept_btn = QPushButton("Delete Selected")
        del_dept_btn.clicked.connect(self._delete_department)
        dept_controls.addWidget(del_dept_btn)

        dept_controls.addStretch()
        dept_layout.addLayout(dept_controls)

        dept_sort_layout = QHBoxLayout()
        dept_sort_layout.addWidget(QLabel("Sort by:"))
        self.dept_sort_combo = QComboBox()
        self.dept_sort_combo.addItems(["ID", "Name"])
        self.dept_sort_combo.currentIndexChanged.connect(self._refresh_departments)
        dept_sort_layout.addWidget(self.dept_sort_combo)
        dept_sort_layout.addStretch()
        dept_layout.addLayout(dept_sort_layout)

        self.dept_table = QTableWidget()
        self.dept_table.setColumnCount(3)
        self.dept_table.setHorizontalHeaderLabels(["Department ID", "Name", "Head Name"])
        self.dept_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.dept_table.horizontalHeader().setStretchLastSection(True)
        self.dept_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.dept_table.setSortingEnabled(True)
        dept_layout.addWidget(self.dept_table)

        self.tabs.addTab(self.departments_tab, "Departments")

        # Positions tab
        self.positions_tab = QWidget()
        positions_layout = QVBoxLayout(self.positions_tab)

        positions_controls = QHBoxLayout()
        positions_controls.setSpacing(12)

        self.position_name_input = QLineEdit()
        self.position_name_input.setPlaceholderText("Position Name")
        positions_controls.addWidget(self.position_name_input)

        add_pos_btn = QPushButton("Add")
        add_pos_btn.clicked.connect(self._add_position)
        positions_controls.addWidget(add_pos_btn)

        edit_pos_btn = QPushButton("Edit")
        edit_pos_btn.clicked.connect(self._edit_position)
        positions_controls.addWidget(edit_pos_btn)

        del_pos_btn = QPushButton("Delete")
        del_pos_btn.clicked.connect(self._delete_position)
        positions_controls.addWidget(del_pos_btn)

        positions_controls.addStretch()
        positions_layout.addLayout(positions_controls)

        self.positions_table = QTableWidget()
        self.positions_table.setColumnCount(2)
        self.positions_table.setHorizontalHeaderLabels(["Position", "Employee Count"])
        self.positions_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.positions_table.horizontalHeader().setStretchLastSection(True)
        self.positions_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.positions_table.setSortingEnabled(True)
        positions_layout.addWidget(self.positions_table)

        self.tabs.addTab(self.positions_tab, "Positions")

        layout.addWidget(self.tabs)

    def _refresh(self) -> None:
        """Refresh all tables from the registry."""
        self._load_employee_filter_combos()
        self._refresh_employees()
        self._refresh_departments()
        self._refresh_positions()

    def _load_employee_filter_combos(self) -> None:
        """Populate the employee filter dropdowns from the master lists."""
        # Position filter: Any, None, positions
        position_text = self.emp_position_combo.currentText() or "Any"
        self.emp_position_combo.clear()
        self.emp_position_combo.addItem("Any", None)
        self.emp_position_combo.addItem("None", None)
        for pos in self.controller.registry.all_positions():
            self.emp_position_combo.addItem(pos, pos)
        for i in range(self.emp_position_combo.count()):
            if self.emp_position_combo.itemText(i) == position_text:
                self.emp_position_combo.setCurrentIndex(i)
                break

        # Department filter: Any, None, departments
        dept_text = self.emp_dept_filter.currentText() or "Any"
        self.emp_dept_filter.clear()
        self.emp_dept_filter.addItem("Any", None)
        self.emp_dept_filter.addItem("None", None)
        for dept in self.controller.registry.all_departments():
            self.emp_dept_filter.addItem(f"{dept.department_id} - {dept.name}", dept.department_id)
        for i in range(self.emp_dept_filter.count()):
            if self.emp_dept_filter.itemText(i) == dept_text:
                self.emp_dept_filter.setCurrentIndex(i)
                break

    def _refresh_positions(self) -> None:
        """Refresh the positions table with master positions and employee counts."""
        positions = self.controller.registry.all_positions()
        employees = self.controller.registry.all_employees()
        counts = Counter(emp.position for emp in employees if emp.position)

        self.positions_table.horizontalHeader().setSortIndicator(-1, Qt.AscendingOrder)
        self.positions_table.setRowCount(0)
        self.positions_table.setRowCount(len(positions))
        for row, position in enumerate(positions):
            self.positions_table.setItem(row, 0, QTableWidgetItem(position))
            self.positions_table.setItem(row, 1, NumericTableItem(str(counts.get(position, 0))))

    def _add_position(self) -> None:
        """Add a new position to the master list."""
        name = self.position_name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Missing Data", "Position name is required.")
            return
        self.controller.registry.add_position(name)
        self.position_name_input.clear()
        self._refresh()

    def _edit_position(self) -> None:
        """Rename the selected position."""
        selected = self.positions_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select a position to edit.")
            return
        row = selected[0].row()
        old_name = self.positions_table.item(row, 0).text()
        new_name, ok = QInputDialog.getText(
            self, "Edit Position", f"Rename '{old_name}' to:", text=old_name
        )
        if not ok or not new_name.strip() or new_name.strip() == old_name:
            return
        new_name = new_name.strip()
        self.controller.registry.rename_position(old_name, new_name)
        self._refresh()

    def _delete_position(self) -> None:
        """Delete the selected position and clear it from any employees."""
        selected = self.positions_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select a position to delete.")
            return
        row = selected[0].row()
        name = self.positions_table.item(row, 0).text()
        if QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete position '{name}'? This will also clear it from any assigned employees.",
        ) == QMessageBox.Yes:
            self.controller.registry.delete_position(name)
            self._refresh()

    def _matches_employee_query(self, emp: Employee) -> bool:
        """Check whether an employee matches the active filter controls."""
        if self.emp_id_input.text().strip():
            q = self.emp_id_input.text().strip().lower()
            if q not in emp.device_user_id.lower():
                return False

        if self.emp_name_input.text().strip():
            q = self.emp_name_input.text().strip().lower()
            if q not in emp.name.lower():
                return False

        if self.emp_full_name_input.text().strip():
            q = self.emp_full_name_input.text().strip().lower()
            if q not in (emp.full_name or "").lower():
                return False

        position_index = self.emp_position_combo.currentIndex()
        if position_index == 1:  # None
            if emp.position is not None:
                return False
        elif position_index > 1:
            if emp.position != self.emp_position_combo.currentData():
                return False

        dept_index = self.emp_dept_filter.currentIndex()
        if dept_index == 1:  # None
            if emp.department_id is not None:
                return False
        elif dept_index > 1:
            if emp.department_id != self.emp_dept_filter.currentData():
                return False

        return True

    def _refresh_employees(self) -> None:
        """Refresh the employee table, sorted and filtered by the current selection."""
        employees = [emp for emp in self.controller.registry.all_employees() if self._matches_employee_query(emp)]
        sort_by = self.emp_sort_combo.currentText()

        if sort_by == "ID":
            employees = sorted(employees, key=_employee_id_key)
        elif sort_by == "Name":
            employees = sorted(employees, key=lambda e: e.name)

        self.emp_table.horizontalHeader().setSortIndicator(-1, Qt.AscendingOrder)
        self.emp_table.setRowCount(0)
        self.emp_table.setRowCount(len(employees))
        for row, emp in enumerate(employees):
            self.emp_table.setItem(row, 0, NumericTableItem(emp.device_user_id))
            self.emp_table.setItem(row, 1, QTableWidgetItem(emp.name))
            self.emp_table.setItem(row, 2, QTableWidgetItem(emp.full_name or ""))
            self.emp_table.setItem(row, 3, QTableWidgetItem(emp.position or ""))
            dept = str(emp.department_id) if emp.department_id is not None else ""
            self.emp_table.setItem(row, 4, NumericTableItem(dept))

    def _refresh_departments(self) -> None:
        """Refresh the department table, sorted by the current selection."""
        departments = self.controller.registry.all_departments()
        sort_by = self.dept_sort_combo.currentText()

        if sort_by == "ID":
            departments = sorted(departments, key=_department_id_key)
        elif sort_by == "Name":
            departments = sorted(departments, key=lambda d: d.name)

        self.dept_table.horizontalHeader().setSortIndicator(-1, Qt.AscendingOrder)
        self.dept_table.setRowCount(0)
        self.dept_table.setRowCount(len(departments))
        for row, dept in enumerate(departments):
            self.dept_table.setItem(row, 0, NumericTableItem(str(dept.department_id)))
            self.dept_table.setItem(row, 1, QTableWidgetItem(dept.name))
            self.dept_table.setItem(row, 2, QTableWidgetItem(dept.head_name or ""))

    def _open_add_employee_dialog(self) -> None:
        dialog = EmployeeAddDialog(self.controller, self)
        dialog.exec()
        self._refresh()

    def _filter_employees(self) -> None:
        """Apply the current filter controls and refresh the table."""
        self._refresh_employees()

    def _edit_employee(self) -> None:
        selected = self.emp_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select an employee to edit.")
            return
        row = selected[0].row()
        emp_id = self.emp_table.item(row, 0).text()
        employee = self.controller.registry.get_employee(emp_id)
        if employee is None:
            return

        dialog = EmployeeEditDialog(self.controller, employee, self)
        dialog.exec()
        self._refresh()

    def _clear_employee_filters(self) -> None:
        """Clear all employee filter controls and refresh the table."""
        self.emp_id_input.clear()
        self.emp_name_input.clear()
        self.emp_full_name_input.clear()
        self.emp_position_combo.setCurrentIndex(0)
        self.emp_dept_filter.setCurrentIndex(0)
        self._refresh_employees()

    def _delete_employee(self) -> None:
        selected = self.emp_table.selectedItems()
        if not selected:
            return
        row = selected[0].row()
        emp_id = self.emp_table.item(row, 0).text()
        self.controller.registry.delete_employee(emp_id)
        self._refresh()

    def _add_department(self) -> None:
        dept_id = self.dept_id_input.value()
        name = self.dept_name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Missing Data", "Department name is required.")
            return

        head_name = self.dept_head_input.text().strip() or None
        department = Department(department_id=dept_id, name=name, head_name=head_name)
        self.controller.registry.upsert_department(department)
        self.dept_name_input.clear()
        self.dept_head_input.clear()
        self._refresh_departments()

    def _edit_department(self) -> None:
        selected = self.dept_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select a department to edit.")
            return
        row = selected[0].row()
        dept_id = int(self.dept_table.item(row, 0).text())
        department = self.controller.registry.get_department(dept_id)
        if department is None:
            return

        dialog = DepartmentEditDialog(self.controller, department, self)
        dialog.exec()
        self._refresh_departments()

    def _delete_department(self) -> None:
        selected = self.dept_table.selectedItems()
        if not selected:
            return
        row = selected[0].row()
        dept_id = int(self.dept_table.item(row, 0).text())
        self.controller.registry.delete_department(dept_id)
        self._refresh_departments()
