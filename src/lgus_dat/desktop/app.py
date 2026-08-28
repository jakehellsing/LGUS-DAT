"""Entry point for the PySide6 desktop application."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from lgus_dat.desktop.desktop_controller import DesktopController
from lgus_dat.desktop.main_window import MainWindow
from lgus_dat.desktop.theme import apply_theme


def main(argv: list[str] | None = None) -> int:
    """Run the PySide6 desktop application."""
    args = argv if argv is not None else sys.argv[1:]
    app = QApplication(args or [])
    apply_theme(app, False)

    controller = DesktopController()
    window = MainWindow(controller)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
