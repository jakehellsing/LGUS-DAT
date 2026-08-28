"""Desktop controller wraps the UIController for PySide6."""

from __future__ import annotations

from pathlib import Path

from lgus_dat.persistence.registry import AttendanceRegistry
from lgus_dat.ui.controller import UIController


class DesktopController:
    """Thin wrapper exposing controller methods to the PySide6 desktop UI."""

    def __init__(self) -> None:
        self.registry = AttendanceRegistry()
        self.ui = UIController(self.registry)
        self._load_stored_logs()

    def _load_stored_logs(self) -> None:
        """Load any previously imported attendance logs from the registry."""
        self.ui.load_from_db()

    def load_attendance(self, path: Path) -> tuple[Path, list, list, int]:
        """Load an attendance .dat file and return parsed records and errors."""
        return self.ui.load_file(path)

    def get_registry_info(self) -> tuple[str, int, int]:
        """Get registry information."""
        return self.ui.get_registry_info()
