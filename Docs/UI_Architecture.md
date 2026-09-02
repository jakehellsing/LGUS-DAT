# UI Architecture Guide

## Overview

The LGUS-DAT desktop UI has been refactored from a monolithic structure to a modular component architecture. This separation of concerns improves maintainability, testability, and enables easier future UI framework migration.

A new **PySide6** desktop UI was added in `src/lgus_dat/desktop/`. It provides a modern, themeable interface with sidebar navigation and is the primary interface moving forward. The legacy **Tkinter** UI remains in `src/lgus_dat/ui/`.

## Architecture

### Directory Structure

```
src/lgus_dat/ui/
  components/          # Reusable UI building blocks
    file_toolbar.py     # File operations (open, process, save, export)
    registry_toolbar.py # Employee/department operations
    date_filter_panel.py # Date/time range filtering
    search_panel.py     # Employee search filtering
    pdf_report_panel.py # PDF generation controls
    progress_dialog.py  # Progress indicator dialog
  views/               # Data display components
    input_preview.py    # Raw input treeview
    output_preview.py   # Processed output treeview
    status_panel.py     # Status messages panel
  dialogs/             # Modal dialogs
    pdf_selection_dialog.py   # PDF report selection
    management_dialog.py       # Employee/department management
    status_edit_dialog.py      # Status editing dialog
  controller.py         # Business logic coordination
  app.py               # Main application orchestration

src/lgus_dat/desktop/  # PySide6 desktop interface
  app.py               # Entry point and QApplication setup
  main_window.py       # Main window with sidebar, menu bar, and stacked pages
  desktop_controller.py # Adapter wrapping UIController
  all_records_window.py # Standalone window for viewing all accumulated records
  theme.py             # Light/dark theme definitions
  pages/               # Page views
    dashboard_page.py  # KPIs and quick actions
    import_page.py     # File import and month-scoped processing
    processed_page.py  # Processed records with search and date filters
    reports_page.py    # DTR PDF, CSV, and attlog export
    employees_page.py  # Employee and department management, including department head name for DTR Verifying Officer
    settings_page.py   # Placeholder settings page
  widgets/             # Reusable widgets
    kpi_card.py        # Dashboard KPI card
    data_table.py      # Reusable data table (currently placeholder)
    progress_dialog.py # Modal progress dialog with worker thread
```

## Component Responsibilities

### Components (`ui/components/`)

**FileToolbar**
- File operations: Open .DAT, Process, Process from DB, Save CSV, Export attlog.dat, Edit Status
- Independent business logic callbacks
- Keyboard shortcut binding (F5)

**RegistryToolbar**
- Employee/department operations: Import user.dat, Import department.dat, Manage Employees
- Registry-related actions

**DateFilterPanel**
- Date and time range filtering
- Provides filter values to controller
- Clear filter functionality

**SearchPanel**
- Employee search by ID or name
- Query string management
- Search and clear actions

**PDFReportPanel**
- Month selection for DTR reports
- PDF generation trigger
- Month validation

**ProgressDialog**
- Modal progress indicator for long-running operations
- Threading support for responsive UI

### Views (`ui/views/`)

**InputPreview**
- Treeview for raw attendance records
- Record mapping and selection
- Employee name resolution
- Data loading and clearing

**OutputPreview**
- Treeview for processed attendance records
- Status color coding (IN=light blue, OUT=light yellow)
- Record updates and selection
- Exception flag display

**StatusPanel**
- Text area for status messages and errors
- Message logging with auto-scroll
- Clear functionality

### Dialogs (`ui/dialogs/`)

**DTRSelectionDialog**
- Employee/department selection for PDF reports
- Multiple selection modes (all, specific employees, by department)
- Search and filter functionality

**ManagementDialog**
- Employee and department management
- CRUD operations for employees and departments
- Department `head_name` field for DTR Verifying Officer
- Device backup import/export
- Department dropdown selection for employee assignment
- Department details view with employee management
- Employee count display per department

**StatusEditDialog**
- Simple status selection dialog (IN/OUT)
- Modal dialog with OK/Cancel buttons

**Internal Dialog Classes**
- `_EmployeeDialog`: Employee add/edit with department dropdown
- `_DepartmentDialog`: Department add/edit with validation and `head_name` field for the DTR Verifying Officer
- `_DepartmentDetailsDialog`: Department details and employee management

### Controller (`ui/controller.py`)

**UIController**
- Business logic coordination
- State management (UIState dataclass)
- File loading and processing
- Filter application
- PDF generation coordination
- Registry operations
- CSV/attlog export

**UIState**
- Dataclass for application state
- Current file path, records, filters
- Centralized state management

**ProgressRunner**
- Helper for background operations with progress dialogs
- Threading and queue management
- Error handling

## Benefits of Modular Architecture

### 1. Separation of Concerns
- Each component has a single, well-defined responsibility
- Business logic separated from UI implementation
- Clear interfaces between components

