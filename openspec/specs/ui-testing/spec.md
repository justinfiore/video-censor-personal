# ui-testing Specification

## Purpose
TBD - created by archiving change add-ui-testing-framework. Update Purpose after archive.
## Requirements
### Requirement: Automated UI Testing Framework
The system SHALL provide an automated testing framework for the desktop UI that enables comprehensive testing of UI components in continuous integration environments without requiring a graphical display server. The framework SHALL support testing on Windows, Linux, and macOS platforms with consistent behavior across all environments.

#### Scenario: UI tests run on Linux without display server
- **WHEN** UI tests are executed in a Linux environment without an X11 display server
- **THEN** a virtual display server (xvfb) is created automatically
- **AND** tests execute successfully with full Tkinter rendering support
- **AND** the virtual display is cleaned up after tests complete

#### Scenario: UI tests run on macOS with native display
- **WHEN** UI tests are executed on macOS
- **THEN** tests use the native Quartz display subsystem
- **AND** no additional display configuration is required
- **AND** tests execute identically to Linux headless tests

#### Scenario: UI tests run on Windows with native display
- **WHEN** UI tests are executed on Windows
- **THEN** tests use the native GDI/DirectX display subsystem
- **AND** no additional display configuration is required
- **AND** tests execute identically to Linux headless tests

#### Scenario: CI pipeline runs UI tests on every commit
- **WHEN** code is pushed to the repository
- **THEN** GitHub Actions automatically runs UI tests on all three platforms
- **AND** test results are reported in the pull request
- **AND** pipeline blocks merge if UI tests fail

### Requirement: Pytest-Based Test Fixtures
The system SHALL define reusable pytest fixtures for common UI testing patterns, enabling consistent test initialization, isolation, and cleanup across all UI tests. Fixtures SHALL manage application lifecycle, window creation, and resource cleanup.

#### Scenario: Application fixture creates isolated instance
- **WHEN** a test uses the `app` fixture
- **THEN** a fresh DesktopApp instance is created for that test
- **AND** the instance is isolated from other tests
- **AND** all resources are cleaned up after the test completes

#### Scenario: Window fixture enables window-specific testing
- **WHEN** a test uses the `app_window` fixture
- **THEN** the application window is created and available
- **AND** the window is properly initialized and visible
- **AND** the window is destroyed and cleaned up after the test completes

#### Scenario: Fixtures prevent resource leaks
- **WHEN** tests create and destroy application instances repeatedly
- **THEN** file handles, memory, and other resources are released
- **AND** no resource warnings or errors are reported
- **AND** system can sustain 100+ test cycles without resource exhaustion

### Requirement: UI Test Coverage
The system SHALL achieve a minimum of 80% code coverage for the UI module (consistent with project testing standards). Test coverage SHALL include initialization, window lifecycle, error handling, and component state management.

#### Scenario: Application initialization is tested
- **WHEN** UI tests execute
- **THEN** application initialization code is covered by tests
- **AND** initialization with various configurations is validated
- **AND** errors during initialization are caught and reported

#### Scenario: Window lifecycle is tested
- **WHEN** UI tests execute
- **THEN** window creation, display, and destruction are tested
- **AND** event handlers for window close are validated
- **AND** cleanup code is verified to execute properly

#### Scenario: Coverage report is generated in CI
- **WHEN** CI tests complete
- **THEN** coverage.xml is generated with UI module metrics
- **AND** coverage is reported as part of CI output
- **AND** coverage for ui module is >= 80%

### Requirement: Headless Display Abstraction
The system SHALL abstract away platform-specific display requirements, enabling UI tests to run identically across Windows, Linux, and macOS without code changes or conditional test execution based on platform.

#### Scenario: Tests use consistent display interface
- **WHEN** a test is written for the UI module
- **THEN** the test code does not contain platform-specific display logic
- **AND** the test runs identically on all supported platforms
- **AND** developers do not need to write separate tests per platform

#### Scenario: Virtual display is transparent to test code
- **WHEN** tests run in a headless Linux CI environment
- **THEN** xvfb is initialized automatically before test execution
- **AND** no test code is aware of xvfb or virtual display
- **AND** Tkinter rendering behaves identically to native display rendering

### Requirement: Test Markers for Selective Execution
The system SHALL provide pytest markers to categorize tests by execution requirements (display-required vs. logic-only), enabling flexible test execution patterns for different environments and development workflows.

#### Scenario: Unit tests can run without display
- **WHEN** tests marked with `@pytest.mark.unit` are executed
- **THEN** the tests do not require a display server
- **AND** tests can run in truly headless environments without xvfb
- **AND** unit tests complete faster than integration tests

#### Scenario: UI tests are marked and identified
- **WHEN** pytest is run with `pytest -m ui` argument
- **THEN** only tests marked with `@pytest.mark.ui` are executed
- **AND** unmarked tests are skipped
- **AND** developers can selectively run subsets of tests

### Requirement: GitHub Actions CI Workflow
The system SHALL define a GitHub Actions workflow that automatically runs UI tests on every commit across Windows, Linux, and macOS platforms, with appropriate display server configuration for each platform and coverage reporting.

#### Scenario: Workflow runs on all three platforms
- **WHEN** code is pushed to a branch
- **THEN** GitHub Actions triggers a test-ui job
- **AND** the job runs on ubuntu-latest, macos-latest, and windows-latest
- **AND** results are reported for all three platforms

#### Scenario: Linux runner has xvfb available
- **WHEN** tests run on the Linux runner
- **THEN** xvfb is installed automatically
- **AND** tests are wrapped with `xvfb-run -a` command
- **AND** display initialization does not cause workflow failure

#### Scenario: Workflow reports coverage
- **WHEN** UI tests complete on any platform
- **THEN** coverage.xml is generated
- **AND** coverage is reported as a job output
- **AND** merge is blocked if coverage falls below 80%

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

