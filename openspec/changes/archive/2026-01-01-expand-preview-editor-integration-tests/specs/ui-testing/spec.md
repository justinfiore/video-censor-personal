## ADDED Requirements

### Requirement: Integration tests for the Preview Editor UI SHALL support both headless and headed execution modes to enable CI automation and interactive debugging.

The system SHALL run all integration tests in headless mode by default (for CI/automated environments). Tests SHALL also support an optional headed mode (activated via environment variable or CLI flag) where the UI window is displayed in real-time, allowing developers to visually observe test execution for debugging purposes.

#### Scenario: Tests run headless by default (CI environment)
- **WHEN** integration tests run with `pytest tests/ui/` (no special flags)
- **THEN** tests execute in headless mode
- **AND** no UI windows are displayed
- **AND** tests complete successfully without requiring a display server
- **AND** tests can run in environments without X11/graphical subsystem (Linux CI)

#### Scenario: Tests run in headed mode with environment variable
- **WHEN** integration tests run with `PYTEST_HEADED=1 pytest tests/ui/`
- **THEN** test windows are displayed in real-time
- **AND** developer can visually observe test actions (segment clicks, state changes)
- **AND** test execution pauses slightly between actions (e.g., 500ms) for visibility
- **AND** each test displays window title identifying the test name

#### Scenario: Tests run in headed mode with CLI flag
- **WHEN** integration tests run with `pytest tests/ui/ --headed`
- **THEN** same behavior as PYTEST_HEADED=1 environment variable
- **AND** both mechanisms work interchangeably
- **AND** headed flag takes precedence if both are specified

#### Scenario: Headed mode aids debugging of visual state issues
- **WHEN** developer runs `PYTEST_HEADED=1 pytest tests/ui/test_integration.py::test_segment_selection_updates_details -v --pdb`
- **THEN** UI window displays test actions in real-time
- **AND** developer can interact with window (resize, move) to observe layout
- **AND** developer can pause test with debugger and inspect widget states
- **AND** visual debugging significantly reduces time to identify UI issues

#### Scenario: Headless mode compatible with CI/CD pipelines
- **WHEN** tests run in GitHub Actions or similar CI environment
- **THEN** no display setup required (no xvfb needed for UI tests)
- **AND** tests complete without warnings about missing display
- **AND** output includes test progress and assertion failures
- **AND** test artifacts (screenshots on failure) are captured for review

### Requirement: Integration tests for the Preview Editor UI SHALL cover file I/O workflows including JSON loading, validation, error handling, and recovery scenarios.

The system SHALL provide integration tests that validate file I/O operations in realistic user scenarios: opening JSON files with relative/absolute video paths, handling missing files, malformed JSON, and external modifications. Tests SHALL verify graceful error handling and recovery options.

#### Scenario: Open JSON file with valid video path (absolute)
- **WHEN** user opens JSON file where video path is absolute and file exists
- **THEN** JSON loads successfully
- **AND** video file is found and loaded without user interaction
- **AND** UI displays segment list, video player, and details pane
- **AND** video can play and segments display correctly

#### Scenario: Open JSON file with valid video path (relative)
- **WHEN** user opens JSON file where video path is relative (e.g., "./video.mp4")
- **THEN** system resolves path relative to JSON file directory
- **AND** video is found and loaded successfully
- **AND** relative path resolution works regardless of current working directory

#### Scenario: Open JSON with missing video file - user browses for it
- **WHEN** user opens JSON but referenced video file doesn't exist
- **THEN** error dialog shows: "Video not found at: /path/to/video.mp4"
- **AND** user is offered "Browse for video" button
- **AND** if user browses and selects correct video, app loads normally
- **AND** JSON can be reviewed in "review-only mode" (segments visible, no playback)

#### Scenario: Open JSON with missing video - user chooses review-only mode
- **WHEN** user opens JSON with missing video and selects "Review only"
- **THEN** segment list loads and displays all segments
- **AND** details pane is functional (show/hide details, toggle allow status)
- **AND** video player shows disabled message: "Video not available"
- **AND** user can still mark segments allowed/not-allowed and save to JSON

#### Scenario: Open malformed JSON - helpful error message
- **WHEN** user opens JSON file with invalid syntax (e.g., missing bracket)
- **THEN** error dialog appears: "Invalid JSON syntax: line 42"
- **AND** JSON file is not loaded
- **AND** app returns to previous state (no broken UI)

#### Scenario: Open JSON with missing required field
- **WHEN** user opens JSON missing required field like "segments" array
- **THEN** error dialog appears: "Invalid JSON schema: missing 'segments' field"
- **AND** error is specific enough for user to debug (field name included)
- **AND** file is not loaded

