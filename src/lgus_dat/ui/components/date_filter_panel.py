"""Date range filter panel component."""

from __future__ import annotations

import tkinter as tk
from datetime import datetime, time
from tkinter import ttk
from typing import Callable, Optional

from tkcalendar import DateEntry


class TimePickerDialog:
    """Simple time picker dialog."""

    def __init__(self, parent: tk.Tk, initial_time: Optional[time] = None) -> None:
        self.result: Optional[time] = initial_time
        
        self.window = tk.Toplevel(parent)
        self.window.title("Select Time")
        self.window.transient(parent)
        self.window.resizable(False, False)
        self.window.grab_set()
        
        self.hour_var = tk.IntVar(value=initial_time.hour if initial_time else 0)
        self.minute_var = tk.IntVar(value=initial_time.minute if initial_time else 0)
        self.second_var = tk.IntVar(value=initial_time.second if initial_time else 0)
        
        self._build_ui()
        
        # Center the dialog
        self.window.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.window.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.window.winfo_height()) // 2
        self.window.geometry(f"+{x}+{y}")
        
        self.window.wait_window(self.window)

    def _build_ui(self) -> None:
        main_frame = ttk.Frame(self.window, padding=12)
        main_frame.pack()
        
        # Time selection
        time_frame = ttk.Frame(main_frame)
        time_frame.pack(pady=(0, 12))
        
        # Hour
        ttk.Label(time_frame, text="Hour:").grid(row=0, column=0, padx=4)
        hour_spinbox = ttk.Spinbox(
            time_frame, 
            from_=0, 
            to=23, 
            width=5, 
            textvariable=self.hour_var,
            format="%02.0f"
        )
        hour_spinbox.grid(row=0, column=1, padx=4)
        
        # Minute
        ttk.Label(time_frame, text="Minute:").grid(row=0, column=2, padx=4)
        minute_spinbox = ttk.Spinbox(
            time_frame, 
            from_=0, 
            to=59, 
            width=5, 
            textvariable=self.minute_var,
            format="%02.0f"
        )
        minute_spinbox.grid(row=0, column=3, padx=4)
        
        # Second
        ttk.Label(time_frame, text="Second:").grid(row=0, column=4, padx=4)
        second_spinbox = ttk.Spinbox(
            time_frame, 
            from_=0, 
            to=59, 
            width=5, 
            textvariable=self.second_var,
            format="%02.0f"
        )
        second_spinbox.grid(row=0, column=5, padx=4)
        
        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack()
        
        ttk.Button(btn_frame, text="OK", command=self._on_ok).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="Cancel", command=self.window.destroy).pack(side=tk.LEFT, padx=4)

    def _on_ok(self) -> None:
        self.result = time(self.hour_var.get(), self.minute_var.get(), self.second_var.get())
        self.window.destroy()


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
        
        self.start_time_button = ttk.Button(
            self, 
            text="Select Time", 
            command=self._on_start_time_click,
            width=10
        )
        self.start_time_button.pack(side=tk.LEFT, padx=(0, 8))

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
        
        self.end_time_button = ttk.Button(
            self, 
            text="Select Time", 
            command=self._on_end_time_click,
            width=10
        )
        self.end_time_button.pack(side=tk.LEFT, padx=(0, 8))

        # Action buttons
        ttk.Button(self, text="Apply Filter", command=self._handle_apply_filter).pack(side=tk.LEFT, padx=4)
        ttk.Button(self, text="Clear", command=self._handle_clear_filter).pack(side=tk.LEFT, padx=4)

    def _on_start_time_click(self) -> None:
        """Handle start time button click."""
        initial_time = None
        if self.start_time_var.get():
            try:
                initial_time = datetime.strptime(self.start_time_var.get(), "%H:%M:%S").time()
            except ValueError:
                pass
        
        dialog = TimePickerDialog(self.winfo_toplevel(), initial_time)
        if dialog.result:
            self.start_time_var.set(dialog.result.strftime("%H:%M:%S"))

    def _on_end_time_click(self) -> None:
        """Handle end time button click."""
        initial_time = None
        if self.end_time_var.get():
            try:
                initial_time = datetime.strptime(self.end_time_var.get(), "%H:%M:%S").time()
            except ValueError:
                pass
        
        dialog = TimePickerDialog(self.winfo_toplevel(), initial_time)
        if dialog.result:
            self.end_time_var.set(dialog.result.strftime("%H:%M:%S"))

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
