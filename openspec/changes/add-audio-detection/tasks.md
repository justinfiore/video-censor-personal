# Implementation Tasks: add-audio-detection

## 1. Audio Extraction Infrastructure

- [x] 1.1 Create `video_censor_personal/audio_extractor.py` with `AudioExtractor` class
  - Implement `extract()` method using ffmpeg + librosa
  - Implement `get_audio_segment(start_time, duration)` for frame-level slicing
  - Implement `cleanup()` for memory management
  - Add caching for full audio (numpy array in memory)
  - Auto-resample to 16kHz

- [x] 1.2 Create `video_censor_personal/audio_segment.py` with `AudioSegment` dataclass
  - Fields: `data` (numpy array), `sample_rate`, `start_time`, `end_time`
  - Methods: `duration()`, `is_empty()`
  - NOTE: AudioSegment already exists in frame.py

- [x] 1.3 Modify `video_censor_personal/video_extractor.py`
  - Add `extract_audio()` method calling AudioExtractor
  - Add `get_audio_segment(start_sec, end_sec)` convenience method
  - Integrate audio cleanup into `close()` and context manager
  - NOTE: extract_audio() already exists in VideoExtractor

- [ ] 1.4 Write unit tests for audio extraction (`tests/test_audio_extractor.py`)
  - Test extraction from sample video
  - Test caching (no re-extraction)
  - Test resampling to 16kHz
  - Test segment extraction by time
  - Test missing audio handling
  - Mock ffmpeg calls for isolation

- [ ] 1.5 Write integration test for audio + video extractor (`tests/test_video_audio_integration.py`)
  - Load sample video, extract frames and audio
  - Verify timecode alignment
  - Verify cleanup releases memory

## 2. Speech Profanity Detector

- [x] 2.1 Create `video_censor_personal/speech_profanity_detector.py`
  - Implement `SpeechProfanityDetector(Detector)` class
  - Initialize Whisper model in `__init__` (model size configurable)
  - Implement `detect(frame_data=None, audio_data)` method
  - Transcribe audio using pipeline("automatic-speech-recognition")
  - Implement `_load_profanity_keywords()` method
  - Implement `_find_profanity(text)` for keyword matching (case-insensitive)
  - Implement `cleanup()` to release Whisper model
  - Return `DetectionResult` with label="Profanity", confidence=0.95 per keyword found

- [x] 2.2 Create profanity keyword data files
  - Create `video_censor_personal/data/profanity_en.txt` (English keywords)
  - Create `video_censor_personal/data/profanity_es.txt` (Spanish keywords)
  - Skip `video_censor_personal/data/profanity_fr.txt` (per user request)
  - One keyword per line, case-insensitive matching

- [x] 2.3 Register detector with DetectorRegistry
  - In detector framework initialization, register `SpeechProfanityDetector` under type "speech-profanity"
  - Updated video_censor_personal/detectors/__init__.py

- [ ] 2.4 Write unit tests for speech detector (`tests/test_speech_profanity_detector.py`)
  - Mock Whisper pipeline
  - Test keyword matching (found, not found, case-insensitive)
  - Test multi-language support
  - Test missing audio (returns empty)
  - Test transcription failure handling
  - Test cleanup releases model

- [ ] 2.5 Write integration test with real Whisper model
  - Create sample audio with speech profanity
  - Run detector end-to-end
  - Verify profanity detected
  - Note: slower test, mark as @pytest.mark.slow

## 3. Audio Classification Detector

- [x] 3.1 Create `video_censor_personal/audio_classification_detector.py`
  - Implement `AudioClassificationDetector(Detector)` class
  - Initialize HuggingFace audio model in `__init__` (configurable model_name)
  - Implement `detect(frame_data=None, audio_data)` method
  - Preprocess audio with AutoFeatureExtractor
  - Run classification with AutoModelForAudioClassification
  - Implement `_build_category_mapping()` method
  - Map audio labels (e.g., "gunshot") to content categories (e.g., "Violence")
  - Return `DetectionResult` for detected categories with model confidence
  - Implement `cleanup()` to release model

- [x] 3.2 Build audio label → content category mapping
  - Fallback default mapping included in detector
  - Document mapping file: `video_censor_personal/data/audio_category_mapping.json`
  - Include mappings for Violence (gunshot, scream, explosion, etc.)
  - Include mappings for Sexual Theme (moaning, etc.)
  - Make extensible for future audio classifiers

