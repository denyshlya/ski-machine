# ski_loadcell.spec
# PyInstaller spec file – generates a single-folder Windows build.
#
# Usage:
#   pyinstaller ski_loadcell.spec
#
# Output:  dist/SkiLoadcell/SkiLoadcell.exe
# ---------------------------------------------------------

import sys
from pathlib import Path

block_cipher = None

ROOT = Path(SPECPATH)

a = Analysis(
    [str(ROOT / "main.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        # Include any extra assets here, e.g.:
        # (str(ROOT / "assets" / "icon.ico"), "assets"),
    ],
    hiddenimports=[
        # tkinter is usually auto-detected, but list extras here if needed
        "tkinter",
        "tkinter.ttk",
        "tkinter.messagebox",
        "matplotlib.backends.backend_tkagg",
        "matplotlib.figure",
        "serial",
        "serial.tools",
        "serial.tools.list_ports",
        # All GUI pages (PyInstaller can miss dynamic imports)
        "gui.pages.home",
        "gui.pages.calibration_mode",
        "gui.pages.debug_mode",
        "gui.pages.loadcell_calibration",
        "gui.pages.actuator_calibration",
        "gui.pages.system_check",
        "gui.pages.actuator_manual",
        "gui.pages.estop_status",
        "gui.pages.system_reboot",
        "gui.pages.saved_measurements",
        "gui.pages.single_measurement",
        "gui.pages.live_view",
        "gui.widgets.loadcell_chart",
        "core.arduino_manager",
        "core.serial_reader",
        "core.data_store",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "PyQt5", "PyQt6", "PySide2", "PySide6",
        "wx", "gi",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="SkiLoadcell",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,           # no terminal window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon="assets/icon.ico",  # uncomment when you have an icon
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="SkiLoadcell",
)
