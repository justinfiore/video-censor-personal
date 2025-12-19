# Tasks: Add Preview / Editing UI

## 1. UI Module Architecture & Framework Integration (CustomTkinter + python-vlc)

- [ ] 1.1 Update `requirements.txt`
  - Add python-vlc with version pin (e.g., `python-vlc>=3.0.0`)
  - CustomTkinter already present in requirements
  - Verify no version conflicts with existing dependencies

- [ ] 1.2 Create VideoPlayer abstraction layer
   - File: `video_censor_personal/ui/video_player.py`
   - Implement VideoPlayer base interface (abstract class or protocol)
   - Implement concrete VideoPlayer subclass using python-vlc
   - Methods: load(), play(), pause(), seek(), set_volume(), get_current_time(), on_time_changed()
   - Implement cleanup() for resource management
   - Add unit tests in `tests/ui/test_video_player.py` for VideoPlayer mock behavior

- [ ] 1.3 Create SegmentManager class for in-memory segment state
   - File: `video_censor_personal/ui/segment_manager.py`
   - Load segments from JSON file into list of Segment objects
   - Provide methods: get_all_segments(), toggle_allow(segment_id), save_to_json()
   - Validate JSON structure before loading (error handling)
   - Add unit tests in `tests/ui/test_segment_manager.py` for loading/saving/toggling

- [ ] 1.4 Create three-pane layout structure (CustomTkinter-based)
   - File: `video_censor_personal/ui/layout.py`
   - Create root container using CTkFrame
   - Define three regions using grid layout:
     - Left pane (20-25% width): CTkFrame for segment list container
     - Center pane (50-60% width): CTkFrame for video player container
     - Bottom pane (20-25% height): CTkFrame for segment details container
   - Implement pane wrapper classes: SegmentListPane, VideoPlayerPane, SegmentDetailsPane
   - Configure grid row/column weights for responsive layout
   - Add unit tests in `tests/ui/test_layout.py` for layout composition and resizing

## 2. Segment List Component

- [ ] 2.1 Implement SegmentListPane (CustomTkinter-based)
  - File: `video_censor_personal/ui/segment_list_pane.py`
  - Use CTkScrollableFrame as base for scrollable segment list
  - For each segment, create a CTkFrame with:
    - CTkLabel for time range (HH:MM:SS format)
    - CTkLabel for labels (comma-separated)
    - CTkLabel for allow indicator (✓) or visual marker
  - Apply CustomTkinter theme colors: green background for allowed, default for not-allowed
  - Bind click events to segment frames; emit callback with selected segment ID
  - Implement selection highlighting using CTkFrame border/background

- [ ] 2.2 Add segment filtering/search (optional initial version, but scaffold support)
  - Filter by label (e.g., show only "Profanity" segments)
  - Filter by allow status (show only not-allowed, show only allowed, show all)
  - Scaffold UI for filter controls (will be enabled in follow-up if time allows)

- [ ] 2.3 Implement selection highlighting
  - Visual indicator for currently selected segment (e.g., highlight row, border)
  - Track currently-playing segment based on video playback timestamp
  - Auto-highlight current segment as video plays
  - Handle deselection when video ends or seeks past all segments

- [ ] 2.4 Write unit tests in `tests/ui/test_segment_list_pane.py` for SegmentListPane
   - Test rendering of multiple segments
   - Test click handling
   - Test auto-highlighting during playback
   - Mock VideoPlayer for time tracking

## 3. Segment Details Panel

- [ ] 3.1 Implement SegmentDetailsPane (CustomTkinter-based)
  - File: `video_censor_personal/ui/segment_details_pane.py`
  - Create layout using CTkFrame containers
  - Use CTkLabel widgets to display:
    - Start time, end time, duration (in separate CTkLabels or combined)
    - Labels (comma-separated)
    - Confidence (as percentage)
    - Description (CTkLabel with text wrapping if possible)
  - Use CTkButton or CTkCheckBox for allow/not-allow toggle
  - Apply CustomTkinter styling for consistent appearance

