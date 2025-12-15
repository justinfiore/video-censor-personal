# Quick Start Guide

Get Video Censor Personal up and running in 15 minutes.

## Prerequisites

- Python 3.13 or later installed (check: `python --version`)
- pip installed (check: `pip --version`)
- ~15-20 GB free disk space for models and environment

## Step 1: Setup Python Environment (2 minutes)

### Create Virtual Environment

```bash
# Navigate to project directory
cd video-censor-personal

# Create virtual environment
python3.13 -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate

# On Windows (PowerShell):
venv\Scripts\Activate.ps1

# On Windows (Command Prompt):
venv\Scripts\activate.bat
```

You should see `(venv)` appear in your terminal prompt.

### Verify Python Installation

```bash
python --version        # Should show 3.13.x
pip --version           # Should show associated version
which python            # Should show path to venv/bin/python
```

## Step 2: Install Python Dependencies (3 minutes)

```bash
# Upgrade pip first (recommended)
pip install --upgrade pip setuptools wheel

# Install project dependencies
pip install -r requirements.txt
```

Expected output should show successful installation of:
- PyYAML
- numpy
- click
- opencv-python

## Step 3: Install ffmpeg (3-5 minutes)

ffmpeg is required to extract frames from videos.

### macOS

Using Homebrew:
```bash
brew install ffmpeg
```

Or download from https://ffmpeg.org/download.html

### Linux (Ubuntu/Debian)

```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

### Linux (Fedora/RHEL)

```bash
sudo dnf install ffmpeg
```

### Windows

1. Go to https://ffmpeg.org/download.html
2. Download the Windows build
3. Extract to `C:\ffmpeg` (or similar location)
4. Add to PATH:
   - Right-click "This PC" → Properties
   - Click "Advanced system settings"
   - Click "Environment Variables"
   - Add `C:\ffmpeg\bin` to PATH
5. Restart terminal and verify:
   ```bash
   ffmpeg -version
   ```

### Verify Installation

```bash
ffmpeg -version
# Output should show FFmpeg version and built-in components
```

## Step 4: Download AI Models (5-10 minutes)

Models are used for content analysis. Download them before your first run.

### Install Transformers Library

```bash
pip install transformers torch torchvision torchaudio
```

### Download CLIP Model (Optional, Lightweight Alternative)

If you want a faster, more memory-efficient detector, use CLIP instead of LLaVA.

#### Method 1: Automatic Download with --download-models Flag

```bash
# First, create a config file that uses CLIP (see example-clip-detector.yaml.example)
# Then run with auto-download:
python -m video_censor --download-models --config video-censor-clip-detector.yaml --input dummy.mp4
```

#### Method 2: Manual Python Download

```bash
python -c "
from transformers import CLIPModel, CLIPProcessor
print('Downloading CLIP ViT-Base model... this may take 2-3 minutes (~600 MB)')
model_name = 'openai/clip-vit-base-patch32'
processor = CLIPProcessor.from_pretrained(model_name)
model = CLIPModel.from_pretrained(model_name)
print('✓ CLIP model downloaded and cached successfully')
print('Model location: ~/.cache/huggingface/hub/')
"
```

**CLIP Model Sizes:**
- **ViT-Base** (`openai/clip-vit-base-patch32`): ~600 MB, faster, good for real-time use
- **ViT-Large** (`openai/clip-vit-large-patch14`): ~900 MB, more accurate, slower

**Advantages over LLaVA:**
- Much faster inference (CLIP is 5-10x faster)
- Lower memory usage (~2 GB vs 7+ GB for LLaVA)
- No model generation phase; direct classification
- Customizable prompts per category

**When to use CLIP:**
- Resource-constrained environments (edge devices, low-RAM servers)
- Need fast real-time processing
- Have simple, well-defined categories with clear text descriptions

**When to use LLaVA:**
- Need detailed reasoning/explanation of detections
- Want automatic discovery of content types
- Have more complex or ambiguous content to detect

### Download LLaVA Model (Recommended for Detailed Analysis)

Choose one of the following methods to download the 7B model (~4 GB download, ~7 GB unpacked):

#### Method 1: Python (Automatic, Recommended)

```bash
python -c "
from transformers import AutoTokenizer, AutoModelForCausalLM
print('Downloading model... this may take 3-5 minutes')
model_name = 'liuhaotian/llava-v1.5-7b'
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, device_map='auto')
print('✓ Model downloaded and cached successfully')
print('Model location: ~/.cache/huggingface/hub/')
"
```

#### Method 2: Browser Download from HuggingFace

1. Visit: https://huggingface.co/liuhaotian/llava-v1.5-7b
2. Click the "Files and versions" tab
3. Download the model files to `~/.cache/huggingface/hub/models--liuhaotian--llava-v1.5-7b/snapshots/`

#### Method 3: Using Git LFS (Command Line)

```bash
# Install Git LFS if not already installed
# macOS: brew install git-lfs
# Ubuntu: sudo apt-get install git-lfs
# Or visit: https://git-lfs.com

