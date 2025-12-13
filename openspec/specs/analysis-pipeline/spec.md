# analysis-pipeline Specification

## Purpose
TBD - created by archiving change implement-analysis-pipeline. Update Purpose after archive.
## Requirements
### Requirement: Analysis Pipeline Orchestration

The system SHALL provide an `AnalysisPipeline` class that orchestrates the complete video analysis workflow: video frame extraction, detector initialization, frame-by-frame analysis, result aggregation, and resource cleanup.

#### Scenario: Initialize pipeline with video and config
- **WHEN** `AnalysisPipeline` is created with video path and configuration
- **THEN** pipeline initializes video extractor and detection pipeline from config

#### Scenario: Analyze video end-to-end
- **WHEN** `analyze()` is called on the pipeline
- **THEN** pipeline iterates all extracted frames, runs detection on each, and returns aggregated results

#### Scenario: Extract frames at configured sample rate
- **WHEN** configuration specifies `processing.frame_sampling.sample_rate = 2.0`
- **THEN** pipeline extracts and analyzes every 2 seconds of video (not every frame)

#### Scenario: Aggregate detection results
- **WHEN** multiple frames return detections
- **THEN** pipeline collects all results and applies segment merging based on config threshold

#### Scenario: Pipeline cleanup releases resources
- **WHEN** pipeline is used as context manager or cleanup() is called
- **THEN** video extractor and all detectors are cleaned up, temp files removed

#### Scenario: Handle detector failures gracefully
- **WHEN** a detector raises exception during frame analysis
- **THEN** error is logged, pipeline continues with remaining detectors for that frame

#### Scenario: Return empty results for video with no detections
- **WHEN** video is analyzed and no frames trigger any detections
- **THEN** pipeline returns empty detection results list

### Requirement: Pipeline Configuration Resolution

The system SHALL resolve detector configuration from the YAML config, supporting both explicit detector chains and fallback from category definitions.

#### Scenario: Explicit detector chain in config
- **WHEN** config contains `detectors:` list with type, name, model, categories
- **THEN** pipeline creates detectors from explicit chain

#### Scenario: Fallback to category-based config
- **WHEN** config has no `detectors:` section but has `detections:` with categories
- **THEN** pipeline auto-generates single default detector covering enabled categories

#### Scenario: Detector initialization with parameters
- **WHEN** detector config includes model_name, sensitivity, or other parameters
- **THEN** detector receives these parameters during initialization

#### Scenario: Invalid detector configuration fails fast
- **WHEN** detector config is missing required fields or has invalid types
- **THEN** pipeline raises descriptive ConfigError before analysis begins

### Requirement: Frame and Result Timecode Management

The system SHALL correctly assign and track timecodes for all frames and detection results.

#### Scenario: Frame timecode from extractor
- **WHEN** frame is extracted from video with sample_rate
- **THEN** frame has correct timecode (e.g., 0.0, 1.0, 2.0 for 1-second intervals)

#### Scenario: Detection results inherit frame timecode
- **WHEN** detector returns results for a frame
- **THEN** each result is assigned the frame's timecode as start_time and end_time

#### Scenario: Results maintain original detector confidence
- **WHEN** multiple detections are returned for different categories
- **THEN** each detection maintains its independent confidence score

### Requirement: Audio Support Infrastructure

The system SHALL support passing audio data to detectors (both visual and audio-based detectors) via the analysis pipeline, enabling multi-modal detection on the same content.

#### Scenario: Extract and cache audio at pipeline start
- **WHEN** pipeline detects audio-capable detectors in configuration
- **THEN** audio is extracted once at pipeline initialization and cached for frame-level slicing

#### Scenario: Pass audio segments to detectors per frame
- **WHEN** frame is analyzed and audio detectors are configured
- **THEN** audio segment (matching frame timecode) is passed to detector.detect() alongside frame data

#### Scenario: Audio extraction failure does not halt pipeline
- **WHEN** audio extraction fails (missing audio, unsupported codec, I/O error)
- **THEN** warning is logged; pipeline continues with visual-only detection; audio_data=None passed to detectors

#### Scenario: Detector handles missing audio gracefully
- **WHEN** video has no audio but audio detector is configured
- **THEN** detector receives audio_data=None; detector either skips audio analysis or returns empty results

#### Scenario: Visual-only detectors skip audio parameter
- **WHEN** detector is visual-only (does not use audio_data)
- **THEN** audio_data parameter is ignored; detector continues as before

#### Scenario: Audio-visual detectors use both modalities
- **WHEN** multi-modal detector receives both frame_data and audio_data
- **THEN** detector can fuse information (e.g., violence detection from motion + impact sound)

#### Scenario: Cleanup releases cached audio
- **WHEN** pipeline analysis completes or cleanup() is called
- **THEN** cached audio is released from memory

### Requirement: CLI Integration

The system SHALL integrate the analysis pipeline into the main entry point to provide end-to-end command-line functionality.

#### Scenario: CLI loads config and runs analysis
- **WHEN** user runs `python video_censor_personal.py --input video.mp4 --config config.yaml --output results.json`
- **THEN** main entry point loads config, initializes pipeline, analyzes video, and writes JSON output

#### Scenario: User provides only input and output
- **WHEN** user runs `python video_censor_personal.py --input video.mp4 --output results.json`
- **THEN** system uses default config location (./video-censor.yaml or ./config.yaml)

#### Scenario: Verbose logging for debugging
- **WHEN** user adds `--verbose` flag
- **THEN** debug-level logging is enabled and pipeline logs frame count, detector progress, etc.

#### Scenario: Errors are reported to user
- **WHEN** pipeline encounters fatal error (invalid config, file not found, etc.)
- **THEN** descriptive error message is logged and CLI exits with non-zero code

