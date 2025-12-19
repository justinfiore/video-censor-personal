## ADDED Requirements

### Requirement: Segment List Pane Component

The system SHALL provide a scrollable list of detected segments in a left-side pane. Each segment SHALL display time range, labels, and a visual indicator of allow/not-allow status. Clicking a segment SHALL select it and trigger updates to dependent UI components (details panel and video player).

#### Scenario: Display all segments in scrollable list
- **WHEN** user opens video + JSON file with detections
- **THEN** segment list displays all segments in chronological order
- **AND** each segment shows: time range (e.g., "00:45:30 - 00:45:35"), labels (comma-separated, e.g., "Profanity, Sexual Theme")
- **AND** list is scrollable if segments exceed visible area
- **AND** scrolling is smooth and responsive

#### Scenario: Visual indicator for allowed segments
- **WHEN** segment has `"allow": true` in JSON
- **THEN** segment list item displays checkmark (✓) or visual marker
- **AND** background color is subtle green to indicate allowed status
- **AND** not-allowed segments have default background with no marker

#### Scenario: Single-selection model
- **WHEN** user clicks a segment in the list
- **THEN** that segment is highlighted/selected
- **AND** any previously selected segment is deselected
- **AND** selected state is visually distinct (bold, background color, border)

#### Scenario: Selection triggers dependent updates
- **WHEN** user clicks segment in list
- **THEN** segment details panel (bottom) updates to show selected segment information
- **AND** video player seeks to segment start time
- **AND** segment details panel reflects current allow status

#### Scenario: Empty segment list handling
- **WHEN** user opens JSON with no detections (segments array is empty)
- **THEN** segment list displays message "No segments detected"
- **AND** details panel and video player are disabled/empty
- **AND** user can still play video for context

#### Scenario: List updates on allow status change
- **WHEN** user toggles allow status in details panel
- **THEN** segment list item immediately updates: checkmark appears/disappears, background color changes
- **AND** list does not scroll or shift (visual stability)

### Requirement: Segment Details Panel Component

The system SHALL display detailed information about the selected segment in a bottom-area pane. The panel SHALL show time range, duration, labels, confidence score, description, and detection reasoning. The panel SHALL provide a toggle to mark segments as allowed/not-allowed with immediate JSON persistence.

#### Scenario: Display segment metadata
- **WHEN** user selects a segment (or video reaches segment)
- **THEN** details panel shows:
  - Start time: "00:45:30" (HH:MM:SS)
  - End time: "00:45:35" (HH:MM:SS)
  - Duration: "5 seconds"
  - Labels: "Profanity, Sexual Theme" (comma-separated)
  - Confidence: "0.92" or "92%" (both formats)
  - Description: Full text from JSON (e.g., "Character uses explicit language in sexual context")
  
#### Scenario: Display detection reasoning
- **WHEN** user clicks "Show Details" button/toggle in details panel
- **THEN** panel expands to show full `detections[]` array:
  - For each detection: label, confidence, reasoning
  - Example: "Profanity: 0.95 confidence. Detected strong profanity in audio."
  - Example: "Sexual Theme: 0.88 confidence. Visual content combined with dialogue suggests sexual context."
- **AND** clicking again collapses the section
- **AND** collapsed by default to reduce visual clutter

#### Scenario: No segment selected state
- **WHEN** no segment is selected (application start, or segment deselected)
- **THEN** details panel displays placeholder: "Select a segment to view details"
- **AND** allow toggle is disabled

#### Scenario: Allow/Not-Allow toggle
- **WHEN** user clicks "Allow" button or checkbox in details panel
- **THEN** segment allow status is toggled: false → true or true → false
- **AND** button/checkbox visual state updates immediately (e.g., button changes color/label)
- **AND** segment list item updates: checkmark appears/disappears, background color changes
- **AND** JSON file is automatically saved (see persistence requirement)

#### Scenario: Toggle disabled while saving
- **WHEN** user clicks allow toggle
- **THEN** toggle is disabled briefly (visual feedback: grayed out or spinner)
- **AND** user cannot rapidly click toggle (prevents double-saves)
- **AND** toggle re-enabled after JSON save completes

#### Scenario: Error feedback on save failure
- **WHEN** JSON file save fails (e.g., disk full, permission denied)
- **THEN** error message displays in details panel: "Failed to save segment changes. Check disk space and permissions."
- **AND** allow status in UI reverts to previous state (user can retry)
- **AND** error is logged to application log file

### Requirement: Persistent Segment Allow Status

The system SHALL automatically save allow status changes to the JSON detection file without requiring user to click a save button. Updates SHALL be atomic to prevent file corruption.

#### Scenario: Save on allow toggle
- **WHEN** user toggles allow status in details panel
- **THEN** system writes updated segment to JSON file
- **AND** operation completes within 500ms (user perceives as immediate)
- **AND** file is persisted before returning control to user (no async ambiguity)

#### Scenario: Atomic write to prevent corruption
- **WHEN** system saves segment allow status
- **THEN** system writes to temporary file first (e.g., filename.json.tmp)
- **AND** after successful write, renames temp file to target (atomic rename)
- **AND** if process crashes mid-write, target file remains unmodified

#### Scenario: Preserve other segment fields
- **WHEN** user toggles allow status and system saves
- **THEN** saved JSON includes all original fields: start_time, end_time, duration_seconds, labels, description, confidence, detections, and updated allow status
- **AND** no fields are lost or corrupted

#### Scenario: Handle missing allow field in input JSON
- **WHEN** user opens JSON from older analysis (no allow field)
- **THEN** system defaults allow to false for all segments
- **AND** when user toggles allow on any segment, all segments now have explicit allow field in output

