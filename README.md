# Video Censor Personal

[![Tests](https://github.com/justinfiore/video-censor-personal/actions/workflows/test.yml/badge.svg)](https://github.com/justinfiore/video-censor-personal/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/justinfiore/video-censor-personal/branch/main/graph/badge.svg)](https://codecov.io/gh/justinfiore/video-censor-personal)

Automatically analyze videos to detect inappropriate or undesired content, then skip, blur, or censor those sections. Get AI-powered content detection with full control over what gets flagged and how it's remediated.

## Capabilities

The system detects:
- **Nudity** - Nude or partially nude content
- **Profanity** - Explicit language and swearing
- **Violence** - Physical violence and aggressive scenes
- **Sexual Themes** - Sexual content and suggestive material
- **Custom Concepts** - User-defined content categories

Remediation options:
- **Audio Censoring** - Automatically bleep or silence profanity
- **Video Censoring** - Blur, cut, or skip visual content
- **Smart Filtering** - Apply different remediation per content type
- **Chapter Markers** - Add skip markers to video files (MKV/MP4) for quick navigation in media players (VLC, Plex, Kodi, etc.)
- **JSON Results** - Detailed analysis with confidence scores and timestamps for manual review

## Quick Start

### 1. Install Python

**macOS (Homebrew)**
```bash
brew install python@3.13
```

**macOS (pyenv - for multiple versions)**
```bash
brew install pyenv tcl-tk
PYTHON_CONFIGURE_OPTS="--with-tcltk" pyenv install 3.13.0
pyenv local 3.13.0
```

**Linux (Ubuntu/Debian)**
```bash
sudo apt-get update
sudo apt-get install python3.13 python3.13-tk
```

**Linux (Fedora/RHEL)**
```bash
sudo dnf install python3.13 python3.13-tkinter
```

**Windows**
- Download from https://www.python.org/downloads/
- During installation, check **"tcl/tk and IDLE"**

### 2. Install External Tools

**ffmpeg** (required for video processing)
```bash
# macOS
brew install ffmpeg

# Linux (Ubuntu/Debian)
sudo apt-get install ffmpeg

# Windows - download from https://ffmpeg.org/download.html
```

**mkvtoolnix** (optional, needed only for chapter markers in MKV files)
```bash
# macOS
brew install mkvtoolnix

# Linux (Ubuntu/Debian)
sudo apt-get install mkvtoolnix

# Windows - download from https://mkvtoolnix.download/
```

### 3. Setup Project

```bash
# Clone repository
git clone <repository-url>
cd video-censor-personal

# Create virtual environment
python3.13 -m venv venv
source venv/bin/activate  # macOS/Linux
# or: venv\Scripts\activate.bat  # Windows

# Install dependencies
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# Verify installation
python video_censor_personal.py --help
```

## Usage

### Command Line

Analyze a video and generate a JSON report with detected segments:

```bash
python video_censor_personal.py \
  --input video.mp4 \
  --config config.yaml \
  --output results.json
```

Remediate a video based on detection results:

```bash
python video_censor_personal.py \
  --input video.mp4 \
  --config config.yaml \
  --input-json results.json \
  --output-video output.mp4
```

Analyze AND remediate in one command:

```bash
python video_censor_personal.py \
  --input video.mp4 \
  --config config.yaml \
  --output results.json \
  --output-video output.mp4
```

### Desktop UI (Preview Editor)

Launch the desktop UI to review detection results and manually adjust which segments get flagged:

**Easiest method** (if you have a results file):
```bash
./launch-ui.sh results.json
```

**From terminal**:
```bash
python -m video_censor_personal.ui.preview_editor results.json
```

**Integrated workflow** (analyze + auto-open editor):
```bash
python video_censor_personal.py \
  --input video.mp4 \
  --config config.yaml \
  --output results.json \
  --edit
```

**macOS App** (install as native application):
```bash
./launch-ui.sh
# Choose "yes" to install to Applications folder
# Then launch from Spotlight (Cmd+Space)
```

### Preview Editor Features

- **Three-pane layout**: Segment list, video player, details panel
- **Video playback**: Built-in player with controls (play/pause, seek, speed, volume)
- **Segment review**: Click to jump to timestamp, view detection details
- **Allow/not-allow**: Toggle segments to exclude them from remediation
- **Keyboard shortcuts**: Space (play/pause), ← → (seek), ↑ ↓ (navigate), A (toggle allow), Enter (jump)
- **Filtering**: View only flagged/allowed segments, filter by content type

See [LAUNCH_UI.md](LAUNCH_UI.md) for detailed UI instructions.

## Configuration

Create a `config.yaml` file to control detection and remediation:

```yaml
detectors:
  - type: "llava"
    name: "llava-primary"
    categories:
      - "Nudity"
      - "Violence"
      - "Sexual Themes"

processing:
  frame_sampling:
    strategy: "uniform"  # extract one frame per second
    sample_rate: 1.0
  max_workers: 4

remediation:
  video:
    mode: "blank"        # blank, cut, or none
  audio:
    mode: "bleep"        # bleep, silence, or none
```

See the example config files in the repository and [CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md) for all options.

## System Requirements

- **Python**: 3.13 or later (with Tkinter for desktop UI)
- **Operating System**: macOS, Linux, or Windows
- **Disk Space**: 
  - ~2-5 GB for Python environment
  - ~10-20 GB for AI models (varies by model)
  - Additional space for videos and output
- **RAM**: 8 GB minimum (16+ GB recommended)
- **GPU**: Optional but recommended for faster processing

## Troubleshooting

### Tkinter Not Found
```
ModuleNotFoundError: No module named '_tkinter'
```

**If using pyenv:**
```bash
brew install tcl-tk
pyenv uninstall 3.13.0
PYTHON_CONFIGURE_OPTS="--with-tcltk" pyenv install 3.13.0
```

**If using Homebrew:**
```bash
brew install python-tk@3.13
```

**If using Windows installer:**
Uninstall Python, then reinstall and check "tcl/tk and IDLE"

### ffmpeg Not Found
```bash
# macOS
brew install ffmpeg

# Linux (Ubuntu/Debian)
sudo apt-get install ffmpeg
```

### Out of Memory
- Reduce batch size in config
- Use smaller model
- Reduce `max_workers`

See [LAUNCH_UI.md](LAUNCH_UI.md) for more troubleshooting.

## Testing

Run tests to verify everything works:

```bash
# Run all tests (including UI tests)
./run-tests.sh

# Run only non-UI tests (recommended during development)
./run-non-ui-tests.sh

# Run only UI tests
./run-ui-tests.sh

# Run specific test file or test
./run-specific-tests.sh "tests/test_module.py"
./run-specific-tests.sh "tests/test_module.py::TestClass::test_method"
```

For more details on testing, see the Testing Instructions in [openspec/AGENTS.md](openspec/AGENTS.md).

## Next Steps

- **Getting Started**: See [QUICK_START.md](QUICK_START.md) for detailed walkthrough
- **Configuration**: See [CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md) for all config options
- **System Details**: See [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md) for architecture and design
- **Testing**: See instructions above or [openspec/AGENTS.md](openspec/AGENTS.md)

## Support

- Check [QUICK_START.md](QUICK_START.md) for common setup issues
- Review configuration examples in the repository
- Use `--verbose` flag for debug output
- Check [LAUNCH_UI.md](LAUNCH_UI.md) for UI-specific issues

## Contributing

Contributions are welcome. Please:
1. Create a feature branch: `git checkout -b feature/description`
2. Make changes and test thoroughly: `pytest`
3. Submit a pull request

## License

This project is provided as-is for personal use.
