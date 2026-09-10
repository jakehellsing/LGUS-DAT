"""Patcher for LGUS-DAT -- updates an existing Windows install from the registry."""
from __future__ import annotations

import ctypes
import shutil
import sys
import winreg
from pathlib import Path

APP_ID = "72D4E2B4-7F6A-4B7E-9C1D-3E8A5F2B1C6D"
VERSION = "1.0.3"


def is_admin() -> bool:
    """Return True if the current process is elevated."""
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:  # pragma: no cover
        return False


def find_install_dir() -> Path | None:
    """Read the Inno Setup uninstall registry key for the install location."""
    roots = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
    ]
    # Inno Setup appends "_is1" to the AppId in the registry key name.
    key_names = [f"{APP_ID}_is1", APP_ID]
    for root, subkey in roots:
        for key_name in key_names:
            try:
                with winreg.OpenKey(root, f"{subkey}\\{key_name}") as k:
                    for value_name in ("InstallLocation", "Inno Setup: App Path"):
                        try:
                            value, _ = winreg.QueryValueEx(k, value_name)
                            if value:
                                return Path(value)
                        except FileNotFoundError:
                            continue
                    try:
                        uninstall, _ = winreg.QueryValueEx(k, "UninstallString")
                        if uninstall:
                            uninstall = uninstall.strip().strip('"')
                            if uninstall.lower().endswith(".exe"):
                                return Path(uninstall).parent
                    except FileNotFoundError:
                        pass
            except FileNotFoundError:
                continue
    return None


def message_box(text: str, title: str = "LGUS-DAT Patcher", style: int = 0x40) -> int:
    """Show a Windows message box."""
    return ctypes.windll.user32.MessageBoxW(0, text, title, style)


def _update_source() -> Path:
    """Return the directory containing the updated application files."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / "update"
    # Development fallback: repo root
    return Path(__file__).resolve().parents[1] / "dist" / "desktop" / f"lgus-dat-desktop-V{VERSION}"


def main(argv: list[str] | None = None) -> int:
    """Run the patcher."""
    if not is_admin():
        message_box(
            "This patcher must be run as Administrator.",
            "LGUS-DAT Patcher",
            0x10,
        )
        return 1

    install_dir = find_install_dir()
    if install_dir is None:
        message_box(
            "LGUS-DAT installation not found in the registry.",
            "LGUS-DAT Patcher",
            0x10,
        )
        return 1

    source = _update_source()
    if not source.exists():
        message_box(
            f"Update files not found at {source}",
            "LGUS-DAT Patcher",
            0x10,
        )
        return 1

    try:
        shutil.copytree(source, install_dir, dirs_exist_ok=True)
    except Exception as e:  # pragma: no cover
        message_box(f"Patch failed: {e}", "LGUS-DAT Patcher", 0x10)
        return 1

    message_box(
        f"LGUS-DAT has been patched successfully in:\n{install_dir}",
        "LGUS-DAT Patcher",
        0x40,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
