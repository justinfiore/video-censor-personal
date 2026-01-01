# System Architecture

This document describes the internal design, architecture, and implementation details of Video Censor Personal.

## Project Structure

```
video-censor-personal/
├── video_censor_personal/          # Main Python package
│   ├── ui/                         # Desktop UI module (CustomTkinter)
│   │   ├── __init__.py
│   │   ├── preview_editor.py       # Main UI application
│   │   └── ...                     # UI component modules
│   ├── __init__.py                 # Package initialization and metadata
│   ├── cli.py                      # Command-line interface and argument parsing
│   ├── config.py                   # Configuration file parsing and validation
│   ├── frame.py                    # Frame and AudioSegment data classes
│   ├── video_extraction.py         # Video frame and audio extraction
│   ├── detection.py                # Content detection engines
│   ├── remediation.py              # Video/audio remediation implementations
│   └── ...                         # Additional modules
│
├── video_censor_personal.py        # Main entry point script
├── requirements.txt                # Python dependencies
├── README.md                       # User-focused readme
├── SYSTEM_ARCHITECTURE.md          # This file
├── QUICK_START.md                  # Quick start guide
├── CONFIGURATION_GUIDE.md          # Configuration reference
├── LAUNCH_UI.md                    # Desktop UI guide
├── launch-ui.sh                    # Launch script (macOS/Linux)
├── launch-ui.command               # Launch script (macOS Finder)
├── launch-ui.bat                   # Launch script (Windows)
├── launch-ui.vbs                   # Launch script (Windows silent)
├── launch-ui.desktop               # Launch script (Linux file manager)
└── tests/                          # Test suite
```

## Architecture Overview

The system follows a multi-stage pipeline architecture:

```
Input Video
    ↓
[Frame & Audio Extraction]
    ↓
[Content Detection] (LLM-based)
    ↓
[Detection Review] (Optional UI editor)
    ↓
[Remediation]
    ↓
Output Video + Metadata
```

### 1. Video Extraction

**Module**: `video_extraction.py`

Extracts video frames and audio at configurable intervals:

- **Frame Extraction**: Uses ffmpeg to extract frames at specified sampling rates
  - Supports uniform sampling (default): extracts frames at regular intervals
  - Supports custom sample rates: configurable in YAML
  - Supports scene-based sampling: extracts frames at scene changes
  - All frames: extract every frame (resource-intensive)

- **Audio Extraction**: Extracts audio track for speech-based detection
  - Converts to 16kHz mono PCM format using ffmpeg
  - Cached after first extraction
  - Supports all ffmpeg audio codecs

- **Supported Formats**: Any format supported by ffmpeg
  - Video codecs: H.264, H.265, VP8, VP9, etc.
  - Audio codecs: AAC, MP3, FLAC, Opus, etc.
  - Container formats: MP4, MKV, AVI, MOV, WebM, FLV, etc.

**Data Structures**:
- `Frame`: Extracted frame with timestamp, index, and pixel data
- `AudioSegment`: Extracted audio segment with timestamp and PCM data

### 2. Content Detection

**Module**: `detection.py`

Uses LLM-based detectors to analyze extracted frames and audio:

**Detector Types**:
- **LLaVA** (default): Vision-language model for visual content
  - Detects nudity, violence, sexual themes, custom concepts
  - Provides confidence scores and reasoning

- **Speech-based**: Audio analysis for profanity/explicit language
  - Analyzes extracted audio tracks
  - Identifies explicit speech patterns

**Detection Flow**:
1. For each extracted frame, send to LLM with detection categories
2. LLM analyzes and returns detected segments with confidence
3. Aggregate results and apply confidence thresholds
4. Output JSON with detected segments

**GPU Acceleration**:
- Automatic detection: CUDA (NVIDIA) → MPS (Apple) → CPU
- Manual override: Set `device` in detector config
- Configuration example:
  ```yaml
  detectors:
    - type: "llava"
      device: "cuda"  # Force CUDA
  ```

**Device Selection**:
```python
# Automatic priority
if torch.cuda.is_available():
    device = "cuda"
elif torch.backends.mps.is_available():
    device = "mps"
else:
    device = "cpu"
```

### 3. Detection Review (Optional)

