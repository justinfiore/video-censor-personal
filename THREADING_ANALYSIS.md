# Video Player Threading Model Analysis (Current)

This document describes the threading architecture of the video player UI as implemented in PyAVVideoPlayer and supporting modules. This represents the current state after implementing A/V synchronization, preview editing, and numerous performance improvements.

## Executive Summary

The video player uses a **three-thread model with audio-master synchronization**:

1. **Main Thread (Tkinter event loop)**: Handles user input, UI updates, canvas display, and periodic polling of video frames
2. **Decode Thread**: Decodes video frames from the container using PyAV, converts to RGB, and queues for rendering
3. **Render Thread**: Retrieves frames, resizes/converts to PIL, and synchronizes with audio playback before queuing for display
4. **Audio Thread**: Uses sounddevice's callback-based streaming to play audio continuously (NOT blocking)

**Key improvement over original**: Audio is now the master clock. The render thread adjusts playback speed by dropping frames (if behind) or waiting (if ahead) to stay in sync with audio time, rather than the reverse.

---

## Thread Architecture Overview

```
┌────────────────────────────────────────────────────────────────────────────┐
│                        MAIN THREAD (Tkinter Event Loop)                     │
│                                                                             │
│  Every 50ms (via self.after()):                                            │
│  1. _update_timecode() - update display time                               │
│  2. _update_canvas_on_main_thread() - poll canvas update queue             │
│     └─> Create PhotoImage from PIL (must be main thread)                   │
│     └─> Update tk.Canvas with frame                                        │
│     └─> Update cached canvas dimensions for render thread                  │
│                                                                             │
│  Button/keyboard events: play, pause, seek, speed control                  │
└────────────┬─────────────────────────────────────────────────────────────┘
             │
             │ play() called
             ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                    DECODE THREAD (daemon, background)                       │
│  pyav_video_player.py:_decode_thread_main()                                │
│                                                                             │
│  1. Handle _pause_event, _seek_event                                       │
│  2. _decode_frames() loop:                                                 │
│     ├─ Acquire container lock (non-blocking)                               │
│     ├─ Decode frames in batches of 3 to yield control                      │
│     ├─ Convert frame to RGB numpy array (CPU work)                         │
│     ├─ Check for seek/pause frequently for responsiveness                  │
│     ├─ Skip frames after seek if necessary (catch-up logic)                │
│     └─ Put frame into _frame_queue (blocks if full, timeout=100ms)         │
│                                                                             │
│  Queue: _frame_queue (maxsize=30, blocking put)                            │
│    - Backpressure on decode if render thread is slow                       │
│    - Dropped frames logged when timeout exceeded                           │
└────────────┬─────────────────────────────────────────────────────────────┘
             │
             │ Frame data with image_array, pts, time
             ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                    RENDER THREAD (daemon, background)                       │
│  pyav_video_player.py:_render_thread_main()                                │
│                                                                             │
│  1. Wait while paused or seeking                                           │
│  2. Get frame from _frame_queue (timeout=50ms)                             │
│  3. Check seek event again (discard stale frames after seek)               │
│  4. Calculate A/V SYNC:                                                    │
│     ├─ Get audio time from audio player                                    │
│     ├─ Get video time from frame PTS                                       │
│     ├─ Calculate drift: audio_time - video_time + av_latency_offset       │
│     ├─ Drop frame if too far behind (>100ms)                               │
│     ├─ Wait if too far ahead (>30ms, interruptible sleep)                  │
│     └─ Log drift stats (first 3 frames, then every 24 at 24fps)            │
│  5. Convert image array to PIL Image                                       │
│  6. Resize using BILINEAR resampling (faster than LANCZOS)                │
│  7. Queue PIL Image for main thread (non-blocking, drop if full)           │
│                                                                             │
│  Queue: _canvas_update_queue (maxsize=3, non-blocking put)                │
│    - Main thread polls this queue                                          │
│    - Larger buffer prevents render thread blocking on full queue           │
└────────────┬─────────────────────────────────────────────────────────────┘
             │
             │ PIL Image ready for display
             ▼
┌────────────────────────────────────────────────────────────────────────────┐
│               MAIN THREAD (canvas update from queue)                        │
│  pyav_video_player.py:_update_canvas_on_main_thread()                      │
│                                                                             │
│  1. Update cached canvas dimensions (read by render thread)                │
│  2. Poll _canvas_update_queue (non-blocking)                               │
│  3. If frame available:                                                    │
│     ├─ Convert PIL Image to PhotoImage (thread-safe, main thread only)     │
│     └─ Update canvas.create_image() to display                             │
│  4. Return immediately if queue empty                                      │
│                                                                             │
│  This is called every 50ms from _start_update_timer()                      │
└────────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────────┐
│                  AUDIO THREAD (sounddevice callback)                        │
│  audio_player.py:_audio_callback() or OutputStream                         │
│                                                                             │
│  NOT a blocking thread anymore! Instead:                                   │
│  1. sounddevice.OutputStream with callback runs in low-latency thread      │
│  2. _audio_callback() is invoked by sounddevice ~44 times per second       │
│  3. Fills output buffer from _audio_frames using _current_frame index      │
│  4. Updates _current_frame as samples are played                           │
│  5. Lock is held only for buffer copy (~1-2ms max)                         │
│  6. No blocking wait() - clean non-blocking operation                      │
│                                                                             │
│  Key: Render thread calls audio_player.get_current_time() to sync video   │
│        This is fast - just reads _current_frame with lock                 │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## Detailed Control Flow

### Play Sequence

```
User clicks Play button (Main Thread)
    ↓
