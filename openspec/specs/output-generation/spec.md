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

The system SHALL support dual time formats (HH:MM:SS.mmm human-readable with millisecond precision and seconds machine-readable) to enable both user reports and downstream processing without losing timing precision.

#### Scenario: Format time as HH:MM:SS.mmm with milliseconds
- **WHEN** output generator formats 3661.456 seconds
- **THEN** result is "01:01:01.456"

#### Scenario: Format time as HH:MM:SS.000 for whole seconds
- **WHEN** output generator formats 3661.0 seconds
- **THEN** result is "01:01:01.000"

#### Scenario: Format time with partial milliseconds
- **WHEN** output generator formats 3661.5 seconds
- **THEN** result is "01:01:01.500"

#### Scenario: Format time as seconds
- **WHEN** output generator formats 3661.5 seconds with format="seconds"
- **THEN** result is "3661"

#### Scenario: Format edge cases
- **WHEN** formatting 0 seconds
- **THEN** HH:MM:SS.mmm format is "00:00:00.000" and seconds format is "0"

#### Scenario: Format large values
- **WHEN** formatting 36000.123 seconds (10 hours)
- **THEN** HH:MM:SS.mmm format is "10:00:00.123"

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

### Requirement: Segment Allow Override

The system SHALL support an optional `allow` property on segments to enable users to exclude false-positive detections from remediation without re-analyzing video.

#### Scenario: Segment includes allow property
- **WHEN** output is generated
- **THEN** each segment includes boolean `allow` property (defaults to false)

#### Scenario: Allowed segment default is false
- **WHEN** detection is processed
- **THEN** segment is initialized with `"allow": false` by default

#### Scenario: Manual override with allow true
- **WHEN** user edits output JSON to set `"allow": true` for false-positive segment(s)
- **THEN** system accepts the modified JSON for remediation use

#### Scenario: Allow flag excludes from remediation
- **WHEN** audio remediation processes segments with `"allow": true`
- **THEN** those segments are skipped (audio not modified)

#### Scenario: Allow flag excludes from chapters
- **WHEN** chapter generation processes segments with `"allow": true`
- **THEN** those segments do not generate chapter markers

#### Scenario: Allow-all-segments CLI flag
- **WHEN** analysis is run with `--allow-all-segments` flag
- **THEN** all detected segments are automatically set to `"allow": true` in output JSON
- **AND** flag only applies during analysis phase (no effect when using `--input-segments` for remediation)

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

### Requirement: Video Metadata Skip Chapters Output

The system SHALL support writing detection segments as chapter markers to video file metadata, with **equal native support for both MKV and MP4 formats**, enabling users to navigate flagged content directly within media players.

#### Scenario: Generate chapters from detection segments
- **WHEN** detection pipeline completes with segments detected at 00:30:45–00:30:50 (Nudity, Sexual Theme, confidence 0.92) and 01:15:30–01:15:45 (Violence, confidence 0.87)
- **THEN** system generates two skip chapters with names `"skip: Nudity, Sexual Theme [92%]"` and `"skip: Violence [87%]"` and timestamps from segment boundaries

#### Scenario: MKV format provides reliable chapter support
- **WHEN** output file extension is `.mkv`
- **THEN** system uses mkvmerge to embed chapters natively in Matroska format
- **AND** chapters are visible in all standard media players (VLC, Plex, Kodi, etc.)

#### Scenario: MP4 format provides native chapter support (UPDATED)
- **WHEN** output file extension is `.mp4`
- **THEN** system uses native MP4 container atoms with mov_text codec to embed chapters
- **AND** chapters are visible in all standard media players (VLC, Plex, Windows Media Player, Kodi, etc.)
- **AND** no warnings are logged about MP4 chapter reliability

#### Scenario: Skip chapters not written when feature disabled
- **WHEN** `output.video.metadata_output.skip_chapters.enabled=false` (default)
- **THEN** no chapter metadata is written to output video file; JSON output proceeds normally

