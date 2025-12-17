# video-remediation Specification

## Purpose
TBD - created by archiving change add-video-segment-removal. Update Purpose after archive.
## Requirements
### Requirement: Video Blank Remediation

The system SHALL replace video frames with a solid color (default black) for detected segments when video remediation is enabled and blank mode is selected.

#### Scenario: Blank nudity segment
- **WHEN** nudity is detected at timecodes 10.5-15.0 and video remediation mode is "blank" with categories=["Nudity"]
- **THEN** video frames from 10.5 to 15.0 seconds are replaced with black screen in output video

#### Scenario: Audio continues during blank
- **WHEN** video is blanked for segment 10.5-15.0
- **THEN** audio track continues playing unchanged during blanked segment (unless separately remediated)

#### Scenario: Skip categories not in remediation list
- **WHEN** nudity (10.5-15.0) and profanity (20.0-21.0) are detected, but video remediation categories=["Nudity"]
- **THEN** nudity segment is blanked; profanity segment video is unchanged

#### Scenario: Handle overlapping detections
- **WHEN** multiple overlapping detections target same video segment
- **THEN** segment is blanked once (no double-processing or extended blank duration)

#### Scenario: Preserve video resolution and framerate
- **WHEN** video is blanked and written to file
- **THEN** output file has same resolution and framerate as input video

### Requirement: Video Cut Remediation

The system SHALL remove both video and audio for detected segments when video remediation is enabled and cut mode is selected, resulting in a shorter output video.

#### Scenario: Cut violence segment
- **WHEN** violence is detected at timecodes 30.0-35.0 and video remediation mode is "cut" with categories=["Violence"]
- **THEN** 5 seconds of video and audio from 30.0 to 35.0 are removed from output video

#### Scenario: Output duration is reduced
- **WHEN** input video is 60 seconds and 10 seconds of segments are cut
- **THEN** output video is approximately 50 seconds in duration

#### Scenario: Handle adjacent cuts
- **WHEN** segments at 10.0-15.0 and 15.5-20.0 are both cut (0.5s gap)
- **THEN** both segments are removed cleanly; intervening 0.5s is preserved

#### Scenario: Keyframe alignment handling
- **WHEN** cut boundary does not align with keyframe
- **THEN** system re-encodes at boundaries to avoid artifacts; non-cut sections maintain quality

### Requirement: Category-Based Mode Defaults

The system SHALL allow YAML configuration of default remediation mode per detection category, enabling different treatment for different content types.

#### Scenario: Configure mode per category
- **WHEN** config specifies `category_modes: { Nudity: "cut", Violence: "blank" }`
- **THEN** nudity segments default to cut mode; violence segments default to blank mode

#### Scenario: Category mode overrides global default
- **WHEN** global default is "blank" but `category_modes.Nudity: "cut"`
- **THEN** nudity segments are cut (category takes precedence over global)

#### Scenario: Multi-label segment uses most restrictive mode
- **WHEN** segment has labels ["Nudity", "Violence"] and `category_modes: { Nudity: "cut", Violence: "blank" }`
- **THEN** segment is cut (cut is more restrictive than blank)

#### Scenario: Unconfigured category uses global default
- **WHEN** segment has label "Profanity" but `category_modes` does not include Profanity
- **THEN** segment uses global default mode

#### Scenario: Empty category_modes uses global default
- **WHEN** config has `category_modes: {}` or omits it entirely
- **THEN** all segments use global default mode

### Requirement: Per-Segment Mode Override

The system SHALL allow each segment in the detection JSON to specify its own video remediation mode, overriding both category and global defaults.

#### Scenario: Segment overrides category mode
- **WHEN** category default for Nudity is "cut" but segment has `"video_remediation": "blank"`
- **THEN** that segment is blanked (segment override takes precedence)

#### Scenario: Segment overrides global mode
- **WHEN** global default is "blank" and no category mode, but segment has `"video_remediation": "cut"`
- **THEN** that segment is cut

#### Scenario: Segment uses category default when not specified
- **WHEN** segment does not have `video_remediation` field (or is null) and category mode exists
- **THEN** category mode is used

#### Scenario: Segment uses global default when no category mode
- **WHEN** segment does not have `video_remediation` field and no category mode configured
- **THEN** global default mode is used

#### Scenario: Mixed modes in same video
- **WHEN** video has segments with different modes (segment override, category default, global default)
- **THEN** each segment is processed according to its resolved mode

