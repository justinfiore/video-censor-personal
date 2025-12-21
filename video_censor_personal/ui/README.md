# Video Censor Personal - UI Architecture

## Overview

The UI module provides a desktop graphical interface for reviewing and editing video detection segments. Built with CustomTkinter and python-vlc, it offers a modern, cross-platform experience for segment review workflows.

## Architecture

### Component Hierarchy

```
PreviewEditorApp (main application)
├── SegmentListPane (left sidebar)
│   ├── Filter controls (label, allow status)
│   └── Scrollable segment list items
├── VideoPlayerPane (center/top)
│   ├── Video canvas (VLC integration)
│   ├── Timeline with segment visualization
│   └── Playback controls (play/pause, skip, speed, volume)
└── SegmentDetailsPane (bottom)
    ├── Segment metadata display
    ├── Allow/not-allow toggle
    └── Expandable detections list
```

### Core Components

#### 1. **VideoPlayer** (`video_player.py`)
- Abstract base class defining video playback interface
- `VLCVideoPlayer`: Concrete implementation using python-vlc
- Methods: `load()`, `play()`, `pause()`, `seek()`, `set_volume()`, `get_current_time()`
- Platform-specific windowed rendering (xwindow/hwnd/nsview)

#### 2. **SegmentManager** (`segment_manager.py`)
- Loads segments from JSON detection files
- In-memory state management
- Atomic JSON persistence with temp file + rename
- Batch operations: `batch_set_allow_by_label()`
- Filtering: `get_segments_by_label()`, `get_segments_by_allow_status()`

#### 3. **SegmentListPane** (`segment_list_pane.py`)
- Scrollable list of segments with filtering
- Visual indicators: ✓ (allowed) / ✗ (not allowed)
- Auto-highlighting during playback
- Navigation: `select_next_segment()`, `select_previous_segment()`

#### 4. **SegmentDetailsPane** (`segment_details_pane.py`)
- Displays segment metadata (time range, labels, confidence, description)
- Allow/not-allow toggle with immediate persistence
- Expandable detections section showing individual detection details
- Error handling for save failures

#### 5. **VideoPlayerPane** (`video_player_pane.py`)
- Video player with embedded VLC canvas
- Timeline canvas with color-coded segment markers
  - Green: allowed segments
  - Red: not-allowed segments
- Controls: play/pause, skip ±10s, speed (0.5x - 2.0x), volume
- Timecode display: `HH:MM:SS.mmm` format
- Time update callback for UI synchronization

#### 6. **KeyboardShortcuts** (`keyboard_shortcuts.py`)
- Global keyboard event handling
- Shortcuts:
  - `Space`: Play/pause
  - `←/→`: Seek ±5 seconds
  - `↑/↓`: Previous/next segment
  - `A`: Toggle allow on selected segment
  - `Enter`: Jump to selected segment start time

### Data Flow

```
1. File Loading:
   User → Open File Dialog → JSON Path
   → SegmentManager.load_from_json()
   → VideoPlayerPane.load_video()
   → SegmentListPane.load_segments()

2. Segment Selection:
   User Click on Segment
   → SegmentListPane (highlight)
   → SegmentDetailsPane (display details)
   → VideoPlayerPane (seek to start time)

3. Allow Toggle:
   User Toggle Allow
   → SegmentDetailsPane._on_allow_toggled()
   → SegmentManager.set_allow() + save_to_json()
   → SegmentListPane.update_segment_allow()
   → VideoPlayerPane.update_timeline_segments()

4. Video Playback:
   Timer Update (100ms interval)
   → VideoPlayer.get_current_time()
   → SegmentListPane.highlight_segment_at_time()
   → TimelineCanvas.set_current_time()
```

## Threading & Performance

- **No worker threads**: All operations run on main/UI thread
- **Timer-based updates**: 100ms polling for video time updates
- **Lazy rendering**: Only visible segments rendered in scrollable pane
- **Atomic writes**: Temp file + rename for JSON persistence

## Platform-Specific Notes

### macOS
- VLC requires ARM64 build for Apple Silicon
- Windowed rendering uses `set_nsobject(widget.winfo_id())`

### Windows
- Windowed rendering uses `set_hwnd(widget.winfo_id())`

### Linux
- Windowed rendering uses `set_xwindow(widget.winfo_id())`

## Testing Strategy

- **Unit tests**: Mock-based testing for all components
- **Integration tests**: End-to-end JSON load/save workflows
- **Test coverage target**: 80% overall for UI module
- **Platform testing**: Full manual testing on macOS, basic testing on Windows/Linux

## Entry Points

### Launch Preview Editor
```bash
python -m video_censor_personal.ui.preview_editor
```

Or programmatically:
```python
from video_censor_personal.ui import launch_preview_editor
launch_preview_editor()
```

### Launch Basic Bootstrap (for testing)
```python
from video_censor_personal.ui import launch_app
launch_app()
```

## Future Enhancements

Potential improvements tracked in separate change proposals:
- Full workflow UI (run analysis + remediation from UI)
- Video export directly from UI
- Undo/redo for segment changes
- Segment comments/notes
- Playlist support (multiple videos)