- [x] 3.3 Register detector with DetectorRegistry
  - Register `AudioClassificationDetector` under type "audio-classification"
  - Updated video_censor_personal/detectors/__init__.py

- [ ] 3.4 Write unit tests for audio classifier (`tests/test_audio_classification_detector.py`)
  - Mock HuggingFace model
  - Test classification → category mapping
  - Test confidence score propagation
  - Test missing audio (returns empty)
  - Test unmapped labels (skipped)
  - Test model failure handling
  - Test cleanup releases model

- [ ] 3.5 Write integration test with real model
  - Create sample audio with sound effect
  - Run detector end-to-end
  - Verify sound effect categorized
  - Mark as @pytest.mark.slow

## 4. Analysis Pipeline Audio Detection Integration

- [x] 4.1 Modify `video_censor_personal/analysis_pipeline.py`
  - Add audio extraction in analyze() with error handling
  - Convert audio bytes to numpy array (mono, float32)
  - Resample via librosa if needed
  - Pass audio_data to detection_pipeline.analyze_frame()
  - Full integration with remediation and muxing logic

- [x] 4.2 Verify `DetectionPipeline.analyze_frame()` accepts audio_data
  - Already supports audio_data parameter
  - Passes audio_data to each detector's detect() method
  - Visual-only detectors ignore audio_data parameter

- [ ] 4.3 Write unit tests for pipeline audio integration (`tests/test_analysis_pipeline_audio.py`)
  - Mock AudioExtractor
  - Mock detectors
  - Test audio extraction on init when audio-capable detectors present
  - Test no extraction when all detectors visual-only
  - Test audio extraction failure → warning, continue
  - Test audio segment slicing per frame
  - Test cleanup

- [ ] 4.4 Write integration test for end-to-end pipeline with audio
  - Use sample video with speech profanity + visual content
  - Run pipeline with both visual and audio detectors
  - Verify profanity detected from audio
  - Verify visual content also detected
  - Mark as @pytest.mark.slow

## 5. Audio Remediation Engine

- [x] 5.1 Create `video_censor_personal/audio_remediator.py` with `AudioRemediator` class
  - Implement `__init__(config)` with mode, categories, bleep_frequency parameters
  - Implement `remediate(audio_data, sample_rate, detections)` method
  - For each detection in remediation categories:
    - Convert timecodes to sample indices
    - If mode="silence": zero out samples
    - If mode="bleep": generate sine wave tone
  - Implement `write_audio(audio_data, sample_rate, output_path)` method
  - Use soundfile to write WAV

- [ ] 5.2 Write unit tests for audio remediator (`tests/test_audio_remediator.py`)
  - Create synthetic audio with known samples
  - Test silence mode (check zeros in output)
  - Test bleep mode (check tone generated)
  - Test per-category filtering (skip categories not in list)
  - Test overlapping detections (no double-process)
  - Test file write (verify output WAV is valid)
  - Test invalid config (unknown mode, negative frequency)

- [ ] 5.3 Write integration test for remediation
  - Use detected segments with timecodes
  - Remediate with both silence and bleep
  - Write output and verify audio is different
  - Verify sample rate preserved
  - Mark as @pytest.mark.slow

## 6. Analysis Pipeline Remediation Integration

- [x] 6.1 Modify `video_censor_personal/analysis_pipeline.py` for remediation
  - In analyze() after frame analysis:
    - Get remediation config from self.config
    - If remediation enabled and audio_data present:
      - Initialize AudioRemediator
      - Call remediate(audio_data, sample_rate, all_results)
      - Write remediated audio to output_path
      - Store remediated_audio_path for muxing
  - Error handling with logging and re-raise

- [x] 6.2 Write unit tests for pipeline remediation integration
  - Mock AudioRemediator
  - Test remediation not applied when disabled
  - Test remediation applied when enabled
  - Test output path included in results
  - Test remediation failure propagates

- [ ] 6.3 Write integration test for end-to-end pipeline with detection + remediation
  - Load sample video with speech profanity
  - Configure with speech-profanity detector + remediation (silence mode)
  - Run pipeline
  - Verify audio remediated and written
  - Verify detection results and output path both returned

## 7. Video Muxing and Output