**Module**: `video_censor_personal/ui/preview_editor.py`

Desktop GUI for reviewing and adjusting detection results:

**Architecture**:
- **CustomTkinter** framework for cross-platform UI
- **Three-pane layout**:
  - Left pane: Segment list (scrollable)
  - Top-right: Video player with timeline
  - Bottom-right: Segment details and metadata

**Key Features**:
- Built-in video player with playback controls
- Click segments to jump to timestamp
- Toggle allow/not-allow status with JSON persistence
- Real-time filtering by label or status
- Keyboard shortcuts for efficient review

**Internals**:
- Loads results from JSON file
- Maintains in-memory segment state
- Automatically saves JSON on modifications
- Handles video playback using FFmpeg subprocess

### 4. Remediation

**Module**: `remediation.py`

Applies transformations to video/audio based on detection results:

**Video Remediation Modes**:
- **blank**: Replace flagged segments with solid color (preserves timing)
- **cut**: Remove flagged segments entirely (changes timing)
- **none**: Skip video processing (detection only)

**Audio Remediation Modes**:
- **bleep**: Replace flagged audio with synthetic beep sound
- **silence**: Replace flagged audio with silence
- **none**: Skip audio processing (detection only)

**Implementation**:
- Uses FFmpeg for frame-based video processing
- PyAV for frame-accurate manipulation
- Temporal alignment between video and detection results
- Efficient streaming to avoid loading entire video in memory

**Multi-Track Audio**:
- Handles videos with multiple audio tracks
- Optionally remediates specific tracks only
- Preserves audio codec and bitrate

### 5. Configuration System

**Module**: `config.py`

YAML-based configuration system with validation:

**Configuration Sections**:

```yaml
detectors:          # Detection engines to use
  - type: ...      # llava, speech, custom
    name: ...      # Detector identifier
    device: ...    # Optional: cuda, mps, cpu
    categories: [] # Content categories to detect

processing:        # Input processing
  frame_sampling:
    strategy: ...  # uniform, scene_based, all
    sample_rate: 1.0
  max_workers: 4

remediation:       # Output remediation
  video:
    mode: ...      # blank, cut, none
  audio:
    mode: ...      # bleep, silence, none
```

**Validation**:
- Schema validation on load
- Default values for missing fields
- Error reporting with context

### 6. CLI Interface

**Module**: `cli.py`

Command-line argument parsing and workflow orchestration:

**Main Workflows**:

```bash
# Analysis only
python video_censor_personal.py --input video.mp4 --config config.yaml --output results.json

# Remediation only (requires existing JSON)
python video_censor_personal.py --input video.mp4 --input-json results.json --output-video output.mp4

# Analysis + Remediation
python video_censor_personal.py --input video.mp4 --config config.yaml --output results.json --output-video output.mp4

# With Preview Editor
python video_censor_personal.py --input video.mp4 --config config.yaml --output results.json --edit
```

**Argument Handling**:
- `--input`: Input video file path
- `--config`: YAML configuration file
- `--output`: Output JSON results file
- `--output-video`: Output remediated video file
- `--input-json`: Existing results JSON (for remediation)
- `--edit`: Auto-launch preview editor after analysis
- `--verbose`: Enable debug logging

### 7. Desktop UI Architecture

**Framework**: CustomTkinter (modern Tkinter with dark theme)

**Component Structure**:

```
PreviewEditorApp
├── MainWindow (root)
│   ├── SegmentListFrame
│   │   ├── SearchBar
│   │   └── SegmentListBox
│   ├── PlayerFrame
│   │   ├── VideoPlayer
│   │   ├── Timeline
│   │   └── PlayerControls
│   └── DetailsFrame
│       ├── SegmentInfo
│       └── MetadataPanel
```

**State Management**:
- Segments stored in-memory with JSON persistence
- Signals/events for cross-pane communication
- Background threads for video loading and playback

**Video Playback**:
- FFmpeg subprocess for frame extraction
- Custom timeline visualization
- Frame-accurate seeking
- Speed and volume controls

**File Operations**:
- Auto-save JSON on segment modifications
- Support for loading/saving results
- Backup creation on write

## Data Flow

### Detection Pipeline

