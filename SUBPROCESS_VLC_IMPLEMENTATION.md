# Subprocess VLC Player Implementation

## Overview

This document describes the implementation of Solution 2 (Subprocess VLC) for macOS video playback in the Preview Editor.

## Problem Statement

VLC's OpenGL video rendering has compatibility issues with tkinter on macOS, resulting in video output not being displayed. Previous solution was audio-only mode.

## Solution Approach

Instead of embedding VLC directly in tkinter, launch VLC as a separate subprocess process and communicate with it via HTTP interface. This:
- Avoids tkinter/OpenGL windowing conflicts on macOS
- Provides native video playback in a separate window
- Maintains all playback control capabilities (seek, play/pause, speed, volume)
- Works on Windows/Linux with embedded VLC (platform-specific behavior)

## Architecture

### Components

```
┌─────────────────────────────────────────┐
│      PreviewEditorApp (tkinter)         │
│   ┌─────────────────────────────────┐   │
│   │ VideoPlayerPaneImpl              │   │
│   │ (UI: timeline, controls)        │   │
│   └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
         │
         │ Uses VideoPlayer interface
         │
    ┌────┴──────────────────┐
    │  get_preferred_video_  │
    │  player()             │
    └────┬──────────────────┘
         │
    ┌────┴────────────────────────────┐
    │  Platform detection             │
    │  (sys.platform == 'darwin')      │
    └────┬─────────────────────────────┘
         │
    ┌────┴───────────────────────────────────────────┐
    │                                                 │
    ▼                                                 ▼
┌──────────────────────┐                    ┌──────────────────────┐
│ SubprocessVLCPlayer  │                    │  VLCVideoPlayer      │
│ (macOS)              │                    │  (Windows/Linux)     │
│                      │                    │                      │
│ ┌──────────────────┐ │                    │ ┌──────────────────┐ │
│ │ HTTP Client      │◄─┼────────────────────┼─┤ python-vlc       │ │
│ │ (requests lib)   │ │  communicate via     │ │ (direct binding) │ │
│ │                  │ │  HTTP interface      │ └──────────────────┘ │
│ └──────────────────┘ │                    │                      │
│        │             │                    │                      │
│        ▼             │                    ▼                      │
│ ┌──────────────────┐ │                ┌──────────────────┐      │
│ │ VLC Subprocess   │ │                │ python-vlc       │      │
│ │ (VLC executable) │ │                │ Library          │      │
│ │ --http-port:8080 │ │                └──────────────────┘      │
│ │                  │ │                         │                 │
│ │ Renders to       │ │                         ▼                 │
│ │ native window    │ │                    ┌──────────────┐       │
│ └──────────────────┘ │                    │ libvlc.dylib │       │
│                      │                    └──────────────┘       │
└──────────────────────┘                    └──────────────────────┘
```

### File Structure

```
video_censor_personal/ui/
├── video_player.py                 (Updated: added get_preferred_video_player())
├── subprocess_vlc_player.py         (NEW: SubprocessVLCPlayer class)
├── video_player_pane.py             (Updated: handle external window mode)
└── preview_editor.py                (Updated: use get_preferred_video_player())
```

## Implementation Details

### 1. SubprocessVLCPlayer Class

**File**: `video_censor_personal/ui/subprocess_vlc_player.py`

Implements `VideoPlayer` interface by:

#### Key Methods

- `load(video_path)`: Launches VLC subprocess with HTTP interface
- `play()`, `pause()`, `seek()`: Send HTTP commands to VLC
- `get_current_time()`, `get_duration()`: Query VLC status via HTTP
- `set_volume()`, `set_playback_rate()`: Control playback parameters
- `_monitor_vlc_status()`: Background thread polls VLC status and triggers callbacks
- `cleanup()`: Terminates subprocess and stops monitoring

#### VLC HTTP Interface Usage

Uses VLC's built-in HTTP interface to control playback:

```
GET http://127.0.0.1:8080/requests/status.json
  → Returns: {"time": 1234, "length": 5000, "state": "playing", ...}

GET http://127.0.0.1:8080/requests/status.json?command=play
  → Starts playback

GET http://127.0.0.1:8080/requests/status.json?command=seek&val=5000
  → Seeks to 5 seconds (in milliseconds)

GET http://127.0.0.1:8080/requests/status.json?command=volume&val=80
  → Sets volume to 80%
```

#### VLC Startup Command

```bash
vlc \
  --http-host 127.0.0.1 \        # Bind only to localhost
  --http-port=8080 \             # HTTP interface port
  --no-osd \                      # No on-screen display
  --fullscreen \                  # Start fullscreen
  --play-and-exit \              # Close when done
  /path/to/video.mp4
```

**Security Note**: HTTP interface only binds to 127.0.0.1 (localhost), preventing network access.

### 2. Platform Detection

**File**: `video_censor_personal/ui/video_player.py`

New function `get_preferred_video_player()`:

```python
def get_preferred_video_player() -> Type[VideoPlayer]:
    if sys.platform == 'darwin':
        # macOS: Use subprocess to avoid tkinter/OpenGL conflicts
        return SubprocessVLCPlayer
    else:
        # Windows/Linux: Use embedded python-vlc
        return VLCVideoPlayer
```

### 3. UI Updates

