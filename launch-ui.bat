@echo off
REM Launch the Video Censor Personal desktop UI
REM 
REM This script launches the desktop application using CustomTkinter.
REM Works on Windows (Command Prompt and PowerShell).
REM
REM Requires: Python 3.13 or higher
REM
REM Usage:
REM   launch-ui.bat
REM   double-click launch-ui.bat in Windows Explorer

setlocal enabledelayedexpansion

REM Get the directory where this script is located
set "SCRIPT_DIR=%~dp0"

REM Check Python version
python3 -c "import sys; major, minor = sys.version_info[:2]; exit(0 if (major > 3 or (major == 3 and minor >= 13)) else 1)" 2>nul
if errorlevel 1 (
    echo Error: Python 3.13 or higher is required
    for /f "tokens=*" %%i in ('python3 --version 2^>nul') do set "PYTHON_VERSION=%%i"
    if defined PYTHON_VERSION (
        echo Current version: %PYTHON_VERSION%
    ) else (
        echo Python 3 is not installed or not in PATH
    )
    echo.
    echo To install Python 3.13 with Tkinter support:
    echo.
    echo Option 1: Windows Package Manager (if installed)
    echo   winget install Python.Python.3.13
    echo.
    echo Option 2: Direct download (recommended)
    echo   1. Visit: https://www.python.org/downloads/
    echo   2. Download Python 3.13.x for Windows
    echo   3. Run the installer
    echo   4. CHECK "tcl/tk and IDLE" during installation
    echo   5. Restart this launcher
    echo.
    echo Option 3: Chocolatey package manager
    echo   choco install python313
    echo.
    pause
    exit /b 1
)

REM Check Tkinter availability
python3 -c "import tkinter" >nul 2>&1
if errorlevel 1 (
    echo Error: Python Tkinter module is not installed
    echo.
    echo Tkinter is required for the desktop UI. Install it using:
    echo.
    echo For most installations, reinstall Python with Tkinter enabled:
    echo   Visit: https://www.python.org/downloads/
    echo   During installation, ensure "tcl/tk and IDLE" is checked
    echo.
    echo Or use Windows Package Manager:
    echo   winget install Python.Python.3.13
    echo.
    pause
    exit /b 1
)

REM Check if virtual environment exists and activate it
if exist "%SCRIPT_DIR%venv\Scripts\activate.bat" (
    call "%SCRIPT_DIR%venv\Scripts\activate.bat"
) else if exist "%SCRIPT_DIR%.venv\Scripts\activate.bat" (
    call "%SCRIPT_DIR%.venv\Scripts\activate.bat"
)

REM Launch the desktop UI
python3 -m video_censor_personal.ui.main

REM Pause so errors are visible if they occur
if errorlevel 1 pause
