"""Entry point for the PySide6 desktop application."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from lgus_dat.desktop.desktop_controller import DesktopController
from lgus_dat.desktop.main_window import MainWindow
from lgus_dat.desktop.theme import apply_theme


def _logo_path() -> Path:
    """Resolve the desktop logo path for source and PyInstaller builds."""
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / "assets" / "icon.ico"
    # src/lgus_dat/desktop/app.py -> repo root
    return Path(__file__).resolve().parents[3] / "assets" / "icon.ico"


def main(argv: list[str] | None = None) -> int:
    """Run the PySide6 desktop application."""
    args = argv if argv is not None else sys.argv[1:]
    app = QApplication(args or [])
    apply_theme(app, False)

    logo = _logo_path()
    if logo.exists():
        icon = QIcon(str(logo))
        app.setWindowIcon(icon)

    controller = DesktopController()
    window = MainWindow(controller)
    window.setWindowIcon(app.windowIcon())
    window.showMaximized()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