#### Scenario: Handle concurrent external modifications
- **WHEN** JSON file is modified externally (e.g., user edits in text editor) while UI session is open
- **THEN** system logs warning: "JSON file was modified externally. Current changes may be lost if you toggle allow status. Recommend reloading."
- **AND** subsequent save shows warning dialog: "File modified externally. Proceed to overwrite? (y/n)"
- **AND** user can choose to reload or overwrite

### Requirement: Three-Pane Layout Integration

The system SHALL organize UI components into three panes (left segment list, center video player, bottom segment details) and ensure components communicate updates through defined interfaces.

#### Scenario: Three-pane layout visible on startup
- **WHEN** preview editor window opens with video + JSON loaded
- **THEN** window displays:
  - Left pane (20-25% width): Segment list
  - Center pane (50-60% width): Video player
  - Bottom pane (20-25% height): Segment details
- **AND** panes are separated by visible borders or padding
- **AND** layout resizes responsively as window is resized

#### Scenario: Pane communication via selection
- **WHEN** user clicks segment in left pane
- **THEN** center pane (video player) seeks to segment start time
- **AND** bottom pane updates to show segment details
- **AND** all updates happen within 200ms (perceive as synchronized)

#### Scenario: Pane communication via playback
- **WHEN** video plays in center pane
- **THEN** left pane highlights currently-playing segment
- **AND** bottom pane reflects current segment details (or "No segment playing")
- **AND** updates happen continuously without UI stutter

#### Scenario: Pane communication via allow toggle
- **WHEN** user toggles allow in bottom pane
- **THEN** left pane item updates (checkmark, color)
- **AND** JSON is saved
- **AND** visual feedback is immediate

### Requirement: Keyboard Navigation

The system SHALL respond to keyboard shortcuts for rapid segment navigation and allow toggling without requiring mouse clicks.

#### Scenario: Up arrow key - previous segment
- **WHEN** user presses up arrow (↑)
- **THEN** segment list selects previous segment (moves selection up by one)
- **AND** video seeks to new segment start time
- **AND** details panel updates with new segment information
- **AND** at first segment, pressing up does nothing (no wrap-around)

#### Scenario: Down arrow key - next segment
- **WHEN** user presses down arrow (↓)
- **THEN** segment list selects next segment (moves selection down by one)
- **AND** video seeks to new segment start time
- **AND** details panel updates with new segment information
- **AND** at last segment, pressing down does nothing (no wrap-around)

#### Scenario: A key - toggle allow
- **WHEN** user presses 'A' or 'a'
- **THEN** currently selected segment's allow status is toggled
- **AND** segment list item and details panel update immediately
- **AND** JSON is saved

#### Scenario: Enter key - seek to selected segment
- **WHEN** user presses Enter while segment is selected (or current)
- **THEN** video seeks to selected segment start time
- **AND** video begins playing from that position

#### Scenario: Keyboard shortcuts work regardless of focus
- **WHEN** focus is in details panel or segment list (any widget)
- **THEN** keyboard shortcuts (↑, ↓, A, Enter) still work globally
- **AND** shortcuts do not interfere with text input (e.g., not typing in a text field)

### Requirement: File Operations - Open Video + JSON

The system SHALL provide a file open dialog enabling users to load a video file and associated JSON detection results. The JSON file path is required; the video file path is inferred from JSON metadata.

#### Scenario: Open dialog accessible from menu
- **WHEN** user clicks File menu → "Open Video + JSON"
- **THEN** file browser dialog opens
- **AND** default directory is last used location (if available)
- **AND** dialog filters for .json files

#### Scenario: Load video path from JSON metadata
- **WHEN** user selects JSON file
- **THEN** system reads JSON metadata.file field (e.g., "path/to/video.mp4")
- **AND** if relative path, resolves relative to JSON file directory
- **AND** if absolute path, uses as-is
- **AND** video file is loaded into video player

#### Scenario: Handle missing video file gracefully
- **WHEN** JSON references video file that does not exist
- **THEN** warning dialog displays: "Video file not found: <path>. You can review segment details but playback will not work. Proceed?"
- **AND** user can choose to proceed (details-only mode) or cancel

#### Scenario: Validation of JSON file format
- **WHEN** user selects JSON file
- **THEN** system validates JSON structure (contains metadata, segments array, etc.)
- **AND** if invalid, error dialog shows: "Invalid detection file format. Expected segments.json from Video Censor analysis."
- **AND** file load is cancelled

#### Scenario: Remember last used location
- **WHEN** user opens JSON file successfully
- **THEN** application remembers directory for next "Open" dialog
- **AND** preference is stored (optional: in config file or application preferences)

### Requirement: Segment Filtering (Optional Scaffold)

The system SHALL scaffold support for filtering segment list by label and allow status. Initial version may show filter controls but can be non-functional with placeholder UI.

#### Scenario: Filter by label (scaffold)
- **WHEN** filter panel is visible (or menu option available)
- **THEN** checkbox options for each label type: Nudity, Profanity, Violence, Sexual Theme, etc.
- **AND** selecting checkbox filters list to show only segments with that label
- **AND** deselecting shows all segments again
- **AND** functionality can be disabled in initial version with comment "TODO: implement filtering"

#### Scenario: Filter by allow status (scaffold)
- **WHEN** filter panel is visible
- **THEN** radio button or dropdown options: "All", "Allowed only", "Not Allowed only"
- **AND** selecting option filters list accordingly
- **AND** functionality can be disabled in initial version

#### Scenario: Combined filtering (scaffold)
- **WHEN** multiple filters are active (e.g., label=Profanity AND allow=false)
- **THEN** list shows only segments matching all criteria
- **AND** combined filtering can be scaffolded for future implementation