#### Scenario: Recent files list persists across sessions
- **WHEN** user opens 3 different JSON files in session 1, then closes app
- **THEN** file menu → Recent Files shows those 3 files
- **WHEN** user opens app again in session 2
- **THEN** recent files are still in the menu

#### Scenario: Auto-load JSON from command-line argument
- **WHEN** user launches app with command: `python -m video_censor_personal.ui.preview_editor /path/to/file.json`
- **THEN** JSON file is automatically loaded on startup
- **AND** UI displays segments and video immediately
- **AND** user does not see "Open File" dialog

#### Scenario: External JSON modification warning
- **WHEN** JSON file is modified externally (e.g., user edits in text editor) while UI session is open
- **THEN** next toggle attempt shows warning: "File modified externally. Proceed to overwrite? (y/n)"
- **AND** if user selects "No", toggle is cancelled
- **AND** if user selects "Yes", save overwrites external changes (with warning dialog again)

### Requirement: Integration tests for the Preview Editor UI SHALL cover cross-component synchronization to ensure all panes remain consistent after user actions.

The system SHALL provide integration tests that validate state consistency across the three-pane layout: when user selects segment, changes allow status, or seeks video, all dependent panes update synchronously without user-perceptible lag.

#### Scenario: Keyboard shortcut navigation updates all panes
- **WHEN** user presses down arrow key to navigate to next segment
- **THEN** segment list selection moves to next segment
- **AND** details pane updates to show next segment information
- **AND** video player seeks to next segment start time
- **AND** all updates occur within 300ms

#### Scenario: Batch allow operation updates all segments and panes
- **WHEN** user performs batch operation (mark all segments with "Profanity" label as allowed)
- **THEN** all matching segments have allow=true in memory
- **AND** JSON file is written with all changes
- **AND** segment list updates markers for all changed segments
- **AND** video player timeline updates colors for all changed segments

#### Scenario: Toggle allow multiple times - state remains consistent
- **WHEN** user toggles allow status 10 times on same segment
- **THEN** final state matches last toggle (true or false)
- **AND** JSON file contains final state
- **AND** segment list marker reflects final state
- **AND** video player timeline color matches final state
- **AND** no orphaned state or partial updates occur

### Requirement: Integration tests for the Preview Editor UI SHALL cover error conditions and recovery scenarios to ensure graceful degradation and data safety.

The system SHALL test error paths: video load failures, JSON save failures, resource exhaustion, and filesystem issues. Tests SHALL verify that errors are handled gracefully, user receives helpful feedback, and data remains in a consistent state.

#### Scenario: Video playback unavailable - UI remains functional
- **WHEN** video player is unavailable or disabled
- **THEN** video player displays: "Video playback unavailable"
- **AND** segment list, details pane, and keyboard navigation remain fully functional
- **AND** user can still toggle allow status and edit JSON

#### Scenario: JSON save fails (disk full) - state reverts with error message
- **WHEN** user toggles allow status but disk is full
- **THEN** error dialog shows: "Failed to save: disk full. Check free disk space."
- **AND** toggle visual state reverts to previous value
- **AND** JSON file on disk is unchanged
- **AND** user can retry after freeing disk space

#### Scenario: Rapid operations while save is in progress
- **WHEN** user toggles allow status (save begins) then immediately clicks another segment
- **THEN** no duplicate saves or conflicting writes occur
- **AND** final JSON state is correct

#### Scenario: User deletes JSON file while session open
- **WHEN** JSON file is deleted externally and user attempts next toggle
- **THEN** error dialog appears: "JSON file no longer exists. Reopen to reload."
- **AND** UI remains functional (can still navigate, view segments)
- **AND** toggle is cancelled

### Requirement: Integration tests for the Preview Editor UI SHALL verify window lifecycle and resource management to ensure proper cleanup and no resource leaks.

The system SHALL test application startup, shutdown, and resource cleanup. Tests SHALL verify that file handles are closed, memory is released, and the application can be reopened without issues.

#### Scenario: App startup with auto-load
- **WHEN** app is launched with JSON file argument
- **THEN** window appears and JSON is loaded
- **AND** video is loaded and playable
- **AND** all UI components are initialized

#### Scenario: App cleanup on close
- **WHEN** app is closed (via window close button)
- **THEN** video player stops (playback halted)
- **AND** file handles are closed (JSON and video files)
- **AND** window is destroyed and resources freed
- **AND** app can be reopened immediately with no issues

#### Scenario: Graceful shutdown with active operations
- **WHEN** user closes app while operations are in progress (e.g., file save)
- **THEN** operations complete or abort safely
- **AND** all resources are released
- **AND** no file corruption occurs