**File**: `video_censor_personal/ui/video_player_pane.py`

Changes:
- Detect if using `SubprocessVLCPlayer` instance
- Skip canvas embedding for subprocess player (uses native VLC window)
- Show appropriate message:
  - Subprocess mode: "🎬 Video in External Window..."
  - macOS fallback: "🔊 Audio-Only Mode..." (if subprocess unavailable)

### 4. App Initialization

**File**: `video_censor_personal/ui/preview_editor.py`

Changed:
```python
# Old
self.video_player = VLCVideoPlayer()

# New
VideoPlayerClass = get_preferred_video_player()
self.video_player = VideoPlayerClass()
```

## Behavior

### macOS

1. User clicks "Open Video + JSON"
2. PreviewEditorApp initializes `SubprocessVLCPlayer`
3. When video loads:
   - VLC subprocess launches in fullscreen window
   - HTTP interface listens on port 8080
   - Preview Editor shows: "Video in External Window..."
4. User can control from Preview Editor:
   - Play/pause buttons
   - Seek via timeline
   - Adjust speed, volume
5. User can close VLC window or Exit Preview Editor (both close VLC)

### Windows/Linux

- Uses embedded `VLCVideoPlayer` (unchanged)
- Video renders in tkinter canvas within Preview Editor

## Error Handling

### VLC Not Found

If VLC is not installed:
- `_check_vlc_available()` fails
- Raises `RuntimeError: "VLC not found in PATH. Install VLC or add to PATH."`
- User sees error dialog with installation instructions

### HTTP Communication Failures

- Status queries fail gracefully with debug logging
- Playback state cached locally (`_is_playing`, `_current_time`)
- Retries at 100ms intervals

### Subprocess Termination

- If VLC crashes/exits, monitoring stops
- Next command attempt will detect process is gone
- Cleanup handles cleanup gracefully

## Installation Requirements

### macOS

1. Install VLC (via Homebrew recommended):
   ```bash
   brew install vlc
   ```

2. Install Python dependencies:
   ```bash
   pip install requests>=2.28.0
   ```

### Windows/Linux

- No additional requirements (existing setup)
- Still need `python-vlc` for embedded player

## Testing Checklist

### Unit Tests Needed

- [ ] `SubprocessVLCPlayer._check_vlc_available()` with VLC installed/missing
- [ ] `SubprocessVLCPlayer.load()` with valid video
- [ ] `SubprocessVLCPlayer.load()` with invalid path
- [ ] `SubprocessVLCPlayer.play()`, `pause()`, `seek()`
- [ ] `SubprocessVLCPlayer.get_current_time()`, `get_duration()`
- [ ] `SubprocessVLCPlayer._monitor_vlc_status()` callback triggering
- [ ] HTTP communication error handling
- [ ] Cleanup properly terminates subprocess

### Integration Tests

- [ ] macOS: Load video → VLC window opens
- [ ] macOS: Timeline scrubbing works
- [ ] macOS: Play/pause buttons work
- [ ] macOS: Speed/volume controls work
- [ ] macOS: Close VLC → Preview Editor still functional
- [ ] macOS: Close Preview Editor → VLC terminates
- [ ] Windows/Linux: Embedded player still works
- [ ] Fallback to audio-only if VLC not found on macOS

### Manual Testing

1. **macOS with VLC**:
   - Open Preview Editor
   - Load video
   - Verify VLC window opens and plays
   - Test timeline click (seek in VLC)
   - Close VLC, verify message displays
   - Close Preview Editor, verify VLC closes

2. **macOS without VLC**:
   - Temporarily remove VLC from PATH
   - Try to open video
   - Verify clear error message

3. **Windows/Linux**:
   - Verify embedded video still works
   - Verify no regression in existing functionality

## Advantages

✅ **Solves macOS video rendering**
- No tkinter/OpenGL conflicts
- Native VLC rendering quality
- Proper fullscreen support

✅ **Maintains UI control**
- Timeline still interactive
- Playback controls work
- Speed/volume controls functional

✅ **Backward compatible**
- Windows/Linux use embedded player (no change)
- Same VideoPlayer interface
- All callbacks preserved

✅ **Graceful degradation**
- If VLC not found, shows clear error
- Can fall back to audio-only mode

## Limitations

⚠️ **Separate window**
- Video not embedded in main UI
- Users can close VLC window accidentally

⚠️ **macOS specific**
- Solution only addresses macOS
- Windows/Linux unchanged (works fine already)

⚠️ **VLC dependency**
- Requires VLC installed
- Adds system dependency

## Future Improvements

### Phase 2: Frame Display
- Use ffmpeg to extract frames during playback
- Display on timeline scrub for visual preview

### Phase 3: Better Window Management
- Try to position VLC window near Preview Editor
- Warn before closing VLC
- Minimize/restore VLC when editor minimized

### Phase 4: Full Integration
- Once tested thoroughly, apply to other platforms
- Use subprocess VLC on all platforms for consistency

## References

- [VLC HTTP Interface Documentation](https://www.videolan.org/doc/vlc-user-guide/en/ch04.html)
- [VLC Command Line Options](https://www.videolan.org/doc/vlc-user-guide/en/ch02.html)
- [Python requests Documentation](https://docs.python-requests.org/)
