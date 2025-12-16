# Configuration Guide

This document provides a comprehensive reference for configuring Video Censor Personal using YAML configuration files.

## Table of Contents

- [Quick Start](#quick-start)
- [Configuration File Location](#configuration-file-location)
- [Top-Level Structure](#top-level-structure)
- [Detections Section](#detections-section)
- [Detectors Section](#detectors-section)
  - [LLaVA Detector](#llava-detector)
  - [CLIP Detector](#clip-detector)
  - [Speech Profanity Detector](#speech-profanity-detector)
  - [Audio Classification Detector](#audio-classification-detector)
  - [Mock Detector](#mock-detector)
- [Audio Section](#audio-section)
- [Processing Section](#processing-section)
- [Output Section](#output-section)
- [Video Section](#video-section)
  - [Video Metadata Output](#video-metadata-output)
  - [Skip Chapters](#skip-chapters)
- [Models Section](#models-section)
- [Complete Example](#complete-example)

---

## Quick Start

Copy an example configuration to get started:

```bash
# Basic visual detection only
cp video-censor.yaml.example video-censor.yaml

# Audio detection (no remediation)
cp video-censor-audio-detection.yaml.example video-censor.yaml

# Audio detection with bleeping
cp video-censor-audio-remediation-bleep.yaml.example video-censor.yaml

# Audio detection with silence
cp video-censor-audio-remediation-silence.yaml.example video-censor.yaml
```

---

## Configuration File Location

The application searches for configuration files in this order:

1. Path specified via `--config` CLI argument
2. `./video-censor.yaml` in current directory
3. `./config.yaml` in current directory

---

## Top-Level Structure

A configuration file has these top-level sections:

```yaml
version: 1.0                    # Optional: configuration version

detections: { ... }             # REQUIRED: Detection category settings
detectors: [ ... ]              # Optional: Detector configurations
audio: { ... }                  # Optional: Audio processing settings
processing: { ... }             # REQUIRED: Frame/video processing settings
output: { ... }                 # REQUIRED: Output format settings
models: { ... }                 # Optional: Model download/cache settings
```

---

## Detections Section

**Required.** Defines content detection categories and their sensitivity levels.

```yaml
detections:
  nudity:
    enabled: true               # Whether this category is active
    sensitivity: 0.7            # 0.0 (permissive) to 1.0 (strict)
    model: "local"              # Model identifier ("local" for built-in)
  
  profanity:
    enabled: true
    sensitivity: 0.8
    model: "local"
  
  violence:
    enabled: true
    sensitivity: 0.6
    model: "local"
  
  sexual_themes:
    enabled: true
    sensitivity: 0.75
    model: "local"
```

### Detection Category Options

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `enabled` | boolean | Yes | - | Enable/disable this detection category |
| `sensitivity` | float | Yes | - | Detection threshold (0.0-1.0) |
| `model` | string | Yes | - | Model identifier (use `"local"` for built-in) |

### Available Categories

| Category | Description |
|----------|-------------|
| `nudity` | Nude or partially nude content |
| `profanity` | Visual profanity (gestures, text) |
| `violence` | Violent imagery or actions |
| `sexual_themes` | Sexually suggestive content |
| `logos` | Brand logos (future feature) |
| `spoilers` | Spoiler content (future feature) |

**Note:** At least one detection category must have `enabled: true`.

---

## Detectors Section

**Optional.** Configures specific detector implementations. If omitted, defaults are used.

```yaml
detectors:
  - type: "llava"                    # Detector type identifier
    name: "llava-primary"            # Unique instance name
    categories:                      # Categories this detector handles
      - "Nudity"
      - "Violence"
    # ... detector-specific options
```

### Common Detector Options

All detectors share these fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | Yes | Detector type (`llava`, `clip`, `speech-profanity`, `audio-classification`, `mock`) |
| `name` | string | Yes | Unique identifier for this detector instance |
| `categories` | list | Yes | Content categories this detector analyzes |
| `enabled` | boolean | No | Enable/disable detector (default: `true`) |
| `device` | string | No | Force device: `"cuda"`, `"mps"`, `"cpu"`, or `null` for auto-detect |

---

### LLaVA Detector

Vision-language detector using LLaVA model for visual content analysis.

```yaml
- type: "llava"
  name: "llava-primary"
  model_name: "liuhaotian/llava-v1.5-7b"
  model_path: null
  prompt_file: "./prompts/llava-detector.txt"
  device: null
  categories:
    - "Nudity"
    - "Violence"
    - "Sexual Theme"
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `model_name` | string | No | `"liuhaotian/llava-v1.5-7b"` | HuggingFace model identifier |
| `model_path` | string | No | `null` | Custom model cache path (null = HF default) |
| `prompt_file` | string | No | `"./prompts/llava-detector.txt"` | Path to prompt template file |
| `device` | string | No | `null` | Device override (auto-detect if null) |

**Model Variants:**
- `liuhaotian/llava-v1.5-7b` - 7B parameter model (~14 GB VRAM)
- `liuhaotian/llava-v1.5-13b` - 13B parameter model (~26 GB VRAM)

---

### CLIP Detector

Lightweight vision-language detector using OpenAI's CLIP model for efficient visual content classification via text prompt matching.

```yaml
- type: "clip"
  name: "clip-detector"
  model_name: "openai/clip-vit-base-patch32"
  confidence_threshold: 0.5
  device: null
  categories:
    - "Nudity"
    - "Violence"
    - "Sexual Theme"
  prompts:
    - category: "Nudity"
      text: ["nude person", "naked body", "exposed genitals"]
    - category: "Violence"
      text: ["fight", "blood", "injury", "weapon"]
    - category: "Sexual Theme"
      text: ["sexual activity", "erotic content"]
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `model_name` | string | No | `"openai/clip-vit-base-patch32"` | HuggingFace model identifier |
| `device` | string | No | `null` | Device override (auto-detect if null) |
| `confidence_threshold` | float | No | `0.5` | Minimum confidence (0.0-1.0) to report detection |
| `prompts` | list | Yes | - | List of category prompt definitions |

**Prompts Configuration:**

Each prompt definition requires:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `category` | string | Yes | Category name (must match a category in `categories` list) |
| `text` | list | Yes | List of candidate text phrases for this category (minimum 1) |

**Available CLIP Model Variants:**

| `model_name` | Parameters | Size | Notes |
|--------------|------------|------|-------|
| `openai/clip-vit-base-patch32` | ~151M | ~600MB | Fastest, lowest quality. ViT-B/32 architecture. |
| `openai/clip-vit-base-patch16` | ~151M | ~600MB | Better than patch32, slower. ViT-B/16 architecture. |
| `openai/clip-vit-large-patch14` | ~428M | ~1.7GB | Best quality for 224px images. ViT-L/14 architecture. |
| `openai/clip-vit-large-patch14-336` | ~428M | ~1.7GB | Highest quality, fine-tuned for 336px input images. |

**Model Trade-offs:**
- **Patch size**: Smaller patches (14 vs 32) = more patches per image = better detail but slower
- **Model size**: `large` models are ~3x bigger than `base` but significantly more accurate
- The `336` variant expects higher-resolution inputs, which can improve accuracy for detailed content

**Confidence Threshold:**

The `confidence_threshold` (default: `0.5`) controls how confident CLIP must be before reporting a detection. Since CLIP outputs softmax probabilities (always between 0.0 and 1.0), a threshold of 0.0 would report everything. Recommended values:

- `0.3-0.4` - Sensitive (catch more potential content, higher false positives)
- `0.5` - Balanced (default, good for most use cases)
- `0.6-0.7` - Conservative (fewer false positives, may miss some content)
- `0.8+` - Very conservative (only report high-confidence detections)

Start with `0.5` and adjust based on your false positive/negative tolerance.

**Prompt Engineering Tips:**

- Use 2-5 candidate phrases per category for better coverage
- Be specific with descriptions (e.g., "nude person" rather than just "nude")
- Include common variations to handle edge cases
- Avoid negations (e.g., don't use "not violent")
- Test prompts with sample frames to validate detection accuracy
- Adjust `confidence_threshold` if you're getting too many false positives/negatives

**CLIP vs LLaVA:**

| Aspect | CLIP | LLaVA |
|--------|------|-------|
| Speed | Fast (per-frame suitable) | Slower (requires reasoning) |
| Memory | Lower (~2-3 GB) | Higher (~14+ GB) |
| Accuracy | Prompt-dependent | Comprehensive visual understanding |
| Config | Text prompts inline | Prompt file reference |
| Use Case | Quick, efficient classification | Detailed visual analysis |

---

### Speech Profanity Detector

Detects profanity in spoken audio using Whisper speech-to-text and keyword matching.

```yaml
- type: "speech-profanity"
  name: "speech-detector"
  enabled: true
  model: "base"
  languages:
    - "en"
    - "es"
  confidence_threshold: 0.8
  device: null
  categories:
    - "Profanity"
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `model` | string | No | `"base"` | Whisper model size |
| `languages` | list | No | `["en"]` | Language codes for profanity detection |
| `confidence_threshold` | float | No | `0.8` | Minimum confidence for detection (0.0-1.0) |
| `device` | string | No | `null` | Device override (auto-detect if null) |

**Whisper Model Sizes:**

| Model | Size | VRAM | Speed | Accuracy |
|-------|------|------|-------|----------|
| `tiny` | 40 MB | ~1 GB | Fastest | Lower |
| `base` | 140 MB | ~1 GB | Fast | Good |
| `small` | 500 MB | ~2 GB | Medium | Better |
| `medium` | 1.5 GB | ~5 GB | Slow | High |
| `large` | 3 GB | ~10 GB | Slowest | Highest |

**Supported Languages:** `en` (English), `es` (Spanish), and all Whisper-supported languages.

---

### Audio Classification Detector

Detects sound effects (gunshots, screams, etc.) using HuggingFace audio classification models.

```yaml
- type: "audio-classification"
  name: "audio-classifier"
  enabled: true
  model: "MIT/ast-finetuned-audioset-10-10-0.4593"
  confidence_threshold: 0.6
  chunk_duration: 2.0
  device: null
  categories:
    - "Violence"
    - "Sexual Theme"
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `model` | string | No | `"MIT/ast-finetuned-audioset-10-10-0.4593"` | HuggingFace model identifier |
| `confidence_threshold` | float | No | `0.6` | Minimum confidence for detection (0.0-1.0) |
| `chunk_duration` | float | No | `2.0` | Audio chunk size in seconds |
| `device` | string | No | `null` | Device override (auto-detect if null) |

**Audio Classification Settings:**

- **chunk_duration**: Controls how much audio context the model sees per inference. Larger values (2-3 seconds) work better for sustained sounds like moaning or screaming. Smaller values (1 second) work for brief sounds like gunshots.
- Audio is processed with 50% overlap between chunks to avoid missing sounds at boundaries.

**Category Mapping:**

The detector maps audio labels to content categories:

| Audio Labels | Content Category |
|-------------|------------------|
| gunshot, gun, shooting, explosion, scream, crash, bang, punch | Violence |
| moan, moaning, pant, panting, breath, groaning | Sexual Theme |

---

### Mock Detector

For testing and development. Returns deterministic results without requiring model downloads.

```yaml
- type: "mock"
  name: "mock-detector"
  enable_nudity: true
  enable_violence: true
  enable_profanity: true
  enable_sexual_theme: true
  categories:
    - "Nudity"
    - "Violence"
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `enable_nudity` | boolean | No | `true` | Return nudity detections |
| `enable_violence` | boolean | No | `true` | Return violence detections |
| `enable_profanity` | boolean | No | `true` | Return profanity detections |
| `enable_sexual_theme` | boolean | No | `true` | Return sexual theme detections |

---

## Audio Section

**Optional.** Controls audio extraction, detection, and remediation.

```yaml
audio:
  detection:
    enabled: true               # Enable audio-based detection
  
  remediation:
    enabled: true               # Enable audio remediation
    mode: "silence"             # "silence" or "bleep"
    categories:                 # Categories to remediate
      - "Profanity"
      - "Violence"
    bleep_frequency: 1000       # Frequency in Hz for bleep mode
```

### Audio Detection Options

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `enabled` | boolean | No | `false` | Enable audio track analysis |

### Audio Remediation Options

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `enabled` | boolean | No | `false` | Enable audio remediation |
| `mode` | string | No | `"silence"` | Remediation mode: `"silence"` or `"bleep"` |
| `categories` | list | No | `[]` | Categories to remediate (empty = all detected) |
| `bleep_frequency` | integer | No | `1000` | Tone frequency in Hz for bleep mode |

**Remediation Modes:**

- **silence**: Replaces detected segments with silence (zero amplitude)
- **bleep**: Replaces detected segments with a sine wave tone

**Note:** When `remediation.enabled: true`, use `--output-video` CLI flag to specify output file.

---

## Processing Section

**Required.** Controls video frame processing behavior.

```yaml
processing:
  frame_sampling:
    strategy: "uniform"         # Sampling strategy
    sample_rate: 1.0            # Seconds between samples
  
  segment_merge:
    enabled: true               # Merge nearby detections
    merge_threshold: 2.0        # Merge within N seconds
  
  max_workers: 4                # Parallel processing threads
```

### Frame Sampling Options

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `strategy` | string | Yes | - | Sampling strategy |
| `sample_rate` | float | No | `1.0` | Seconds between frame samples |

**Sampling Strategies:**

| Strategy | Description |
|----------|-------------|
| `uniform` | Sample frames at fixed intervals (most common) |
| `scene_based` | Sample at scene changes (requires scene detection) |
| `all` | Analyze every frame (slow, high accuracy) |

### Segment Merge Options

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `enabled` | boolean | No | `true` | Enable segment merging |
| `merge_threshold` | float | No | `2.0` | Merge segments within N seconds |

### Processing Options

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `max_workers` | integer | Yes | - | Number of parallel workers (must be > 0) |

---

## Output Section

**Required.** Controls output format and content.

```yaml
output:
  format: "json"                # Output format (only "json" supported)
  include_confidence: true      # Include confidence scores
  pretty_print: true            # Human-readable formatting
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `format` | string | Yes | - | Output format (must be `"json"`) |
| `include_confidence` | boolean | No | `true` | Include detection confidence scores |
| `pretty_print` | boolean | No | `true` | Format JSON with indentation |

### Segment Allow Override

Each segment in the output JSON supports an optional `allow` property for user remediation control:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `allow` | boolean | No | `false` | When `true`, segment is excluded from remediation |

**Behavior:**
- Segments with `"allow": true` are excluded from audio bleep/silence, chapter generation, and all remediation
- Missing `allow` property is treated as `false` (backward compatible)
- Original detection data is always preserved regardless of allow status

**Use Case - False Positive Handling:**
1. Run analysis to generate JSON output
2. Review detected segments
3. Set `"allow": true` on false positives
4. Run remediation - only non-allowed segments are processed

**CLI Flag:**

Use `--allow-all-segments` during analysis to pre-mark all segments as allowed:

```bash
python video_censor_personal.py \
  --input video.mp4 \
  --config config.yaml \
  --output results.json \
  --allow-all-segments
```

This is useful for "preview mode" where you want to analyze but not remediate until you've reviewed the detections. The flag has no effect during remediation phase (when using `--input-segments`).

---

## Video Section

**Optional.** Controls video output and metadata writing.

```yaml
video:
  metadata_output:
    skip_chapters:
      enabled: false              # Write detection segments as chapter markers
```

### Video Metadata Output

Enables writing detection segments as chapter markers in the output video file (MKV or MP4), allowing users to jump between flagged content sections directly in their media player.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `skip_chapters.enabled` | boolean | No | `false` | Enable skip chapter marker output |
| `skip_chapters.name_format` | string | No | See below | Custom chapter name format (future feature) |

### Skip Chapters

When skip chapters are enabled, the system:

1. **Extracts existing chapters** from the input video (if present)
2. **Generates skip chapters** from detection segments with names like:
   ```
   skip: Nudity [92%]
   skip: Violence, Sexual Theme [85%]
   ```
3. **Merges chapters** by timestamp (existing + skip chapters)
4. **Writes combined metadata** to the output video file using native chapter atoms

#### Supported Formats

- **MKV** (Matroska) - Uses mkvmerge for native Matroska chapter support
- **MP4** - Uses ffmpeg with native MP4 container atoms for chapter support

Both formats provide reliable, cross-platform chapter support in all standard media players (VLC, Plex, Windows Media Player, Kodi, etc.).

#### Requirements

- **ffmpeg** >= 8.0 must be installed and in PATH (for native chapter support and re-muxing)
- **mkvmerge** (included with mkvtoolnix) for MKV format support
- `--output-video` CLI argument is required when skip chapters are enabled
- Output file must be different from input file (to prevent data loss)
- Output format determined by file extension: `.mkv` or `.mp4`

#### Example Usage

Configuration:
```yaml
video:
  metadata_output:
    skip_chapters:
      enabled: true
```

Command line:
```bash
python video_censor_personal.py \
  --input original.mp4 \
  --config video-censor.yaml \
  --output results.json \
  --output-video output_with_chapters.mp4
```

#### Player Compatibility

Most modern media players support MP4 chapter markers:

- **VLC** - Chapters display as a list in the Playlist panel (View → Playlist)
- **Plex** - Chapters appear as navigation points in the timeline
- **QuickTime** - Chapters show in the timeline
- **Windows Media Player** - Chapters supported in newer versions
- **mpv** - Full chapter support with keyboard navigation

#### Performance Considerations

- Re-muxing large video files can take several minutes (depends on file size and disk speed)
- No transcoding occurs; video quality is preserved
- Original chapters are preserved when merged with skip chapters
- If no detections found, existing chapters are copied to output file

#### Error Handling

- If chapter writing fails, the JSON output still succeeds (JSON is primary output)
- Detailed error messages help diagnose ffmpeg issues
- Non-interactive mode (CI/CD) requires different input/output paths (no overwrite confirmation prompt)

---

## Models Section

**Optional.** Controls model downloading and caching.

```yaml
models:
  cache_dir: null               # Custom cache directory (null = platform default)
  auto_download: false          # Auto-download on startup (future feature)
  
  sources:                      # Downloadable model definitions
    - name: "llava-7b"
      url: "https://..."
      checksum: "sha256:..."
      size_bytes: 3825156096
      algorithm: "sha256"
      optional: false
```

### Models Options

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `cache_dir` | string | No | Platform default | Custom model cache directory |
| `auto_download` | boolean | No | `false` | Auto-download models on startup |
| `sources` | list | No | `[]` | Model source definitions |

### Model Source Options

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `name` | string | Yes | - | Model identifier |
| `url` | string | Yes | - | Download URL |
| `checksum` | string | Yes | - | Hash for integrity verification |
| `size_bytes` | integer | Yes | - | Expected file size in bytes |
| `algorithm` | string | No | `"sha256"` | Checksum algorithm |
| `optional` | boolean | No | `false` | Continue if download fails |

**Default Cache Locations:**
- Linux/macOS: `~/.cache/video-censor/models`
- Windows: `%APPDATA%\video-censor\models`

---

## Complete Example

A full configuration with all sections:

```yaml
version: 1.0

# Content detection categories
detections:
  nudity:
    enabled: true
    sensitivity: 0.7
    model: "local"
  
  profanity:
    enabled: true
    sensitivity: 0.8
    model: "local"
  
  violence:
    enabled: true
    sensitivity: 0.6
    model: "local"
  
  sexual_themes:
    enabled: true
    sensitivity: 0.75
    model: "local"

# Detector implementations
detectors:
  # Visual detection with CLIP
  - type: "clip"
    name: "clip-detector"
    model_name: "openai/clip-vit-base-patch32"
    confidence_threshold: 0.5
    device: null
    categories:
      - "Nudity"
      - "Violence"
      - "Sexual Theme"
    prompts:
      - category: "Nudity"
        text: ["nude person", "naked body", "exposed genitals"]
      - category: "Violence"
        text: ["fight", "blood", "injury", "weapon"]
      - category: "Sexual Theme"
        text: ["sexual activity", "erotic content"]
  
  # Speech profanity detection
  - type: "speech-profanity"
    name: "speech-detector"
    enabled: true
    model: "base"
    languages:
      - "en"
    confidence_threshold: 0.8
    categories:
      - "Profanity"
  
  # Sound effect detection
  - type: "audio-classification"
    name: "audio-classifier"
    enabled: true
    model: "MIT/ast-finetuned-audioset-10-10-0.4593"
    confidence_threshold: 0.6
    chunk_duration: 2.0
    categories:
      - "Violence"
      - "Sexual Theme"

# Audio processing
audio:
  detection:
    enabled: true
  
  remediation:
    enabled: true
    mode: "bleep"
    categories:
      - "Profanity"
    bleep_frequency: 1000

# Video processing
processing:
  frame_sampling:
    strategy: "uniform"
    sample_rate: 1.0
  
  segment_merge:
    enabled: true
    merge_threshold: 2.0
  
  max_workers: 4

# Output settings
output:
  format: "json"
  include_confidence: true
  pretty_print: true

# Model management
models:
  cache_dir: null
  auto_download: false
```

---

## See Also

- [README.md](README.md) - Quick start and installation
- [AUDIO.md](AUDIO.md) - Detailed audio detection and remediation guide
- [CONTRIBUTING.md](CONTRIBUTING.md) - Development and testing guidelines
