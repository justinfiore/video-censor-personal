# Audio Detection and Remediation Guide

This guide covers the audio detection and remediation capabilities of Video Censor Personal.

## Overview

Video Censor Personal supports two types of audio detection:

1. **Speech Profanity Detection** - Uses Whisper ASR to transcribe speech and match against profanity keyword lists
2. **Audio Classification** - Uses HuggingFace audio models to classify sounds (gunshots, screams, etc.)

Audio remediation can either **silence** or **bleep** detected segments, then mux the cleaned audio back into the video.

## Model Selection and Setup

### Whisper Models (Speech Detection)

Whisper is used for speech-to-text transcription. Choose a model size based on your needs:

| Model | Size | RAM Required | Speed | Accuracy |
|-------|------|--------------|-------|----------|
| tiny | ~40 MB | ~1 GB | Fastest | Lower |
| base | ~140 MB | ~2 GB | Fast | Good |
| small | ~500 MB | ~3 GB | Medium | Better |
| medium | ~1.5 GB | ~5 GB | Slow | High |
| large | ~3 GB | ~10 GB | Slowest | Highest |

**Recommendation**: Use `base` for most use cases. It provides a good balance of speed and accuracy.

### Audio Classification Model

The default audio classification model is `MIT/ast-finetuned-audioset-10-10-0.4593` (~300 MB), trained on AudioSet for recognizing 527 sound classes.

## Pre-downloading Models

Models download automatically on first use, but you can pre-cache them:

### Whisper Model

```bash
python -c "
from transformers import pipeline
print('Downloading Whisper base model...')
pipe = pipeline('automatic-speech-recognition', model='openai/whisper-base')
print('✓ Whisper model cached successfully')
"
```

### Audio Classification Model

```bash
python -c "
from transformers import AutoModelForAudioClassification, AutoFeatureExtractor
print('Downloading audio classification model...')
processor = AutoFeatureExtractor.from_pretrained('MIT/ast-finetuned-audioset-10-10-0.4593')
model = AutoModelForAudioClassification.from_pretrained('MIT/ast-finetuned-audioset-10-10-0.4593')
print('✓ Audio classification model cached successfully')
"
```

## Model Caching and Storage

### Cache Locations

Models are cached in HuggingFace's default locations:

| OS | Default Path |
|----|--------------|
| Linux | `~/.cache/huggingface/hub/` |
| macOS | `~/.cache/huggingface/hub/` |
| Windows | `C:\Users\<user>\.cache\huggingface\hub\` |

### Environment Variables

Override cache locations with:

```bash
# Set custom HuggingFace cache directory
export HF_HOME=/path/to/custom/cache

# Or specifically for transformers
export TRANSFORMERS_CACHE=/path/to/custom/cache
```

### Disk Space Requirements

| Configuration | Approximate Size |
|--------------|------------------|
| Base models only | ~500 MB |
| With small Whisper | ~1 GB |
| With large Whisper | ~4 GB |
| Full setup (all models) | ~5 GB |

## First-Run Behavior

On first run with audio detection enabled:

1. **Model Download**: If not cached, models download automatically
2. **Expected Latency**: 
   - Whisper base: ~1-3 minutes to download
   - Audio classifier: ~30 seconds to download
3. **Subsequent Runs**: Models load from cache (~5-10 seconds)

## Audio Detection Architecture

### Speech Profanity Detection

```
Audio → Whisper ASR → Transcription → Keyword Matching → Profanity Results
```

1. **Audio Extraction**: Extract audio track from video via ffmpeg
2. **Transcription**: Whisper model transcribes speech to text
3. **Keyword Matching**: Case-insensitive regex matching against profanity lists
4. **Results**: DetectionResult with label="Profanity" and confidence=0.95

### Audio Classification

```
Audio → Feature Extraction → Audio Model → Label Prediction → Category Mapping → Results
```

1. **Audio Extraction**: Extract audio track from video
2. **Feature Extraction**: Process audio into model-compatible format
3. **Classification**: Model predicts audio class (e.g., "gunshot")
4. **Category Mapping**: Map audio labels to content categories (e.g., "gunshot" → "Violence")
5. **Results**: DetectionResult with mapped category and model confidence

### Category Mapping

Audio labels are mapped to content categories:

| Audio Label | Content Category |
|------------|------------------|
| gunshot, explosion, scream, crash | Violence |
| moan, pant, groaning | Sexual Theme |

## Audio Remediation

### Silence Mode

Replaces detected audio segments with silence (zero amplitude):
- Natural-sounding (gaps in audio)
- No audible cue that content was censored

### Bleep Mode

Replaces detected audio segments with a sine wave tone:
- Default frequency: 1000 Hz
- Clear indication of censored content
- Configurable frequency (800-2000 Hz typical)

### Per-Category Control

You can choose which categories to remediate:

```yaml
audio:
  remediation:
    enabled: true
    mode: "silence"
    categories:
      - "Profanity"     # Silence profanity
      # Violence sounds detected but NOT silenced