#### Scenario: Skip chapters written when feature enabled
- **WHEN** `output.video.metadata_output.skip_chapters.enabled=true` and `--output-video /path/to/output.mkv` or `--output-video /path/to/output.mp4` provided
- **THEN** system writes detection segments as chapter markers to output video file using appropriate backend (mkvmerge for MKV, ffmpeg for MP4)

#### Scenario: Existing chapters preserved when no detections found
- **WHEN** video is processed with no detections found, but input has existing chapters
- **THEN** output video is created with original chapters intact; no new skip chapters added

#### Scenario: Confidence percentage displayed in chapter names
- **WHEN** segment has merged confidence score 0.876
- **THEN** chapter name includes `"[88%]"` (rounded to nearest integer)

### Requirement: Output Video File Requirement

The system SHALL require `--output-video` argument when skip chapters metadata output is enabled, preventing ambiguity about where the video with chapter metadata should be written.

#### Scenario: Error when skip chapters enabled without output-video
- **WHEN** config sets `skip_chapters.enabled=true` and `--output-video` argument is missing
- **THEN** system exits with error message: `"--output-video argument required when skip_chapters.enabled=true. Specify: --output-video output.mp4"`

#### Scenario: Error when output-video provided without skip chapters
- **WHEN** `--output-video` is provided but `skip_chapters.enabled=false`
- **THEN** system warns user: `"--output-video argument provided but skip_chapters.enabled=false. Output video will be ignored."` (pipeline continues, no output video written)

### Requirement: Input/Output Overwrite Protection

The system SHALL warn users when `--input` and `--output-video` paths are identical and require explicit confirmation to prevent accidental file overwriting.

#### Scenario: Warning and confirmation prompt for identical paths
- **WHEN** `--input video.mp4` and `--output-video video.mp4` are the same path
- **THEN** system displays warning: `"WARNING: Output video file matches input file. This will overwrite the original video. Continue? (y/n)"` and awaits user input

#### Scenario: Operation proceeds on user confirmation
- **WHEN** user responds `"y"` to overwrite prompt
- **THEN** chapter metadata write proceeds to overwrite input file

#### Scenario: Operation cancelled on user rejection
- **WHEN** user responds `"n"` to overwrite prompt
- **THEN** system exits without writing video or metadata; JSON output succeeds

#### Scenario: No prompt when paths differ
- **WHEN** `--input video.mp4` and `--output-video output-with-chapters.mp4` are different paths
- **THEN** system proceeds without prompting; video copy and chapter write happen normally

### Requirement: Configuration Schema for Video Metadata Output

The system SHALL support configuration of video metadata output behavior via YAML configuration under `output.video.metadata_output` section.

#### Scenario: Default configuration
- **WHEN** config omits `output.video.metadata_output`
- **THEN** system applies defaults: `skip_chapters.enabled=false`

#### Scenario: Explicit enable in config
- **WHEN** config contains:
  ```yaml
  output:
    video:
      metadata_output:
        skip_chapters:
          enabled: true
  ```
- **THEN** configuration is valid and skip chapters mode is active

#### Scenario: Config validation rejects invalid enabled values
- **WHEN** config sets `skip_chapters.enabled` to non-boolean value (e.g., "yes" or 1)
- **THEN** system rejects config with validation error

### Requirement: Chapter Metadata Formatting

The system SHALL format chapter metadata for compatibility with standard media players, using clear naming conventions with "skip:" prefix and proper timestamp boundaries.

#### Scenario: Chapter names include all labels with skip prefix
- **WHEN** segment has labels `["Nudity", "Violence", "Sexual Theme"]` with confidence 0.85
- **THEN** chapter name is exactly `"skip: Nudity, Violence, Sexual Theme [85%]"` (skip: prefix, comma-separated labels, bracketed confidence)

#### Scenario: Single-label chapter naming with skip prefix
- **WHEN** segment has single label `"Profanity"` with confidence 0.92
- **THEN** chapter name is `"skip: Profanity [92%]"`

#### Scenario: Chapter timestamps match segment boundaries
- **WHEN** segment spans 00:05:30.500 to 00:05:45.250 seconds
- **THEN** chapter start time is 330.5 seconds and end time is 345.25 seconds in ffmpeg metadata

