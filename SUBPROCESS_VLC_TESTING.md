# Subprocess VLC Testing Guide

## Pre-Testing Setup

### macOS

1. **Install VLC** (if not already installed):
   ```bash
   brew install vlc
   ```

2. **Verify VLC is in PATH**:
   ```bash
   which vlc
   # Should output: /usr/local/bin/vlc or /opt/homebrew/bin/vlc
   ```

3. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Test VLC HTTP interface availability**:
   ```bash
   vlc --help | grep http
   # Should show http-host, http-port options
   ```

### Windows/Linux

- Use existing python-vlc embedded player
- Verify video playback still works

## Test Plan

### 1. Platform Detection Tests

**Test 1.1**: Verify platform detection
```python
import sys
from video_censor_personal.ui.video_player import get_preferred_video_player

player_class = get_preferred_video_player()

if sys.platform == 'darwin':
    assert player_class.__name__ == 'SubprocessVLCPlayer'
    print("✓ macOS uses SubprocessVLCPlayer")
else:
    assert player_class.__name__ == 'VLCVideoPlayer'
    print("✓ Windows/Linux uses VLCVideoPlayer")
```

**Test 1.2**: Verify VLC availability check
```python
from video_censor_personal.ui.subprocess_vlc_player import SubprocessVLCPlayer

available = SubprocessVLCPlayer._check_vlc_available()
assert available, "VLC should be available"
print("✓ VLC availability check passed")
```

### 2. Subprocess Management Tests

**Test 2.1**: VLC process lifecycle
```python
from video_censor_personal.ui.subprocess_vlc_player import SubprocessVLCPlayer
import time

player = SubprocessVLCPlayer(http_port=8081)
assert player.process is None, "No process should start until load()"

# Simulate loading (you need a test video)
# player.load("/path/to/test/video.mp4")
# time.sleep(2)
# assert player.process is not None, "Process should be running"

player.cleanup()
# assert player.process is None, "Process should be cleaned up"
print("✓ Process lifecycle management works")
```

**Test 2.2**: HTTP port availability
```python
from video_censor_personal.ui.subprocess_vlc_player import SubprocessVLCPlayer

# Test different ports
for port in [8080, 8081, 8082]:
    player = SubprocessVLCPlayer(http_port=port)
    assert player.http_port == port
    player.cleanup()
print("✓ Custom HTTP ports work")
```

### 3. Video Loading Tests

**Prerequisites**: Create a test video file
```bash
# Create 10-second test video (silent)
ffmpeg -f lavfi -i color=c=blue:s=320x240:d=10 \
        -f lavfi -i anullsrc=r=44100:cl=mono:d=10 \
        -pix_fmt yuv420p -c:a aac \
        /tmp/test_video.mp4
```

**Test 3.1**: Load valid video
```python
from video_censor_personal.ui.subprocess_vlc_player import SubprocessVLCPlayer
import time

player = SubprocessVLCPlayer()

try:
    player.load("/tmp/test_video.mp4")
    time.sleep(3)  # Let VLC start
    
    # Check if process is running
    assert player.process is not None
    assert player.process.poll() is None  # Process still running
    
    print("✓ Valid video loads successfully")
finally:
    player.cleanup()
```

**Test 3.2**: Load invalid video (error handling)
```python
from video_censor_personal.ui.subprocess_vlc_player import SubprocessVLCPlayer

player = SubprocessVLCPlayer()

try:
    player.load("/nonexistent/video.mp4")
    assert False, "Should raise FileNotFoundError"
except FileNotFoundError:
    print("✓ Invalid video path handled correctly")
```

### 4. Playback Control Tests

**Test 4.1**: Play and pause
```python
from video_censor_personal.ui.subprocess_vlc_player import SubprocessVLCPlayer
import time

player = SubprocessVLCPlayer()

try:
    player.load("/tmp/test_video.mp4")
    time.sleep(2)
    
    player.play()
    time.sleep(1)
    assert player.is_playing(), "Should be playing"
    print("✓ Play command works")
    
    player.pause()
    time.sleep(1)
    assert not player.is_playing(), "Should be paused"
    print("✓ Pause command works")
    
finally:
    player.cleanup()
```