git lfs install
git clone https://huggingface.co/liuhaotian/llava-v1.5-7b
mkdir -p ~/.cache/huggingface/hub/models--liuhaotian--llava-v1.5-7b/snapshots
cp -r llava-v1.5-7b/* ~/.cache/huggingface/hub/models--liuhaotian--llava-v1.5-7b/snapshots/
```

### Download 13B Model (More Accurate but Slower)

~26 GB total, requires 30+ GB RAM or GPU.

#### Method 1: Python (Automatic)

```bash
python -c "
from transformers import AutoTokenizer, AutoModelForCausalLM
print('Downloading 13B model... this may take 10-15 minutes')
model_name = 'liuhaotian/llava-v1.5-13b'
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, device_map='auto')
print('✓ Model downloaded and cached successfully')
"
```

#### Method 2: Browser Download from HuggingFace

1. Visit: https://huggingface.co/liuhaotian/llava-v1.5-13b
2. Click the "Files and versions" tab
3. Download the model files

#### Method 3: Using wget/curl

```bash
# Create directory structure
mkdir -p ~/.cache/huggingface/hub/models--liuhaotian--llava-v1.5-7b/snapshots/SNAPSHOT_ID/

# Download individual files (replace SNAPSHOT_ID with actual snapshot)
wget -P ~/.cache/huggingface/hub/models--liuhaotian--llava-v1.5-7b/snapshots/SNAPSHOT_ID/ \
  https://huggingface.co/liuhaotian/llava-v1.5-7b/resolve/main/config.json \
  https://huggingface.co/liuhaotian/llava-v1.5-7b/resolve/main/pytorch_model.bin

# Note: For specific snapshot IDs, check the HuggingFace page
```

### Verify Model Installation

```bash
python -c "
from transformers import AutoTokenizer, AutoModelForCausalLM
model_name = 'liuhaotian/llava-v1.5-7b'
try:
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name)
    print('✓ LLaVA 7B model loaded successfully')
except Exception as e:
    print(f'✗ Error: {e}')
    print('Check internet connection and disk space')
"
```

### Model Location

Models are cached at: `~/.cache/huggingface/hub/`

Custom location:
```bash
export HF_HOME=/your/custom/path
```

Disk usage:
- LLaVA 7B: ~7 GB
- LLaVA 13B: ~26 GB

## Step 5: Download Audio Models (Optional)

If you plan to use audio detection (speech profanity or sound effects), download these models:

### Whisper Model (Speech Detection)

```bash
python -c "
from transformers import pipeline
print('Downloading Whisper base model (~140 MB)...')
pipe = pipeline('automatic-speech-recognition', model='openai/whisper-base')
print('✓ Whisper model cached successfully')
"
```

### Audio Classification Model (Sound Effects)

```bash
python -c "
from transformers import AutoModelForAudioClassification, AutoFeatureExtractor
print('Downloading audio classification model (~300 MB)...')
processor = AutoFeatureExtractor.from_pretrained('MIT/ast-finetuned-audioset-10-10-0.4593')
model = AutoModelForAudioClassification.from_pretrained('MIT/ast-finetuned-audioset-10-10-0.4593')
print('✓ Audio model cached successfully')
"
```

**Note**: Audio models download automatically on first use if not pre-cached. Pre-downloading is optional but speeds up your first analysis.

Total audio model storage: ~500 MB

## Step 6: Create Configuration File (1 minute)

Create a `video-censor.yaml` file in the project directory:

```yaml
version: 1.0

detections:
  nudity:
    enabled: true
    sensitivity: 0.7
    model: "local"
  
  profanity:
    enabled: true
    sensitivity: 0.8
    model: "local"
    languages:
      - en
  
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
    strategy: "uniform"
    sample_rate: 1.0          # Analyze every second
  
  segment_merge:
    enabled: true
    merge_threshold: 2.0
  
  max_workers: 4

output:
  format: "json"
  include_confidence: true
  pretty_print: true
```

Save this as `video-censor.yaml` in the project root directory.

## Step 7: Test Without Downloading Models (Optional - 1 minute)

If you want to quickly test the pipeline without downloading large models:

### Create Mock Configuration

```yaml
# test-mock.yaml
detections:
  nudity:
    enabled: true
    sensitivity: 0.7
    model: "local"
  violence:
    enabled: true
    sensitivity: 0.6
    model: "local"

processing:
  frame_sampling:
    strategy: "uniform"
    sample_rate: 1.0
  segment_merge:
    merge_threshold: 2.0
  max_workers: 4

output:
  format: "json"
  include_confidence: true
  pretty_print: true

detectors:
  - type: "mock"
    name: "mock-detector"
    categories: ["Nudity", "Violence"]
```

### Run with Mock Detector

```bash
python video_censor_personal.py \
  --input /path/to/video.mp4 \
  --config test-mock.yaml \
  --output results.json
```

The mock detector returns deterministic results without requiring any model downloads, allowing you to test the complete pipeline immediately.

## Step 8: Run Your First Analysis with LLaVA (5+ minutes)

### Prepare a Test Video

Use your own video or download a sample video for testing:

```bash
# Example: Download a short video (~10 seconds) for testing
# You can use any MP4 video you have
```

### Run Analysis

```bash
python video_censor_personal.py \
  --input /path/to/video.mp4 \
  --config video-censor.yaml \
  --output results.json
```

### With Verbose Output (Recommended for First Run)

```bash
python video_censor_personal.py \
  --input /path/to/video.mp4 \
  --config video-censor.yaml \
  --output results.json \
  --verbose
```

### View Results

```bash
# Pretty print the results
python -m json.tool results.json | less

# Or open in your editor
# results.json will contain detected segments with timestamps and confidence scores
```

## Common Commands

```bash
# Get help
python video_censor_personal.py --help

# Analyze with custom config
python video_censor_personal.py \
  --input video.mp4 \
  --config my-config.yaml \
  --output output.json

# Verbose mode for troubleshooting
python video_censor_personal.py \
  --input video.mp4 \
  --config video-censor.yaml \
  --verbose

# Show version
python video_censor_personal.py --version
```

## Troubleshooting

### Issue: "Python 3.13 or later is required"

**Solution**: Install Python 3.13+
```bash
# Check your version
python --version

# Install from python.org or:
# macOS: brew install python@3.13
# Ubuntu: sudo apt-get install python3.13
```

### Issue: "ffmpeg command not found"

**Solution**: Install ffmpeg (see Step 3 above)

### Issue: Virtual Environment Not Activating

**Windows users**: If you get execution policy error:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then try activating again:
```powershell
venv\Scripts\Activate.ps1
```

### Issue: Model Download Fails / Timeout

**Solutions**:
1. Check internet connection
2. Increase timeout:
   ```bash
   HF_HUB_READ_TIMEOUT=100 python -c "from transformers import ..."
   ```
3. Try again - sometimes HuggingFace servers are slow

### Issue: "Out of Memory" or "CUDA out of memory"

**Solutions**:
1. Use smaller model (7B instead of 13B)
2. Reduce `max_workers` in config from 4 to 2 or 1
3. Process videos in smaller chunks
4. Close other applications to free RAM
5. Force CPU mode by setting `device: cpu` in detector config (slower but uses less memory)

## GPU Acceleration

Video Censor Personal automatically detects and uses available GPU acceleration:

- **NVIDIA CUDA**: Automatically detected on systems with NVIDIA GPUs
- **Apple MPS (Metal)**: Automatically detected on Apple Silicon Macs
- **CPU Fallback**: Used when no GPU is available

### Checking GPU Availability

```bash
python -c "
import torch
print(f'CUDA available: {torch.cuda.is_available()}')
if hasattr(torch.backends, 'mps'):
    print(f'MPS available: {torch.backends.mps.is_available()}')
"
```

### Manual Device Override

You can force a specific device in your detector config:

```yaml
detectors:
  - type: "llava"
    name: "llava-primary"
    device: "cuda"    # Force CUDA (will error if unavailable)
    # device: "mps"   # Force Apple MPS
    # device: "cpu"   # Force CPU (slow but always available)
    categories:
      - "Nudity"
      - "Violence"
```

### GPU Troubleshooting

**CUDA not detected?**
1. Verify NVIDIA drivers: `nvidia-smi`
2. Reinstall PyTorch with CUDA: `pip install torch --index-url https://download.pytorch.org/whl/cu118`

**MPS not working on Mac?**
1. Requires macOS 12.3+ and Apple Silicon
2. Ensure PyTorch 2.0+ is installed: `pip install --upgrade torch`

### Issue: Permission Denied on Video File

**Solution**:
```bash
# Make video readable
chmod +r /path/to/video.mp4

# Make output directory writable
chmod +w /path/to/output/dir
```

### Issue: "Configuration file not found"

**Solution**: Make sure `video-censor.yaml` is in the same directory as `video_censor_personal.py`, or specify full path:

```bash
python video_censor_personal.py \
  --input video.mp4 \
  --config /full/path/to/config.yaml
```

## Using Video Extraction

The video extraction system automatically processes your videos, extracting frames and audio for analysis.

### Frame Extraction Examples

Extract frames at different sampling rates by modifying your config:

```yaml
processing:
  frame_sampling:
    strategy: "uniform"      # Extract frames uniformly across video
    sample_rate: 1.0         # Every 1 second (default)
    # sample_rate: 0.5       # Every 0.5 seconds (more detailed)
    # sample_rate: 2.0       # Every 2 seconds (faster processing)
    # strategy: "all"        # Extract every frame (resource-intensive)
```

### Using VideoExtractor Directly

For advanced usage, you can use the VideoExtractor API:

```python
from video_censor_personal.video_extraction import VideoExtractor

# Extract frames from a video
with VideoExtractor("path/to/video.mp4") as extractor:
    print(f"Duration: {extractor.get_duration_seconds()} seconds")
    print(f"FPS: {extractor.get_fps()}")
    
    # Extract frames at 1-second intervals
    for frame in extractor.extract_frames(sample_rate=1.0):
        print(f"Frame {frame.index} at {frame.timestamp_str()}")
        # Process frame.data (numpy array in BGR format)
        
    # Extract audio
    audio = extractor.extract_audio()
    print(f"Audio duration: {audio.duration()} seconds")
    
    # Extract specific audio segment
    segment = extractor.extract_audio_segment(start_sec=10.0, end_sec=15.0)
```

## Next Steps

1. **Customize Detection Settings**: Adjust sensitivity levels in `video-censor.yaml`
2. **Add Custom Detections**: Create custom detection categories
3. **Batch Processing**: Create a script to analyze multiple videos
4. **Integrate Results**: Use the JSON output in your own applications

## Getting Help

1. **Check README.md** for detailed documentation
2. **Run with `--verbose`** to see debug output
3. **Review configuration** - most issues are config-related
4. **Check disk space** - required for models and temporary files

## Quick Syntax Reference

```bash
# All required arguments
python video_censor_personal.py --input FILE --config FILE [--output FILE]

# All optional arguments
--output FILE      # Output JSON file (default: results.json)
--config FILE      # Config file (default: ./video-censor.yaml)
--verbose          # Debug output
--help             # Show help
--version          # Show version
```

---

**Estimated Total Setup Time**: 15-20 minutes (including model download)

**Ready to analyze?** 🎬

```bash
python video_censor_personal.py --input video.mp4 --config video-censor.yaml --verbose
```