#### Scenario: Chapters ordered chronologically
- **WHEN** segments are provided in any order
- **THEN** system sorts chapters by start time before writing to file

### Requirement: Merge Skip Chapters with Existing Chapters

The system SHALL preserve existing chapters in the input video and merge skip chapters alongside them, maintaining both original and detection-based chapter markers.

#### Scenario: Merge with existing chapters
- **WHEN** input video contains chapters "Chapter 1" (00:00:00–00:05:00), "Chapter 2" (00:05:00–00:10:00) and detections create skip chapters "skip: Nudity [85%]" (00:02:00–00:02:30) and "skip: Violence [90%]" (00:07:00–00:07:15)
- **THEN** output video contains all four chapters merged and sorted by start time: Chapter 1, skip: Nudity [85%], skip: Violence [90%], Chapter 2

#### Scenario: Extract and preserve existing chapters
- **WHEN** system processes input video with existing chapters
- **THEN** system extracts existing chapters using ffmpeg metadata before writing skip chapters, ensuring no chapter data is lost

#### Scenario: Write combined chapters to output
- **WHEN** skip chapters are merged with existing chapters
- **THEN** system writes combined chapter list to output video in chronological order

#### Scenario: No existing chapters case
- **WHEN** input video has no existing chapters
- **THEN** output video contains only skip chapters (no merging needed)

### Requirement: Graceful Failure Handling for Chapter Writing

The system SHALL handle chapter metadata write failures gracefully, logging errors while allowing JSON output to succeed and notifying user of partial failure.

#### Scenario: Log warning on mkvmerge unavailable
- **WHEN** mkvmerge tool is not installed on system
- **THEN** system logs error: `"mkvmerge not found. Please install mkvtoolnix to use chapter writing with MKV format. Continuing with JSON output only."` and continues

#### Scenario: Log warning on ffmpeg failure for MP4
- **WHEN** ffmpeg subprocess fails during MP4 metadata write (e.g., corrupted input, insufficient disk space)
- **THEN** system logs error: `"Failed to write skip chapters to <path>: <ffmpeg error>"` and continues

#### Scenario: JSON output succeeds despite chapter write failure
- **WHEN** skip chapters write fails (either MKV via mkvmerge or MP4 via ffmpeg)
- **THEN** JSON detection results are still written to `--output` file normally; user receives warning but analysis is not lost

#### Scenario: User notified of partial completion
- **WHEN** pipeline completes with chapter write failure
- **THEN** final log includes: `"Detection analysis complete. JSON output written to <path>. Warning: Skip chapters metadata could not be written to video file."`

### Requirement: Chapter Format Detection and Routing

The system SHALL automatically detect output file format from extension and route chapter writing to appropriate backend (mkvmerge for MKV, **ffmpeg with native MP4 atoms for MP4**).

#### Scenario: Auto-detect MKV format
- **WHEN** --output-video path ends with `.mkv`
- **THEN** system routes to mkvmerge implementation for native chapter support

#### Scenario: Auto-detect MP4 format (UPDATED)
- **WHEN** --output-video path ends with `.mp4`
- **THEN** system routes to ffmpeg implementation with native MP4 container atom embedding
- **AND** no warning is logged about limited MP4 support (MP4 now has equal native support)

#### Scenario: Unknown format defaults to ffmpeg
- **WHEN** --output-video path has unrecognized extension (e.g., `.avi`, `.mov`)
- **THEN** system logs warning about unsupported format and attempts ffmpeg native atom fallback

#### Scenario: Merged chapters sorted chronologically
- **WHEN** existing and skip chapters are merged
- **THEN** all chapters in output are sorted by start timestamp in ascending order

### Requirement: Bulk Allow Override via CLI Flag

The system SHALL support a `--allow-all-segments` CLI flag that automatically marks all detected segments as allowed during the analysis phase.

#### Scenario: Analysis with --allow-all-segments flag
- **WHEN** analysis is run with `--allow-all-segments` flag
- **THEN** all detected segments in the output JSON SHALL have `"allow": true`
- **AND** original detection data (`labels`, `confidence`, `description`, `detections`) MUST be preserved
- **AND** this is purely a convenience feature for pre-populating the allow status during analysis