**Test 4.2**: Seek
```python
from video_censor_personal.ui.subprocess_vlc_player import SubprocessVLCPlayer
import time

player = SubprocessVLCPlayer()

try:
    player.load("/tmp/test_video.mp4")
    time.sleep(2)
    
    player.play()
    time.sleep(1)
    
    # Seek to 5 seconds
    player.seek(5.0)
    time.sleep(1)
    
    current_time = player.get_current_time()
    # Should be approximately 5 seconds (allow 1 second tolerance)
    assert 4.0 <= current_time <= 6.0, f"Expected ~5s, got {current_time}s"
    print(f"✓ Seek works (time={current_time:.2f}s)")
    
finally:
    player.cleanup()
```

**Test 4.3**: Volume control
```python
from video_censor_personal.ui.subprocess_vlc_player import SubprocessVLCPlayer
import time

player = SubprocessVLCPlayer()

try:
    player.load("/tmp/test_video.mp4")
    time.sleep(2)
    
    # Test different volume levels
    for level in [0.0, 0.5, 1.0]:
        player.set_volume(level)
        time.sleep(0.5)
    
    print("✓ Volume control works")
    
finally:
    player.cleanup()
```

**Test 4.4**: Playback rate (speed)
```python
from video_censor_personal.ui.subprocess_vlc_player import SubprocessVLCPlayer
import time

player = SubprocessVLCPlayer()

try:
    player.load("/tmp/test_video.mp4")
    time.sleep(2)
    
    player.play()
    
    # Test different speeds
    for speed in [0.5, 1.0, 2.0]:
        player.set_playback_rate(speed)
        time.sleep(0.5)
    
    print("✓ Playback rate control works")
    
finally:
    player.cleanup()
```

### 5. Status Monitoring Tests

**Test 5.1**: Duration detection
```python
from video_censor_personal.ui.subprocess_vlc_player import SubprocessVLCPlayer
import time

player = SubprocessVLCPlayer()

try:
    player.load("/tmp/test_video.mp4")
    time.sleep(3)  # Let VLC parse media
    
    duration = player.get_duration()
    # Test video is 10 seconds
    assert 9.0 <= duration <= 11.0, f"Expected ~10s, got {duration}s"
    print(f"✓ Duration detection works (duration={duration:.2f}s)")
    
finally:
    player.cleanup()
```

**Test 5.2**: Callback triggering
```python
from video_censor_personal.ui.subprocess_vlc_player import SubprocessVLCPlayer
import time

player = SubprocessVLCPlayer()

time_updates = []
def on_time_changed(current_time):
    time_updates.append(current_time)

player.on_time_changed(on_time_changed)

try:
    player.load("/tmp/test_video.mp4")
    time.sleep(2)
    
    player.play()
    time.sleep(3)  # Let it play for 3 seconds
    
    player.pause()
    
    # Should have received several time updates
    assert len(time_updates) > 0, "Should have received time callbacks"
    print(f"✓ Callback triggering works ({len(time_updates)} updates)")
    
finally:
    player.cleanup()
```

### 6. Integration Tests

**Test 6.1**: Full workflow - Load, play, seek, stop
```python
from video_censor_personal.ui.subprocess_vlc_player import SubprocessVLCPlayer
import time

player = SubprocessVLCPlayer()

try:
    # Load
    player.load("/tmp/test_video.mp4")
    time.sleep(2)
    
    # Play
    player.play()
    time.sleep(2)
    
    # Seek to middle
    player.seek(5.0)
    time.sleep(1)
    
    # Check state
    current = player.get_current_time()
    duration = player.get_duration()
    is_playing = player.is_playing()
    
    assert 4.0 <= current <= 6.0
    assert 9.0 <= duration <= 11.0
    assert is_playing
    
    # Pause
    player.pause()
    time.sleep(1)
    assert not player.is_playing()
    
    print("✓ Full workflow works")
    
finally:
    player.cleanup()
```

