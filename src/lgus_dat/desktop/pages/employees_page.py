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

        self.position_edit = QLineEdit(self.employee.position or "")
        layout.addRow("Position (DTR only):", self.position_edit)

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
        position = self.position_edit.text().strip() or None
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

        emp_controls = QHBoxLayout()
        emp_controls.setSpacing(12)

        self.emp_id_input = QLineEdit()
        self.emp_id_input.setPlaceholderText("Employee ID")
        self.emp_id_input.setMaximumWidth(120)
        emp_controls.addWidget(self.emp_id_input)

        self.emp_name_input = QLineEdit()
        self.emp_name_input.setPlaceholderText("Employee Name")
        emp_controls.addWidget(self.emp_name_input)

        self.emp_full_name_input = QLineEdit()
        self.emp_full_name_input.setPlaceholderText("Full Name (DTR only)")
        emp_controls.addWidget(self.emp_full_name_input)

        self.emp_position_input = QLineEdit()
        self.emp_position_input.setPlaceholderText("Position (DTR only)")
        emp_controls.addWidget(self.emp_position_input)

        self.emp_dept_input = QSpinBox()
        self.emp_dept_input.setMinimum(0)
        self.emp_dept_input.setMaximum(999999)
        self.emp_dept_input.setSpecialValueText("None")
        emp_controls.addWidget(self.emp_dept_input)

        self.add_emp_btn = QPushButton("Add Employee")
        self.add_emp_btn.clicked.connect(self._add_employee)
        emp_controls.addWidget(self.add_emp_btn)

        edit_emp_btn = QPushButton("Edit Selected")
        edit_emp_btn.clicked.connect(self._edit_employee)
        emp_controls.addWidget(edit_emp_btn)

        del_emp_btn = QPushButton("Delete Selected")
        del_emp_btn.clicked.connect(self._delete_employee)
        emp_controls.addWidget(del_emp_btn)

        emp_controls.addStretch()
        emp_layout.addLayout(emp_controls)

        emp_sort_layout = QHBoxLayout()
        emp_sort_layout.addWidget(QLabel("Sort by:"))
        self.emp_sort_combo = QComboBox()
        self.emp_sort_combo.addItems(["ID", "Name"])
        self.emp_sort_combo.currentIndexChanged.connect(self._refresh_employees)
        emp_sort_layout.addWidget(self.emp_sort_combo)
        emp_sort_layout.addStretch()
        emp_layout.addLayout(emp_sort_layout)

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

        add_dept_btn = QPushButton("Add Department")
        add_dept_btn.clicked.connect(self._add_department)
        dept_controls.addWidget(add_dept_btn)

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
        self.dept_table.setColumnCount(2)
        self.dept_table.setHorizontalHeaderLabels(["Department ID", "Name"])
        self.dept_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.dept_table.horizontalHeader().setStretchLastSection(True)
        self.dept_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.dept_table.setSortingEnabled(True)
        dept_layout.addWidget(self.dept_table)

        self.tabs.addTab(self.departments_tab, "Departments")

        # Positions tab
        self.positions_tab = QWidget()
        positions_layout = QVBoxLayout(self.positions_tab)

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
        self._refresh_employees()
        self._refresh_departments()
        self._refresh_positions()

    def _refresh_positions(self) -> None:
        """Refresh the positions table with unique positions and counts."""
        employees = self.controller.registry.all_employees()
        counts = Counter(emp.position for emp in employees if emp.position)

        self.positions_table.setRowCount(len(counts))
        for row, (position, count) in enumerate(sorted(counts.items())):
            self.positions_table.setItem(row, 0, QTableWidgetItem(position))
            self.positions_table.setItem(row, 1, QTableWidgetItem(str(count)))

    def _refresh_employees(self) -> None:
        """Refresh the employee table, sorted by the current selection."""
        employees = self.controller.registry.all_employees()
        sort_by = self.emp_sort_combo.currentText()

        if sort_by == "ID":
            employees = sorted(employees, key=_employee_id_key)
        elif sort_by == "Name":
            employees = sorted(employees, key=lambda e: e.name)

        self.emp_table.setRowCount(len(employees))
        for row, emp in enumerate(employees):
            self.emp_table.setItem(row, 0, QTableWidgetItem(emp.device_user_id))
            self.emp_table.setItem(row, 1, QTableWidgetItem(emp.name))
            self.emp_table.setItem(row, 2, QTableWidgetItem(emp.full_name or ""))
            self.emp_table.setItem(row, 3, QTableWidgetItem(emp.position or ""))
            dept = str(emp.department_id) if emp.department_id is not None else ""
            self.emp_table.setItem(row, 4, QTableWidgetItem(dept))

    def _refresh_departments(self) -> None:
        """Refresh the department table, sorted by the current selection."""
        departments = self.controller.registry.all_departments()
        sort_by = self.dept_sort_combo.currentText()

        if sort_by == "ID":
            departments = sorted(departments, key=_department_id_key)
        elif sort_by == "Name":
            departments = sorted(departments, key=lambda d: d.name)

        self.dept_table.setRowCount(len(departments))
        for row, dept in enumerate(departments):
            self.dept_table.setItem(row, 0, QTableWidgetItem(str(dept.department_id)))
            self.dept_table.setItem(row, 1, QTableWidgetItem(dept.name))

    def _add_employee(self) -> None:
        emp_id = self.emp_id_input.text().strip()
        name = self.emp_name_input.text().strip()
        full_name = self.emp_full_name_input.text().strip() or None
        position = self.emp_position_input.text().strip() or None
        if not emp_id or not name:
            QMessageBox.warning(self, "Missing Data", "Employee ID and name are required.")
            return

        dept_id = self.emp_dept_input.value() if self.emp_dept_input.value() > 0 else None
        employee = Employee(device_user_id=emp_id, name=name, full_name=full_name, position=position, department_id=dept_id)
        self.controller.registry.upsert_employee(employee)
        self._clear_employee_inputs()
        self._refresh()

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

    def _clear_employee_inputs(self) -> None:
        self.emp_id_input.clear()
        self.emp_name_input.clear()
        self.emp_full_name_input.clear()
        self.emp_position_input.clear()
        self.emp_dept_input.setValue(0)

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

        department = Department(department_id=dept_id, name=name)
        self.controller.registry.upsert_department(department)
        self._refresh_departments()

    def _delete_department(self) -> None:
        selected = self.dept_table.selectedItems()
        if not selected:
            return
        row = selected[0].row()
        dept_id = int(self.dept_table.item(row, 0).text())
        self.controller.registry.delete_department(dept_id)
        self._refresh_departments()
