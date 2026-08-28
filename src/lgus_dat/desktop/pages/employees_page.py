"""Employees and departments management page."""

from __future__ import annotations

from PySide6.QtWidgets import (
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

        self.emp_dept_input = QSpinBox()
        self.emp_dept_input.setMinimum(0)
        self.emp_dept_input.setMaximum(999999)
        self.emp_dept_input.setSpecialValueText("None")
        emp_controls.addWidget(self.emp_dept_input)

        add_emp_btn = QPushButton("Add Employee")
        add_emp_btn.clicked.connect(self._add_employee)
        emp_controls.addWidget(add_emp_btn)

        del_emp_btn = QPushButton("Delete Selected")
        del_emp_btn.clicked.connect(self._delete_employee)
        emp_controls.addWidget(del_emp_btn)

        emp_controls.addStretch()
        emp_layout.addLayout(emp_controls)

        self.emp_table = QTableWidget()
        self.emp_table.setColumnCount(3)
        self.emp_table.setHorizontalHeaderLabels(["Employee ID", "Name", "Department ID"])
        self.emp_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.emp_table.horizontalHeader().setStretchLastSection(True)
        self.emp_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
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

        self.dept_table = QTableWidget()
        self.dept_table.setColumnCount(2)
        self.dept_table.setHorizontalHeaderLabels(["Department ID", "Name"])
        self.dept_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.dept_table.horizontalHeader().setStretchLastSection(True)
        self.dept_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        dept_layout.addWidget(self.dept_table)

        self.tabs.addTab(self.departments_tab, "Departments")

        layout.addWidget(self.tabs)

    def _refresh(self) -> None:
        """Refresh both tables from the registry."""
        employees = self.controller.registry.all_employees()
        self.emp_table.setRowCount(len(employees))
        for row, emp in enumerate(employees):
            self.emp_table.setItem(row, 0, QTableWidgetItem(emp.device_user_id))
            self.emp_table.setItem(row, 1, QTableWidgetItem(emp.name))
            dept = str(emp.department_id) if emp.department_id is not None else ""
            self.emp_table.setItem(row, 2, QTableWidgetItem(dept))

        departments = self.controller.registry.all_departments()
        self.dept_table.setRowCount(len(departments))
        for row, dept in enumerate(departments):
            self.dept_table.setItem(row, 0, QTableWidgetItem(str(dept.department_id)))
            self.dept_table.setItem(row, 1, QTableWidgetItem(dept.name))

    def _add_employee(self) -> None:
        emp_id = self.emp_id_input.text().strip()
        name = self.emp_name_input.text().strip()
        if not emp_id or not name:
            QMessageBox.warning(self, "Missing Data", "Employee ID and name are required.")
            return

        dept_id = self.emp_dept_input.value() if self.emp_dept_input.value() > 0 else None
        employee = Employee(device_user_id=emp_id, name=name, department_id=dept_id)
        self.controller.registry.upsert_employee(employee)
        self._refresh()

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
        self._refresh()

    def _delete_department(self) -> None:
        selected = self.dept_table.selectedItems()
        if not selected:
            return
        row = selected[0].row()
        dept_id = int(self.dept_table.item(row, 0).text())
        self.controller.registry.delete_department(dept_id)
        self._refresh()
