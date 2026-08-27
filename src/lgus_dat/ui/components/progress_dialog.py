"""Progress dialog component for long-running operations."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class ProgressDialog:
    """Small modal progress window with an indeterminate progress bar."""

    def __init__(self, parent: tk.Tk | tk.Toplevel, title: str = "Working...") -> None:
        self.window = tk.Toplevel(parent)
        self.window.title(title)
        self.window.transient(parent)
        self.window.resizable(False, False)
        self.window.grab_set()

        self.label = ttk.Label(self.window, text="Please wait...")
        self.label.pack(pady=12)

        self.bar = ttk.Progressbar(self.window, mode="indeterminate", length=300)
        self.bar.pack(padx=20, pady=(0, 12))
        self.bar.start(15)

        self.window.update()

    def set_text(self, text: str) -> None:
        """Update the progress dialog text."""
        self.label.config(text=text)
        self.window.update()

    def close(self) -> None:
        """Close the progress dialog."""
        self.bar.stop()
        self.window.destroy()