- [x] 7.1 Create `video_censor_personal/video_muxer.py` with `VideoMuxer` class
  - Implement `__init__(original_video_path, remediated_audio_path)`
  - Implement `mux_video(output_video_path)` method
  - Use ffmpeg command with flags: `-c:v copy`, `-c:a aac`, `-map 0:v:0 -map 1:a:0`, `-shortest`
  - Parse ffmpeg stderr and raise descriptive error on failure
  - Handle file permissions and missing files gracefully

- [ ] 7.2 Write unit tests for video muxer (`tests/test_video_muxer.py`)
  - Mock subprocess to simulate ffmpeg calls
  - Test successful muxing (check command and args)
  - Test ffmpeg failure handling
  - Test invalid input paths
  - Test output file creation

- [ ] 7.3 Write integration test for video muxing
  - Use sample video file
  - Create synthetic remediated audio WAV
  - Run muxer end-to-end
  - Verify output video file contains both video and audio
  - Verify output is valid MP4 (playable)
  - Mark as @pytest.mark.slow

- [x] 7.4 Modify `video_censor_personal/analysis_pipeline.py` for video output
  - Add `output_video_path` parameter to `__init__`
  - After audio remediation completes:
    - If remediation enabled and output_video_path provided:
      - Initialize VideoMuxer
      - Call mux_video()
      - Log output_video_path
  - Error handling for muxing failures with re-raise

- [x] 7.5 Write unit tests for pipeline video muxing integration
  - Mock VideoMuxer
  - Test muxing called when remediation enabled and output path provided
  - Test muxing skipped when remediation disabled
  - Test muxing skipped when output path not provided
  - Test output path logged in pipeline

## 8. CLI and Configuration

- [x] 8.1 Update YAML configuration schema in `video_censor_personal/config.py`
  - Add support for audio detectors in config parsing (NOTE: existing framework supports)
  - Add support for audio remediation config parsing (NOTE: custom validation in pipeline)
  - New audio detection fields: `model`, `languages` (array), `confidence_threshold`
  - New audio remediation fields: `enabled`, `mode`, `categories`, `bleep_frequency`

- [x] 8.2 Update main entry point (`video_censor_personal.py`)
  - Add `--output-video` argument to cli.py
  - Add validation in main():
    - If remediation enabled and no --output-video → error with guidance
    - If --output-video provided but remediation disabled → error with guidance
  - Pass output_video_path to AnalysisRunner
  - Updated help text

- [ ] 8.3 Create example configs with audio and muxing
  - Create `video-censor-audio-detection.yaml.example` (detection only, no muxing)
  - Create `video-censor-audio-remediation-silence.yaml.example` (silence mode, shows muxing)
  - Create `video-censor-audio-remediation-bleep.yaml.example` (bleep mode)
  - Document usage with CLI examples showing --output-video
  - Clearly note that output-video is required when remediation enabled

- [ ] 8.4 Write config validation tests (`tests/test_config_audio.py`)
  - Test valid audio detector configs load
  - Test invalid detector type rejected
  - Test missing required fields rejected
  - Test languages array parsed correctly
  - Test model parameter passed to detector
  - Test valid remediation config loads
  - Test invalid remediation mode rejected
  - Test remediation categories validated

- [x] 8.5 Write CLI argument tests (`tests/test_cli_args.py`)
  - Test --output-video argument parsed correctly
  - Test fail-fast when remediation enabled but no --output-video
  - Test error message is clear and helpful
  - Test --output-video optional when remediation disabled
  - Test dual validation logic implemented

## 9. Dependencies and Documentation

- [x] 9.1 Update `requirements.txt`
  - Add `librosa` with pinned version
  - Add `soundfile` for audio file writing
  - Add `scipy` for audio signal processing
  - Add `transformers` (already present)
  - Add `torch` (already present)
  - Updated requirements.txt with audio packages

- [ ] 9.2 Update README.md
  - Add section "Audio Detection Setup" with model download instructions
  - Document speech profanity detection
  - Document audio classification (sound effects)
  - Document audio remediation (silence vs bleep)
  - List supported languages
  - Include Whisper model size reference (base ~140MB, etc.)
  - Include pre-download commands for models
  - Document configuration examples
  - Add link to AUDIO.md for detailed setup

