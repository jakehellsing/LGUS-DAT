"""Date range filter panel component."""

from __future__ import annotations

import tkinter as tk
from datetime import datetime
from tkinter import ttk
from typing import Callable, Optional

from tkcalendar import DateEntry


class DateFilterPanel(ttk.LabelFrame):
    """Panel for date and time range filtering."""

    def __init__(
        self,
        parent: tk.Widget,
        on_apply_filter: Optional[Callable[[], None]] = None,
        on_clear_filter: Optional[Callable[[], None]] = None,
    ) -> None:
        super().__init__(parent, text="Date Range Filter", padding=8)
        
        self.on_apply_filter = on_apply_filter
        self.on_clear_filter = on_clear_filter
        
        self.start_date_var = tk.StringVar()
        self.start_time_var = tk.StringVar()
        self.end_date_var = tk.StringVar()
        self.end_time_var = tk.StringVar()
        
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the date filter UI components."""
        # Start date/time
        ttk.Label(self, text="Start:").pack(side=tk.LEFT)
        self.start_date_entry = DateEntry(
            self,
            textvariable=self.start_date_var,
            width=12,
            date_pattern="y-mm-dd",
        )
        self.start_date_entry.delete(0, tk.END)
        self.start_date_entry.pack(side=tk.LEFT, padx=(4, 2))
        
        self.start_time_entry = ttk.Entry(self, textvariable=self.start_time_var, width=8)
        self.start_time_entry.pack(side=tk.LEFT, padx=(0, 8))

        # End date/time
        ttk.Label(self, text="End:").pack(side=tk.LEFT)
        self.end_date_entry = DateEntry(
            self,
            textvariable=self.end_date_var,
            width=12,
            date_pattern="y-mm-dd",
        )
        self.end_date_entry.delete(0, tk.END)
        self.end_date_entry.pack(side=tk.LEFT, padx=(4, 2))
        
        self.end_time_entry = ttk.Entry(self, textvariable=self.end_time_var, width=8)
        self.end_time_entry.pack(side=tk.LEFT, padx=(0, 8))

        # Action buttons
        ttk.Button(self, text="Apply Filter", command=self._handle_apply_filter).pack(side=tk.LEFT, padx=4)
        ttk.Button(self, text="Clear", command=self._handle_clear_filter).pack(side=tk.LEFT, padx=4)

    def _handle_apply_filter(self) -> None:
        """Handle apply filter button click."""
        if self.on_apply_filter:
            self.on_apply_filter()

    def _handle_clear_filter(self) -> None:
        """Handle clear filter button click."""
        self.start_date_var.set("")
        self.start_time_var.set("")
        self.end_date_var.set("")
        self.end_time_var.set("")
        
        if self.on_clear_filter:
            self.on_clear_filter()

    def get_start_datetime(self) -> Optional[datetime]:
        """Get the start datetime from the filter inputs."""
        date_text = self.start_date_var.get().strip()
        time_text = self.start_time_var.get().strip()
        
        if not date_text and not time_text:
            return None
        
        try:
            from datetime import date
            
            if date_text:
                parsed_date = date.fromisoformat(date_text)
            else:
                parsed_date = date.today()
            
            if time_text:
                parsed_time = datetime.strptime(time_text, "%H:%M:%S").time()
                return datetime.combine(parsed_date, parsed_time)
            else:
                return datetime.combine(parsed_date, datetime.min.time())
        except ValueError:
            return None

    def get_end_datetime(self) -> Optional[datetime]:
        """Get the end datetime from the filter inputs."""
        date_text = self.end_date_var.get().strip()
        time_text = self.end_time_var.get().strip()
        
        if not date_text and not time_text:
            return None
        
        try:
            from datetime import date
            
            if date_text:
                parsed_date = date.fromisoformat(date_text)
            else:
                parsed_date = date.today()
            
            if time_text:
                parsed_time = datetime.strptime(time_text, "%H:%M:%S").time()
                return datetime.combine(parsed_date, parsed_time)
            else:
                return datetime.combine(parsed_date, datetime.min.time())
        except ValueError:
            return None

    def has_filter(self) -> bool:
        """Check if any filter is set."""
        return bool(
            self.start_date_var.get().strip() or
            self.start_time_var.get().strip() or
            self.end_date_var.get().strip() or
            self.end_time_var.get().strip()
        )