#### Scenario: Invalid segment mode value
- **WHEN** segment has `"video_remediation": "blur"` (invalid value)
- **THEN** system logs warning and falls back to category or global default

### Requirement: Segment Allow Override Integration

The system SHALL skip video remediation for segments marked with `"allow": true` in the detection JSON, enabling user-approved segments to pass through unchanged.

#### Scenario: Skip allowed segment
- **WHEN** segment has `"allow": true` and video remediation is enabled
- **THEN** segment video is NOT blanked or cut; passes through unchanged

#### Scenario: Remediate non-allowed segment
- **WHEN** segment does not have `"allow": true` (or has `"allow": false`)
- **THEN** segment is remediated according to its mode (segment-level or default)

#### Scenario: Allow takes precedence over segment mode
- **WHEN** segment has `"allow": true` AND `"video_remediation": "cut"`
- **THEN** segment is NOT remediated (allow takes precedence)

### Requirement: Combined Audio and Video Remediation

The system SHALL apply both audio and video remediation in a single output when both are enabled, avoiding separate processing passes.

#### Scenario: Bleep audio and blank video for same segment
- **WHEN** audio remediation (mode=bleep) and video remediation (mode=blank) are both enabled for same segment
- **THEN** output video has blanked video AND bleeped audio for that segment

#### Scenario: Different categories for audio vs video
- **WHEN** audio remediation categories=["Profanity"] and video remediation categories=["Nudity"]
- **THEN** profanity segments have audio bleeped (video unchanged); nudity segments have video blanked (audio unchanged)

#### Scenario: Single ffmpeg pass
- **WHEN** both audio and video remediation are enabled
- **THEN** remediation is performed in single ffmpeg pass (not separate passes that degrade quality)

### Requirement: Video Remediation Configuration

The system SHALL accept YAML configuration specifying video remediation default mode, categories, and options.

#### Scenario: Video remediation disabled by default
- **WHEN** user provides config without `remediation.video` section
- **THEN** video remediation is disabled; video output is unchanged (audio may still be remediated)

#### Scenario: Enable with blank as global default mode
- **WHEN** config specifies `remediation.video.enabled: true` and `mode: "blank"`
- **THEN** segments without category or segment override are blanked with black screen

#### Scenario: Enable with cut as global default mode
- **WHEN** config specifies `remediation.video.enabled: true` and `mode: "cut"`
- **THEN** segments without category or segment override are removed entirely

#### Scenario: Global default mode when not specified
- **WHEN** config specifies `remediation.video.enabled: true` but omits `mode`
- **THEN** global default mode is "blank" (safer option that preserves timing)

#### Scenario: Configure category_modes
- **WHEN** config specifies `category_modes: { Nudity: "cut", Violence: "blank" }`
- **THEN** category defaults are applied before falling back to global default

#### Scenario: Validate category_modes values
- **WHEN** config specifies `category_modes: { Nudity: "blur" }` (invalid mode)
- **THEN** system raises ConfigError during pipeline initialization

#### Scenario: Configure blank color
- **WHEN** config specifies `blank_color: "#FF0000"`
- **THEN** blanked segments show red instead of black

#### Scenario: Validate remediation config
- **WHEN** config specifies invalid mode (e.g., "blur" instead of "blank"/"cut")
- **THEN** system raises ConfigError during pipeline initialization

#### Scenario: Require output-video when enabled
- **WHEN** video remediation is enabled but `--output-video` is not provided
- **THEN** system fails fast with clear error message explaining requirement

### Requirement: Video Remediation Error Handling

The system SHALL handle video processing errors gracefully and provide clear error messages.

#### Scenario: Handle ffmpeg failure
- **WHEN** ffmpeg command fails (invalid input, missing codec, etc.)
- **THEN** error is logged with ffmpeg stderr; pipeline returns error; partial output is cleaned up

#### Scenario: Handle invalid detection timecodes
- **WHEN** detection has timecode greater than video duration
- **THEN** detection is skipped with warning; other detections remediated normally

#### Scenario: Handle unsupported codec
- **WHEN** input video uses unsupported codec
- **THEN** system logs error with codec name; suggests supported alternatives; fails gracefully

#### Scenario: Disk space check
- **WHEN** output path has insufficient disk space
- **THEN** error is detected early (before processing starts) with clear message