VideoPlayerPaneImpl._on_play_pause() [main thread]
    ↓
PyAVVideoPlayer.play() [main thread, holds _frame_lock]
    │
    ├─ Determine start position (pending seek target or current time)
    │
    ├─ Sync audio to start position via audio_player.seek()
    │
    ├─ If resuming from pause:
    │  └─ Set _seek_event to trigger seek in decode thread
    │  └─ Call audio_player.play() to resume
    │
    ├─ Clear pause event and any stale frames
    │
    ├─ Initialize audio SYNCHRONOUSLY (if needed)
    │  └─ Call _initialize_audio_player() [runs on main thread]
    │  └─ Decodes entire audio stream into memory
    │  └─ Creates SoundDeviceAudioPlayer with all frames
    │
    └─ Start audio playback via audio_player.play()
    │  └─ Creates sounddevice OutputStream (non-blocking)
    │  └─ Audio now streaming via callbacks
    │
    └─ Start decode thread (if not already running)
       └─ _decode_thread_main() loop begins
```

### Frame Processing During Playback

```
DECODE THREAD: _decode_frames()
    │
    ├─ Check for seek/pause events (responsive)
    ├─ Acquire container lock
    ├─ Demux video stream and get packets
    │
    ├─ For each frame:
    │  ├─ Check seek/pause again (inner loop responsiveness)
    │  ├─ Skip frames if catching up from seek
    │  ├─ Convert to RGB numpy array (frame.to_rgb().to_ndarray())
    │  │  └─ PyAV frame becomes invalid after scope, so convert immediately
    │  │
    │  ├─ Put frame_data into _frame_queue [BLOCKS if full, timeout=100ms]
    │  │  └─ Backpressure: decode waits if render can't keep up
    │  │
    │  ├─ Start render thread if not running (should already be started)
    │  │
    │  └─ Sleep 1ms every 3 frames to yield to other threads
    │
    └─ Exit loop on stop/pause/seek events

