#!/bin/bash
# Launch the Video Censor Personal desktop UI from Finder
# 
# This file can be double-clicked in macOS Finder to launch the desktop UI.
# Make it executable with: chmod +x launch-ui.command
#
# The .command extension is recognized by macOS and can be double-clicked.
# Requires: Python 3.13 or higher

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Function to check Python version
check_python_version() {
    if ! command -v python3 &> /dev/null; then
        echo "Error: Python 3 is not installed or not in PATH"
        echo ""
        echo "To install Python 3.13 with Tkinter support on macOS:"
        echo ""
        echo "Option 1: Using Homebrew (simpler, recommended for new users)"
        echo "  brew install python@3.13"
        echo ""
        echo "Option 2: Using pyenv (recommended, allows multiple Python versions)"
        echo "  Install dependencies and pyenv:"
        echo "    brew install pyenv tcl-tk"
        echo ""
        echo "  Then install Python 3.13 with Tkinter:"
        echo "    PYTHON_CONFIGURE_OPTS=\"--with-tcltk\" pyenv install 3.13.0"
        echo "    pyenv local 3.13.0"
        echo ""
        echo "After installation, please restart this launcher."
        echo ""
        sleep 5
        exit 1
    fi

    local python_version
    python_version=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null)
    
    local required_version="3.13"
    if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
        echo "Error: Python 3.13 or higher is required"
        echo "Current version: Python $python_version"
        echo ""
        echo "To upgrade to Python 3.13 with Tkinter support on macOS:"
        echo ""
        echo "Option 1: Using Homebrew (simpler, recommended for new users)"
        echo "  brew install python@3.13"
        echo ""
        echo "Option 2: Using pyenv (recommended, allows multiple Python versions)"
        echo "  brew install tcl-tk  (if not already installed)"
        echo "  PYTHON_CONFIGURE_OPTS=\"--with-tcltk\" pyenv install 3.13.0"
        echo "  pyenv local 3.13.0"
        echo ""
        echo "After installation, please restart this launcher."
        echo ""
        sleep 5
        exit 1
    fi
}

# Function to check if Tkinter is available
check_tkinter() {
    if ! python3 -c "import tkinter" 2>/dev/null; then
        echo "Error: Python Tkinter module is not installed"
        echo ""
        echo "Tkinter is required for the desktop UI. Install it on macOS using:"
        echo ""
        echo "Option 1: Using Homebrew (simpler)"
        echo "  brew install python-tk@3.13"
        echo ""
        echo "Option 2: Reinstall Python with Tkinter support using pyenv"
        echo "  brew install tcl-tk  (required for Tkinter support)"
        echo "  pyenv uninstall 3.13.0"
        echo "  PYTHON_CONFIGURE_OPTS=\"--with-tcltk\" pyenv install 3.13.0"
        echo "  pyenv local 3.13.0"
        echo ""
        echo "If you installed Python with Homebrew initially, use Option 1."
        echo "If you used pyenv, use Option 2 (install tcl-tk first!)."
        echo ""
        sleep 5
        exit 1
    fi
}

# Check if virtual environment exists and activate it
if [ -d "$SCRIPT_DIR/venv" ]; then
    source "$SCRIPT_DIR/venv/bin/activate"
elif [ -d "$SCRIPT_DIR/.venv" ]; then
    source "$SCRIPT_DIR/.venv/bin/activate"
fi

# Check Python version before proceeding
check_python_version

# Check Tkinter availability
check_tkinter

# First, create/update the app bundle if needed
if [ ! -d "$SCRIPT_DIR/Video Censor Personal.app" ]; then
    echo "Creating macOS app bundle..."
    bash "$SCRIPT_DIR/create-macos-app.sh"
    
    # Offer to install to Applications folder
    echo ""
    echo "Installation:"
    echo "For a better experience, you can install the app to your Applications folder."
    echo "This will make it available in Spotlight, Launchpad, and the dock."
    echo ""
    read -p "Copy to ~/Applications? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cp -r "$SCRIPT_DIR/Video Censor Personal.app" ~/Applications/
        echo "App installed to ~/Applications/Video Censor Personal.app"
    fi
fi

# Launch the app bundle (this will use the proper CFBundleName from Info.plist)
open -a "Video Censor Personal"
