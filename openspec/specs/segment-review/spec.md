# segment-review Specification

## Purpose
TBD - created by archiving change expand-preview-editor-integration-tests. Update Purpose after archive.
## Requirements
### Requirement: Segment Review UI Integration Testing
The system SHALL be thoroughly tested with integration tests covering segment review workflows including segment list interaction, details pane updates, JSON persistence, and state synchronization. Integration tests SHALL verify that segment selection triggers synchronous updates across UI components, allow status changes persist atomically to JSON, and error scenarios are handled gracefully.

#### Scenario: User clicks segment in list - all panes update synchronously
- **WHEN** user clicks segment #3 in the segment list
- **THEN** segment #3 is highlighted in the list (visual selection state)
- **AND** details pane updates to display segment #3 information within 100ms
- **AND** video player seeks to segment #3 start time within 200ms
- **AND** timeline in video player shows segment #3 as selected/highlighted

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

#### Scenario: Rapid toggles - final state persisted correctly
- **WHEN** user rapidly clicks allow toggle 5 consecutive times (< 200ms between clicks)
- **THEN** final allow state matches last click
- **AND** only final state is persisted to JSON (single write, not 5 writes)
- **AND** no save operation conflicts or file corruption occurs

#### Scenario: Large segment list remains responsive
- **WHEN** segment list contains 100+ segments
- **THEN** clicking any segment updates all panes within 300ms
- **AND** scrolling list is smooth (not choppy or laggy)
- **AND** memory usage remains stable (no accumulation of widget references)

#### Scenario: Batch operation consistency - mark all profanity segments as allowed
- **WHEN** user selects "Mark all Profanity segments as allowed"
- **THEN** all profanity segments have allow=true in JSON after operation
- **AND** JSON is written atomically (single write operation)
- **AND** segment list updates all profanity markers
- **AND** video player timeline updates all profanity segment colors
- **AND** if save fails mid-operation, JSON reverts to pre-operation state

