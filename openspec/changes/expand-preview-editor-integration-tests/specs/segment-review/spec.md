## MODIFIED Requirements

### Requirement: The system SHALL provide a scrollable list of detected segments in a left-side pane. Each segment SHALL display time range, labels, and a visual indicator of allow/not-allow status. Clicking a segment SHALL select it and trigger updates to dependent UI components (details panel and video player).

The system SHALL provide a scrollable list of detected segments in a left-side pane. Each segment SHALL display time range, labels, and a visual indicator of allow/not-allow status. Clicking a segment SHALL select it and trigger updates to dependent UI components (details panel and video player). **Integration testing SHALL verify that segment selection triggers synchronous updates to both the details pane and video player without user-perceptible delay.**

#### Scenario: User clicks segment in list - all panes update synchronously
- **WHEN** user clicks segment #3 in the segment list
- **THEN** segment #3 is highlighted in the list (visual selection state)
- **AND** details pane updates to display segment #3 information within 100ms
- **AND** video player seeks to segment #3 start time within 200ms
- **AND** timeline in video player shows segment #3 as selected/highlighted

#### Scenario: Video playback progresses - segment list auto-highlights
- **WHEN** video is playing and reaches time 00:45:32 (during segment #3)
- **THEN** segment #3 is automatically highlighted in the segment list
- **AND** highlighting occurs within 300ms of video time update
- **AND** segment list auto-scrolls to keep highlighted segment visible

#### Scenario: Large segment list remains responsive
- **WHEN** segment list contains 100+ segments
- **THEN** clicking any segment updates all panes within 300ms
- **AND** scrolling list is smooth (not choppy or laggy)
- **AND** memory usage remains stable (no accumulation of widget references)

#### Scenario: Multiple rapid segment clicks
- **WHEN** user rapidly clicks 5 different segments (< 100ms between clicks)
- **THEN** final selected segment is correct
- **AND** details pane shows final segment (not intermediate segments)
- **AND** video player seeks to final segment start time
- **AND** no duplicate seeks or update events occur

### Requirement: The system SHALL display detailed information about the selected segment in a bottom-area pane. The panel SHALL show time range, duration, labels, confidence score, description, and detection reasoning. The panel SHALL provide a toggle to mark segments as allowed/not-allowed with immediate JSON persistence.

The system SHALL display detailed information about the selected segment in a bottom-area pane. The panel SHALL show time range, duration, labels, confidence score, description, and detection reasoning. The panel SHALL provide a toggle to mark segments as allowed/not-allowed with immediate JSON persistence. **Integration testing SHALL verify that allow/not-allow state changes persist to JSON file atomically and remain consistent across all UI components.**

#### Scenario: User toggles allow status - JSON persists and UI updates everywhere
- **WHEN** user clicks "Allow" toggle for selected segment
- **THEN** toggle visual state updates immediately (checked/unchecked)
- **AND** JSON file is written atomically within 500ms
- **AND** segment list marker updates (checkmark appears/disappears)
- **AND** video player timeline segment color changes (green for allowed, red for not-allowed)
- **AND** if user reloads JSON file, allow state matches what was toggled

#### Scenario: Error during JSON save - state reverts with user notification
- **WHEN** user toggles allow status but JSON write fails (disk full, permission denied)
- **THEN** error dialog appears with explanation: "Failed to save: disk full"
- **AND** toggle visual state reverts to previous value (not showing new state)
- **AND** segment list marker reverts to previous state
- **AND** JSON file on disk is unchanged (remains in safe state)
- **AND** user can retry the toggle operation

#### Scenario: Toggle allow rapidly (5+ times)
- **WHEN** user rapidly clicks allow toggle 5 consecutive times (< 200ms between clicks)
- **THEN** final allow state matches last click
- **AND** only final state is persisted to JSON (single write, not 5 writes)
- **AND** no save operation conflicts or file corruption occurs

#### Scenario: Expand detections section - shows reasoning for each label
- **WHEN** user clicks "Show Details" button in details pane
- **THEN** detections array expands showing each detection label, confidence, reasoning
- **AND** expansion contains text like "Profanity: 0.95 confidence. Detected strong profanity in audio."
- **AND** clicking again collapses the section

### Requirement: The system SHALL automatically save allow status changes to the JSON detection file without requiring user to click a save button. Updates SHALL be atomic to prevent file corruption.

The system SHALL automatically save allow status changes to the JSON detection file without requiring user to click a save button. Updates SHALL be atomic to prevent file corruption. **Integration testing SHALL verify atomicity: failed saves do not corrupt file, and crashes during save do not leave JSON in inconsistent state.**

#### Scenario: Save succeeds despite external JSON modification detection
- **WHEN** JSON file was modified externally and user attempts to toggle allow
- **THEN** warning dialog appears: "File modified externally. Overwrite? (y/n)"
- **AND** if user selects "Yes", save proceeds and overwrites external changes
- **AND** if user selects "No", toggle is cancelled and state reverts
- **AND** JSON file remains in consistent state either way

#### Scenario: Batch operation consistency - mark all profanity segments as allowed
- **WHEN** user selects "Mark all Profanity segments as allowed" (future feature)
- **THEN** all profanity segments have allow=true in JSON after operation
- **AND** JSON is written atomically (single write operation)
- **AND** segment list updates all profanity markers
- **AND** video player timeline updates all profanity segment colors
- **AND** if save fails mid-operation, JSON reverts to pre-operation state
