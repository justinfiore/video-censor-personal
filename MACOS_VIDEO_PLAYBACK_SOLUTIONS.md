# macOS Video Playback Solutions

## Root Cause Analysis

**Issue**: Video playback doesn't work on macOS in the Preview Editor UI.

**Root Cause**: VLC's video rendering engine (OpenGL) has compatibility issues with tkinter on macOS. When VLC tries to render video output to a tkinter Canvas/Frame widget, the windowing system conflicts prevent proper frame display.

**Evidence**: In `video_player.py` line 121-124:
```python
elif sys.platform == 'darwin':
    logger.warning("Video output not supported on macOS with tkinter. Audio-only mode enabled.")
    # macOS has issues with VLC and tkinter OpenGL rendering
    # Just play audio without video output
```

The current code explicitly disables video output on macOS, only enabling audio playback.

---

## Solution Options

### Solution 1: Native AVFoundation Player (Recommended, Best UX)

**Pros:**
- Native macOS experience
- Proper fullscreen/window management
- Best performance
- No external dependencies beyond Python stdlib

**Cons:**
- Requires separate implementation for macOS only
- Needs PyObjC library

**Implementation Approach:**
1. Create `AVFoundationVideoPlayer` class that wraps AVFoundation
2. Use `AVPlayer` for playback control
3. Embed `AVPlayerViewController` into tkinter using PyObjC
4. Fall back to audio-only if AVFoundation unavailable

**Effort**: 2-3 days (moderate)

**Code Structure**:
```python
# video_censor_personal/ui/av_video_player.py
class AVFoundationVideoPlayer(VideoPlayer):
    def __init__(self, video_widget=None):
        # Use AVPlayer from AVFoundation framework
        # Embed AVPlayerViewController
        
    def load(self, video_path: str) -> None:
        # Create AVAsset and AVPlayerItem
        
    def play(self) -> None:
        # self.player.play()
```

---

### Solution 2: Native Window with Subprocess VLC (Practical Alternative)

**Pros:**
- Uses robust VLC engine
- Clean separation of concerns
- Works well across all platforms
- Relatively quick to implement

**Cons:**
- Separate window from main UI (not embedded)
- Requires process management
- Less integrated feel

**Implementation Approach:**
1. Launch VLC in windowed mode as subprocess: `vlc --fullscreen /path/to/video`
2. Use OS APIs to position/embed the VLC window (harder on macOS)
3. Communicate seek/play commands via VLC socket/HTTP interface
4. Update timeline based on callbacks

**Effort**: 1-2 days

**Code Structure**:
```python
# video_censor_personal/ui/subprocess_vlc_player.py
class SubprocessVLCPlayer(VideoPlayer):
    def __init__(self):
        self.process = None
        self.http_port = None
        
    def load(self, video_path: str) -> None:
        # Start VLC subprocess with --http-port
        # Listen to HTTP interface for status
        
    def play(self) -> None:
        # Send HTTP command to VLC
```

---

### Solution 3: ffmpeg + PIL/OpenCV Display (Lightweight Alternative)

**Pros:**
- Pure Python, no external video engine
- Simple architecture
- Cross-platform compatible
- Good for embedded preview

**Cons:**
- Software decoding (CPU-intensive)
- Can't handle all video codecs efficiently
- Slower performance
- No hardware acceleration

**Implementation Approach:**
1. Extract video frames using ffmpeg (already done for analysis)
2. Decode frames in-memory with OpenCV
3. Display decoded frames on tkinter Canvas using PhotoImage
4. Implement playback loop with timer-based frame advancement

**Effort**: 1-2 days

**Code Structure**:
```python
# video_censor_personal/ui/framebuffer_player.py
class FramebufferVideoPlayer(VideoPlayer):
    def __init__(self):
        self.frames = []
        self.current_frame_idx = 0
        self.is_playing = False
        
    def load(self, video_path: str) -> None:
        # Use ffmpeg to extract all/sample frames
        # Load into numpy arrays
        
    def play(self) -> None:
        # Start frame advancement timer
```

---

### Solution 4: Browser-Based Playback (Modern Web Approach)

**Pros:**
- HTML5 video has excellent codec support
- Modern, proven technology
- Easy to customize UI
- Cross-platform native support

**Cons:**
- Requires local web server
- Adds web framework dependency
- More moving parts

**Implementation Approach**:
1. Keep current tkinter UI for segment list/metadata
2. Launch embedded Chromium/Edge using `pywebview` or similar
3. Serve video via local HTTP server
4. Use JavaScript for playback control

**Effort**: 2-3 days (but cleaner architecture)

---

## Recommended Implementation Path

### Phase 1: Audio-Only Mode with Clear Messaging (Immediate, 0.5 days)
Update the current code to:
- Show informative message: "Video preview coming soon. Audio playback enabled."
- Extract and display video thumbnail/first frame as static image
- Keep all current functionality (timeline, seeking, segment review)

**Benefits**:
- Unblocks macOS users immediately
- Segments can still be reviewed by audio + timeline position
- Low effort, high value

**Implementation**:
```python
# In VideoPlayerPaneImpl.__init__:
if sys.platform == 'darwin':
    # Show first frame as thumbnail
    # Show "Audio-only mode" message prominently
    # Explain users can still review by listening + timeline
```