```

## Video Muxing

After remediation, the cleaned audio is muxed back into the video:

```
Original Video + Remediated Audio → ffmpeg → Output Video
```

ffmpeg flags used:
- `-c:v copy`: Video passthrough (no re-encoding, fast)
- `-c:a aac`: Audio encoded as AAC
- `-shortest`: Stop at shortest stream

## CLI Usage

### Detection Only (No Remediation)

```bash
python video_censor_personal.py \
  --input video.mp4 \
  --config video-censor-audio-detection.yaml \
  --output results.json
```

### With Remediation (Requires --output-video)

```bash
python video_censor_personal.py \
  --input video.mp4 \
  --config video-censor-audio-remediation-silence.yaml \
  --output results.json \
  --output-video censored_video.mp4
```

**Important**: If remediation is enabled in config, `--output-video` is required. The CLI will fail-fast with a clear error if not provided.

## Configuration Examples

### Detection Only

```yaml
detectors:
  - type: "speech-profanity"
    name: "speech-detector"
    model: "base"
    categories: ["Profanity"]
    languages: ["en", "es"]

audio:
  detection:
    enabled: true
  remediation:
    enabled: false
```

### Remediation with Bleep

```yaml
detectors:
  - type: "speech-profanity"
    name: "speech-detector"
    model: "base"
    categories: ["Profanity"]
    languages: ["en"]

audio:
  detection:
    enabled: true
  remediation:
    enabled: true
    mode: "bleep"
    categories: ["Profanity"]
    bleep_frequency: 1000
```

## Performance Notes

| Operation | Typical Duration |
|-----------|------------------|
| Audio extraction | ~1-2 seconds per minute of video |
| Whisper transcription (base) | ~0.5x real-time on CPU |
| Audio classification | ~100ms per frame |
| Remediation (silence/bleep) | <1 second total |
| Video muxing (ffmpeg) | ~2-5 seconds |

### Tips for Faster Processing

1. Use `tiny` or `base` Whisper models
2. Increase `sample_rate` in config (analyze fewer frames)
3. Process on GPU if available (transformers auto-detects)

## Troubleshooting

### Missing Audio Track

**Symptom**: "No audio data provided" or empty detections

**Solution**:
- Verify video has audio: `ffprobe video.mp4`
- Check ffmpeg is installed: `ffmpeg -version`

### Model Download Errors

**Symptom**: Connection timeout or download failure

**Solution**:
```bash
# Increase timeout
export HF_HUB_READ_TIMEOUT=300

# Retry download
python -c "from transformers import pipeline; pipeline('automatic-speech-recognition', model='openai/whisper-base')"
```

### Transcription Failures

**Symptom**: Empty transcriptions for audio with speech

**Solution**:
- Check audio quality (noisy audio may fail)
- Try larger Whisper model (`small` or `medium`)
- Verify audio sample rate (16kHz expected)

### Muxing Issues

**Symptom**: "ffmpeg muxing failed"

**Solution**:
- Verify ffmpeg is installed: `ffmpeg -version`
- Check output path is writable
- Ensure input video is valid: `ffprobe -v error video.mp4`

### Out of Memory

**Symptom**: OOM error during transcription

**Solution**:
- Use smaller Whisper model (`tiny` or `base`)
- Process shorter videos
- Reduce `max_workers` in config

## Supported Languages

Profanity keyword lists are provided for:
- English (`en`)
- Spanish (`es`)

To add additional languages, create `video_censor_personal/data/profanity_<lang>.txt` with one keyword per line.