```
Video File
    ↓ (ffmpeg)
Frame Extraction
    ↓
[Frame] → [LLM Analysis] → [Detections]
    ↓
[Frame] → [LLM Analysis] → [Detections]
    ...
    ↓
Aggregate Results
    ↓
JSON Output {
    segments: [
        {timestamp, label, confidence, ...}
    ],
    metadata: {...}
}
```

### Remediation Pipeline

```
JSON Results + Video File
    ↓
Build Segment Map
    ↓
[Frame] → Check Against Map → [Modified Frame]
[Audio] → Check Against Map → [Modified Audio]
    ↓
Encode/Mux Output
    ↓
Output Video File
```

## Performance Considerations

### Parallelization

- **Frame extraction**: Sequential (limited by I/O)
- **Frame analysis**: Parallel using configured `max_workers`
- **Video encoding**: Single-threaded (FFmpeg limitation)

### Memory Management

- Frames loaded on-demand (not entire video)
- Batch processing for LLM inference
- Streaming output encoding
- Configurable batch sizes in config

### GPU Acceleration

- Automatic CUDA/MPS detection
- Models loaded once per detector instance
- Batch inference where applicable
- Mixed precision support (optional)

### Caching

- Audio extraction cached after first run
- Model weights cached by PyTorch/Hugging Face
- Frame cache cleared after processing

## Testing

**Test Structure**:
```
tests/
├── test_video_extraction.py    # Video processing tests
├── test_detection.py           # Detection engine tests
├── test_remediation.py         # Remediation tests
├── test_config.py              # Configuration parsing
├── test_ui.py                  # UI component tests
└── test_integration.py         # End-to-end workflow tests
```

**Running Tests**:
```bash
pytest                          # Run all tests
pytest --cov                    # With coverage
pytest -v                       # Verbose
```

## Extension Points

### Adding Custom Detectors

Implement the `Detector` interface:

```python
class CustomDetector(Detector):
    def __init__(self, config):
        self.config = config
    
    def detect(self, frame: Frame) -> List[Detection]:
        # Analyze frame and return detections
        pass
```

Register in config:

```yaml
detectors:
  - type: "custom"
    name: "my-detector"
    categories: [...]
```

### Adding Custom Remediation

Implement remediation logic in `remediation.py`:

```python
def apply_custom_remediation(video_path, results, output_path):
    # Custom remediation logic
    pass
```

### Adding Detector Categories

Define new categories in detection module and reference in config:

```yaml
detectors:
  - type: "llava"
    categories:
      - "Custom Category Name"
```

## Dependencies

**Core Libraries**:
- `torch`: Deep learning framework
- `torchvision`: Computer vision utilities
- `transformers`: Hugging Face model library
- `PIL`: Image processing
- `numpy`: Numerical computing
- `pyyaml`: YAML parsing
- `customtkinter`: Modern UI framework

**Media Processing**:
- `ffmpeg-python`: FFmpeg wrapper
- `opencv-python`: Video/image processing
- `av`: FFmpeg bindings for Python

**Development**:
- `pytest`: Testing framework
- `black`: Code formatting
- `flake8`: Linting
- `pytest-cov`: Coverage reporting

See `requirements.txt` for full list with versions.

## Logging

**Logger Configuration**:
```python
import logging
logger = logging.getLogger(__name__)
```

**Log Levels**:
- `DEBUG`: Detailed trace information (frame-by-frame)
- `INFO`: General informational messages
- `WARNING`: Warning conditions
- `ERROR`: Error conditions
- `CRITICAL`: Critical failures

**Enable Verbose Output**:
```bash
python video_censor_personal.py --verbose
```

## Future Improvements

- [ ] Multi-GPU support for batch analysis
- [ ] Distributed processing for large video libraries
- [ ] ML model fine-tuning on custom datasets
- [ ] Additional detector types (audio ML models, etc.)
- [ ] Real-time video processing (streaming input)
- [ ] Web UI alternative to desktop UI
- [ ] Plugin system for custom detectors/remediators

## References

- PyTorch Documentation: https://pytorch.org/docs/
- Hugging Face Transformers: https://huggingface.co/docs/transformers/
- FFmpeg Documentation: https://ffmpeg.org/documentation.html
- CustomTkinter: https://github.com/TomSchimansky/CustomTkinter
