## MODIFIED Requirements

### Requirement: Preview Editor Initialization

The preview editor SHALL initialize and display the UI responsively regardless of video length or segment count.

#### Scenario: Small video (15 segments) loads quickly
- **WHEN** user launches the preview editor with a 5-minute video containing 15 segments
- **THEN** the UI displays within 500ms and is immediately responsive to user interaction

#### Scenario: Large video (200+ segments) loads responsively
- **WHEN** user launches the preview editor with a 1.5-hour video containing 206 segments
- **THEN** the UI displays within 3 seconds, segment list populates within 10 seconds total, and the UI remains responsive throughout (no freezing or hangs)

#### Scenario: Very large video (500+ segments) is supported
- **WHEN** user launches the preview editor with a video containing 500+ segments
- **THEN** the preview editor handles the load gracefully, displaying UI quickly and populating the segment list without blocking the main thread

### Requirement: Segment List Rendering Performance

The segment list SHALL render efficiently and support large numbers of segments without performance degradation.

#### Scenario: Scrolling through large segment list is smooth
- **WHEN** user scrolls through a segment list with 200+ segments
- **THEN** scrolling is smooth with no lag, visible items render quickly, and selection/navigation remains responsive

#### Scenario: Segment selection works at any position in large list
- **WHEN** user selects a segment near the beginning, middle, or end of a 200+ segment list
- **THEN** the segment is selected, highlighted, and the video player seeks to the correct timestamp without delay

#### Scenario: Memory usage remains reasonable with large videos
- **WHEN** preview editor is open with a 1.5-hour video (200+ segments)
- **THEN** memory usage remains under 2GB (no memory leaks or unbounded growth)

### Requirement: Audio Loading and Playback

The audio SHALL be loaded efficiently and cached appropriately to avoid redundant operations.

#### Scenario: Audio is loaded once and reused
- **WHEN** preview editor initializes with a large video
- **THEN** audio is extracted and cached once, and subsequent playback operations reuse the cached audio without re-extracting or re-decoding

#### Scenario: Audio loading does not block segment list rendering
- **WHEN** preview editor is initializing with a large video
- **THEN** the segment list can begin rendering while audio is still being loaded in the background, and the UI remains responsive

## ADDED Requirements

### Requirement: Performance Monitoring

The system SHALL provide performance monitoring and profiling capabilities to track UI initialization and identify bottlenecks.

#### Scenario: Detailed timing logs are available for debugging
- **WHEN** preview editor initializes, all phases (JSON load, segment list creation, video initialization, audio load) are logged with timestamps
- **THEN** developers can review the logs to identify slow operations and optimize accordingly

#### Scenario: Performance metrics can be collected for regression testing
- **WHEN** integration tests run the preview editor with large videos
- **THEN** timing metrics (initial UI display, full load time, segment list population time) are collected and can be compared against baseline thresholds to detect regressions

### Requirement: Large-Scale Testing

The system SHALL be tested with large video datasets to ensure scaling correctness and prevent performance regressions.

#### Scenario: Integration tests validate performance with 200+ segment videos
- **WHEN** integration test suite runs
- **THEN** tests include scenarios with 50, 100, and 206+ segment videos, and all tests pass with timing assertions (initial display < 3s, full load < 10s)

#### Scenario: Tests prevent regressions when UI code is modified
- **WHEN** a developer modifies segment list or video player code
- **THEN** integration tests run in CI and fail if performance degrades below baseline thresholds, alerting the developer before merge

### Requirement: Optimized Logging with Debug/Trace Levels

The system SHALL minimize logging overhead during normal operation while preserving diagnostic detail for troubleshooting.

#### Scenario: Dense/chatty logs are at TRACE level only
- **WHEN** the preview editor processes a large video with default log level (INFO or DEBUG)
- **THEN** dense repetitive logs (e.g., audio frame extraction details) are NOT logged, reducing overhead and log file size by 50%+

#### Scenario: Important diagnostics remain at DEBUG level
- **WHEN** the preview editor runs at DEBUG log level
- **THEN** meaningful phase transitions are logged (JSON load complete, segment list started, audio extraction started, etc.) but frame-by-frame details are not logged

#### Scenario: TRACE level provides full diagnostic detail when needed
- **WHEN** a developer enables TRACE logging (e.g., via environment variable `VIDEO_CENSOR_TRACE=1` or logger config)
- **THEN** all dense logs (audio frames, layout calculations, widget creation details) are available for deep troubleshooting

#### Scenario: Log level can be controlled without code changes
- **WHEN** user or developer wants to change log verbosity
- **THEN** logging level can be set via environment variable or config file without requiring code modification or recompilation
