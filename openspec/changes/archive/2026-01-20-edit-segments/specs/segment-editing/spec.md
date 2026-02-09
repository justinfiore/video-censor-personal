# segment-editing Specification

## ADDED Requirements

### Requirement: Edit Segment Mode
The system SHALL provide an "Edit Segment" mode that allows users to modify the start time, end time, and labels of a selected segment. Edit mode SHALL be visually distinct from the default view mode.

#### Scenario: Enter edit mode via button
- **WHEN** user clicks "Edit Segment" button in the segment details pane
- **THEN** the UI enters edit mode for the selected segment
- **AND** the timeline zooms to show segment ± 30 seconds
- **AND** start/end scrubber controls appear on the timeline
- **AND** start/end time text inputs appear in the details pane
- **AND** "Edit Segment" button is replaced with "Cancel" and "Apply" buttons

#### Scenario: Edit mode visual distinction
- **WHEN** the UI is in edit mode
- **THEN** the segment details pane has a distinct border color (e.g., blue/highlight)
- **AND** the timeline background changes to indicate edit mode
- **AND** a "Editing Segment" label is displayed

#### Scenario: Cancel discards changes
- **WHEN** user clicks "Cancel" button while in edit mode
- **THEN** all changes to start time, end time, and labels are discarded
- **AND** segment reverts to its original values
- **AND** UI returns to view mode

#### Scenario: Apply persists changes
- **WHEN** user clicks "Apply" button while in edit mode
- **THEN** changes to start time, end time, and labels are saved to the segment
- **AND** segment duration_seconds is recalculated
- **AND** change is queued for async JSON persistence
- **AND** UI returns to view mode

### Requirement: Timeline Zoom in Edit Mode
The system SHALL zoom the timeline to show the segment's time range plus 30 seconds on each side when in edit mode.

#### Scenario: Timeline zooms on edit mode entry
- **WHEN** user enters edit mode for a segment at 01:00 - 01:10
- **THEN** the timeline shows range 00:30 - 01:40 (±30s)
- **AND** the segment is visually centered in the timeline

#### Scenario: Timeline clamps to video bounds
- **WHEN** user enters edit mode for a segment at 00:10 - 00:20 (near video start)
- **THEN** the timeline shows range 00:00 - 00:50 (clamped at 0)

#### Scenario: Timeline expands when scrubber reaches edge
- **WHEN** user drags the end scrubber to the right edge of the visible timeline
- **AND** releases the scrubber
- **THEN** an additional 30 seconds is added to the visible timeline end
- **AND** the timeline redraws to show the expanded range

### Requirement: Scrubber Controls for Time Adjustment
The system SHALL provide draggable scrubber controls on the timeline for adjusting segment start and end times.

#### Scenario: Drag start scrubber
- **WHEN** user drags the start scrubber to position 00:45
- **THEN** the segment's start time updates to 00:45 in real-time
- **AND** the start time text input updates to show "00:45.000"
- **AND** the scrubber position reflects the new time

#### Scenario: Drag end scrubber
- **WHEN** user drags the end scrubber to position 01:30
- **THEN** the segment's end time updates to 01:30 in real-time
- **AND** the end time text input updates to show "01:30.000"

#### Scenario: Scrubbers cannot cross
- **WHEN** user attempts to drag start scrubber past end scrubber
- **THEN** the start scrubber stops at 100ms before the end scrubber position
- **AND** minimum segment duration of 100ms is maintained

#### Scenario: Scrubber snap to 100ms increments
- **WHEN** user drags scrubber to position 01:23.456
- **THEN** the scrubber snaps to 01:23.400 or 01:23.500 (nearest 100ms)

### Requirement: Time Input Text Fields
The system SHALL provide text input fields for start time and end time that display in MM:SS.mmm format and allow manual entry.

#### Scenario: Text inputs display current times
- **WHEN** segment with start 01:23.400 and end 01:45.600 is being edited
- **THEN** start time input shows "01:23.400"
- **AND** end time input shows "01:45.600"

#### Scenario: Manual time entry updates scrubbers
- **WHEN** user types "02:00.000" in the end time input
- **AND** presses Enter or tabs away
- **THEN** the end scrubber moves to position 02:00.000
- **AND** the segment end time is updated