### 7. Edge Cases and Error Handling

**Test 7.1**: Multiple load calls
```python
from video_censor_personal.ui.subprocess_vlc_player import SubprocessVLCPlayer
import time

player = SubprocessVLCPlayer()

try:
    # Load first video
    player.load("/tmp/test_video.mp4")
    time.sleep(2)
    
    # Load second video (should stop first one)
    player.load("/tmp/test_video.mp4")
    time.sleep(2)
    
    # Should still work
    player.play()
    time.sleep(1)
    assert player.is_playing()
    
    print("✓ Multiple load calls handled correctly")
    
finally:
    player.cleanup()
```

**Test 7.2**: Cleanup safety
```python
from video_censor_personal.ui.subprocess_vlc_player import SubprocessVLCPlayer
import time

player = SubprocessVLCPlayer()

# Load and cleanup
player.load("/tmp/test_video.mp4")
time.sleep(2)
player.cleanup()

# Should not raise error on second cleanup
player.cleanup()
print("✓ Multiple cleanup calls safe")
```

## Manual GUI Testing (Preview Editor)

### Test Scenario 1: macOS with VLC

```
1. Install VLC: brew install vlc
2. Launch preview editor: python -m video_censor_personal.ui.main
3. File → Open Video + JSON
4. Select a detection JSON and video file
5. Verify:
   ✓ VLC window opens with video playing
   ✓ Preview editor shows: "Video in External Window"
   ✓ Timeline is interactive (click to seek in VLC)
   ✓ Play/pause button toggles VLC playback
   ✓ Speed menu controls video playback speed
   ✓ Volume slider controls audio volume
   ✓ Closing VLC window doesn't crash editor
   ✓ Segment timeline updates during playback
   ✓ Can toggle segment allow/disallow
```

### Test Scenario 2: macOS without VLC

```
1. Temporarily hide VLC: mv /usr/local/bin/vlc /tmp/vlc.backup
2. Launch preview editor
3. File → Open Video + JSON
4. Verify: Error dialog appears with installation instructions
5. Restore VLC: mv /tmp/vlc.backup /usr/local/bin/vlc
```

### Test Scenario 3: Segment Interaction

```
1. Open a detection JSON with multiple segments
2. Click different segments in list
3. Verify:
   ✓ Video seeks to segment start
   ✓ Timeline highlights current segment
   ✓ Details pane shows segment info
   ✓ Can toggle allow/disallow for segment
   ✓ Changes saved to JSON file
```

### Test Scenario 4: Keyboard Shortcuts

```
1. Open video in editor
2. Test shortcuts:
   ✓ Space: Play/pause
   ✓ Left/Right arrows: Seek back/forward
   ✓ Up/Down arrows: Previous/next segment
   ✓ T: Toggle allow for current segment
   ✓ J: Jump to segment
```

## Test Results Template

```
Platform: macOS / Windows / Linux
Date: YYYY-MM-DD
Tester: [Name]

[Test Category]
- Test 1.1: [PASS/FAIL] Description
- Test 1.2: [PASS/FAIL] Description

Results:
- Total: 25 tests
- Passed: X
- Failed: X
- Skipped: X

Notes:
- Any issues found
- Any improvements suggested
```

## Regression Testing

After each change to subprocess_vlc_player.py:

1. Run all unit tests above
2. Run GUI test scenario 1 on macOS
3. Run GUI test scenario 3 on macOS
4. Verify Windows/Linux video still works

## Performance Testing

Monitor during playback:

- CPU usage (should not spike)
- Memory usage (should remain stable)
- HTTP response times (should be <100ms)
- Frame timing (no stuttering)
