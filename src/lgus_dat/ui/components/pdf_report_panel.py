"""PDF report generation panel component."""

from __future__ import annotations

import tkinter as tk
from datetime import date
from tkinter import ttk
from typing import Callable, Optional

from tkcalendar import DateEntry


class PDFReportPanel(ttk.LabelFrame):
    """Panel for DTR PDF report generation."""

    def __init__(
        self,
        parent: tk.Widget,
        on_generate_pdf: Optional[Callable[[], None]] = None,
    ) -> None:
        super().__init__(parent, text="DTR PDF Report", padding=8)
        
        self.on_generate_pdf = on_generate_pdf
        
        self.report_month_var = tk.StringVar()
        
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the PDF report UI components."""
        ttk.Label(self, text="Month:").pack(side=tk.LEFT)
        self.report_month_entry = DateEntry(
            self,
            textvariable=self.report_month_var,
            width=12,
            date_pattern="y-mm-dd",
        )
        self.report_month_entry.delete(0, tk.END)
        self.report_month_entry.pack(side=tk.LEFT, padx=(4, 8))

        ttk.Button(self, text="Generate DTR PDF", command=self._handle_generate_pdf).pack(side=tk.LEFT, padx=4)

    def _handle_generate_pdf(self) -> None:
        """Handle generate PDF button click."""
        if self.on_generate_pdf:
            self.on_generate_pdf()

    def get_selected_month(self) -> Optional[date]:
        """Get the selected month from the date picker."""
        month_text = self.report_month_var.get().strip()
        if not month_text:
            return None
        
        try:
            return date.fromisoformat(month_text)
        except ValueError:
            return None

    def has_month_selected(self) -> bool:
        """Check if a month is selected."""
        return bool(self.report_month_var.get().strip())
