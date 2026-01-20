# Tasks: Edit Segments

## 1. Data Layer & Segment Manager Updates

- [x] 1.1 Add `update_segment()` method to `SegmentManager`
  - Parameters: segment_id, new_start_time, new_end_time, new_labels
  - Recalculate duration_seconds from new times
  - Queue change for async persistence
  - File: `video_censor_personal/ui/segment_manager.py`

- [x] 1.2 Add `duplicate_segment()` method to `SegmentManager`
  - Create new segment with unique ID (UUID)
  - Copy all properties from source segment
  - Insert new segment after source in segment list
  - Queue change for async persistence
  - Return the new segment

- [x] 1.3 Add `delete_segment()` method to `SegmentManager`
  - Remove segment from segment list by ID
  - Queue change for async JSON persistence
  - Return the next segment in list (for auto-selection) or None

- [x] 1.4 Add unit tests for segment manager updates
  - Test `update_segment()` with valid times
  - Test `update_segment()` rejects invalid times (start > end)
  - Test `duplicate_segment()` creates independent copy
  - Test `delete_segment()` removes segment and returns next
  - File: `tests/ui/test_segment_manager.py`

## 2. Edit Mode State Management

- [x] 2.1 Create `EditModeController` class
  - File: `video_censor_personal/ui/edit_mode_controller.py`
  - Properties: `is_editing`, `original_segment` (for cancel), `edited_start`, `edited_end`, `edited_labels`
  - Methods: `enter_edit_mode(segment)`, `cancel()`, `apply()`, `update_start()`, `update_end()`, `add_label()`, `remove_label()`
  - Emit callbacks for state changes

- [x] 2.2 Integrate `EditModeController` into `PreviewEditorApp`
  - Wire up callbacks between controller and UI components
  - Pass controller reference to details pane and video player pane
  - File: `video_censor_personal/ui/preview_editor.py`

- [x] 2.3 Add unit tests for `EditModeController`
  - Test enter/cancel restores original values
  - Test enter/apply persists changes
  - Test scrubber-cannot-cross validation
  - File: `tests/ui/test_edit_mode_controller.py`

## 3. Segment Details Pane Updates

- [x] 3.1 Add "Edit Segment", "Duplicate Segment", and "Delete Segment" buttons
  - Add buttons below checkbox row
  - "Edit Segment" enters edit mode
  - "Duplicate Segment" duplicates and enters edit mode for new segment
  - "Delete Segment" shows confirmation dialog, then deletes
  - File: `video_censor_personal/ui/segment_details_pane.py`

- [x] 3.2 Implement delete confirmation dialog
  - Show modal dialog: "Delete this segment? This cannot be undone."
  - "Cancel" closes dialog, no action
  - "Delete" removes segment and auto-selects next segment

- [x] 3.3 Add edit mode UI elements
  - Replace buttons with "Cancel" and "Apply" when in edit mode
  - Add distinct border/background to indicate edit mode
  - Add "Editing Segment" label header

- [x] 3.4 Add start/end time text inputs
  - Two CTkEntry fields for MM:SS.mmm format
  - Real-time validation (highlight red on invalid)
  - Bidirectional sync with scrubbers via controller

- [x] 3.5 Add label editing UI
  - Display labels as removable chips (CTkButton with X icon)
  - "Add Label" button opens dropdown with known labels
  - Labels sourced from all segments in current file

- [x] 3.6 Add unit tests for segment details pane edit mode
  - Test edit mode button visibility toggling
  - Test time input validation
  - Test label chip add/remove
  - Test delete confirmation dialog
  - File: `tests/ui/test_segment_details_pane.py`

## 4. Timeline & Scrubber Implementation

- [x] 4.1 Add zoom range state to `TimelineCanvas`
  - Add `visible_start_time` and `visible_end_time` properties
  - Modify rendering to use visible range instead of full duration
  - Add `set_zoom_range(start, end)` method
  - File: `video_censor_personal/ui/video_player_pane.py`

- [x] 4.2 Implement scrubber UI elements
  - Add two draggable handles (start/end) as canvas items
  - Style: distinct from playhead, e.g., triangular markers
  - Only visible when `is_editing` is True

