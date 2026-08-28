"""Main window for the PySide6 desktop UI."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from lgus_dat.desktop.desktop_controller import DesktopController
from lgus_dat.desktop.pages.dashboard_page import DashboardPage
from lgus_dat.desktop.pages.employees_page import EmployeesPage
from lgus_dat.desktop.pages.import_page import ImportPage
from lgus_dat.desktop.pages.processed_page import ProcessedPage
from lgus_dat.desktop.pages.reports_page import ReportsPage
from lgus_dat.desktop.pages.settings_page import SettingsPage
from lgus_dat.desktop.theme import apply_theme


class MainWindow(QMainWindow):
    """Primary desktop window with sidebar navigation and stacked pages."""

    def __init__(self, controller: DesktopController) -> None:
        super().__init__()
        self.controller = controller
        self.setWindowTitle("LGUS-DAT — MB10-VL Attendance Processor")
        self.setMinimumSize(1200, 800)

        # Central widget and layout
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        self.sidebar = self._build_sidebar()
        main_layout.addWidget(self.sidebar)

        # Content area
        self.stack = QStackedWidget()

        self.dashboard_page = DashboardPage(self.controller)
        self.import_page = ImportPage(self.controller)
        self.processed_page = ProcessedPage(self.controller)
        self.import_page.process_requested.connect(self._on_process_requested)

        self.pages: dict[str, QWidget] = {
            "Dashboard": self.dashboard_page,
            "Import": self.import_page,
            "Processed": self.processed_page,
            "Reports": ReportsPage(self.controller),
            "Employees": EmployeesPage(self.controller),
            "Settings": SettingsPage(),
        }
        for page in self.pages.values():
            self.stack.addWidget(page)

        main_layout.addWidget(self.stack, 1)

        # Status bar
        self.statusBar().showMessage("Ready")

        # Default page
        self._on_nav_clicked("Dashboard")

    def _build_sidebar(self) -> QWidget:
        """Build the sidebar with navigation and theme toggle."""
        sidebar = QWidget()
        sidebar.setFixedWidth(220)
        sidebar.setObjectName("sidebar")

        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(12, 16, 12, 16)
        sidebar_layout.setSpacing(8)

        sidebar_label = QLabel("LGUS-DAT")
        sidebar_label.setStyleSheet("font-weight: bold; font-size: 20px;")
        sidebar_label.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(sidebar_label)

        version_label = QLabel("Attendance & DTR")
        version_label.setStyleSheet("font-size: 11px; color: gray;")
        version_label.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(version_label)

        sidebar_layout.addSpacing(24)

        self.nav_buttons: list[QPushButton] = []
        for name in ["Dashboard", "Import", "Processed", "Reports", "Employees", "Settings"]:
            btn = QPushButton(name)
            btn.setCheckable(True)
            btn.setAutoExclusive(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, n=name: self._on_nav_clicked(n))
            self.nav_buttons.append(btn)
            sidebar_layout.addWidget(btn)

        sidebar_layout.addStretch()

        self.theme_button = QPushButton("Dark Mode")
        self.theme_button.setCheckable(True)
        self.theme_button.clicked.connect(self._on_theme_toggle)
        sidebar_layout.addWidget(self.theme_button)

        return sidebar

    def _on_nav_clicked(self, name: str) -> None:
        """Switch the content area to the selected page."""
        page = self.pages.get(name)
        if page is None:
            return
        self.stack.setCurrentWidget(page)
        for btn in self.nav_buttons:
            if btn.text() == name:
                btn.setChecked(True)
        if name == "Dashboard":
            self.dashboard_page.refresh()
        self.statusBar().showMessage(f"Viewing {name}")

    def _on_process_requested(self) -> None:
        """Handle the process records signal from the import page."""
        self.processed_page.refresh()
        self._on_nav_clicked("Processed")

    def _on_theme_toggle(self) -> None:
        """Toggle between light and dark themes."""
        app = QApplication.instance()
        if app is None:
            return
        dark = self.theme_button.isChecked()
        apply_theme(app, dark)
        self.theme_button.setText("Light Mode" if dark else "Dark Mode")