RENDER THREAD: _render_thread_main()
    │
    ├─ While not stopped:
    │  │
    │  ├─ If paused: sleep 50ms and skip
    │  │
    │  ├─ If seek pending: sleep 10ms to let decode handle it, skip
    │  │
    │  ├─ Get frame from _frame_queue [timeout=50ms]
    │  │  └─ Non-blocking after timeout
    │  │
    │  ├─ Check seek event again (discard stale frame if new seek started)
    │  │
    │  ├─ A/V SYNCHRONIZATION LOGIC:
    │  │  │
    │  │  ├─ Get audio_time from audio_player.get_current_time()
    │  │  │  └─ Very fast: just reads _current_frame with lock
    │  │  │
    │  │  ├─ Get video_time from frame.pts converted to seconds
    │  │  │
    │  │  ├─ Calculate drift = audio_time - video_time + av_latency_offset
    │  │  │  └─ av_latency_offset is configured (default 1500ms positive)
    │  │  │  └─ Positive offset delays video (video plays later)
    │  │  │
    │  │  ├─ Log drift stats:
    │  │  │  └─ Always log first 3 frames
    │  │  │  └─ Then every 24 frames (~1 second at 24fps)
    │  │  │  └─ Always log if drift exceeds ±100ms
    │  │  │  └─ Format: "A/V DRIFT: frame#N video=X.XXXs audio=Y.YYYs drift=±Z.Zms (avg=±A.Ams)"
    │  │  │
    │  │  ├─ If drift > 100ms (video far behind):
    │  │  │  └─ Drop frame and continue (can't catch up by waiting)
    │  │  │
    │  │  └─ If drift > 30ms and < 100ms (video slightly ahead):
    │  │     └─ Wait interruptibly (20ms chunks, check for seek/pause/stop)
    │  │     └─ Allows quick response to user input
    │  │
    │  ├─ Convert image array to PIL Image
    │  │
    │  ├─ Resize with BILINEAR (fast, good quality)
    │  │  └─ Uses cached canvas dimensions from main thread
    │  │  └─ Aspect-preserving resize
    │  │
    │  └─ Put PIL Image into _canvas_update_queue [non-blocking]
    │     └─ If full, frame is dropped (main thread is slow)
    │
    └─ Catch queue.Empty exception and continue on timeout

MAIN THREAD: _update_canvas_on_main_thread() (called every 50ms)
    │
    ├─ Update cached canvas dimensions
    │  └─ Read by render thread to avoid calling winfo from background thread
    │
    ├─ Poll _canvas_update_queue (non-blocking get_nowait)
    │
    ├─ If frame available:
    │  ├─ Extract PIL Image and canvas dimensions
    │  ├─ Convert PIL to PhotoImage (must be main thread for Tkinter safety)
    │  ├─ Store reference to prevent GC
    │  ├─ Delete old canvas content
    │  ├─ Create new image on canvas (fast, just image swap)
    │  └─ Log successful update
    │
    └─ If queue empty: return immediately (no work)
```

---

## Queue Architecture

```
┌──────────────┐
│ Decode Thread│
│              │ (frame data: image_array, pts, time)
│ Produces:    │
│ YUV→RGB      │ ┌──────────────────────┐
│ conversion   │─→│  _frame_queue       │
│              │  │  maxsize=30         │
└──────────────┘  │  BLOCKING put       │
                  │  timeout=100ms      │
                  │  (backpressure)     │
                  └──────┬───────────────┘
                         │
                         │ (frame data)
                         ▼
              ┌──────────────────────┐
              │ Render Thread        │
              │                      │ (PIL Image: resized, ready for display)
              │ Produces:            │
              │ PIL Image + resize   │ ┌──────────────────────┐
              │                      │─→│_canvas_update_queue │
              └──────────────────────┘  │ maxsize=3           │
                                        │ NON-BLOCKING put    │
                                        │ (drop if full)      │
                                        └──────┬───────────────┘
                                               │
                                               │ (PIL Image)
                                               ▼
                                        ┌──────────────────────┐
                                        │ Main Thread          │
                                        │                      │
                                        │ Consumes:            │
                                        │ PhotoImage creation  │
                                        │ Canvas update        │
                                        │                      │
                                        │ Polling every 50ms   │
                                        └──────────────────────┘
```

### Why These Queue Sizes?

- **_frame_queue (maxsize=30)**: Decode thread produces frames fast (33ms apart at 30fps), render thread is slower due to PIL/resize. Buffer allows decode to get ahead without blocking, providing smooth playback. At 24fps render, 30-frame buffer = ~1.25 seconds of decoded-ahead frames.

- **_canvas_update_queue (maxsize=3)**: Render thread produces fast, main thread polls every 50ms (slowest). Increased from 1 to 3 to give render thread a small buffer, reducing frame drops when main thread is briefly busy. At 24fps, 3 frames = ~125ms worth.

---

## A/V Synchronization (Audio-Master Model)

### Core Principle

**Audio is the master clock**. Video frames are displayed when their PTS matches audio time, with adjustments for presentation latency differences.

### Drift Calculation

In the render thread for each frame:

```python
audio_time = audio_player.get_current_time()  # Fast, lock-based read
video_time = frame_pts_in_seconds
adjusted_drift = (audio_time - video_time) + av_latency_offset

# av_latency_offset = 1500ms by default (positive = video delayed)
# This compensates for platform presentation latency differences:
# - Audio: ~50-75ms latency through sounddevice
# - Video: ~100-130ms latency through Tkinter display stack
# - Difference: ~50ms, but empirically 1500ms works best (may account for
#   buffering differences in the full playback pipeline)
```

### Frame Timing Logic

```
For each frame received from decode thread:
│
├─ Calculate adjusted_drift (audio_time - video_time + offset)
│
├─ IF adjusted_drift > 100ms (video far behind audio):
│  └─ DROP FRAME
│     Reason: Even if we wait, we can't catch up in real-time
│     Frame is too old to display
│
├─ ELIF 30ms < adjusted_drift <= 100ms (video slightly behind):
│  ├─ WAIT: But not blocking! Interruptible 20ms chunks
│  └─ Allows quick response to seek/pause/stop events
│
└─ ELSE adjusted_drift <= 30ms (video ahead or within tolerance):
   └─ DISPLAY: Put frame into canvas update queue
      Reason: Video is roughly in sync or ahead, safe to display
```

### A/V Offset Tuning (User-Configurable)

Users can adjust `av_sync_offset_ms` in the UI:

1. Enter value in "A/V Sync (ms)" field (default 1500)
2. Click "Apply" or press Enter
3. Video_player_pane._on_av_sync_changed() calls player.set_av_sync_offset(ms)
4. Player converts to seconds and updates _av_latency_offset
5. Next frame's drift calculation uses new offset
6. No restart needed, tuning is live during playback

**Common adjustments**:
- Value too low (e.g., 1000): Audio will appear ahead (audio playing before corresponding video)
- Value too high (e.g., 2000): Audio will appear behind (video showing before corresponding audio)
- Default 1500: Balances typical presentation latencies

### Drift Logging for Diagnostics

The render thread logs A/V drift information to help diagnose sync issues:

```
Logged when:
├─ Frame #1, #2, #3 (first frames always)
├─ Then every 24 frames thereafter (~1 second at 24fps)
└─ Or whenever |drift| > 100ms (threshold exceeded)

Format:
  A/V DRIFT: frame#123 video=45.678s audio=45.722s drift=+44ms (avg=+22ms)

Fields:
├─ frame#: Frame count since playback started
├─ video_time: Current video frame timestamp (PTS)
├─ audio_time: Current audio playback position
├─ drift: Adjusted drift (audio - video + offset)
└─ avg: Running average of last 100 drift samples (for trend analysis)
```

Users can analyze logs to:
- **Growing positive drift** → video falling behind → use faster resampling or larger queue
- **Growing negative drift** → video getting ahead → reduce offset or increase render delays
- **Oscillating drift** → frames being dropped → increase canvas queue size
- **Stable ±20ms** → good sync, no tuning needed

---

## Synchronization Primitives

| Primitive | Purpose | Scope |
|-----------|---------|-------|
| `_frame_lock` (RLock) | Protects `_is_playing`, `_current_time`, playback state | Main thread + decode/render threads |
| `_container_lock` (RLock) | Protects PyAV container from concurrent decode/seek | Decode thread + render thread (seeking) |
| `_frame_queue` | Frame data from decode to render | Decode → Render |
| `_canvas_update_queue` | PIL images from render to main thread | Render → Main thread |
| `_stop_event` (threading.Event) | Signal to stop all threads | Decoded by all threads |
| `_pause_event` (threading.Event) | Signal to pause decoding | Checked by decode thread |
| `_seek_event` (threading.Event) | Signal that a seek is pending | Checked by decode/render threads |
| Audio `_lock` (RLock) | Protects audio player state | Audio callback + main thread |

### Lock Ordering (to prevent deadlock)

1. `_frame_lock` must be acquired BEFORE accessing `_audio_player` (main thread when checking is_playing)
2. Never hold `_frame_lock` while acquiring audio locks
3. Render thread acquires audio's lock only briefly via `get_current_time()` which is safe
4. All lock scopes are minimal to prevent contention

---

## Seek Behavior

### Seek Event Flow

```
User clicks timeline or seeks via API
    │
    └─ PyAVVideoPlayer.seek(time)
       │
       ├─ Acquire _frame_lock
       ├─ Set _seek_target = time
       ├─ Set _seek_event
       │
       └─ Return immediately (non-blocking)

DECODE THREAD detects _seek_event:
    │
    ├─ Return early from decode loop
    ├─ Call _perform_seek():
    │  ├─ Acquire _container_lock
    │  ├─ Convert time to container timestamp
    │  ├─ Call container.seek()
    │  ├─ Clear _frame_queue (discard pre-seek frames)
    │  ├─ Clear _canvas_update_queue (discard stale queued frames)
    │  └─ Release lock
    │
    ├─ Clear _seek_event flag
    ├─ Continue decoding from new position
    └─ Skip frames until reaching target time (frame_time >= target_time - 33ms)

RENDER THREAD detects _seek_event:
    │
    ├─ Skip processing (sleep 10ms, let decode handle)
    ├─ Discard frame if one was already fetched (might be stale)
    └─ Continue main loop
```

### Why Clear Queues on Seek?

- **_frame_queue**: Contains frames from OLD position. Clearing allows decode thread to fill it with frames from NEW position.
- **_canvas_update_queue**: Contains PIL Images that are about to be displayed from OLD position. Clearing prevents visual jump/stutter when new frames arrive.

---

## Performance Characteristics

### Bottlenecks and Solutions

| Bottleneck | Original Problem | Current Solution |
|------------|------------------|-------------------|
| LANCZOS resize | Very slow (~50-100ms per frame) | Switched to BILINEAR (~5-10ms per frame) |
| Audio thread blocking | Audio.wait_done() held lock for entire audio duration, blocking render/main threads | Replaced with sounddevice callback-based streaming (non-blocking) |
| Canvas dimension queries | winfo_width/height called from render thread (can hang) | Cache dimensions on main thread, render thread reads cache |
| Timeline redraw every frame | Redrawing all segments every 50ms | Only redraw playhead position, segments redrawn on load/resize |
| Main thread starvation | Rendering was not responsive due to Tkinter blocking | PhotoImage creation still on main thread but render prep happens in background |

### Timing Budget (24fps target)

```
Time available per frame: 1000ms / 24fps ≈ 42ms

Decode thread work:
  ├─ Demux: ~5-10ms
  ├─ Decode (YUV→RGB): ~15-25ms
  └─ Queue put: ~1ms
  Total: ~20-35ms (fits within 42ms, but can overlap)

Render thread work:
  ├─ Get frame: ~1ms
  ├─ PIL Image creation: ~5-8ms
  ├─ BILINEAR resize: ~5-10ms
  ├─ A/V sync calc + sleep: ~1-40ms (variable based on drift)
  └─ Queue put: ~1ms
  Total: ~13-60ms (can exceed 42ms, triggers frame drops)

Main thread work (every 50ms):
  ├─ _update_timecode: ~1-2ms
  ├─ Poll canvas queue: ~1ms
  ├─ PhotoImage creation: ~5-10ms (if frame available)
  ├─ Canvas update: ~1-2ms
  └─ Timeline playhead update: ~1ms
  Total: ~10-20ms per poll
```

Frame drops occur when:
- Render thread gets behind (resize + sync wait exceeds 42ms)
- Main thread is busy and doesn't poll canvas update queue frequently enough

Mitigations:
- `_canvas_update_queue` size of 3 gives 3 * 42ms = 126ms buffer
- Render thread can safely wait 30-100ms for audio without missing deadlines
- Main thread polls every 50ms which is faster than frame interval

---

## Improvements Made Since Original Analysis

| Change | Impact | Status |
|--------|--------|--------|
| Replaced simpleaudio with sounddevice | Eliminated use-after-free crashes, made audio non-blocking | ✅ Complete |
| Added A/V sync offset control | Made sync tunable without code changes | ✅ Complete |
| Added A/V drift logging | Enabled data-driven tuning | ✅ Complete |
| Switched LANCZOS → BILINEAR resize | ~5x faster rendering (50ms → 10ms) | ✅ Complete |
| Cached canvas dimensions | Eliminated winfo_width/height hang from render thread | ✅ Complete |
| Optimized timeline rendering | Only redraw playhead each frame, segments on resize | ✅ Complete |
| Added seek frame skipping logic | Smooth seeking without displaying old frames | ✅ Complete |
| Increased canvas queue size | 1 → 3 to reduce frame drops during main thread busy | ✅ Complete |
| Synchronous audio init before play | Ensured audio ready before video threads start | ✅ Complete |
| Interruptible A/V sync sleep | Can respond to seek/pause during wait, not blocking | ✅ Complete |

---

## Current Known Limitations and Areas for Improvement

### Limitations

1. **Audio fully loaded into memory**: Entire audio stream decoded and stored as numpy array. Works for videos up to ~30 minutes but becomes problematic for longer videos or memory-constrained systems.
   - Mitigation: Stream audio on-demand instead of pre-loading
   - Impact: High for long-form content

2. **Seek takes time to process**: Container seek is fast, but decode thread must skip frames to reach the target, which can cause brief stall (100-500ms).
   - Mitigation: Keyframe seeking in decode thread, or hardware decoding
   - Impact: Medium for interactive seeking

3. **Single-threaded container access**: While locked to prevent concurrent access, PyAV container isn't thread-safe at the application level
   - Current mitigation: Decode and render threads coordinate via seek/pause events
   - Impact: Low, but could be cleaner with a dedicated container access thread

4. **Tkinter canvas is single-threaded**: All canvas operations must happen on main thread, including PhotoImage creation (~5-10ms per frame)
   - Mitigation: None without switching away from Tkinter
   - Impact: Medium - limits overall frame rate and can cause stutter if main thread busy

5. **Timeline fully redrawn on resize**: While playhead is now optimized, segment rendering still redraws all segments when canvas resizes
   - Mitigation: Cache segment paths and only update playhead
   - Impact: Low - resize is infrequent

### Recommended Improvements (Not Yet Implemented)

1. **Streaming Audio Decoding**: Decode audio on-demand in chunks rather than pre-loading all
   - Reduces memory footprint from O(duration_in_seconds * sample_rate * channels) to O(chunk_size)
   - Would also allow variable bitrate handling

2. **Hardware Video Decoding**: Use GPU-accelerated decoding (NVDEC, VAAPI, VideoToolbox) for higher frame rates
   - PyAV supports hardware decoding with proper codec selection
   - Would reduce CPU load on decode/render threads

3. **Direct Rendering Backend**: Replace Tkinter canvas with pygame or OpenGL for direct pixel manipulation
   - Faster rendering, lower latency
   - More control over frame timing
   - Would eliminate PhotoImage creation overhead

4. **Keyframe Index for Fast Seeking**: Build index of keyframe positions during load
   - Reduce seek time from 100-500ms to <50ms
   - Better user experience for timeline scrubbing

5. **Render Thread Scheduling**: Dedicate render thread to CPU core, lower OS thread priority for decode
   - More consistent frame timing
   - Reduce OS scheduler variance

6. **A/V Sync Smoothing**: Low-pass filter drift values to reduce oscillation
   - Current: Every frame independently calculated
   - Proposed: Rolling average drift with grace periods before dropping frames
   - Would reduce flickering/stuttering on noisy systems

---

## Thread Safety Summary

### Thread-Safe Operations

- **Queue operations**: `put()`, `get()`, `get_nowait()` with proper timeout handling
- **Event operations**: `set()`, `clear()`, `is_set()` (atomic)
- **Sounddevice callback**: Properly locked access to audio data
- **Canvas dimension caching**: Main thread writes, render thread reads (no synchronization needed, stale reads are acceptable)

### Potential Race Conditions (Current Status: MITIGATED)

| Condition | Cause | Mitigation |
|-----------|-------|-----------|
| Render thread accessing None audio_player | Main thread hasn't initialized yet | Render thread checks `if self._audio_player is None` before calling |
| Seek during decode | User seeks while decode running | Decode checks `_seek_event` frequently and handles via `_perform_seek()` |
| Pause during audio playback | User pauses while audio streaming | Audio player checks `_is_playing` in callback (safe) |
| Canvas resize during render | User resizes window during rendering | Canvas dimensions read from cache, stale values acceptable |

---

## Logging Strategy for Debugging

Key logging points:

- **INFO level**: Play/pause/seek start/end, audio init, frame counts, sync changes
- **DEBUG level**: Frame gets/puts, queue operations, canvas updates, sync values (verbose)
- **WARNING level**: Queue drops, missing audio player, canvas not ready, seek failures
- **ERROR level**: Thread crashes, stream errors, corruption

To trace a specific issue:

```bash
# Enable debug logging
export LOGLEVEL=DEBUG

# Example: Trace frame timing during playback
grep "A/V DRIFT" logs.txt | tail -50

# Example: Find frame drops
grep "dropped\|FULL" logs.txt | head -20

# Example: Trace seek behavior
grep "Performing seek\|Caught up\|FRAME_SKIP" logs.txt
```

---

## Conclusion

The video player threading model balances complexity with responsiveness:

- **Main thread** handles UI and user input responsively (50ms poll cycle)
- **Decode thread** produces frames with backpressure via blocking queue
- **Render thread** synchronizes video to audio while preparing frames efficiently
- **Audio thread** plays continuously via non-blocking callback mechanism

Audio is the master clock, providing stable time reference. Video frames are dropped or delayed to stay in sync, rather than trying to catch up in real-time. This ensures audio quality is never compromised and playback remains smooth even under load.

The main opportunity for improvement is replacing Tkinter canvas with a faster rendering backend and streaming audio decoding for longer videos. Current implementation is solid for typical use cases (videos up to ~30 minutes on modern hardware).
