"""Reports page for DTR PDF, CSV, and attlog export."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from lgus_dat.desktop.desktop_controller import DesktopController
from lgus_dat.desktop.widgets.progress_dialog import ProgressDialog


class DTRScopeDialog(QDialog):
    """Dialog to select the scope for a DTR PDF report."""

    def __init__(self, controller: DesktopController, parent=None) -> None:
        super().__init__(parent)
        self.controller = controller
        self.setWindowTitle("DTR Report Scope")
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Scope:"))

        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["All", "By Department", "By Employee"])
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        mode_layout.addWidget(self.mode_combo)

        layout.addLayout(mode_layout)

        self.scope_label = QLabel("Select departments:")
        layout.addWidget(self.scope_label)

        self.scope_list = QListWidget()
        self.scope_list.setSelectionMode(QListWidget.MultiSelection)
        layout.addWidget(self.scope_list)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._on_mode_changed(0)

    def _on_mode_changed(self, index: int) -> None:
        self.scope_list.clear()

        if index == 0:  # All
            self.scope_label.setText("All employees selected")
            self.scope_list.setEnabled(False)
        elif index == 1:  # By Department
            self.scope_label.setText("Select departments:")
            self.scope_list.setEnabled(True)
            for dept in self.controller.registry.all_departments():
                item = QListWidgetItem(f"{dept.department_id} - {dept.name}")
                item.setData(Qt.UserRole, dept.department_id)
                self.scope_list.addItem(item)
        elif index == 2:  # By Employee
            self.scope_label.setText("Select employees:")
            self.scope_list.setEnabled(True)
            for emp in self.controller.registry.all_employees():
                item = QListWidgetItem(f"{emp.device_user_id} - {emp.name}")
                item.setData(Qt.UserRole, emp.device_user_id)
                self.scope_list.addItem(item)

    def get_selection(self) -> dict:
        """Return the selection dictionary for the DTR report."""
        index = self.mode_combo.currentIndex()

        if index == 0:
            return {"mode": "all"}

        ids = []
        for i in range(self.scope_list.count()):
            item = self.scope_list.item(i)
            if item.isSelected():
                ids.append(item.data(Qt.UserRole))

        if index == 1:
            return {"mode": "departments", "department_ids": ids}

        return {"mode": "employees", "employee_ids": ids}


class ReportsPage(QWidget):
    """Page for generating DTR reports and exporting data."""

    def __init__(self, controller: DesktopController, parent=None) -> None:
        super().__init__(parent)
        self.controller = controller
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        header = QLabel("Reports & Exports")
        header.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(header)

        info = QLabel("Generate DTR PDF, CSV, and attlog exports here.")
        layout.addWidget(info)

        # DTR PDF section
        pdf_layout = QVBoxLayout()
        pdf_label = QLabel("DTR PDF Report")
        pdf_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        pdf_layout.addWidget(pdf_label)

        pdf_fields = QHBoxLayout()
        pdf_fields.setSpacing(12)

        self.month_edit = QLineEdit()
        self.month_edit.setPlaceholderText("YYYY-MM")
        self.month_edit.setText(QDate.currentDate().toString("yyyy-MM"))
        pdf_fields.addWidget(QLabel("Month:"))
        pdf_fields.addWidget(self.month_edit)

        pdf_btn = QPushButton("Generate DTR PDF")
        pdf_btn.clicked.connect(self._generate_pdf)
        pdf_fields.addWidget(pdf_btn)

        pdf_fields.addStretch()
        pdf_layout.addLayout(pdf_fields)
        layout.addLayout(pdf_layout)

        # Export section
        export_layout = QVBoxLayout()
        export_label = QLabel("Data Export")
        export_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        export_layout.addWidget(export_label)

        export_buttons = QHBoxLayout()
        export_buttons.setSpacing(12)

        csv_btn = QPushButton("Export CSV")
        csv_btn.clicked.connect(self._export_csv)
        export_buttons.addWidget(csv_btn)

        attlog_btn = QPushButton("Export attlog")
        attlog_btn.clicked.connect(self._export_attlog)
        export_buttons.addWidget(attlog_btn)

        export_buttons.addStretch()
        export_layout.addLayout(export_buttons)
        layout.addLayout(export_layout)

        layout.addStretch()

    def _generate_pdf(self) -> None:
        month_text = self.month_edit.text().strip()
        try:
            report_date = date.fromisoformat(f"{month_text}-01")
        except ValueError:
            return

        scope_dialog = DTRScopeDialog(self.controller, self)
        if scope_dialog.exec() != QDialog.Accepted:
            return

        self.controller.ui.ensure_processed()
        if not self.controller.ui.state.all_processed_records:
            return

        selection = scope_dialog.get_selection()

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save DTR PDF",
            f"DTR_{report_date.strftime('%Y_%m')}.pdf",
            "PDF files (*.pdf);;All files (*.*)",
        )
        if not path:
            return

        ProgressDialog("Generating", "Creating DTR PDF...", self).run_task(
            lambda: self.controller.ui.generate_dtr_pdf(selection, report_date, Path(path))
        )

    def _export_csv(self) -> None:
        self.controller.ui.ensure_processed()
        if not self.controller.ui.state.processed_records:
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save CSV",
            "attendance.csv",
            "CSV files (*.csv);;All files (*.*)",
        )
        if not path:
            return

        ProgressDialog("Exporting", "Saving CSV...", self).run_task(
            lambda: self.controller.ui.save_csv(Path(path))
        )

    def _export_attlog(self) -> None:
        self.controller.ui.ensure_processed()
        if not self.controller.ui.state.processed_records:
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save attlog",
            "attendance.dat",
            "DAT files (*.dat);;All files (*.*)",
        )
        if not path:
            return

        ProgressDialog("Exporting", "Saving attlog...", self).run_task(
            lambda: self.controller.ui.export_attlog(Path(path))
        )
