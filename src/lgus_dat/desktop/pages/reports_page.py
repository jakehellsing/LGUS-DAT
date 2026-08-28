"""Reports page for DTR PDF, CSV, and attlog export."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from lgus_dat.desktop.desktop_controller import DesktopController


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
        if not self.controller.ui.state.all_processed_records:
            return

        month_text = self.month_edit.text().strip()
        try:
            report_date = date.fromisoformat(f"{month_text}-01")
        except ValueError:
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save DTR PDF",
            f"DTR_{report_date.strftime('%Y_%m')}.pdf",
            "PDF files (*.pdf);;All files (*.*)",
        )
        if not path:
            return

        selection = {"mode": "all"}
        self.controller.ui.generate_dtr_pdf(selection, report_date, Path(path))

    def _export_csv(self) -> None:
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

        self.controller.ui.save_csv(Path(path))

    def _export_attlog(self) -> None:
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

        self.controller.ui.export_attlog(Path(path))
