#!/usr/bin/env bash
# Launch the Video Censor Personal desktop UI
# 
# This script launches the desktop application using CustomTkinter.
# Works on macOS, Linux, and other Unix-like systems with Bash.
#
# Requires: Python 3.13 or higher
#
# Usage:
#   ./launch-ui.sh
#   bash launch-ui.sh

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Function to detect Linux distribution
detect_linux_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        echo "$ID"
    elif [ -f /etc/redhat-release ]; then
        echo "rhel"
    else
        echo "unknown"
    fi
}

# Function to check Python version
check_python_version() {
    if ! command -v python3 &> /dev/null; then
        echo "Error: Python 3 is not installed or not in PATH"
        echo ""
        echo "To install Python 3.13:"
        echo ""
        
        # Detect OS and provide platform-specific instructions
        if [[ "$OSTYPE" == "darwin"* ]]; then
            echo "macOS detected"
            echo ""
            echo "Option 1: Using Homebrew (simpler, recommended for new users)"
            echo "  brew install python@3.13"
            echo ""
            echo "Option 2: Using pyenv (recommended, allows multiple Python versions)"
            echo "  brew install pyenv tcl-tk"
            echo "  PYTHON_CONFIGURE_OPTS=\"--with-tcltk\" pyenv install 3.13.0"
            echo "  pyenv local 3.13.0"
            echo ""
            echo "After installation, open a new terminal and try again."
        elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
            local distro=$(detect_linux_distro)
            echo "Linux detected (distro: $distro)"
            echo ""
            
            if [[ "$distro" =~ ^(ubuntu|debian)$ ]]; then
                echo "Ubuntu/Debian installation:"
                echo "  sudo apt-get update"
                echo "  sudo apt-get install python3.13 python3.13-tk"
            elif [[ "$distro" =~ ^(fedora|rhel|centos)$ ]]; then
                echo "Fedora/RHEL/CentOS installation:"
                echo "  sudo dnf install python3.13 python3.13-tkinter"
            else
                echo "Ubuntu/Debian installation:"
                echo "  sudo apt-get update"
                echo "  sudo apt-get install python3.13 python3.13-tk"
                echo ""
                echo "Or for Fedora/RHEL/CentOS:"
                echo "  sudo dnf install python3.13 python3.13-tkinter"
            fi
            echo ""
            echo "After installation, open a new terminal and try again."
        else
            echo "Unsupported OS type: $OSTYPE"
            echo "Visit: https://www.python.org/downloads/"
            echo "Select Python 3.13.x and ensure Tkinter is included"
        fi
        echo ""
        exit 1
    fi

    local python_version
    python_version=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null)
    
    local required_version="3.13"
    if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
        echo "Error: Python 3.13 or higher is required"
        echo "Current version: Python $python_version"
        echo ""
        echo "To upgrade to Python 3.13 with Tkinter support:"
        echo ""
        
        # Detect OS and provide platform-specific instructions
        if [[ "$OSTYPE" == "darwin"* ]]; then
            echo "macOS detected"
            echo ""
            echo "Option 1: Using Homebrew (simpler, recommended for new users)"
            echo "  brew install python@3.13"
            echo ""
            echo "Option 2: Using pyenv (recommended, allows multiple Python versions)"
            echo "  brew install tcl-tk  (if not already installed)"
            echo "  PYTHON_CONFIGURE_OPTS=\"--with-tcltk\" pyenv install 3.13.0"
            echo "  pyenv local 3.13.0"
            echo ""
            echo "After installation, open a new terminal and try again."
        elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
            local distro=$(detect_linux_distro)
            echo "Linux detected (distro: $distro)"
            echo ""
            
            if [[ "$distro" =~ ^(ubuntu|debian)$ ]]; then
                echo "Ubuntu/Debian installation:"
                echo "  sudo apt-get update"
                echo "  sudo apt-get install python3.13 python3.13-tk"
            elif [[ "$distro" =~ ^(fedora|rhel|centos)$ ]]; then
                echo "Fedora/RHEL/CentOS installation:"
                echo "  sudo dnf install python3.13 python3.13-tkinter"
            else
                echo "Ubuntu/Debian installation:"
                echo "  sudo apt-get update"
                echo "  sudo apt-get install python3.13 python3.13-tk"
                echo ""
                echo "Or for Fedora/RHEL/CentOS:"
                echo "  sudo dnf install python3.13 python3.13-tkinter"
            fi
            echo ""
            echo "After installation, open a new terminal and try again."
        else
            echo "Visit: https://www.python.org/downloads/"
            echo "Select Python 3.13.x and ensure Tkinter is included"
        fi
        echo ""
        exit 1
    fi
}

