# Agent Instructions

When working on this repository, always consult the project blueprint in `Docs/MB10-VL_Sequential_IN_OUT_Dev_Blueprint.md` before making system changes or adding features.

The blueprint defines the core business rules, architecture, and acceptance criteria for the MB10-VL Sequential IN/OUT `.DAT` Processor. Any change to parsing, status assignment, output format, validation, or processing behavior must remain consistent with the blueprint. If a change contradicts the blueprint, discuss it with the user first and update the blueprint if approved.

## Git Workflow

Do not create branches. Use tags for checkpoints and releases instead.

## Build & Release Conventions

- The project version is the single source of truth in `pyproject.toml`.
- When building the PySide6 desktop executable with PyInstaller, name the output file using the current version tag: `lgus-dat-desktop-V{VERSION}.exe` (Windows) or `lgus-dat-desktop-V{VERSION}` (Linux).
- Example for version `0.21.0`: `lgus-dat-desktop-V0.21.0.exe`.
- Always update `pyproject.toml` and `Docs/status.md` to the same version before building a release executable.