### 2. Improved Maintainability
- Reduced `app.py` from ~750 to ~465 lines (38% reduction)
- Easier to locate and fix bugs
- Changes isolated to specific components

### 3. Enhanced Testability
- Individual components can be unit tested
- Mock interfaces for testing
- Clear dependencies

### 4. Reusability
- Components can be reused in different contexts
- Dialogs can be used from multiple locations
- Views can be embedded in different layouts

### 5. Future Framework Migration
- Business logic is UI framework independent
- Only component implementations need to change for new frameworks
- Easy to switch from Tkinter to Qt, web-based, or other frameworks

### 6. Team Collaboration
- Multiple developers can work on different components
- Clear ownership and interfaces
- Reduced merge conflicts

## Usage Examples

### Creating a New Component

```python
from lgus_dat.ui.components import ttk

class NewComponent(ttk.Frame):
    def __init__(self, parent, on_action=None):
        super().__init__(parent, padding=8)
        self.on_action = on_action
        self._build_ui()
    
    def _build_ui(self):
        ttk.Button(self, text="Action", command=self._handle_action).pack()
    
    def _handle_action(self):
        if self.on_action:
            self.on_action()
```

### Using Components in Main App

```python
from lgus_dat.ui.components import NewComponent

class ProcessorApp:
    def __init__(self, root):
        self.new_component = NewComponent(
            root,
            on_action=self._handle_component_action
        )
        self.new_component.pack(fill=tk.X)
    
    def _handle_component_action(self):
        # Handle action
        pass
```

### Extending the Controller

```python
class UIController:
    def new_business_method(self, data):
        # Business logic
        pass
```

## Migration Path for UI Framework Changes

If you need to switch UI frameworks (e.g., from Tkinter to Qt):

1. **Keep Business Logic**: No changes needed to `controller.py` or business logic
2. **Implement Component Interfaces**: Create new component implementations using new framework
3. **Update Views**: Reimplement view components with new framework widgets
4. **Adapt Dialogs**: Recreate dialogs using new framework dialog system
5. **Update Main App**: Modify `app.py` to use new component implementations

The core business logic, data models, and processing remain completely unchanged.

## Testing Strategy

### Unit Testing Components

```python
def test_file_toolbar():
    # Create mock parent and callbacks
    toolbar = FileToolbar(parent, on_open=mock_callback)
    # Test button clicks and callbacks
    assert toolbar.on_open == mock_callback
```

### Integration Testing

```python
def test_controller_workflow():
    registry = AttendanceRegistry()
    controller = UIController(registry)
    # Test complete workflow
    controller.load_file(test_file)
    controller.process_records()
    assert len(controller.state.processed_records) > 0
```

## Performance Considerations

- Components are lightweight and fast to instantiate
- Progress dialogs prevent UI freezing during long operations
- Efficient data filtering and treeview updates
- State management minimizes redundant operations

## Recent UI/UX Improvements

### Department Management Enhancements

**Employee Dialog Improvements**
- Replaced department ID text input with dropdown selection
- Shows department names instead of numeric IDs
- Includes empty option for unassigned employees
- Improved validation and user experience

**Department Tab Enhancements**
- Added "View Details" button for comprehensive department management
- Added employee count column to department treeview
- Implemented safety check to prevent deletion of departments with assigned employees
- Enhanced sorting to handle empty values properly

**Department Details Dialog**
- New `_DepartmentDetailsDialog` class for viewing department information
- Shows department ID, name, and current employee count
- Employee management within department:
  - Add employees from available unassigned pool
  - Remove employees from department (sets to unassigned)
  - View current department members
- Real-time employee count updates

**Employee Display Improvements**
- Changed column header from "Department ID" to "Department"
- Displays department names instead of numeric IDs
- Updated search functionality to work with department names
- Improved filtering by department name

### All Records Window

A standalone `AllRecordsWindow` is available from **View → All Records** in the main menu bar. It loads every attendance log directly from `AttendanceRegistry`, processes them into IN/OUT rows, and provides the same search and date-range filters as the Processed page. Because it reads from the persisted registry rather than the in-memory `UIState`, it always reflects the full accumulated dataset and can be refreshed after new imports without requiring the workflow-driven Processed tab.

## Future Enhancements

Potential improvements to the modular architecture:

- **Theme System**: Pluggable UI themes
- **Plugin System**: Dynamic component loading
- **Accessibility**: Enhanced screen reader support
- **Internationalization**: Multi-language support
- **Custom Components**: User-defined UI components
- **Layout Engine**: More flexible layout management
- **State Persistence**: Save/restore UI state

## Conclusion

The modular UI architecture provides a solid foundation for future development while maintaining all existing functionality. The PySide6 desktop UI is now the primary interface and shares the same business logic and registry as the legacy Tkinter UI through `UIController` and `DesktopController`. This dual-stack approach preserves existing work while enabling a modern, maintainable interface.