# Function to check if Tkinter is available
check_tkinter() {
    if ! python3 -c "import tkinter" 2>/dev/null; then
        echo "Error: Python Tkinter module is not installed"
        echo ""
        echo "Tkinter is required for the desktop UI. Install it using:"
        echo ""
        
        # Detect OS and provide platform-specific instructions
        if [[ "$OSTYPE" == "darwin"* ]]; then
            echo "macOS detected"
            echo ""
            echo "Option 1: Using Homebrew"
            echo "  brew install python-tk@3.13"
            echo ""
            echo "Option 2: Reinstall Python with pyenv (if originally installed with pyenv)"
            echo "  PYTHON_CONFIGURE_OPTS=\"--with-tcltk\" pyenv install 3.13.0"
            echo "  pyenv local 3.13.0"
        elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
            local distro=$(detect_linux_distro)
            echo "Linux detected (distro: $distro)"
            echo ""
            
            if [[ "$distro" =~ ^(ubuntu|debian)$ ]]; then
                echo "Ubuntu/Debian installation:"
                echo "  sudo apt-get update"
                echo "  sudo apt-get install python3.13-tk"
            elif [[ "$distro" =~ ^(fedora|rhel|centos)$ ]]; then
                echo "Fedora/RHEL/CentOS installation:"
                echo "  sudo dnf install python3.13-tkinter"
            else
                echo "Ubuntu/Debian installation:"
                echo "  sudo apt-get update"
                echo "  sudo apt-get install python3.13-tk"
                echo ""
                echo "Or for Fedora/RHEL/CentOS:"
                echo "  sudo dnf install python3.13-tkinter"
            fi
        else
            echo "Unsupported OS type: $OSTYPE"
            echo ""
            echo "Please install Tkinter for your OS:"
            echo "  macOS: brew install python-tk@3.13"
            echo "  Linux: sudo apt-get install python3.13-tk  (Ubuntu/Debian)"
            echo "         sudo dnf install python3.13-tkinter (Fedora/RHEL)"
        fi
        echo ""
        exit 1
    fi
}

# Parse optional JSON file argument
JSON_FILE="${1:-}"

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

echo "Launching application with Python Version: $(python3 --version)"

# On macOS, use the app bundle for proper menu bar integration
if [[ "$OSTYPE" == "darwin"* ]]; then
    if [ ! -d "$SCRIPT_DIR/Video Censor Personal.app" ]; then
        echo "Creating macOS app bundle..."
        bash "$SCRIPT_DIR/create-macos-app.sh"
    fi
    
    # Pass JSON file to app bundle if provided
    if [ -n "$JSON_FILE" ]; then
        # Convert relative path to absolute
        if [[ ! "$JSON_FILE" = /* ]]; then
            JSON_FILE="$(cd "$(dirname "$JSON_FILE")" && pwd)/$(basename "$JSON_FILE")"
        fi
        # Set environment variable and open app
        export VIDEO_CENSOR_JSON_FILE="$JSON_FILE"
    fi
    
    # Open the app bundle (this is asynchronous on macOS)
    # Any errors will be logged to logs/ui_error.log
    open -a "Video Censor Personal"
    echo "App launched. Check logs/ui_error.log if the app doesn't appear."
else
    # On Linux and other platforms, launch directly
    if [ -n "$JSON_FILE" ]; then
        exec python3 -m video_censor_personal.ui.main "$JSON_FILE"
    else
        exec python3 -m video_censor_personal.ui.main
    fi
fi
