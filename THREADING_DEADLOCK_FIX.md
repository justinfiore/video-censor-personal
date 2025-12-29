# Video Playback Threading Deadlock Fix

## Problem
When clicking the Play button on macOS, the UI would freeze with a beachball spinner and hang indefinitely.

## Root Causes

### 1. **Unsafe Tkinter Canvas Updates from Worker Threads**
- The render thread was calling `canvas.delete()` and `canvas.create_image()` directly
- Tkinter is NOT thread-safe and requires all GUI operations on the main thread
- This caused deadlocks between the render thread and main UI thread

### 2. **CPU-Intensive Audio Decoding Blocking Critical Paths**
- Audio initialization (`_initialize_audio_player()`) decoded ALL audio frames synchronously
- This was happening on the main thread during `play()`, blocking UI responsiveness
- Later, even when moved to decode thread, it blocked video frame decoding

### 3. **Render Thread Not Yielding Control**
- The `_decode_frames()` method was in an infinite loop without yielding
- This caused thread starvation and prevented proper thread scheduling
- Combined with audio decoding, made the UI completely unresponsive

### 4. **Container Access Race Conditions**
- PyAV containers are NOT thread-safe
- Audio and video streams were being accessed from multiple threads without synchronization
- This could cause buffer corruption or decode failures

## Solutions Implemented

### 1. **Thread-Safe Canvas Updates via Queue**
**File**: `video_censor_personal/ui/pyav_video_player.py`

- Added `_canvas_update_queue` for non-blocking communication from render thread to main thread
- Created `_update_canvas_on_main_thread()` method that runs on main thread via `after()`
- Render thread now only converts frames to PhotoImage and queues an update signal
- Main event loop (via `_start_update_timer` in video_player_pane.py) polls the queue and updates canvas

**Before**:
```python
# From render thread - UNSAFE!
self._canvas.delete("all")
self._canvas.create_image(...)
```

**After**:
```python
# From render thread - thread-safe queue signal
self._canvas_update_queue.put(True, block=False)

# From main thread (via after)
def _update_canvas_on_main_thread(self):
    self._canvas.delete("all")
    self._canvas.create_image(...)
```

### 2. **Async Audio Decoding at Load Time**
**File**: `video_censor_personal/ui/pyav_video_player.py`

- Moved audio decoding from `play()` to `load()` method
- Audio decoding now happens in a separate daemon thread during load (non-blocking)
- Decode thread only starts audio playback if audio was successfully loaded
- Prevents blocking on `play()` button click

**Before**:
```python
def play(self):
    with self._frame_lock:
        self._initialize_audio_player()  # BLOCKS!
        self._decode_thread.start()
```

**After**:
```python
def load(self, video_path):
    # ... load video ...
    audio_thread = threading.Thread(target=self._initialize_audio_player, daemon=True)
    audio_thread.start()  # Non-blocking

def play(self):
    # Just start playback if audio already loaded
    self._audio_player.play()
```

### 3. **Decode Thread Yields Control**
**File**: `video_censor_personal/ui/pyav_video_player.py`

- Modified `_decode_frames()` to decode in batches and yield control
- Added `time.sleep(0.001)` every 3 frames to allow thread scheduling
- Prevents CPU starvation and allows other threads to run

**Before**:
```python
def _decode_frames(self):
    for packet in self._container.demux(self._video_stream):
        for frame in packet.decode():
            # ... infinite loop without yielding ...
```

**After**:
```python
def _decode_frames(self):
    frames_decoded = 0
    for packet in self._container.demux(self._video_stream):
        for frame in packet.decode():
            # ...
            frames_decoded += 1
            if frames_decoded >= 3:
                time.sleep(0.001)  # Yield to scheduler
                frames_decoded = 0
```

### 4. **First Frame Rendering in Background**
**File**: `video_censor_personal/ui/pyav_video_player.py`

- Changed from `_render_first_frame()` (blocking) to `_render_first_frame_bg()` (async)
- Renders first frame in a daemon thread after canvas is realized
- Waits up to 5 seconds for canvas dimensions before attempting render

### 5. **Fixed Audio Playback Timing**
**File**: `video_censor_personal/ui/audio_player.py`

- Corrected sample frame calculation for multichannel audio
- Fixed array indexing for both 1D and 2D audio arrays
- Properly handles mono vs stereo audio duration

## Testing Recommendations

1. **Click Play button** - Should return immediately, no beachball
2. **Video should start playing** - Within 1-2 seconds (audio decode happens in background)
3. **Seek operations** - Should be smooth, no UI blocking
4. **Long videos** - Audio decode shouldn't block anything
5. **Pause/Resume** - Should be instant

## Performance Impact

- **Faster UI response**: No blocking on audio decode
- **Smoother playback**: Threads yield control properly
- **Higher CPU usage initially**: Audio decode at load time (unavoidable for long videos)
- **Lower memory**: Frames are decoded on-demand, not pre-loaded

## Files Modified

1. `video_censor_personal/ui/pyav_video_player.py`
   - Added `_canvas_update_queue`
   - Modified `play()` to remove audio initialization
   - Modified `load()` to async decode audio
   - Modified `_decode_thread_main()` to start audio playback
   - Modified `_decode_frames()` to yield control
   - Changed `_render_first_frame()` to `_render_first_frame_bg()`
   - Added `_update_canvas_on_main_thread()`
   - Modified `_render_frame_to_canvas()` to use queue

2. `video_censor_personal/ui/audio_player.py`
   - Fixed `seek()` for 1D/2D arrays
   - Fixed `get_duration()` for 1D/2D arrays
   - Fixed frame counting in `_playback_thread_main()`

3. `video_censor_personal/ui/video_player_pane.py`
   - Added queue import
   - Modified `_start_update_timer()` to poll canvas update queue
   - Reduced timer interval from 100ms to 50ms for faster updates
