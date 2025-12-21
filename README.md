# Video Censor Personal

[![Tests](https://github.com/justinfiore/video-censor-personal/actions/workflows/test.yml/badge.svg)](https://github.com/justinfiore/video-censor-personal/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/justinfiore/video-censor-personal/branch/main/graph/badge.svg)](https://codecov.io/gh/justinfiore/video-censor-personal)

A personalized video censoring system that analyzes video content and identifies segments containing inappropriate or undesired material. The system enables users to make informed decisions about which sections to skip or censor based on their preferences.

## Features

The system detects:
- **Nudity** - Nude or partially nude content
- **Profanity** - Explicit language and swearing
- **Violence** - Physical violence and aggressive scenes
- **Sexual Themes** - Sexual content and suggestive material
- **Custom Concepts** - User-defined content categories

Output and Enhancement Options:
- **JSON Detection Results** - Detailed analysis with confidence scores and timestamps
- **Audio Remediation** - Automatically bleep or silence profanity
- **Video Remediation** - Blank or cut visual content (blank mode preserves timing, cut mode removes segments)
- **Skip Chapter Markers** - Add chapter markers to video files (MKV or MP4) for easy navigation to flagged segments in media players (VLC, Plex, Kodi, etc.)

## System Requirements

### Prerequisites

- **Python**: 3.13 or later (with Tkinter support for desktop UI)
- **Operating System**: macOS, Linux, or Windows
- **Disk Space**: 
  - ~2-5 GB for Python environment and dependencies
  - ~10-20 GB for AI models (varies by model size)
  - Additional space for video files and analysis output

### Python 3.13 Installation

**macOS (Homebrew - Simplest)**
```bash
brew install python@3.13
```

**macOS (pyenv - Recommended for Multiple Versions)**
```bash
# Install tcl-tk FIRST (required for Tkinter support)
brew install pyenv tcl-tk

# Install Python 3.13
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
- **Important**: During installation, check the box for **"tcl/tk and IDLE"**

**Verify Installation**
```bash
python3 --version          # Should show 3.13.x
python3 -c "import tkinter; print('Tkinter works!')"
```

### External Tools

- **ffmpeg**: Required for video frame extraction and metadata processing
  - Download: https://ffmpeg.org/download.html
  - Used to extract frames from videos for analysis

- **mkvtoolnix**: Required for chapter writing to MKV files
  - Download: https://mkvtoolnix.download/
  - Used to embed chapter markers natively in Matroska video files
  - Alternative: Use MP4 output format with ffmpeg for native MP4 chapter atoms

## Desktop UI (Optional)

Video Censor Personal includes a desktop graphical interface built with CustomTkinter. The UI is optional—you can use the command-line interface instead.

### Preview Editor UI

The **Preview Editor** provides a visual interface for reviewing detection results and marking segments as allowed/not-allowed:

- **Three-pane layout**: Segment list (left), video player (center/top), segment details (bottom)
- **Video playback**: Built-in player with timeline visualization, controls (play/pause, skip, speed, volume)
- **Segment review**: Click segments to jump to timestamp, view detailed detection reasoning
- **Allow/not-allow marking**: Toggle segment allow status with immediate JSON persistence
- **Keyboard shortcuts**: Space (play/pause), ←/→ (seek), ↑/↓ (navigate segments), A (toggle allow), Enter (jump to segment)
- **Filtering**: Filter segments by label or allow status

#### Launching Preview Editor

**Simplest Method** (with results file):
```bash
./launch-ui.sh output-video/results.json
```

**Command Line** (no file):
```bash
python -m video_censor_personal.ui.preview_editor
```

**With results file** (command line):
```bash
python -m video_censor_personal.ui.preview_editor /path/to/results.json
```

**From Python**:
```python
from video_censor_personal.ui import launch_preview_editor
launch_preview_editor(json_file="/path/to/results.json")  # Optional
```

**Automated Workflow**:
```bash
# Run analysis and automatically open results in editor
python video_censor_personal.py --input video.mp4 --config config.yaml --output results.json --edit
```

**Manual Workflow**:
1. Run detection analysis: `python video_censor_personal.py ...`
2. Open Preview Editor with results: `./launch-ui.sh output-video/results.json`
3. Review segments, mark as allowed/not-allowed
4. JSON file is automatically saved on each change
5. Use updated JSON for remediation workflows

### Launching the Desktop UI

After completing the installation steps below, launch the UI using one of these methods:

#### macOS (Recommended: Install as macOS App)

For the best experience on macOS with proper menu bar integration:

1. Open Terminal and navigate to the project directory
2. Run: `./launch-ui.sh`
3. This will automatically create an app bundle and offer to install it to your Applications folder
4. When prompted, choose **yes** to install to ~/Applications
5. Once installed, you can:
   - Launch from Spotlight (Cmd+Space, type "Video Censor Personal")
   - Pin to your dock
   - Use Cmd+Tab to switch between apps
   - See the app name in the menu bar (not "Python")

**Note on Updates**: The app bundle is a lightweight wrapper that runs your Python code from the original project directory. Python code changes take effect immediately without reinstalling the app.

If you need to reinstall the app bundle after moving the project directory:
```bash
rm -rf "Video Censor Personal.app"
./launch-ui.sh
```

#### macOS (Alternative: Run from Terminal)
```bash
./launch-ui.sh
```

#### Windows (Explorer Double-Click - Graphical, No Console)
1. Open Windows Explorer and navigate to the project directory
2. Double-click **launch-ui.vbs**
3. The UI will launch silently

#### Windows (Explorer Double-Click - With Console)
1. Open Windows Explorer and navigate to the project directory
2. Double-click **launch-ui.bat**
3. A console will appear during startup, then close when the UI opens

#### Linux (File Manager - Recommended)
1. Open your file manager (Nautilus, Dolphin, Thunar, etc.)
2. Navigate to the project directory
3. Double-click **launch-ui.desktop**
4. Choose "Execute" when prompted

#### Linux/macOS (Terminal Alternative)
```bash
./launch-ui.sh
```

All launch scripts automatically detect and activate your Python virtual environment (venv or .venv) and verify Python version and Tkinter availability before starting the UI.

See `LAUNCH_UI.md` for detailed UI launching instructions and troubleshooting.

## Installation

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd video-censor-personal
```

### Step 2: Create a Python Virtual Environment

Create an isolated Python environment to avoid dependency conflicts:

```bash
# macOS/Linux
python3.13 -m venv venv
source venv/bin/activate

# Windows (PowerShell)
python -m venv venv
venv\Scripts\Activate.ps1

# Windows (Command Prompt)
python -m venv venv
venv\Scripts\activate.bat
```

Verify activation - you should see `(venv)` in your terminal prompt.

### Step 3: Upgrade pip and Install Dependencies

```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### Step 4: Verify Installation

```bash
python video_censor_personal.py --help
```

You should see the help message with available arguments.

## Installing External Tools

### ffmpeg Installation

ffmpeg is required to extract frames from videos.

#### macOS

Using Homebrew (recommended):
```bash
brew install ffmpeg
```

Or download from https://ffmpeg.org/download.html

#### Linux (Ubuntu/Debian)

```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

#### Linux (Fedora/RHEL)

```bash
sudo dnf install ffmpeg
```

#### Windows

1. Download from https://ffmpeg.org/download.html
2. Extract to a folder (e.g., `C:\ffmpeg`)
3. Add the folder to your PATH environment variable
4. Verify installation:
   ```bash
   ffmpeg -version
   ```

### mkvtoolnix Installation (Optional but Recommended)

mkvtoolnix is needed for reliable chapter writing to MKV video files. Skip this if you only plan to use MP4 output or don't need chapter support.

#### macOS

Using Homebrew (recommended):
```bash
brew install mkvtoolnix
```

Or download from https://mkvtoolnix.download/

#### Linux (Ubuntu/Debian)

```bash
sudo apt-get update
sudo apt-get install mkvtoolnix
```

#### Linux (Fedora/RHEL)

```bash
sudo dnf install mkvtoolnix
```

#### Windows

1. Download from https://mkvtoolnix.download/
2. Run the installer and follow the setup wizard
3. Verify installation:
   ```bash
   mkvmerge --version
   ```

## Downloading and Setting Up Models

Video Censor Personal uses local AI models for analysis. Download and configure them before your first analysis.

### Supported Models

#### LLaVA (Recommended)

LLaVA is a vision-language model that can analyze images and perform content classification with detailed reasoning.

#### CLIP (Lightweight Alternative)

CLIP is a lightweight, efficient model for content classification via text prompts. Use CLIP for faster inference and lower memory usage.

**CLIP Advantages:**
- 5-10x faster than LLaVA
- Uses ~2 GB memory vs 7+ GB for LLaVA
- Simple configuration with text prompts
- Ideal for edge devices and real-time processing

**CLIP Disadvantages:**
- No detailed reasoning about detections
- Relies on prompt quality for accuracy

**When to use CLIP:**
- Resource-constrained environments
- Need real-time or near-real-time processing
- Have well-defined content categories

**When to use LLaVA:**
- Need detailed explanation of detections
- Want automatic discovery of content types
- Have complex content to classify

### Download CLIP Model (Optional)

#### Available CLIP Model Variants

| `model_name` | Parameters | Size | Notes |
|--------------|------------|------|-------|
| `openai/clip-vit-base-patch32` | ~151M | ~600MB | Fastest, lowest quality. ViT-B/32 architecture. |
| `openai/clip-vit-base-patch16` | ~151M | ~600MB | Better than patch32, slower. ViT-B/16 architecture. |
| `openai/clip-vit-large-patch14` | ~428M | ~1.7GB | Best quality for 224px images. ViT-L/14 architecture. |
| `openai/clip-vit-large-patch14-336` | ~428M | ~1.7GB | Highest quality, fine-tuned for 336px input images. |

**Trade-offs:**
- **Patch size**: Smaller patches (14 vs 32) = more patches per image = better detail but slower
- **Model size**: `large` models are ~3x bigger than `base` but significantly more accurate
- The `336` variant expects higher-resolution inputs, which can improve accuracy for detailed content

Choose one model variant:

**ViT-Base (Fast, Recommended)** - 600 MB, suitable for most cases
```bash
python -c "
from transformers import CLIPModel, CLIPProcessor
print('Downloading CLIP ViT-Base model...')
model = CLIPModel.from_pretrained('openai/clip-vit-base-patch32')
processor = CLIPProcessor.from_pretrained('openai/clip-vit-base-patch32')
print('✓ CLIP model downloaded successfully')
"
```

**ViT-Large (More Accurate)** - 1.7 GB, better accuracy but slower
```bash
python -c "
from transformers import CLIPModel, CLIPProcessor
print('Downloading CLIP ViT-Large model...')
model = CLIPModel.from_pretrained('openai/clip-vit-large-patch14')
processor = CLIPProcessor.from_pretrained('openai/clip-vit-large-patch14')
print('✓ CLIP model downloaded successfully')
"
```

**Configuration Example:**
See `video-censor-clip-detector.yaml.example` for a complete CLIP configuration with text prompts.

### Download LLaVA 1.5 (7B - 4GB)

Choose one of the following methods:

**Method 1: Python (Automatic)**
```bash
pip install transformers torch torchvision torchaudio

python -c "
from transformers import AutoTokenizer, AutoModelForCausalLM
model_name = 'liuhaotian/llava-v1.5-7b'
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, device_map='auto')
print('✓ Model downloaded successfully')
"
```

**Method 2: Browser Download**
1. Visit: https://huggingface.co/liuhaotian/llava-v1.5-7b
2. Click "Files and versions" tab
3. Download model files to `~/.cache/huggingface/hub/models--liuhaotian--llava-v1.5-7b/snapshots/`

**Method 3: Git LFS (Command Line)**
```bash
# Install Git LFS: https://git-lfs.com
git lfs install
git clone https://huggingface.co/liuhaotian/llava-v1.5-7b
mkdir -p ~/.cache/huggingface/hub/models--liuhaotian--llava-v1.5-7b/snapshots
cp -r llava-v1.5-7b/* ~/.cache/huggingface/hub/models--liuhaotian--llava-v1.5-7b/snapshots/
```

**Method 4: wget/curl (Individual Files)**
```bash
mkdir -p ~/.cache/huggingface/hub/models--liuhaotian--llava-v1.5-7b/snapshots/SNAPSHOT_ID/

# Download specific model files
wget https://huggingface.co/liuhaotian/llava-v1.5-7b/resolve/main/config.json \
  -O ~/.cache/huggingface/hub/models--liuhaotian--llava-v1.5-7b/snapshots/SNAPSHOT_ID/config.json
wget https://huggingface.co/liuhaotian/llava-v1.5-7b/resolve/main/pytorch_model.bin \
  -O ~/.cache/huggingface/hub/models--liuhaotian--llava-v1.5-7b/snapshots/SNAPSHOT_ID/pytorch_model.bin

# Replace SNAPSHOT_ID with actual snapshot ID from the HuggingFace page
```

### Download LLaVA 1.5 (13B - 26GB - More Accurate)

Requires 30+ GB RAM or GPU.

**Method 1: Python (Automatic)**
```bash
python -c "
from transformers import AutoTokenizer, AutoModelForCausalLM
model_name = 'liuhaotian/llava-v1.5-13b'
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, device_map='auto')
print('✓ Model downloaded successfully')
"
```

**Method 2: Browser Download**
1. Visit: https://huggingface.co/liuhaotian/llava-v1.5-13b
2. Click "Files and versions" tab
3. Download model files

**Method 3: Git LFS (Command Line)**
```bash
git lfs install
git clone https://huggingface.co/liuhaotian/llava-v1.5-13b
mkdir -p ~/.cache/huggingface/hub/models--liuhaotian--llava-v1.5-13b/snapshots
cp -r llava-v1.5-13b/* ~/.cache/huggingface/hub/models--liuhaotian--llava-v1.5-13b/snapshots/
```

### Model Storage

Models will be cached in: `~/.cache/huggingface/hub/` by default

To specify a custom location, set the environment variable:
```bash
export HF_HOME=/path/to/models
```

### Verifying Model Installation

```bash
python -c "
from transformers import AutoTokenizer, AutoModelForCausalLM
model_name = 'liuhaotian/llava-v1.5-7b'
try:
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name)
    print('✓ Model loaded successfully')
except Exception as e:
    print(f'✗ Error loading model: {e}')
"
```

## Audio Detection Setup

Video Censor Personal supports audio-based detection for speech profanity and sound classification.

### Audio Detection Models

#### Whisper (Speech Profanity Detection)

Whisper transcribes speech to text, which is then matched against profanity keyword lists.

```bash
# Download Whisper base model (~140 MB)
python -c "
from transformers import pipeline
print('Downloading Whisper model...')
pipe = pipeline('automatic-speech-recognition', model='openai/whisper-base')
print('✓ Whisper model cached successfully')
"
```

Model sizes: `tiny` (40 MB), `base` (140 MB), `small` (500 MB), `medium` (1.5 GB), `large` (3 GB)

#### Audio Classification (Sound Effects)

Detects sound effects like gunshots, screams, and explosions. Audio is processed in configurable chunks (default: 2 seconds) with 50% overlap for accurate detection.

```bash
# Download audio classification model (~300 MB)
python -c "
from transformers import AutoModelForAudioClassification, AutoFeatureExtractor
print('Downloading audio classification model...')
processor = AutoFeatureExtractor.from_pretrained('MIT/ast-finetuned-audioset-10-10-0.4593')
model = AutoModelForAudioClassification.from_pretrained('MIT/ast-finetuned-audioset-10-10-0.4593')
print('✓ Audio classification model cached successfully')
"
```

Configuration options:
- `chunk_duration`: Audio chunk size in seconds (default: 2.0). Larger values provide more context for sustained sounds.
- `confidence_threshold`: Minimum confidence for detection (default: 0.6)

### Audio Remediation

Detected audio content can be censored using silence or bleep tones:

- **Silence mode**: Replaces detected segments with silence
- **Bleep mode**: Replaces detected segments with a beep tone

When remediation is enabled, use `--output-video` to specify the output file:

```bash
python video_censor_personal.py \
  --input video.mp4 \
  --config video-censor-audio-remediation-silence.yaml \
  --output results.json \
  --output-video censored_video.mp4
```

See [AUDIO.md](AUDIO.md) for detailed audio setup and configuration.

### Video Remediation

Detected visual content can be censored by either blanking or cutting segments:

- **Blank mode**: Replaces video with a solid color (black by default) while keeping audio
- **Cut mode**: Removes both video and audio segments from the timeline entirely

Video remediation supports:
- **Global default mode**: Apply blank or cut to all detections
- **Per-category modes**: Different remediation for different categories (e.g., cut nudity, blank violence)
- **Per-segment overrides**: Manual control via JSON editing after detection

When video remediation is enabled, use `--output-video` to specify the output file:

```bash
python video_censor_personal.py \
  --input video.mp4 \
  --config video-censor-video-remediation.yaml \
  --output results.json \
  --output-video censored_video.mp4
```

Example configuration:
```yaml
remediation:
  video:
    enabled: true
    mode: "blank"         # Global default
    blank_color: "#000000"  # Black
    category_modes:
      Nudity: "cut"       # Cut nudity entirely
      Violence: "blank"   # Blank violence (preserves timing)
```

See `video-censor-video-remediation.yaml.example` for a complete configuration template.

### Skip Chapter Markers

Add chapter markers to your output video to easily navigate between flagged segments in media players (VLC, Plex, Kodi, etc.):

**MKV output (uses mkvmerge):**
```bash
python video_censor_personal.py \
  --input video.mp4 \
  --config video-censor-skip-chapters.yaml \
  --output results.json \
  --output-video output.mkv
```

**MP4 output (uses native MP4 atoms via ffmpeg):**
```bash
python video_censor_personal.py \
  --input video.mp4 \
  --config video-censor-skip-chapters.yaml \
  --output results.json \
  --output-video output.mp4
```

Both MKV and MP4 formats are fully supported with native chapter atoms that work reliably in all standard media players (VLC, Plex, Windows Media Player, Kodi, etc.).

**Requirements:**
- ffmpeg >= 8.0 (for native MP4 chapter support)
- mkvtoolnix (for MKV format)

To enable skip chapters in your config file:
```yaml
output:
  video:
    metadata_output:
      skip_chapters:
        enabled: true
```

**Chapter naming format:** `skip: [Label] [Confidence%]`  
Example: `skip: Nudity, Sexual Theme [89%]`

See `video-censor-skip-chapters.yaml.example` for a complete skip chapters configuration.

## Configuration

Video Censor Personal uses YAML configuration files to control detection behavior.

### Configuration File Format

See `video-censor.yaml.example` for a complete configuration template.

Basic configuration structure:
```yaml
version: 1.0

detections:
  nudity:
    enabled: true
    sensitivity: 0.7      # 0.0 (permissive) to 1.0 (strict)
    model: "local"
  
  profanity:
    enabled: true
    sensitivity: 0.8
    model: "local"
    languages:
      - en
      - es
  
  violence:
    enabled: true
    sensitivity: 0.6
    model: "local"
  
  sexual_themes:
    enabled: true
    sensitivity: 0.75
    model: "local"

processing:
  frame_sampling:
    strategy: "uniform"    # uniform, scene_based, all
    sample_rate: 1.0       # seconds between frames
  
  segment_merge:
    enabled: true
    merge_threshold: 2.0   # merge segments within N seconds
  
  max_workers: 4           # parallel processing

output:
  format: "json"
  include_confidence: true
  pretty_print: true
```

### Default Configuration Location

Place your configuration file in one of these locations:
1. `./video-censor.yaml` (current directory)
2. `./config.yaml` (current directory)
3. Specify explicitly with `--config /path/to/config.yaml`

## Analysis Pipeline

The video analysis pipeline orchestrates the entire workflow:

1. **Video Extraction**: Extracts frames and audio at configured sample rates
2. **Detector Initialization**: Loads configured detectors (e.g., LLaVA, mock)
3. **Frame Analysis**: Processes sampled frames through detector pipeline
4. **Result Aggregation**: Combines detections from all frames
5. **Segment Merging**: Merges nearby detections into coherent segments
6. **Output Generation**: Produces JSON results with metadata

### Detector Configuration

Detectors are specified in the `detectors` section of the YAML configuration:

```yaml
detectors:
  - type: "llava"              # Detector type
    name: "llava-vision"       # Instance name
    categories:                # Categories to analyze
      - "Nudity"
      - "Violence"
```

If `detectors` section is missing, the pipeline auto-discovers detectors from enabled categories.

### Mock Detector for Testing

For integration testing without downloading models, use the mock detector:

```yaml
detectors:
  - type: "mock"
    name: "mock-detector"
    categories: ["Nudity", "Violence"]
```

The mock detector returns deterministic results based on frame content, allowing you to validate the complete pipeline without model dependencies.

## Basic Usage

### Analyze a Video

```bash
python video_censor_personal.py \
  --input /path/to/video.mp4 \
  --config /path/to/config.yaml \
  --output results.json
```

### Arguments

- `--input PATH` (required): Path to video file to analyze
- `--output PATH` (optional): Path to output JSON file (default: `results.json`)
- `--config PATH` (optional): Path to YAML configuration file
- `--output-video PATH` (optional): Path to output video with remediated audio and/or skip chapters
- `--input-segments PATH` (optional): Path to segments JSON file from previous analysis (skips detection, remediation only)
- `--allow-all-segments`: Mark all detected segments as allowed (useful for preview/review mode)
- `--download-models`: Automatically download required models before analysis
- `--log-level LEVEL`: Logging level: INFO, DEBUG, or TRACE (default: INFO)
- `--help`: Show help message

### Segment Allow Override

The `allow` property enables you to mark false positives or intentionally skip specific segments from remediation without re-analyzing the video:

1. **Analyze video** - Run detection to generate the JSON output
2. **Review segments** - Inspect the detected segments in the output file
3. **Mark allowed segments** - Set `"allow": true` on any segment you want to exclude from remediation
4. **Run remediation** - Only segments with `allow: false` (or missing) will be processed

Use `--allow-all-segments` during analysis to pre-mark all segments as allowed (preview mode):
```bash
python video_censor_personal.py \
  --input video.mp4 \
  --config config.yaml \
  --output results.json \
  --allow-all-segments
```

Then un-allow specific segments by editing the JSON and setting `"allow": false` before remediation.

### Three-Phase Workflow: Analyze → Review → Remediate

For iterative workflows where you want to analyze once and remediate multiple times with different settings, use the `--input-segments` option:

#### Phase 1: Analyze (One Time)

Run the full analysis pipeline and save segments to JSON:

```bash
python video_censor_personal.py \
  --input video.mp4 \
  --config video-censor.yaml \
  --output segments.json
```

#### Phase 2: Review & Edit

Open `segments.json` and mark false positives as allowed:

```json
{
  "segments": [
    {
      "start_time": "00:05:30",
      "start_time_seconds": 330.0,
      "end_time": "00:05:45",
      "end_time_seconds": 345.0,
      "labels": ["Violence"],
      "allow": true
    }
  ]
}
```

#### Phase 3: Remediate (Skip Analysis)

Apply remediation using the edited segments file—no ML re-analysis required:

```bash
python video_censor_personal.py \
  --input video.mp4 \
  --input-segments segments.json \
  --config video-censor.yaml \
  --output-video output.mp4
```

This loads segments directly from `segments.json` and applies audio remediation and/or skip chapters without running any detection. Segments marked `"allow": true` are skipped.

#### Re-Remediate with Different Settings

Change remediation settings (e.g., switch from silence to bleep) and re-run without re-analyzing:

```bash
python video_censor_personal.py \
  --input video.mp4 \
  --input-segments segments.json \
  --config video-censor-bleep.yaml \
  --output-video output-bleep.mp4
```

**Benefits:**
- Skip expensive ML analysis when only adjusting remediation settings
- Iterate on allow flags without re-processing the entire video
- Test different bleep frequencies, silence modes, or chapter configurations
- Preserve original analysis as the single source of truth

### Output Format

Analysis results are saved as JSON with detected segments:

```json
{
  "metadata": {
    "file": "video.mp4",
    "duration": "1:23:45",
    "processed_at": "2025-12-13T14:30:00Z",
    "config": "config.yaml"
  },
  "segments": [
    {
      "start_time": "00:48:25",
      "end_time": "00:48:26",
      "duration_seconds": 1,
      "labels": ["Profanity", "Sexual Theme"],
      "description": "A character uses explicit language in a sexual context",
      "confidence": 0.92,
      "allow": false,
      "detections": [
        {
          "label": "Profanity",
          "confidence": 0.95,
          "reasoning": "Detected strong profanity in audio"
        }
      ]
    }
  ],
  "summary": {
    "total_segments_detected": 2,
    "total_flagged_duration": 16,
    "detection_counts": {
      "Profanity": 1,
      "Violence": 1
    }
  }
}
```

## Video Extraction

Video extraction is the foundational step that prepares video content for analysis. The system extracts video frames and audio at configurable intervals to feed into the LLM for content detection.

### Frame Extraction

The system extracts video frames using ffmpeg with configurable sampling rates:

- **Uniform Sampling** (default): Extracts frames at regular time intervals (e.g., every 1 second)
- **Custom Sample Rates**: Configure `processing.frame_sampling.sample_rate` in YAML (in seconds)
- **All Frames**: Set `strategy: "all"` to extract every frame (resource-intensive)

Each extracted frame includes:
- **Index**: Frame number in sequence
- **Timecode**: Precise timestamp in seconds
- **Pixel Data**: As numpy array in BGR format (OpenCV standard)

### Audio Extraction

Audio is extracted from the video file for profanity and speech-based detection:

- Extracted using ffmpeg subprocess
- Converted to 16kHz mono PCM format
- Cached after first extraction to avoid re-processing
- Supports standard video codecs (AAC, MP3, etc.)

### Supported Video Formats

The system supports video formats handled by ffmpeg, including:
- **Common formats**: MP4, MKV, AVI, MOV, WebM, FLV
- **Video codecs**: H.264, H.265, VP8, VP9, and others supported by ffmpeg
- **Audio codecs**: AAC, MP3, FLAC, Opus, and others supported by ffmpeg

For a complete list of supported formats, run:
```bash
ffmpeg -formats
```

### Configuration Example

```yaml
processing:
  frame_sampling:
    strategy: "uniform"    # uniform, scene_based, all
    sample_rate: 1.0       # extract one frame per second
  max_workers: 4           # parallel processing workers
```

## Project Structure

```
video-censor-personal/
├── video_censor_personal/          # Main Python package
│   ├── ui/                         # Desktop UI module (CustomTkinter)
│   │   ├── __init__.py
│   │   └── main.py
│   ├── __init__.py                 # Package initialization and metadata
│   ├── cli.py                      # Command-line interface
│   ├── config.py                   # Configuration file parsing
│   ├── frame.py                    # Frame and AudioSegment data classes
│   └── video_extraction.py         # Video extraction engine (frames and audio)
│
├── video_censor_personal.py        # Main entry point script
├── requirements.txt                # Python dependencies
├── README.md                       # This file
├── QUICK_START.md                  # Quick start guide
├── LAUNCH_UI.md                    # Desktop UI launching guide
├── launch-ui.sh                    # Launch script (macOS/Linux)
├── launch-ui.command               # Launch script (macOS Finder)
├── launch-ui.bat                   # Launch script (Windows)
├── launch-ui.vbs                   # Launch script (Windows silent)
├── launch-ui.desktop               # Launch script (Linux file manager)
└── video-censor.yaml.example       # Example configuration
```

## Troubleshooting

### Common Issues

**Python Tkinter Module Not Found**
```
ModuleNotFoundError: No module named '_tkinter'
```

This happens when Python is installed without Tkinter support. Solutions:

**If you used pyenv (Most Common):**
You must install `tcl-tk` BEFORE installing Python:
```bash
# 1. Install tcl-tk dependency
brew install tcl-tk

# 2. Uninstall broken Python
pyenv uninstall 3.13.0

# 3. Reinstall with Tkinter support
PYTHON_CONFIGURE_OPTS="--with-tcltk" pyenv install 3.13.0
pyenv local 3.13.0

# 4. Verify
python3 -c "import tkinter; print('Tkinter works!')"
```

**If you used Homebrew:**
```bash
brew install python-tk@3.13
```

**If you used Windows installer:**
- Uninstall Python 3.13
- Reinstall from https://www.python.org/downloads/
- **CHECK** "tcl/tk and IDLE" during installation

See `LAUNCH_UI.md` for detailed troubleshooting.

**Python Version Error**
```
Error: Python 3.13 or later is required
```
Solution: Install Python 3.13+ (see System Requirements above)

**ffmpeg Not Found**
```
Error: ffmpeg command not found
```
Solution: Install ffmpeg (see External Tools section)

**Model Download Fails**
```
Error: Failed to download model from Hugging Face
```
- Check internet connection
- Increase timeout: `HF_HUB_READ_TIMEOUT=100 python script.py`
- Try manual download from https://huggingface.co/

**Out of Memory (OOM) Error**
```
RuntimeError: CUDA out of memory or system out of memory
```
Solutions:
- Reduce batch size in configuration
- Use smaller model (7B instead of 13B)
- Reduce `max_workers` in configuration
- Process videos in segments

**Permission Denied**
```
PermissionError: [Errno 13] Permission denied
```
- Ensure read access to video files: `chmod +r video.mp4`
- Ensure write access to output directory: `chmod +w /output/dir`

## GPU Acceleration

Video Censor Personal automatically detects and uses available GPU acceleration for model inference:

### Automatic Device Detection

The system detects GPU availability in this order:
1. **CUDA** (NVIDIA GPUs) - Fastest for most workloads
2. **MPS** (Apple Silicon) - Native Metal acceleration on Mac
3. **CPU** - Fallback when no GPU is available

Device selection is logged at INFO level when detectors initialize:
```
INFO - Using device: cuda
INFO - Initialized LLaVA detector 'llava-primary' with model 'liuhaotian/llava-v1.5-7b' on device 'cuda'
```

### Manual Device Override

Override automatic detection per-detector in your YAML config:

```yaml
detectors:
  - type: "llava"
    name: "llava-primary"
    device: "cuda"    # Force CUDA (errors if unavailable)
    # device: "mps"   # Force Apple MPS
    # device: "cpu"   # Force CPU (slow but always works)
    categories:
      - "Nudity"
      - "Violence"
```

### GPU Requirements

**NVIDIA CUDA**:
- NVIDIA GPU with CUDA support
- CUDA toolkit installed
- PyTorch with CUDA: `pip install torch --index-url https://download.pytorch.org/whl/cu118`

**Apple MPS**:
- Apple Silicon Mac (M1/M2/M3)
- macOS 12.3 or later
- PyTorch 2.0+: `pip install --upgrade torch`

### Performance Tips

```bash
# Check GPU availability
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"

# For NVIDIA multi-GPU systems, select specific GPU
export CUDA_VISIBLE_DEVICES=0

# Use mixed precision for faster inference (optional)
export TORCH_DTYPE=float16
```

See [PyTorch documentation](https://pytorch.org/docs/stable/notes/cuda.html) for more environment variables.

## Development

### Running Tests

```bash
pip install pytest pytest-cov
pytest
pytest --cov=video_censor_personal  # with coverage
```

### Code Style

This project follows PEP 8 with a 100-character line limit.

```bash
pip install black flake8
black video_censor_personal/
flake8 video_censor_personal/
```

## Contributing

Contributions are welcome! Please:
1. Create a feature branch: `git checkout -b feature/description`
2. Make changes and test thoroughly
3. Submit a pull request with clear description

## License

This project is provided as-is for personal use.

## Support

For issues and questions:
- Check QUICK_START.md for common setup issues
- Review configuration examples
- Enable `--verbose` flag for debug output
