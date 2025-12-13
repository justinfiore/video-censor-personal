# Change: Add Audio Processing, Detection, and Remediation

## Why

The existing system detects inappropriate visual content (nudity, violence, etc.) but cannot detect or remediate audio-based issues like profanity in speech, explicit language, or sound effects (gunshots, screams). Audio analysis unlocks deeper content understanding through speech-to-text profanity detection, language classification, and sound effect recognition. Audio remediation (silencing or bleeping detected profanity/inappropriate sounds) enables users to automatically censor content without manual editing. This change adds infrastructure, detectors, and remediation tools for audio modalities while maintaining the existing visual detection system.

## What Changes

- **New Audio Detection Infrastructure**: Audio extraction, caching, and frame-level audio segmentation (new capability)
- **Audio-Capable Detector Types**: Speech profanity detector (using Whisper ASR) and audio classification detector (new implementations)
- **Audio Remediation Engine**: Dubbing/silencing detected audio content with configurable silence or bleep options (new capability)
- **Video Output and Muxing**: Re-mux remediated audio back into video container (new capability)
- **CLI Output Video Argument**: Command-line `--output-video` option for specifying dubbing output; fail-fast if remediation enabled without output, and fail-fast if output specified without remediation enabled (new CLI requirement)
- **Video Extractor Enhancement**: Extract audio track and cache for detector reuse (modification to existing capability)
- **Analysis Pipeline Enhancement**: Audio data orchestration, detection, remediation, and video muxing (modification to existing capability)
- **Configuration Support**: YAML schema for audio detection, remediation options (silence/bleep), and per-category dubbing control (configuration)

## Impact

- **Affected specs**: 
  - `audio-detection` (new)
  - `audio-remediation` (new)
  - `output-generation` (modified - add video muxing)
  - `video-extraction` (modified)
  - `analysis-pipeline` (modified)
  - `project-foundation` (modified - add CLI output-video argument)
  
- **Affected code**: 
  - New modules: `video_censor_personal/audio_detector.py`, `video_censor_personal/audio_remediator.py`, `video_censor_personal/video_muxer.py`
  - Modified: `video_censor_personal/video_extractor.py` (audio extraction)
  - Modified: `video_censor_personal/analysis_pipeline.py` (audio orchestration, remediation, and video muxing)
  - Modified: `video_censor_personal/config.py` (audio detection and remediation config validation)
  - Modified: `video_censor_personal.py` (CLI with --output-video argument)
  - New tests: `tests/test_audio_detector.py`, `tests/test_audio_extraction.py`, `tests/test_audio_remediator.py`, `tests/test_video_muxer.py`

- **CLI Changes**: 
  - New argument: `--output-video` (path to save remediated video file)
  - Validation: If audio remediation enabled in config, --output-video is required (fail-fast)
  - Validation: If --output-video provided but remediation disabled in config, error and exit (fail-fast)
  - No video file is written if remediation is not enabled

- **Output Changes**: 
  - JSON output includes `remediated_audio_path` when remediation is enabled
  - JSON output includes `output_video_path` when video muxing is enabled
  - New detection metadata: `timecode_range` for audio segment boundaries

- **Breaking Changes**: None; audio detection, remediation, and video output are opt-in via configuration and CLI

- **New Dependencies**: 
  - `openai-whisper` (speech-to-text)
  - `librosa` (audio feature extraction and manipulation)
  - `scipy` (audio signal processing for bleeping)
  - `pydub` or similar (audio container handling)

- **Model Downloads Required**:
  - Whisper models (base, small, medium, large) - downloaded on first use or pre-cached
  - HuggingFace audio classification models - downloaded on first use
  - Profanity keyword lists (bundled with package)

- **Documentation Updates**:
  - README.md: Add section on audio detection setup and model downloads
  - QUICK_START.md: Add step-by-step guide for downloading models before first run
  - AUDIO.md: Detailed model selection, caching, and storage requirements
  - Model availability and size reference (e.g., Whisper base ~140MB, large ~3GB)