#### Scenario: Flag has no effect during remediation
- **WHEN** `--allow-all-segments` flag is provided alongside `--input-segments` (remediation phase)
- **THEN** the flag MUST be ignored
- **AND** segments will use their existing `allow` property values from the input JSON
- **AND** system logs info: `"--allow-all-segments ignored in remediation mode; using allow values from input segments"`

#### Scenario: Use case - preview mode analysis
- **WHEN** user wants to analyze a video without intending to remediate yet
- **THEN** they can use `--allow-all-segments` during analysis to prevent accidental remediation
- **AND** they can later un-allow specific segments by setting `"allow": false` and running remediation

### Requirement: Segment Time Formatting

The system SHALL output segment timestamps with millisecond precision to preserve timing accuracy across analysis and remediation phases.

#### Scenario: Output segment times with milliseconds
- **WHEN** output is generated for segment spanning 10.456 to 15.789 seconds
- **THEN** output.segments[0].start_time is "00:00:10.456" and end_time is "00:00:15.789"

#### Scenario: Numeric timestamp fields remain unchanged
- **WHEN** output is generated
- **THEN** start_time_seconds and end_time_seconds continue to provide raw float values

### Requirement: Input Timestamp Parsing Flexibility

The system SHALL parse timestamp strings in both HH:MM:SS.mmm (with milliseconds) and HH:MM:SS (without milliseconds) formats to accommodate manual JSON editing.

#### Scenario: Parse HH:MM:SS.mmm format
- **WHEN** segment input contains start_time: "00:01:23.456"
- **THEN** system parses it as 83.456 seconds (1*60 + 23 + 0.456)

#### Scenario: Parse HH:MM:SS format without milliseconds
- **WHEN** segment input contains start_time: "00:01:23"
- **THEN** system parses it as 83.0 seconds (1*60 + 23)

#### Scenario: Parse MM:SS.mmm format (backward compatibility)
- **WHEN** segment input contains start_time: "01:23.456"
- **THEN** system parses it as 83.456 seconds

#### Scenario: Parse MM:SS format without milliseconds (backward compatibility)
- **WHEN** segment input contains start_time: "01:23"
- **THEN** system parses it as 83.0 seconds

#### Scenario: Numeric timestamps still supported
- **WHEN** segment input contains start_time_seconds: 83.456
- **THEN** system uses 83.456 directly (preferred over string format if both present)

#### Scenario: Invalid milliseconds rejected
- **WHEN** segment input contains start_time: "00:01:23.abc"
- **THEN** system raises SegmentsLoadError with clear message

### Requirement: Duration Always Derived from Times

The system SHALL calculate duration exclusively from start_time and end_time values; any duration field in input JSON is ignored during segment loading and recalculated.

#### Scenario: Duration recalculated from segment times
- **WHEN** segment is loaded with start_time: "00:00:10.500", end_time: "00:00:15.750"
- **THEN** system calculates duration_seconds as 5.25 (15.750 - 10.500)

#### Scenario: Input duration field ignored
- **WHEN** segment input contains duration_seconds: 999.0 but start_time: "00:00:10", end_time: "00:00:15"
- **THEN** system uses calculated duration of 5.0, ignoring the 999.0 value

#### Scenario: Duration never used in remediation
- **WHEN** remediation processes segments (audio or video)
- **THEN** remediation uses only start_time and end_time values; duration_seconds is informational only

### Requirement: Output Video Title Update

The system SHALL append " (Censored)" to the original video title when generating remediated output video, providing clear visual indication that a video has been processed.

#### Scenario: Simple title update
- **WHEN** output video is generated for input video with title "Family Video"
- **THEN** output video metadata includes updated title "Family Video (Censored)"

#### Scenario: Title already contains suffix
- **WHEN** input video already has title "Family Video (Censored)" and is remediated again
- **THEN** output video title becomes "Family Video (Censored)"
- We don't want to repeat the suffix if it's already there

#### Scenario: No title in input
- **WHEN** input video has no title metadata
- **THEN** output video title is set to the input filename plus "(Censored)"