- [ ] 3.2 Add "Show Details" expansion (collapsible section with CustomTkinter)
  - Use CTkButton to toggle expansion state
  - Use CTkFrame with grid layout for expandable section containing full `detections[]` array
  - Per-detection: CTkLabel for label, confidence (as percentage), reasoning
  - Collapsed by default to reduce visual clutter
  - Use CustomTkinter text styling for consistent appearance

- [ ] 3.3 Implement allow/not-allow toggle with persistence (CustomTkinter)
  - Use CTkCheckBox or CTkButton for allow/not-allow toggle
  - Apply CustomTkinter styling for visual feedback
  - Bind to event handler that calls SegmentManager.toggle_allow() and save_to_json()
  - Show brief success message ("Saved") using CTkLabel or toast-like notification
  - Show error message in CTkLabel if JSON write fails (suggest retry)
  - Disable toggle briefly while saving using state management (prevent double-clicks)

- [ ] 3.4 Write unit tests in `tests/ui/test_segment_details_pane.py` for SegmentDetailsPane
   - Test rendering with various segment configurations
   - Test allow toggle functionality
   - Test error handling (JSON save failure)
   - Mock SegmentManager and VideoPlayer

## 4. Video Player Integration

- [ ] 4.1 Implement VideoPlayerPane (CustomTkinter-based)
  - File: `video_censor_personal/ui/video_player_pane.py`
  - Create outer CTkFrame container
  - Embed python-vlc video output in inner Frame/Canvas (VLC windowed rendering requires native window ID)
  - Add control buttons using CTkButton:
    - Play/Pause button (toggle icon/label based on state)
    - Skip backward 10s button
    - Skip forward 10s button
  - Add CTkSlider for volume control (0-100%)
  - Add CTkLabel for current timecode display (HH:MM:SS.mmm format)
  - Use CustomTkinter layout and styling throughout