#### Scenario: Invalid time entry shows error
- **WHEN** user types "abc" in the time input
- **THEN** the input field is highlighted in red
- **AND** no change is applied to the segment
- **AND** a validation message appears: "Invalid time format"

#### Scenario: Time entry clamps to valid range
- **WHEN** user enters start time greater than end time
- **THEN** the input is rejected with error highlight
- **AND** message shows: "Start time must be before end time"

### Requirement: Play Segment Button
The system SHALL provide a "Play Segment" button in edit mode that plays the video from the current start time to the current end time.

#### Scenario: Play segment from start to end
- **WHEN** user clicks "Play Segment" button in edit mode
- **THEN** the playhead moves to the current segment start time
- **AND** video playback begins from the start time
- **AND** playback automatically stops when reaching the segment end time

#### Scenario: Play segment reflects edited times
- **WHEN** user has adjusted start time to 01:00 and end time to 01:15 via scrubbers
- **AND** user clicks "Play Segment"
- **THEN** playback starts at 01:00 and stops at 01:15

#### Scenario: Play Segment button only visible in edit mode
- **WHEN** user is in edit mode
- **THEN** the "Play Segment" button is visible
- **WHEN** user is NOT in edit mode
- **THEN** the "Play Segment" button is hidden

### Requirement: Playback Stops at Segment End in Edit Mode
The system SHALL stop video playback when the playhead reaches the segment end time while in edit mode.

#### Scenario: Playback stops at segment end
- **WHEN** user is in edit mode with segment end time 01:15
- **AND** user plays video (via Play Segment or regular play)
- **THEN** playback stops when reaching 01:15

#### Scenario: Normal playback in view mode
- **WHEN** user is NOT in edit mode
- **THEN** playback continues to end of video as normal

### Requirement: Duplicate Segment
The system SHALL allow users to duplicate a segment, creating a new segment with the same properties that can be edited independently.

#### Scenario: Duplicate segment creates copy
- **WHEN** user clicks "Duplicate Segment" button
- **THEN** a new segment is created with same start_time, end_time, labels, and description
- **AND** the new segment gets a unique ID
- **AND** the new segment is inserted after the original in the segment list
- **AND** the UI enters edit mode for the new segment

#### Scenario: Duplicated segment is independent
- **WHEN** user edits the duplicated segment's times
- **THEN** the original segment's times are unchanged

### Requirement: Delete Segment
The system SHALL allow users to delete a segment from the segment list with confirmation.

#### Scenario: Delete segment with confirmation
- **WHEN** user clicks "Delete Segment" button in segment details pane
- **THEN** a confirmation dialog appears: "Delete this segment? This cannot be undone."
- **AND** dialog has "Cancel" and "Delete" buttons

#### Scenario: Confirm delete removes segment
- **WHEN** user clicks "Delete" in the confirmation dialog
- **THEN** the segment is removed from the segment list
- **AND** the change is queued for async JSON persistence
- **AND** the segment details pane shows "No segment selected"
- **AND** the next segment in the list is auto-selected (if any)

#### Scenario: Cancel delete keeps segment
- **WHEN** user clicks "Cancel" in the confirmation dialog
- **THEN** the segment remains in the list
- **AND** no changes are made

#### Scenario: Delete Segment button always visible
- **WHEN** a segment is selected
- **THEN** the "Delete Segment" button is visible (in both view and edit mode)

### Requirement: Edit Segment Labels
The system SHALL allow users to add and remove labels from a segment while in edit mode.

#### Scenario: View current labels as editable chips
- **WHEN** user is in edit mode
- **THEN** segment labels are displayed as removable chips/tags
- **AND** each chip has an X button to remove the label

#### Scenario: Remove label from segment
- **WHEN** user clicks X on a label chip
- **THEN** the label is removed from the segment's labels list
- **AND** the chip disappears from the UI

#### Scenario: Add label to segment
- **WHEN** user clicks "Add Label" button
- **THEN** a dropdown appears with available labels (from existing segments)
- **AND** user can select a label to add
- **AND** the label is added to the segment's labels list