#### Scenario: Title with special characters preserved
- **WHEN** input title contains special characters like quotes, accents, or unicode: "La Película: Noche & Día"
- **THEN** output title is "La Película: Noche & Día (Censored)" with all special characters preserved

### Requirement: Remediation Metadata Tags

The system SHALL write custom metadata tags to the output MP4 container to track remediation configuration, timestamp, and enabled modes. Tags use underscore separator to ensure compatibility across media players.

#### Scenario: Write config filename metadata
- **WHEN** output video is generated using config file "video-censor-analysis.yaml"
- **THEN** MP4 container includes metadata tag `video_censor_personal_config_file` with value `"video-censor-analysis.yaml"`

#### Scenario: Write segment filename metadata
- **WHEN** output video is generated using segment file "results-2025-12-29.json"
- **THEN** MP4 container includes metadata tag `video_censor_personal_segment_file` with value `"results-2025-12-29.json"`

#### Scenario: Write processed date with timezone
- **WHEN** remediation starts at 2025-12-29 14:30:45.123 in timezone PST (UTC-8)
- **THEN** MP4 container includes metadata tag `video_censor_personal_processed_date` with value `"2025-12-29T14:30:45.123-08:00"` (ISO8601 format)

#### Scenario: Write audio remediation enabled flag (true)
- **WHEN** remediation is performed with audio remediation enabled
- **THEN** MP4 container includes metadata tag `video_censor_personal_audio_remediation_enabled` with value `"true"`

#### Scenario: Write audio remediation enabled flag (false)
- **WHEN** remediation is performed with audio remediation disabled
- **THEN** MP4 container includes metadata tag `video_censor_personal_audio_remediation_enabled` with value `"false"`

#### Scenario: Write video remediation enabled flag (true)
- **WHEN** remediation is performed with video remediation enabled
- **THEN** MP4 container includes metadata tag `video_censor_personal_video_remediation_enabled` with value `"true"`

#### Scenario: Write video remediation enabled flag (false)
- **WHEN** remediation is performed with video remediation disabled
- **THEN** MP4 container includes metadata tag `video_censor_personal_video_remediation_enabled` with value `"false"`

#### Scenario: Metadata tags survive codec copying
- **WHEN** output video is generated with `-c:v copy` (video passthrough without re-encoding)
- **THEN** all metadata tags are preserved in output file

#### Scenario: Only filename, not full path
- **WHEN** remediation uses `/full/path/to/config-file.yaml`
- **THEN** metadata tag stores only `"config-file.yaml"` (basename), not the full path

#### Scenario: Metadata valid in standard media players
- **WHEN** output video is opened in standard media player (VLC, Windows Media Player, Kodi)
- **THEN** metadata tags are accessible via metadata/info views (format-dependent)

### Requirement: Debug Logging of Metadata

The system SHALL log all remediation metadata tags and their values at DEBUG level to aid troubleshooting and auditing.

#### Scenario: Log all metadata during output generation
- **WHEN** output video is being generated with metadata tags
- **THEN** system logs at DEBUG level for each tag:
  - `"Setting video metadata: video_censor_personal_config_file = 'video-censor.yaml'"`
  - `"Setting video metadata: video_censor_personal_segment_file = 'results.json'"`
  - `"Setting video metadata: video_censor_personal_processed_date = '2025-12-29T14:30:45.123-08:00'"`
  - `"Setting video metadata: video_censor_personal_audio_remediation_enabled = 'true'"`
  - `"Setting video metadata: video_censor_personal_video_remediation_enabled = 'false'"`

#### Scenario: Log title update
- **WHEN** output video title is updated
- **THEN** system logs at DEBUG level: `"Updating video title: 'Original Title' → 'Original Title (Censored)'"`

#### Scenario: Logs appear before ffmpeg execution
- **WHEN** metadata is being prepared for writing
- **THEN** DEBUG logs appear before ffmpeg command is executed, enabling users to see intended metadata before processing

#### Scenario: Log ffmpeg metadata command
- **WHEN** ffmpeg is invoked to write metadata
- **THEN** system logs at DEBUG level the ffmpeg command with metadata arguments