- [x] 4.3 Implement scrubber drag handling
  - Bind mouse events (Button-1, B1-Motion, ButtonRelease-1)
  - Calculate time from x position using visible range
  - Snap to 100ms increments
  - Enforce minimum segment duration (100ms)
  - Call controller `update_start()` / `update_end()`

- [x] 4.4 Implement timeline expansion on scrubber edge drag
  - Detect when scrubber reaches edge of visible range
  - On release, expand visible range by 30s in that direction
  - Clamp to video bounds

- [x] 4.5 Implement "Play Segment" button
  - Add button to VideoPlayerPane (visible only in edit mode)
  - On click: seek to edited start time, then play
  - Track `edit_mode_start_time` and `edit_mode_end_time` properties

- [x] 4.6 Implement playback stop at segment end in edit mode
  - On time update, check if current_time >= edit_mode_end_time
  - If so, pause playback

- [x] 4.7 Add unit tests for timeline/scrubber
  - Test zoom range rendering
  - Test scrubber drag calculations
  - Test snap to 100ms
  - Test scrubber cannot cross
  - Test timeline expansion
  - File: `tests/ui/test_video_player_pane.py`

## 5. Integration & Wiring

- [x] 5.1 Wire edit mode entry from details pane button
  - Click "Edit Segment" → controller.enter_edit_mode(segment)
  - Controller notifies video player pane to show scrubbers and zoom
  - Controller notifies details pane to show edit UI

- [x] 5.2 Wire scrubber changes to time inputs
  - Scrubber drag → controller.update_start/end → details pane updates text inputs

- [x] 5.3 Wire time input changes to scrubbers
  - Time input change → controller.update_start/end → timeline updates scrubber position

- [x] 5.4 Wire duplicate segment flow
  - Click "Duplicate Segment" → segment_manager.duplicate_segment()
  - Auto-enter edit mode for new segment
  - Segment list refreshes to show new segment

- [x] 5.5 Wire apply/cancel
  - Cancel → controller.cancel() → restore original values, exit edit mode
  - Apply → controller.apply() → segment_manager.update_segment(), exit edit mode

## 6. Integration Tests

- [x] 6.1 Create integration test file
  - File: `tests/ui/test_edit_segments_integration.py`

- [x] 6.2 Test edit mode workflow
  - Enter edit mode, modify times, apply, verify segment updated
  - Enter edit mode, modify times, cancel, verify segment unchanged

- [x] 6.3 Test duplicate segment workflow
  - Duplicate segment, verify new segment created with same properties
  - Edit duplicated segment, verify original unchanged

- [x] 6.4 Test scrubber interaction
  - Drag scrubbers, verify time inputs update
  - Type in time inputs, verify scrubbers move

- [x] 6.5 Test label editing
  - Add label, verify segment labels updated
  - Remove label, verify segment labels updated

## 7. Documentation & Cleanup

- [x] 7.1 Update TESTING_GUIDE.md with edit mode test cases
- [x] 7.2 Add inline documentation for EditModeController
- [x] 7.3 Update keyboard shortcuts help dialog (if applicable)
  - N/A: Edit mode uses button clicks, not keyboard shortcuts
- [x] 7.4 Run full test suite and fix any regressions
  - 1172 tests pass (25 new integration tests added)

---

## Implementation Notes

### Parallelization Opportunities
- 1.x (data layer) and 2.x (controller) can proceed in parallel
- 3.x (details pane) depends on 2.x
- 4.x (timeline) depends on 2.x
- 5.x (wiring) depends on 3.x and 4.x

### Critical Path
1. `EditModeController` (2.1) - central coordination
2. Timeline zoom & scrubbers (4.1, 4.2, 4.3) - core visual interaction
3. Details pane edit UI (3.1, 3.2, 3.3) - buttons and inputs
4. Integration wiring (5.x) - connect everything

### Estimated Effort
- Data layer updates (1.x): 0.5 days
- Edit mode controller (2.x): 1 day
- Details pane updates (3.x): 1.5 days
- Timeline & scrubbers (4.x): 2 days
- Integration wiring (5.x): 1 day
- Integration tests (6.x): 1 day
- Documentation (7.x): 0.5 days
- **Total: 7-8 days**