- [ ] 4.2 Implement timeline segment visualization (CustomTkinter/Canvas-based)
  - Create timeline using CTkCanvas (or standard Tkinter Canvas if CustomTkinter doesn't have equivalent)
  - For each segment, draw visual markers based on segment position:
    - Small rectangles/blocks at segment boundaries
    - Color-code: green for allowed, red for not-allowed, gray for neutral
  - Bind tooltip/hover events to show segment time range and labels
  - Optional: colored background regions for segment spans (if canvas performance permits)
  - Ensure timeline syncs with playback time

- [ ] 4.3 Implement video-to-UI synchronization
  - Listen to VideoPlayer.on_time_changed() callback
  - Update current timecode display
  - Update timeline position marker
  - Emit signal to SegmentListPane to update current segment highlight

- [ ] 4.4 Implement playback controls (CustomTkinter-based)
  - Use CTkButton for Play/Pause (toggle state, disable until video loaded)
  - Use CTkButton for Skip backward 10s, Skip forward 10s buttons
  - Use CTkSlider for Volume (0%-100% display, maps to 0.0-1.0 internal)
  - Bind button clicks to VideoPlayer methods
  - Apply CustomTkinter styling and theming
  - Speed controls optional (not in initial version)

- [ ] 4.5 Write unit tests in `tests/ui/test_video_player_pane.py` for VideoPlayerPane
   - Test control button functionality
   - Test timeline rendering
   - Test synchronization with VideoPlayer
   - Mock VideoPlayer for deterministic testing

## 5. Keyboard Shortcuts

- [ ] 5.1 Implement global keyboard event handling
  - Register handlers for: Space, ←, →, ↑, ↓, A, Enter
  - Ensure shortcuts work when UI elements have focus

- [ ] 5.2 Map shortcuts to actions
  - Space → play/pause
  - ← → seek -5s; → → seek +5s
  - ↑ → previous segment (move selection up in list)
  - ↓ → next segment (move selection down in list)
  - A → toggle allow on selected segment
  - Enter → jump video to selected segment start time

- [ ] 5.3 Write unit tests in `tests/ui/test_keyboard_shortcuts.py` for keyboard handling
   - Mock keyboard events
   - Verify correct action triggered for each key
   - Test edge cases (no segment selected, video not loaded)

- [ ] 5.4 Document shortcuts in help/tooltips
  - Add tooltip on buttons/controls showing keyboard shortcut
  - Optional: Create help dialog showing all shortcuts

## 6. JSON File Loading & Persistence

- [ ] 6.1 Implement file loading in SegmentManager
  - Load JSON from provided path
  - Validate schema against output-generation spec
  - Parse all segment fields: start_time, end_time, duration_seconds, labels, description, confidence, detections, allow (optional)
  - Handle missing `allow` field (default to false)
  - Error handling: file not found, invalid JSON, schema mismatch

- [ ] 6.2 Implement atomic JSON persistence
  - Write to temporary file first (same directory as original)
  - Read current content to preserve any fields changed externally (defensive)
  - Rename temp file to target (atomic on most filesystems)
  - Handle errors: disk full, permission denied, path issues
  - Log warnings if external changes detected (user info)

- [ ] 6.3 Implement application file open dialog
  - File menu: "Open Video + JSON" dialog
  - User selects JSON file
  - Application infers video path from JSON metadata `file` field
  - Load both video and segments
  - Handle missing video file (warn user, allow review-only mode)

- [ ] 6.4 Write integration tests in `tests/ui/test_file_io.py` for file I/O
   - Load sample JSON, verify all fields parsed correctly
   - Toggle allow status, verify JSON written correctly
   - Handle corrupted JSON gracefully
   - Test with large segment lists (performance)

## 7. Main Application Integration

- [ ] 7.1 Update DesktopApp to support preview-editor mode
  - File: `video_censor_personal/ui/main.py`
  - Refactor: Separate window bootstrap from layout logic
  - Add mode selection or entry points:
    - Mode 1: Bootstrap only (existing behavior, for tests)
    - Mode 2: Preview Editor (new)
  - Integrate all components (panes, segment manager, video player)
  - Wire up event signals/callbacks between components

- [ ] 7.2 Create menu bar with File, Actions menus (CustomTkinter-compatible)
  - Use standard Tkinter Menu widget (CustomTkinter uses native menu system via parent Tk root)
  - File menu: "Open Video + JSON", "Save JSON" (optional manual save), "Preferences", "Quit"
  - Actions menu: (placeholder for future features like "Process Video" from ui-full-workflow)
  - Connect menu items to appropriate handlers
  - Note: CustomTkinter uses Tkinter's native menu system; styling applied at OS level

- [ ] 7.3 Implement error dialogs and user feedback (CustomTkinter-based)
  - Use CTkToplevel for modal dialogs (error, warning, info messages)
  - Display errors if file loading fails (CTkToplevel with CTkLabel + CTkButton)
  - Show warning if JSON write fails (CTkToplevel with suggestion to retry)
  - Show info message on successful segment update (brief notification or CTkLabel in main window)
  - Log all errors to application log file
  - Use CustomTkinter styling for dialog buttons and text

- [ ] 7.4 Update __init__.py to export main entry points
  - Ensure CLI can invoke UI without knowing internal structure
  - Keep bootstrap and preview-editor modes available

## 8. Testing & Quality

- [ ] 8.1 Unit test coverage for all components (tests in `tests/ui/`)
   - VideoPlayer abstraction: 80%+ coverage (`tests/ui/test_video_player.py`)
   - SegmentManager: 90%+ coverage (`tests/ui/test_segment_manager.py`) - critical business logic
   - SegmentListPane: 70%+ coverage (`tests/ui/test_segment_list_pane.py`)
   - SegmentDetailsPane: 70%+ coverage (`tests/ui/test_segment_details_pane.py`)
   - VideoPlayerPane: 70%+ coverage (`tests/ui/test_video_player_pane.py`) - mocked video backend
   - Keyboard handling: 80%+ coverage (`tests/ui/test_keyboard_shortcuts.py`)
   - Layout composition: 70%+ coverage (`tests/ui/test_layout.py`)

- [ ] 8.2 Integration tests in `tests/ui/test_integration.py`
   - End-to-end: Load JSON, select segment, toggle allow, verify JSON file updated
   - Load video, play, pause, seek, verify timecode updates
   - Load JSON with no allow field, verify default to false
   - Error scenarios: missing file, invalid JSON, permission denied

- [ ] 8.3 Manual testing on macOS
  - Load sample video + JSON file
  - Play/pause, seek, volume, all controls functional
  - Click segments, details update, video seeks correctly
  - Toggle allow, JSON saved immediately, indicator updates
  - Keyboard shortcuts work as documented
  - Application exits cleanly without resource leaks

- [ ] 8.4 Platform testing checklist (basic)
  - **macOS**: Full testing (development platform)
  - **Windows**: Video loads and plays, UI responsive, no crashes
  - **Linux**: Video loads and plays, UI responsive, no crashes
  - Document any platform-specific workarounds needed

- [ ] 8.5 Performance testing
  - Load JSON with 50+ segments, verify list scrolls smoothly
  - Play video, verify UI remains responsive (no lag)
  - Rapidly toggle allow status, verify JSON writes don't corrupt
  - Memory usage stable after extended use

## 9. Documentation & Demo

- [ ] 9.1 Update README with preview-editor-ui section
  - Brief description of feature
  - Screenshot (if possible) or ASCII diagram
  - Instructions for launching: `python -m video_censor_personal.ui`
  - List of keyboard shortcuts

- [ ] 9.2 Create/update inline code documentation
  - Docstrings for all public classes and methods
  - Inline comments for complex logic (timeline rendering, synchronization)
  - Architecture overview in `video_censor_personal/ui/README.md`

- [ ] 9.3 Create demo video or animated GIF
  - Show loading a video + JSON
  - Navigate between segments
  - Toggle allow status
  - Keyboard shortcuts in action

- [ ] 9.4 Document framework choice decision
  - Update design.md with decision summary
  - Document any platform-specific issues or workarounds (especially VLC windowed rendering)
  - Link to VLC documentation for reference

## 10. Cleanup & Final QA

- [ ] 10.1 Code review checklist
  - PEP 8 compliance (line length, naming, imports)
  - Type hints on all functions
  - Docstrings complete and accurate
  - No hardcoded paths or magic numbers

- [ ] 10.2 Dependency audit
  - Verify python-vlc installed and functional
  - Check for conflicting versions with existing stack
  - Update requirements.txt with pins and comments
  - Run `pip install -r requirements.txt` fresh; verify import works

- [ ] 10.3 Git cleanup
  - Squash work-in-progress commits if necessary
  - Write comprehensive commit message(s)
  - Link to this proposal in commit body

- [ ] 10.4 Final validation
   - Run full test suite (unit + integration in `tests/ui/`): 100% pass
   - Manual smoke test on macOS: load video, navigate, toggle, save
   - Check code coverage: target minimum 80% overall for UI module (via `tests/ui/`)
   - Verify CLI-first design: all UI features accessible from CLI (or documented as future)

## Implementation Notes

### Parallelization Opportunities
- 1.1-1.4 (infrastructure setup) can proceed immediately
- 2.x, 3.x, 4.x (component implementation) can overlap but depend on 1.x
- 5.x, 6.x (shortcuts, persistence) can start with 2.x

### Critical Path
- 1.x (infrastructure: VideoPlayer, SegmentManager, layout) → blocks everything else
- 2.x, 3.x, 4.x (components) → can start after 1.x, overlap with each other
- 5.x, 6.x (keyboard, persistence) → can start with 2.x
- 7.x (integration) → depends on 2.x, 3.x, 4.x completion
- 8.x (testing) → can start with 2.x; completes after 7.x
- 9.x, 10.x (documentation, cleanup) → final phase

### Estimated Effort
- Infrastructure setup (1.x): 1-2 days
- Component implementation (2.x, 3.x, 4.x): 3-5 days
- Keyboard shortcuts & persistence (5.x, 6.x): 1-2 days
- Main app integration (7.x): 1 day
- Testing & polish (8.x): 2-3 days
- Documentation & cleanup (9.x, 10.x): 1 day
- **Total: 9-14 days** (single developer; faster than prototyping phase)

### Risk Mitigation Checkpoints
- After 1.x: Verify VideoPlayer abstraction works with VLC windowed mode on macOS
- After 2.x, 3.x, 4.x: Validate UI layout and component interactions before keyboard/persistence
- After 5.x, 6.x: Test keyboard shortcuts and JSON persistence end-to-end
- After 7.x: Manual testing before automated test suite