### Phase 2: ffmpeg-based Frame Display (1-2 weeks)
Add option to display video frames extracted from frames used for analysis:
- Use existing frame extraction logic
- Display frames on timeline scrub
- Show current segment's frames

**Benefits**:
- Visual reference without full playback
- Low CPU usage
- Uses existing infrastructure

### Phase 3: Full Playback (Future)
Implement one of the above solutions based on user feedback:
- If users want embedded video: AVFoundation or ffmpeg playback loop
- If users accept external windows: Subprocess VLC or browser

---

## Implementation Plan: Phase 1 (Recommended First Step)

### Files to Modify

1. **video_player.py**: Add macOS audio-only indicator
2. **video_player_pane.py**: Improve UI messaging
3. **README.md**: Update documentation about macOS limitation

### Specific Changes

#### video_player.py
```python
# Add method to check if video rendering is supported
def supports_video_rendering() -> bool:
    """Check if platform supports video rendering."""
    import sys
    return sys.platform != 'darwin'

# In VLCVideoPlayer._attach_to_widget:
if sys.platform == 'darwin':
    logger.info("macOS: Video rendering not supported. Audio-only mode.")
    # Don't call set_xwindow/set_hwnd - just return
```

#### video_player_pane.py
```python
# Enhance the audio-only message:
if sys.platform == 'darwin':
    self.audio_only_label = ctk.CTkLabel(
        self.video_container,
        text="📱 Audio-only mode on macOS\n\nPlayback and audio controls enabled. Use the timeline to navigate. See README for full video playback on other platforms.",
        text_color="white",
        font=("Arial", 12),
        wraplength=400,
        justify="center"
    )
    self.audio_only_label.pack(pady=40)
```

#### README.md
Add macOS-specific section:
```markdown
### Known Limitations

**macOS Video Playback**:
Video rendering in the Preview Editor is not supported on macOS due to VLC/tkinter compatibility.
- Audio playback and controls work normally
- Timeline navigation works normally
- Video playback is available on Linux and Windows
- Workaround: Use external video player (VLC, QuickTime) alongside Preview Editor

**Timeline & Segments Review**:
You can still fully review segments using:
1. Audio playback (listen for content)
2. Timeline position (visual marker shows playback position)
3. Frame jumping (click timeline to jump to segment)
4. External video player (open video.mp4 in separate window)
```

---

## Implementation Status: Solution 2 Complete ✓

### What Was Implemented

**Solution 2: Native Window with Subprocess VLC** has been implemented and is now ready for testing.

#### Files Created

1. **video_censor_personal/ui/subprocess_vlc_player.py** (NEW)
   - `SubprocessVLCPlayer` class implementing `VideoPlayer` interface
   - HTTP client for communicating with VLC subprocess
   - Background monitoring thread for status updates and callbacks
   - Proper process lifecycle management and error handling

#### Files Modified

1. **video_censor_personal/ui/video_player.py**
   - Added `get_preferred_video_player()` function for platform detection
   - Automatically selects `SubprocessVLCPlayer` on macOS
   - Falls back to `VLCVideoPlayer` on Windows/Linux

2. **video_censor_personal/ui/video_player_pane.py**
   - Detects subprocess player type
   - Shows "Video in External Window" message for subprocess mode
   - Skips canvas embedding for subprocess player
   - Maintains audio-only fallback for native embedding

3. **video_censor_personal/ui/preview_editor.py**
   - Uses `get_preferred_video_player()` instead of hardcoded `VLCVideoPlayer`
   - Proper error handling for player initialization

4. **requirements.txt**
   - Added `requests>=2.28.0` dependency for HTTP communication

#### Documentation

1. **SUBPROCESS_VLC_IMPLEMENTATION.md** (NEW)
   - Comprehensive architecture overview
   - Implementation details and design decisions
   - HTTP interface usage guide
   - Error handling and edge cases
   - Future improvement roadmap

2. **SUBPROCESS_VLC_TESTING.md** (NEW)
   - Complete testing guide with 7+ test categories
   - Unit test examples with code
   - Integration test scenarios
   - Manual GUI testing procedures
   - Regression testing checklist

### How It Works

1. **macOS**: Preview Editor uses `SubprocessVLCPlayer`
   - Launches VLC as subprocess with HTTP interface (port 8080)
   - Communicates via HTTP REST calls
   - Video plays in native VLC window
   - Preview Editor stays in tkinter, controls playback remotely

2. **Windows/Linux**: Preview Editor uses `VLCVideoPlayer` (unchanged)
   - Embedded video in tkinter canvas
   - Direct python-vlc bindings
   - No changes to existing functionality

### Testing Checklist (New Implementation)

- [ ] Audio plays on macOS
- [ ] Timeline scrubbing works
- [ ] Volume controls work
- [ ] Playback speed controls work
- [ ] Segment timeline displays correctly
- [ ] Clicking timeline seeks audio
- [ ] Windows/Linux video playback still works
- [ ] User message is clear and helpful

---

## Alternative: Quick Cross-Platform Fix

If you want video on ALL platforms immediately, use **ffmpeg frame display**:

1. Extract video frames (already done in analysis pipeline)
2. Display frames at correct playback speed
3. Simple, works on all platforms
4. Less resource-intensive than full codec decoding

**Effort**: 3-5 days for clean implementation

Would you like me to implement Phase 1 (immediate fix with better messaging) or start on Phase 2/3 (actual video display)?
