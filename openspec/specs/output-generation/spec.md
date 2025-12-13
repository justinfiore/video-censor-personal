# output-generation Specification

## Purpose
TBD - created by archiving change add-output-generation. Update Purpose after archive.
## Requirements
### Requirement: Detection Result Data Model

The system SHALL define a standard data class to represent individual detection results from detection engines, enabling consistent communication between components.

#### Scenario: Create a detection result
- **WHEN** a detection engine identifies problematic content at 00:30:45 to 00:30:47 with "Profanity" label and 0.92 confidence
- **THEN** the system creates a DetectionResult with start_time=1845.0, end_time=1847.0, label="Profanity", confidence=0.92, and reasoning describing what was detected

#### Scenario: Detection result includes optional fields
- **WHEN** a detection result is created with optional frame data or description
- **THEN** the fields are preserved and available for output inclusion

#### Scenario: Multiple detections per frame
- **WHEN** multiple detection engines identify different issues in the same timeframe
- **THEN** each creates separate DetectionResult objects; merging happens at output stage

### Requirement: Segment Merging

The system SHALL merge overlapping or nearby detection results based on configurable time threshold to reduce output fragmentation and improve readability.

#### Scenario: Merge overlapping detections
- **WHEN** detections overlap in time (e.g., 00:30:45-00:30:48 and 00:30:47-00:30:50)
- **THEN** the system merges into single segment spanning 00:30:45-00:30:50 with both labels

#### Scenario: Merge nearby detections within threshold
- **WHEN** merge_threshold=2.0 and detections are at 00:30:45-00:30:47 and 00:30:48-00:30:50 (1 second gap)
- **THEN** the system merges into single segment spanning 00:30:45-00:30:50

#### Scenario: Do not merge distant detections
- **WHEN** merge_threshold=2.0 and detections are at 00:30:45-00:30:47 and 00:30:50-00:30:52 (3 second gap)
- **THEN** the system keeps as two separate segments

#### Scenario: Merged segment includes all labels
- **WHEN** merging detections with different labels (Profanity, Sexual Theme)
- **THEN** merged segment includes both labels in labels array

#### Scenario: Merged segment confidence is averaged
- **WHEN** merging detections with confidences 0.90 and 0.94
- **THEN** merged segment confidence is 0.92 (mean)

### Requirement: Summary Statistics Calculation

The system SHALL automatically calculate summary statistics across all flagged segments to provide users with quick insight into content distribution.

#### Scenario: Calculate total segments
- **WHEN** output is generated with 15 merged segments
- **THEN** summary includes total_segments_detected=15

#### Scenario: Calculate total flagged duration
- **WHEN** segments have durations 5, 10, 3, 2 seconds
- **THEN** summary includes total_flagged_duration=20

#### Scenario: Calculate detection counts by label
- **WHEN** segments contain Profanity (3 times), Violence (2 times), Sexual Theme (1 time)
- **THEN** summary includes detection_counts with each label and count

#### Scenario: Empty detection list
- **WHEN** no detections are found in video
- **THEN** summary shows total_segments_detected=0, total_flagged_duration=0, empty detection_counts

### Requirement: Time Formatting

The system SHALL support dual time formats (HH:MM:SS human-readable and seconds machine-readable) to enable both user reports and downstream processing.

#### Scenario: Format time as HH:MM:SS
- **WHEN** output generator formats 3661.5 seconds
- **THEN** result is "01:01:01"

#### Scenario: Format time as seconds
- **WHEN** output generator formats 3661.5 seconds with format="seconds"
- **THEN** result is "3661"

#### Scenario: Format edge cases
- **WHEN** formatting 0 seconds
- **THEN** HH:MM:SS format is "00:00:00" and seconds format is "0"

#### Scenario: Format large values
- **WHEN** formatting 36000 seconds (10 hours)
- **THEN** HH:MM:SS format is "10:00:00"

### Requirement: Config-Driven Output Formatting

The system SHALL respect configuration settings to control output verbosity, size, and formatting.

#### Scenario: Include confidence scores
- **WHEN** config.output.include_confidence=true
- **THEN** each detection in output includes confidence field

