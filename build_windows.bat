@echo off
REM ─────────────────────────────────────────────────────────────────────────────
REM  build_windows.bat
REM  Builds SkiLoadcell.exe using PyInstaller.
REM
REM  Requirements:
REM    pip install -r requirements.txt
REM
REM  Output:
REM    dist\SkiLoadcell\SkiLoadcell.exe   (and supporting files)
REM ─────────────────────────────────────────────────────────────────────────────

echo.
echo ============================================================
echo  Ski Load Cell System – Windows build
echo ============================================================
echo.

REM Install / upgrade dependencies
echo [1/3] Installing dependencies...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo ERROR: pip install failed.
    pause & exit /b 1
)

REM Clean previous build
echo [2/3] Cleaning previous build...
if exist build   rmdir /s /q build
if exist dist    rmdir /s /q dist

REM Run PyInstaller
echo [3/3] Running PyInstaller...
pyinstaller ski_loadcell.spec --noconfirm
if errorlevel 1 (
    echo ERROR: PyInstaller failed.
    pause & exit /b 1
)

echo.
echo ============================================================
echo  Build complete!
echo  Executable: dist\SkiLoadcell\SkiLoadcell.exe
echo ============================================================
echo.
pause
