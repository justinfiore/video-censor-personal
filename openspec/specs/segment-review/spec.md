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

### Requirement: Segment Reviewed State Property
Each segment SHALL have a `reviewed` boolean property that tracks whether the user has reviewed the segment. If the `reviewed` property is absent from JSON, it SHALL default to `false`.

#### Scenario: Load JSON without reviewed property (backwards compatibility)
- **WHEN** a JSON file is loaded that does not contain `reviewed` on segments
- **THEN** all segments have `reviewed` set to `false`
- **AND** the UI displays all segments as unreviewed

#### Scenario: Load JSON with reviewed property
- **WHEN** a JSON file is loaded with segments containing `"reviewed": true`
- **THEN** those segments display as reviewed in the UI
- **AND** the reviewed checkbox is checked for those segments

#### Scenario: Save includes reviewed property
- **WHEN** the segment JSON is saved
- **THEN** each segment includes its current `reviewed` value in the output

### Requirement: Reviewed Checkbox in Segment Details
The segment details pane SHALL include a "Reviewed" checkbox that allows the user to manually toggle the reviewed state of the selected segment.

#### Scenario: User manually marks segment as reviewed
- **WHEN** user checks the "Reviewed" checkbox
- **THEN** the segment's `reviewed` property is set to `true`
- **AND** the change is queued for async persistence

#### Scenario: User manually unmarks segment as reviewed
- **WHEN** user unchecks the "Reviewed" checkbox
- **THEN** the segment's `reviewed` property is set to `false`
- **AND** the change is queued for async persistence

### Requirement: Auto-Review on Segment Selection Duration
The system SHALL automatically mark a segment as reviewed when it has been selected (clicked) for more than 1 second.

#### Scenario: Segment selected for more than 1 second
- **WHEN** user clicks on a segment
- **AND** the segment remains selected for more than 1 second
- **THEN** the segment's `reviewed` property is set to `true`
- **AND** the "Reviewed" checkbox updates to checked

#### Scenario: Segment selected for less than 1 second
- **WHEN** user clicks on a segment
- **AND** selects a different segment within 1 second
- **THEN** the first segment's `reviewed` property is NOT changed

### Requirement: Auto-Review on Full Segment Playback
The system SHALL automatically mark a segment as reviewed when video playback covers the entire timespan of the segment.

#### Scenario: Video plays through entire segment
- **WHEN** video playback starts before or at the segment start time
- **AND** playback continues past the segment end time
- **THEN** the segment's `reviewed` property is set to `true`
- **AND** the "Reviewed" checkbox updates to checked

#### Scenario: Partial segment playback
- **WHEN** video playback covers only part of a segment
- **THEN** the segment's `reviewed` property is NOT automatically changed

### Requirement: Async JSON Write Queue
The system SHALL use an asynchronous write queue for JSON persistence that batches changes and writes at most once every 5 seconds.

#### Scenario: Multiple rapid changes batched into single write
- **WHEN** user makes 10 changes within 3 seconds (reviewed, allow toggles)
- **THEN** all changes are persisted in a single JSON write
- **AND** no more than 1 file write occurs within any 5-second window

#### Scenario: Changes persisted after debounce period
- **WHEN** user makes a change
- **AND** no further changes occur for 5 seconds
- **THEN** the JSON file is written with all pending changes
- **AND** the sync status indicator shows "Synchronized"

#### Scenario: Allow changes use async queue
- **WHEN** user toggles the "Allowed" checkbox
- **THEN** the change is queued for async persistence (not written synchronously)

#### Scenario: Flush on application exit
- **WHEN** the user closes the application
- **AND** there are pending unsaved changes
- **THEN** the system performs a synchronous flush before exiting
- **AND** all pending changes are written to the JSON file

#### Scenario: Flush on interrupt signal
- **WHEN** the application receives SIGINT (Ctrl+C)
- **AND** there are pending unsaved changes
- **THEN** the system performs a synchronous flush before terminating
- **AND** all pending changes are written to the JSON file

### Requirement: Sync Status Indicator
The system SHALL display a sync status indicator in the bottom-right gutter of the UI showing whether there are pending unsaved changes.

#### Scenario: Pending changes indicator
- **WHEN** there are changes not yet written to JSON
- **THEN** an orange circle icon is displayed
- **AND** text shows "Pending Changes"

#### Scenario: Synchronized indicator
- **WHEN** all changes have been written to JSON
- **THEN** a green circle icon is displayed
- **AND** text shows "Synchronized"

#### Scenario: Status updates after write completes
- **WHEN** the async write queue flushes changes to disk
- **THEN** the indicator transitions from orange/Pending to green/Synchronized

### Requirement: Review Status Filter
The segment list pane SHALL include a filter dropdown for review status with options: "All Review Status", "Reviewed", "Unreviewed".

#### Scenario: Filter to show only unreviewed segments
- **WHEN** user selects "Unreviewed" from the review status filter
- **THEN** only segments with `reviewed: false` are displayed in the list
- **AND** pagination resets to page 1

#### Scenario: Filter to show only reviewed segments
- **WHEN** user selects "Reviewed" from the review status filter
- **THEN** only segments with `reviewed: true` are displayed in the list

#### Scenario: Filter shows all segments by default
- **WHEN** the UI loads
- **THEN** the review status filter defaults to "All Review Status"
- **AND** all segments are visible regardless of reviewed state

### Requirement: Bulk Mark Reviewed/Unreviewed Actions
The segment list filter frame SHALL include "Mark All Reviewed" and "Mark All Unreviewed" buttons that apply to all currently filtered segments.

#### Scenario: Mark all filtered segments as reviewed
- **WHEN** user clicks "Mark All Reviewed"
- **THEN** all segments matching current filters have `reviewed` set to `true`
- **AND** the segment list updates to reflect the new reviewed state
- **AND** a single write is queued to persist all changes

#### Scenario: Mark all filtered segments as unreviewed
- **WHEN** user clicks "Mark All Unreviewed"
- **THEN** all segments matching current filters have `reviewed` set to `false`
- **AND** the segment list updates to reflect the new reviewed state
- **AND** a single write is queued to persist all changes

#### Scenario: Bulk action respects active filters
- **WHEN** label filter is set to "Profanity"
- **AND** user clicks "Mark All Reviewed"
- **THEN** only segments with "Profanity" label are marked as reviewed
- **AND** segments with other labels are unchanged

