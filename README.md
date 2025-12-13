# Video Censor Personal

A personalized video censoring system that analyzes video content and identifies segments containing inappropriate or undesired material. The system enables users to make informed decisions about which sections to skip or censor based on their preferences.

## Features

The system detects:
- **Nudity** - Nude or partially nude content
- **Profanity** - Explicit language and swearing
- **Violence** - Physical violence and aggressive scenes
- **Sexual Themes** - Sexual content and suggestive material
- **Custom Concepts** - User-defined content categories

## System Requirements

### Prerequisites

- **Python**: 3.13 or later
- **Operating System**: macOS, Linux, or Windows
- **Disk Space**: 
  - ~2-5 GB for Python environment and dependencies
  - ~10-20 GB for AI models (varies by model size)
  - Additional space for video files and analysis output

### External Tools

- **ffmpeg**: Required for video frame extraction and metadata processing
  - Download: https://ffmpeg.org/download.html
  - Used to extract frames from videos for analysis

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

## Downloading and Setting Up Models

Video Censor Personal uses local AI models for analysis. Download and configure them before your first analysis.

### Supported Models

#### LLaVA (Recommended)

LLaVA is a vision-language model that can analyze images and perform content classification.

**Download LLaVA 1.5 (7B - 4GB)**:
```bash
# Create models directory
mkdir -p models

# Download the model (this will take a few minutes depending on internet speed)
# Using Hugging Face transformers library (after pip install transformers)
python -c "
from transformers import AutoTokenizer, AutoModelForCausalLM
model_name = 'liuhaotian/llava-v1.5-7b'
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, device_map='auto')
"
```

**Download LLaVA 1.5 (13B - 26GB - More Accurate)**:
```bash
python -c "
from transformers import AutoTokenizer, AutoModelForCausalLM
model_name = 'liuhaotian/llava-v1.5-13b'
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, device_map='auto')
"
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
- `--verbose`: Enable debug-level logging for troubleshooting
- `--help`: Show help message

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
└── video-censor.yaml.example       # Example configuration
```

## Troubleshooting

### Common Issues

**Python Version Error**
```
Error: Python 3.13 or later is required
```
Solution: Install Python 3.13+ from python.org

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
