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

### Requirement: Remediation-Only Mode via Input Segments

The system SHALL support a remediation-only mode that skips all analysis and loads detection segments from an existing JSON file, enabling decoupled three-phase workflows.

#### Scenario: CLI accepts --input-segments argument
- **WHEN** user runs `python -m video_censor --input video.mp4 --input-segments segments.json --output-video output.mp4 --config config.yaml`
- **THEN** CLI parses `--input-segments` argument with the path to existing segments JSON

#### Scenario: Skip analysis when --input-segments is provided
- **WHEN** `--input-segments` is provided
- **THEN** system MUST NOT initialize `AnalysisPipeline`
- **AND** system MUST NOT run any detection (vision models, audio analysis, etc.)
- **AND** system loads segments directly from the specified JSON file

#### Scenario: Proceed to remediation with loaded segments
- **WHEN** segments are loaded from JSON file
- **THEN** system proceeds to remediation phase based on config settings
- **AND** all remediation modes work (audio bleep/silence, skip chapters)

#### Scenario: Validate --input-segments requires --input
- **WHEN** user provides `--input-segments` without `--input` video file
- **THEN** system exits with error: `"--input-segments requires --input video file for remediation"`

#### Scenario: Warn when --output is specified with --input-segments
- **WHEN** user provides `--input-segments` alongside `--output` (JSON output path)
- **THEN** system logs warning: `"--output is ignored in remediation mode; segments are loaded from --input-segments, not generated"`
- **AND** no new JSON output is written

### Requirement: Segments JSON File Loading

The system SHALL load and validate pre-existing segments JSON files for use in remediation-only mode.

#### Scenario: Load valid segments JSON
- **WHEN** valid segments JSON file is provided via `--input-segments`
- **THEN** system parses JSON and extracts `segments` array
- **AND** each segment retains all properties: `start_time`, `end_time`, `labels`, `confidence`, `allow`, etc.

#### Scenario: Validate JSON structure
- **WHEN** JSON file is missing required `segments` array
- **THEN** system exits with error: `"Invalid segments file: missing 'segments' array"`

#### Scenario: Handle malformed JSON
- **WHEN** JSON file is syntactically invalid
- **THEN** system exits with error: `"Failed to parse segments file: <json error details>"`

#### Scenario: Handle missing file
- **WHEN** `--input-segments` path does not exist
- **THEN** system exits with error: `"Segments file not found: <path>"`

### Requirement: Input Video Validation Against Segments

The system SHALL validate that the segments JSON file matches the input video to prevent accidental misuse.

#### Scenario: Warn on filename mismatch
- **WHEN** `metadata.file` in segments JSON does not match input video filename
- **THEN** system logs warning: `"Warning: Segments file was generated for '<metadata.file>' but input video is '<actual filename>'. Proceeding anyway."`
- **AND** remediation continues (non-fatal warning)

#### Scenario: Optional duration validation
- **WHEN** `metadata.duration` is present in segments JSON
- **THEN** system compares against input video duration
- **AND** if difference exceeds 1 second, logs warning: `"Warning: Video duration mismatch. Segments: <X>, Video: <Y>"`
- **AND** remediation continues (non-fatal warning)

#### Scenario: Missing metadata is acceptable
- **WHEN** segments JSON has no `metadata` section (e.g., manually created)
- **THEN** system skips validation and proceeds with remediation

