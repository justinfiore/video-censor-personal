## MODIFIED Requirements

### Requirement: Video Metadata Skip Chapters Output

The system SHALL support writing detection segments as chapter markers to video file metadata, with full native support for MKV format and limited support for MP4 format, enabling users to navigate flagged content directly within media players.

#### Scenario: Generate chapters from detection segments
- **WHEN** detection pipeline completes with segments detected at 00:30:45–00:30:50 (Nudity, Sexual Theme, confidence 0.92) and 01:15:30–01:15:45 (Violence, confidence 0.87)
- **THEN** system generates two skip chapters with names `"skip: Nudity, Sexual Theme [92%]"` and `"skip: Violence [87%]"` and timestamps from segment boundaries

#### Scenario: MKV format provides reliable chapter support
- **WHEN** output file extension is `.mkv`
- **THEN** system uses mkvmerge to embed chapters natively in Matroska format
- **AND** chapters are visible in all standard media players (VLC, Plex, Kodi, etc.)

#### Scenario: MP4 format has degraded chapter support
- **WHEN** output file extension is `.mp4`
- **THEN** system uses ffmpeg FFMETADATA format (legacy method)
- **AND** system logs warning: "MP4 containers have limited chapter support. For reliable chapter navigation, consider using .mkv format instead."
- **AND** chapters may not be visible in some players

#### Scenario: Skip chapters not written when feature disabled
- **WHEN** `output.video.metadata_output.skip_chapters.enabled=false` (default)
- **THEN** no chapter metadata is written to output video file; JSON output proceeds normally

#### Scenario: Skip chapters written when feature enabled
- **WHEN** `output.video.metadata_output.skip_chapters.enabled=true` and `--output-video /path/to/output.mkv` provided
- **THEN** system writes detection segments as chapter markers to output MKV file using mkvmerge

#### Scenario: Existing chapters preserved when no detections found
- **WHEN** video is processed with no detections found, but input has existing chapters
- **THEN** output video is created with original chapters intact; no new skip chapters added

#### Scenario: Confidence percentage displayed in chapter names
- **WHEN** segment has merged confidence score 0.876
- **THEN** chapter name includes `"[88%]"` (rounded to nearest integer)

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

The system SHALL automatically detect output file format from extension and route chapter writing to appropriate backend (mkvmerge for MKV, ffmpeg for MP4).

#### Scenario: Auto-detect MKV format
- **WHEN** --output-video path ends with `.mkv`
- **THEN** system routes to mkvmerge implementation for native chapter support

#### Scenario: Auto-detect MP4 format
- **WHEN** --output-video path ends with `.mp4`
- **THEN** system routes to ffmpeg FFMETADATA implementation with warning about limited support

#### Scenario: Unknown format defaults to ffmpeg
- **WHEN** --output-video path has unrecognized extension (e.g., `.avi`, `.mov`)
- **THEN** system logs warning about unsupported format and attempts ffmpeg fallback

#### Scenario: Merged chapters sorted chronologically
- **WHEN** existing and skip chapters are merged
- **THEN** all chapters in output are sorted by start timestamp in ascending order