- [ ] 9.3 Update QUICK_START.md
  - Add "Step 3: Download Audio Models (Optional)" section
  - Explain when audio models are needed (if using speech-profanity or audio-classification detectors)
  - Provide quick-start commands:
    - `python -c "from transformers import pipeline; pipeline('automatic-speech-recognition', model='openai/whisper-base')"` for Whisper
    - `python -c "from transformers import AutoModelForAudioClassification; AutoModelForAudioClassification.from_pretrained('audioset-vit-base')"` for audio classification
  - Show cache locations and how to check if models already cached
  - Estimate download time and storage (~500 MB total for base models)
  - Document environment variable overrides (TRANSFORMERS_CACHE, HF_HOME)
  - Note: Models download automatically on first use if not pre-cached

- [ ] 9.4 Write AUDIO.md setup and reference guide
  - Section: "Model Selection and Setup"
    - Whisper model sizes and performance (tiny 40MB → large 3GB)
    - Recommendation: base model for most use cases
    - Audio classification model (audioset-vit-base ~300MB)
  - Section: "Pre-downloading Models"
    - Step-by-step commands to download before first run
    - Cache locations by OS (Linux, macOS, Windows)
  - Section: "Model Caching and Storage"
    - Default cache paths
    - How to override with environment variables
    - Disk space requirements (~500MB to 4GB depending on models)
  - Section: "First-Run Behavior"
    - Automatic download if not cached
    - Expected latency on first speech detection run
  - Audio detection architecture
  - Speech profanity detection approach (Whisper + keywords)
  - Audio classification approach (HuggingFace)
  - Audio remediation approach (silence vs bleep)
  - Video muxing approach (ffmpeg, lossless video passthrough)
  - Performance notes (model load time, inference time, muxing speed)
  - Remediation + muxing workflow and output integration
  - CLI usage with --output-video examples
  - Troubleshooting (missing audio, model download errors, transcription failures, muxing issues)

- [ ] 9.5 Update tests/README.md or TESTING.md
  - Document how to run audio, remediation, and muxing tests
  - Section: "Audio Tests and Model Downloads"
    - Note: tests automatically download Whisper model on first run
    - Expected download size and time (~140MB for base model)
    - Tests marked with @pytest.mark.slow
  - Note: remediation tests create output WAV files in temp directory
  - Note: muxing tests create output MP4 files in temp directory
  - Cache notes: models persist across test runs
  - How to skip slow tests: `pytest -m "not slow"`

## 10. Final Validation and Testing

- [ ] 10.1 Run full test suite
  - `pytest tests/ --cov` should pass with >80% coverage
  - No warnings except expected deprecations
  - Audio tests run (or skip if marked slow)
  - Muxing tests verify output files created

- [ ] 10.2 Integration test with real sample video
  - Use sample MP4 with both visual and speech content
  - Configure pipeline with both visual and audio detectors
  - Verify results include both visual and profanity detections
  - Verify output JSON is valid and complete

- [ ] 10.3 Integration test with audio remediation and muxing
  - Load sample video with speech profanity
  - Configure with speech detector + remediation (silence mode) + muxing
  - Run pipeline with `--output-video` CLI argument
  - Verify output audio file created and is valid WAV
  - Verify output video file created and is valid MP4
  - Verify profanity segments are silenced (zeros) in audio
  - Test with bleep mode and verify output video contains bleep tone
  - Verify output video is playable and audio is synced

- [ ] 10.4 Test fail-fast validation
  - Run with remediation enabled but no --output-video
  - Verify program exits immediately with code 1
  - Verify error message clearly explains the issue
  - Verify error message shows example of correct usage

- [ ] 10.5 Test backwards compatibility
  - Ensure existing configs (visual-only) still work
  - Ensure existing tests still pass
  - Audio detection is opt-in, no breaking changes
  - --output-video optional when remediation disabled

- [ ] 10.6 Performance profiling
  - Measure audio extraction time for 1-minute video
  - Measure Whisper inference time per frame
  - Measure audio classification inference time per frame
  - Measure remediation time (silence vs bleep)
  - Measure output WAV file write time
  - Measure video muxing time (ffmpeg)
  - Document latencies and memory usage

- [ ] 10.7 Code review checklist
  - All code follows PEP 8 (100-char line limit)
  - All functions have type hints and docstrings
  - All public methods documented (Google-style)
  - No hardcoded paths or magic numbers
  - Error messages are clear and actionable
  - Logging at appropriate levels (info, warning, error)
  - Audio remediation and muxing error handling is comprehensive
  - CLI validation fail-fast messages are user-friendly
