# Launching Video Censor Personal UI

## Requirements

- **Python 3.13 or higher** (all launch scripts verify this automatically)
- **Tkinter module** (required for the GUI, all launch scripts verify this automatically)
- Virtual environment created in project directory (venv or .venv)
- Dependencies installed: `pip install -r requirements.txt`

All launch scripts will automatically check both your Python version and Tkinter availability before launching the UI, providing clear instructions if either is missing.

## Launch Methods

Choose the appropriate method for your operating system:

### Opening Results (Optional)
You can optionally pass a JSON file path to automatically load results for review:
```bash
./launch-ui.sh path/to/results.json
```

This is useful after running analysis with the `--edit` flag, or to directly review previous analysis results.

## macOS

### Method 1: Double-click in Finder (Recommended)
1. Open Finder and navigate to the project directory
2. Double-click **launch-ui.command**
3. The UI will launch automatically

### Method 2: Terminal
```bash
./launch-ui.sh
```

### Method 3: Terminal with Results File
To open the UI and automatically load a results JSON file:
```bash
./launch-ui.sh output-video/results.json
```

## Windows

### Method 1: Double-click in Explorer (Graphical, No Console)
1. Open Windows Explorer and navigate to the project directory
2. Double-click **launch-ui.vbs**
3. The UI will launch silently without showing a console window

### Method 2: Double-click Batch File (With Console)
1. Open Windows Explorer and navigate to the project directory
2. Double-click **launch-ui.bat**
3. The UI will launch (console window will appear during startup, then close when the UI opens)

### Method 3: Command Prompt/PowerShell
```cmd
launch-ui.bat
```

### Method 4: Command Prompt/PowerShell with Results File
```cmd
launch-ui.bat path\to\results.json
```

For example:
```cmd
launch-ui.bat output-video\Psych1_1.json
```

## Linux

### Method 1: Double-click in File Manager (Recommended)
1. Open your file manager (Nautilus, Dolphin, Thunar, etc.)
2. Navigate to the project directory
3. Double-click **launch-ui.desktop**
4. Choose "Execute" when prompted
5. The UI will launch in a terminal window

**First-time setup**: If your file manager doesn't recognize .desktop files as executable, right-click on launch-ui.desktop, select "Properties" or "Permissions", and enable "Execute as program" or "Allow executing file as program".

### Method 2: Terminal
```bash
./launch-ui.sh
```

### Method 3: Terminal with Results File
To open the UI and automatically load a results JSON file:
```bash
./launch-ui.sh output-video/results.json
```

### Method 4: Programmatically
You can also make launch-ui.desktop the default launcher by copying it to your applications directory:
```bash
mkdir -p ~/.local/share/applications
cp launch-ui.desktop ~/.local/share/applications/
```

Then search for "Video Censor Personal" in your applications menu.

## All Methods

All launch files automatically detect and activate your Python virtual environment (venv or .venv) before starting the UI, so you don't need to manually activate it. Python version is verified before launching.

## Using with Analysis Pipeline

After running analysis, you can automatically open the results in the preview editor:

```bash
# Run analysis and open the editor automatically
python video_censor_personal.py --input video.mp4 --config config.yaml --output results.json --edit
```

Or, if you've already run analysis and just want to review the results:

```bash
# Launch the UI with a previously generated results file
./launch-ui.sh results.json

# Or with absolute path
./launch-ui.sh /path/to/results.json
```

The script will automatically convert relative paths to absolute paths for proper loading.

### Troubleshooting

**"Python Tkinter module is not installed" or "_tkinter ModuleNotFoundError"**
- Your Python installation is missing Tkinter support
- This often happens when Python is installed without the optional Tcl/Tk library

**If you used pyenv to install Python:**
This is the most common cause. You must install `tcl-tk` via Homebrew BEFORE installing Python:
```bash
# 1. Install tcl-tk (required dependency)
brew install tcl-tk

# 2. Uninstall the broken Python
pyenv uninstall 3.13.0

# 3. Reinstall Python with Tkinter support
PYTHON_CONFIGURE_OPTS="--with-tcltk" pyenv install 3.13.0

# 4. Set it for this project
pyenv local 3.13.0

# 5. Verify it works
python3 -c "import tkinter; print('Tkinter works!')"
```

**macOS (Homebrew):**
```bash
brew install python-tk@3.13
```

**macOS (pyenv - Recommended):**
```bash
PYTHON_CONFIGURE_OPTS="--with-tcltk" pyenv install 3.13.0
pyenv local 3.13.0
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install python3.13-tk
```

**Linux (Fedora/RHEL):**
```bash
sudo dnf install python3.13-tkinter
```

**Windows:**
- Uninstall Python 3.13
- Reinstall Python 3.13 from https://www.python.org/downloads/
- **Important**: During installation, check the box for **"tcl/tk and IDLE"**
- Or use: `winget install Python.Python.3.13`

**Verify Tkinter is installed:**
```bash
python3 -c "import tkinter; print('Tkinter is installed')"
```

**"Python 3.13 or higher is required"**
- You're using an older Python version
- The launcher provides platform-specific installation instructions

**macOS (Homebrew):**
```bash
brew install python@3.13
```

**macOS (pyenv - Recommended):**
```bash
# Important: Install tcl-tk first (required for Tkinter support)
brew install pyenv tcl-tk

# Then install Python 3.13 with Tkinter
PYTHON_CONFIGURE_OPTS="--with-tcltk" pyenv install 3.13.0
pyenv local 3.13.0

# Verify Tkinter works
python3 -c "import tkinter; print('Tkinter works!')"
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install python3.13 python3.13-tk
```

**Linux (Fedora/RHEL):**
```bash
sudo dnf install python3.13 python3.13-tkinter
```

**Windows (Direct Download):**
1. Visit: https://www.python.org/downloads/
2. Download Python 3.13.x for Windows
3. Run the installer
4. **CHECK "tcl/tk and IDLE"** during installation
5. Restart the launcher

**Windows (Package Managers):**
```cmd
winget install Python.Python.3.13
REM or
choco install python313
```

**Verify installation:**
```bash
python3 --version
```

**"Command not found" or "No such file"**
- Make sure you're in the project root directory
- On Linux/macOS, ensure the script has execute permissions: `chmod +x launch-ui.sh launch-ui.command launch-ui.desktop`

**"Python not found"**
- Ensure Python 3.13+ is installed and in your PATH
- Check: `python3 --version`

**Virtual environment not activated**
- Ensure venv or .venv directory exists in the project root
- Create it if needed: `python3.13 -m venv venv`

**Script won't execute (Windows)**
- On Windows, if .vbs scripts are disabled, try the .bat method instead
- Or check your Windows Defender/Antivirus settings

**Permission denied (Linux/macOS)**
- Make executable: `chmod +x launch-ui.desktop launch-ui.sh launch-ui.command`
