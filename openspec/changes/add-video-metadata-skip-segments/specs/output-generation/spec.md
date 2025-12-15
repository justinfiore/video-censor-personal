## ADDED Requirements

### Requirement: Video Metadata Skip Chapters Output

The system SHALL support writing detection segments as chapter markers to MP4 video file metadata, enabling users to navigate flagged content directly within media players (VLC, Plex, etc.) via chapter skip functionality.

#### Scenario: Generate chapters from detection segments
- **WHEN** detection pipeline completes with segments detected at 00:30:45–00:30:50 (Nudity, Sexual Theme, confidence 0.92) and 01:15:30–01:15:45 (Violence, confidence 0.87)
- **THEN** system generates two skip chapters with names `"skip: Nudity, Sexual Theme [92%]"` and `"skip: Violence [87%]"` and timestamps from segment boundaries

#### Scenario: Skip chapters not written when feature disabled
- **WHEN** `output.video.metadata_output.skip_chapters.enabled=false` (default)
- **THEN** no chapter metadata is written to output video file; JSON output proceeds normally

#### Scenario: Skip chapters written when feature enabled
- **WHEN** `output.video.metadata_output.skip_chapters.enabled=true` and `--output-video /path/to/output.mp4` provided
- **THEN** system writes detection segments as chapter markers to output MP4 file using ffmpeg

#### Scenario: Existing chapters preserved when no detections found
- **WHEN** video is processed with no detections found, but input has existing chapters
- **THEN** output video is copied with original chapters intact; no new skip chapters added

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
- **THEN** system writes combined chapter list to output video in chronological order using ffmpeg FFMETADATA format

#### Scenario: No existing chapters case
- **WHEN** input video has no existing chapters
- **THEN** output video contains only skip chapters (no merging needed)

### Requirement: Graceful Failure Handling

The system SHALL handle metadata write failures gracefully, logging errors while allowing JSON output to succeed and notifying user of partial failure.

#### Scenario: Log warning on ffmpeg failure
- **WHEN** ffmpeg subprocess fails (e.g., corrupted input, insufficient disk space)
- **THEN** system logs error: `"Failed to write skip chapters to <path>: <ffmpeg error>"` and continues

#### Scenario: JSON output succeeds despite metadata write failure
- **WHEN** skip chapters write fails
- **THEN** JSON detection results are still written to `--output` file normally; user receives warning but analysis is not lost

#### Scenario: User notified of partial completion
- **WHEN** pipeline completes with metadata write failure
- **THEN** final log includes: `"Detection analysis complete. JSON output written to <path>. Warning: Skip chapters metadata could not be written to video file."`
