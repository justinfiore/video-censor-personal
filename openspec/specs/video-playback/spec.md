# video-playback Specification

## Purpose
TBD - created by archiving change add-av-sync-tuning. Update Purpose after archive.
## Requirements
### Requirement: A/V Synchronization Offset Control

The video player SHALL accept an `av_sync_offset_ms` parameter during initialization and provide runtime methods to adjust audio-video presentation latency compensation. The system SHALL apply this offset in the render thread's drift calculation to account for differences in buffering latency between audio and video pipelines.

#### Scenario: Initialize with custom offset

- **WHEN** PyAVVideoPlayer is created with `av_sync_offset_ms=1500.0`
- **THEN** the player stores the offset and applies it to frame timing calculations
- **AND** positive offsets delay video (play video later) relative to audio
- **AND** negative offsets advance video (play video earlier) relative to audio

#### Scenario: Adjust offset at runtime

- **WHEN** `set_av_sync_offset(offset_ms)` is called during playback
- **THEN** the new offset is applied to subsequent drift calculations
- **AND** no restart or video reload is required
- **AND** playback continues uninterrupted

#### Scenario: User adjusts offset via UI

- **WHEN** user enters a value in the A/V Sync control and clicks Apply (or presses Enter)
- **THEN** the offset is updated immediately
- **AND** the UI reflects the new value
- **AND** playback adapts to the new timing without interruption

### Requirement: A/V Sync Drift Logging

The render thread SHALL log detailed A/V synchronization information to help diagnose and tune sync parameters. Logs SHALL include frame number, video time, audio time, drift amount, and running average.

#### Scenario: Log drift information

- **WHEN** a frame is rendered during playback
- **WHEN** the frame count is 1, 2, 3, or every 24 frames thereafter (≈1 second at 24fps)
- **OR** when drift exceeds ±100ms threshold
- **THEN** log format: `A/V DRIFT: frame#N video=X.XXXs audio=Y.YYYs drift=±Z.Zzms (avg=±A.Ams)`
- **AND** track running average of last 100 drift samples

#### Scenario: Analyze drift patterns

- **WHEN** user collects drift logs during playback
- **THEN** logs show oscillating drift → frames being dropped, increase queue size
- **AND** logs show growing positive drift → video falling behind, use faster resampling
- **AND** logs show stable ±20ms drift → acceptable sync, no adjustment needed

### Requirement: Default A/V Sync Offset

The system SHALL initialize with a default `av_sync_offset_ms` value suitable for typical playback scenarios.

#### Scenario: Default initialization

- **WHEN** PyAVVideoPlayer is created without explicit offset parameter
- **THEN** default offset is 1500ms (positive, delays video relative to audio)
- **AND** this compensates for typical platform presentation latency differences
- **AND** UI displays "1500" as the placeholder and initial value

### Requirement: A/V Sync Tuning Guide

Documentation SHALL provide users with step-by-step instructions for identifying and fixing sync issues based on observed drift patterns.

#### Scenario: Quick reference for common issues

- **WHEN** user observes drift pattern (stable/growing/oscillating/negative)
- **THEN** documentation maps pattern to root cause
- **AND** suggests specific parameter adjustments (offset value, queue size, resampling method)
- **AND** includes before/after measurement process

#### Scenario: Support multiple tuning strategies

- **WHEN** user has growing drift (video falling behind)
- **THEN** options include: switch to faster BILINEAR resampling, increase frame queue size, reduce video resolution
- **AND** documentation explains trade-offs (quality vs speed)

- **WHEN** user has oscillating drift (frames dropping)
- **THEN** option is to increase frame queue buffer size
- **AND** larger queue prevents render thread blocking on full queue

- **WHEN** user has stable acceptable drift (±20-50ms)
- **THEN** no tuning needed if sync sounds/looks correct

