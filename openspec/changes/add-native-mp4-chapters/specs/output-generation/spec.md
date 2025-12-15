# Spec Delta: output-generation

## MODIFIED Requirements

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