#### Scenario: Exclude confidence scores
- **WHEN** config.output.include_confidence=false
- **THEN** detections do not include confidence field (size optimization)

#### Scenario: Include frame data with metadata
- **WHEN** config.output.include_frames=true
- **THEN** each segment includes frame_data object with:
  - image: base64-encoded pixel data
  - frame_index: frame number in video
  - timecode_hms: HH:MM:SS format
  - timecode_seconds: raw seconds

#### Scenario: Frame metadata enables direct labeling
- **WHEN** frame_data is included with timecode_hms and frame_index
- **THEN** downstream tools can display frame with proper label without correlating to segment metadata

#### Scenario: Exclude frame data by default
- **WHEN** config.output.include_frames=false (default)
- **THEN** frame data is not included in output

#### Scenario: Pretty print enabled
- **WHEN** config.output.pretty_print=true
- **THEN** JSON output is formatted with indentation and newlines

#### Scenario: Pretty print disabled
- **WHEN** config.output.pretty_print=false
- **THEN** JSON output is single-line compact format

### Requirement: JSON Output Structure

The system SHALL generate well-formed JSON output with metadata, flagged segments, and summary statistics following the documented schema.

#### Scenario: Output includes metadata
- **WHEN** output is generated for video.mp4 using config.yaml
- **THEN** output.metadata includes file, duration (HH:MM:SS), processed_at (ISO8601), config path

#### Scenario: Output includes flagged segments
- **WHEN** detections are merged and ready for output
- **THEN** output.segments is array of segments with start_time, end_time, duration_seconds, labels, description, confidence, detections[]

#### Scenario: Output includes summary
- **WHEN** output is generated
- **THEN** output.summary includes total_segments_detected, total_flagged_duration, detection_counts

#### Scenario: Empty detection list in output
- **WHEN** no detections found
- **THEN** segments array is empty, summary reflects zeros

#### Scenario: Detection object includes reasoning
- **WHEN** detections are included in output
- **THEN** each detection includes label, confidence, reasoning (if include_confidence=true)

### Requirement: Output File Writing

The system SHALL write generated JSON to a file path specified in configuration or command-line arguments.

#### Scenario: Write output to specified file
- **WHEN** user specifies --output results.json
- **THEN** system writes JSON to results.json in current directory

#### Scenario: Create output directory if missing
- **WHEN** output path is results/output/report.json and directory does not exist
- **THEN** system creates directory structure

#### Scenario: Handle file write errors
- **WHEN** output path is not writable
- **THEN** system raises descriptive error indicating path and permission issue

#### Scenario: Validate output directory exists after write
- **WHEN** writing to file completes successfully
- **THEN** file exists with valid JSON content readable by standard JSON parsers

### Requirement: Video Output with Audio

The system SHALL re-mux remediated audio back into the original video container when audio remediation is enabled.

#### Scenario: Mux remediated audio into video
- **WHEN** audio remediation is enabled and completes with remediated audio file
- **THEN** system uses ffmpeg to mux remediated audio into original video container
- **AND** output video is written to user-specified path

#### Scenario: Video codec is passed through losslessly
- **WHEN** video is muxed with remediated audio
- **THEN** video codec is copied without re-encoding (using ffmpeg `-c:v copy`)
- **AND** muxing completes quickly (no video re-encoding overhead)

#### Scenario: Audio is encoded to AAC
- **WHEN** remediated audio (WAV format) is muxed into video
- **THEN** audio is encoded to AAC format for compatibility
- **AND** sample rates are automatically handled by ffmpeg

#### Scenario: Output video file is created
- **WHEN** muxing completes successfully
- **THEN** output video file is written to specified path
- **AND** file contains both original video and remediated audio

#### Scenario: Handle muxing failure gracefully
- **WHEN** ffmpeg muxing fails (disk full, corrupted video, etc.)
- **THEN** error is logged with ffmpeg stderr
- **AND** pipeline raises exception with clear message

#### Scenario: Output video path included in results
- **WHEN** video muxing completes
- **THEN** JSON results include `output_video_path` field with path to muxed file

