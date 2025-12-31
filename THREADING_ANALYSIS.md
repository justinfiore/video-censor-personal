# Video Player Threading Model Analysis

This document analyzes the threading model used in the video player UI, specifically focusing on what happens when the Play button is clicked. The analysis is based on code inspection and log analysis from a session where the app became unresponsive.

## Executive Summary

**The root cause of the UI freeze**: The render thread puts frames into `_canvas_update_queue`, but **no code is consuming those frames from the queue and updating the canvas**. The main thread's `_update_canvas_on_main_thread()` is being called every 50ms, but the logs show "Canvas update queue is empty" repeatedly - even though the render thread is successfully processing frames.

Looking at the logs:
```
2025-12-31 09:31:52,973 - Render thread started
2025-12-31 09:31:52,973 - Frame #1: image_array type=<class 'numpy.ndarray'>, size=(720, 1280, 3)
2025-12-31 09:31:54,222 - Frame queue full, dropped 10 frames total
...
2025-12-31 09:32:04,301 - Frame queue full, dropped 100 frames total
```

Meanwhile, the main thread keeps reporting:
```
2025-12-31 09:30:XX,XXX - Canvas update queue is empty
```

**Key Problem**: The render thread is getting stuck or blocked, not pushing frames to `_canvas_update_queue`. The decode thread keeps decoding and fills up the frame queue, while the render thread can't keep up, resulting in massive frame drops and eventual system hang.

---

## Thread Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              MAIN THREAD (Tkinter Event Loop)                │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │  _start_update_timer() - called every 50ms via self.after()             │ │
│  │                                                                          │ │
│  │  1. _update_timecode() - updates time display                            │ │
│  │  2. _update_canvas_on_main_thread() - polls canvas update queue          │ │
│  │     └─> Creates PhotoImage from PIL (thread-safe only on main thread)    │ │
│  │     └─> Updates tk.Canvas with frame                                     │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  Button clicks, keyboard events, window redraws                              │
└────────────────────────────┬────────────────────────────────────────────────┘
                             │
                             │ play() called
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DECODE THREAD (daemon)                               │
│  pyav_video_player.py:279 - _decode_thread_main()                           │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │  Loop:                                                                   │ │
│  │    1. Check _pause_event, _seek_event                                    │ │
│  │    2. Call _decode_frames() - decode video frames using PyAV             │ │
│  │       └─> frame.to_rgb().to_ndarray() - CPU-intensive conversion         │ │
│  │       └─> Put numpy array into _frame_queue (maxsize=30)                 │ │
│  │       └─> BLOCKS if queue full (timeout=0.1s), drops frame on timeout   │ │
│  │    3. Start render thread if not running                                 │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  Also starts audio player if initialized                                     │
└────────────────────────────┬────────────────────────────────────────────────┘
                             │
                             │ Frames enqueued to _frame_queue
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         RENDER THREAD (daemon)                               │
│  pyav_video_player.py:485 - _render_thread_main()                           │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │  Loop:                                                                   │ │
│  │    1. Get frame from _frame_queue (timeout=0.05s)                        │ │
│  │    2. Create PIL Image from numpy array                                  │ │
│  │    3. Resize image (CPU-intensive LANCZOS resampling)                    │ │
│  │    4. Throttle to 24fps (skip frames if too fast)                        │ │
│  │    5. Put PIL Image into _canvas_update_queue (maxsize=1, non-blocking)  │ │
│  │       └─> If queue full, frame is dropped                                │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  NOTE: Does NOT call canvas.after() or any Tkinter methods                   │
└────────────────────────────┬────────────────────────────────────────────────┘
                             │
                             │ PIL Images enqueued to _canvas_update_queue
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                 MAIN THREAD (polling _canvas_update_queue)                   │
│  pyav_video_player.py:642 - _update_canvas_on_main_thread()                 │
│                                                                              │
│  Called every 50ms by _start_update_timer() in video_player_pane.py:395     │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │  1. Try to get frame from _canvas_update_queue (non-blocking)            │ │
│  │  2. If frame available:                                                  │ │
│  │     a. Create PhotoImage from PIL Image (must be on main thread)         │ │
│  │     b. canvas.delete("all")                                              │ │
│  │     c. canvas.create_image()                                             │ │
│  │  3. If queue empty, return immediately                                   │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                     AUDIO PLAYBACK THREAD (daemon)                           │
│  audio_player.py:238 - _playback_thread_main()                              │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │  Loop:                                                                   │ │
│  │    1. Get audio segment from current frame position                      │ │
│  │    2. Apply volume scaling (CPU work on full remaining audio!)           │ │
│  │    3. simpleaudio.play_buffer() - starts native audio playback           │ │
│  │    4. wait_done() - BLOCKING wait for audio segment to finish            │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  PROBLEM: Plays ALL remaining audio from current position in one call!      │
│           Then blocks waiting for it to finish                               │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                   AUDIO INITIALIZATION THREAD (daemon)                       │
│  pyav_video_player.py:705 - _initialize_audio_player()                      │
│                                                                              │
│  Runs once when video loads to decode all audio frames into memory           │
│  This is done in background so it doesn't block UI                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Detailed Flow When Play Button is Clicked

### 1. Button Click Handler (Main Thread)
**File**: `video_player_pane.py` lines 278-297

```python
def _on_play_pause(self) -> None:
    """Handle play/pause button."""
    try:
        logger.info("_on_play_pause called")
        if not self.is_loaded or self.video_player is None:
            return
        
        if self.video_player.is_playing():
            self.video_player.pause()
            self.play_pause_button.configure(text="▶ Play")
        else:
            logger.info("Playing video")
            self.video_player.play()  # <-- Calls PyAVVideoPlayer.play()
            self.play_pause_button.configure(text="⏸ Pause")
```

### 2. PyAVVideoPlayer.play() (Main Thread)
**File**: `pyav_video_player.py` lines 136-161

```python
def play(self) -> None:
    """Start or resume playback."""
    with self._frame_lock:
        if self._is_playing:
            return
        
        logger.info("Starting playback")
        self._is_playing = True
        self._pause_event.clear()
        self._stop_event.clear()
        
        # Ensure audio is initialized before starting playback
        if self._audio_stream is not None and self._audio_player is None:
            logger.info("Initializing audio before playback")
            audio_thread = threading.Thread(target=self._initialize_audio_player, daemon=True)
            audio_thread.start()
        
        # Start decode thread
        if self._decode_thread is None or not self._decode_thread.is_alive():
            self._decode_thread = threading.Thread(target=self._decode_thread_main, daemon=True)
            self._decode_thread.start()
```

### 3. Decode Thread Loop (Background Thread)
**File**: `pyav_video_player.py` lines 279-311, 415-483

```python
def _decode_thread_main(self) -> None:
    # Start audio playback if initialized
    if self._audio_stream is not None and self._audio_player is not None:
        self._audio_player.play()
    
    while not self._stop_event.is_set():
        if self._pause_event.is_set():
            continue
        if self._seek_event.is_set():
            self._perform_seek()
            continue
        self._decode_frames()  # Decodes video frames

def _decode_frames(self) -> None:
    frames_decoded = 0
    max_frames_per_batch = 3
    
    with self._container_lock:
        demux_iter = self._container.demux(self._video_stream)
    
    for packet in demux_iter:
        for frame in packet.decode():
            # CPU-intensive: Convert to RGB numpy array
            image_array = frame.to_rgb().to_ndarray()
            
            frame_data = {
                'image_array': image_array,
                'pts': frame.pts,
                'time': frame.time,
            }
            
            # BLOCKING put with 0.1s timeout
            try:
                self._frame_queue.put(frame_data, block=True, timeout=0.1)
            except queue.Full:
                self._dropped_frames += 1
            
            # Start render thread if not running
            if self._render_thread is None or not self._render_thread.is_alive():
                self._render_thread = threading.Thread(target=self._render_thread_main, daemon=True)
                self._render_thread.start()
```

### 4. Render Thread Loop (Background Thread)
**File**: `pyav_video_player.py` lines 485-640

```python
def _render_thread_main(self) -> None:
    last_canvas_update = -float('inf')
    target_fps = 24
    min_frame_interval = 1.0 / target_fps
    
    while not self._stop_event.is_set():
        # Get frame from queue (0.05s timeout)
        frame_data = self._frame_queue.get(timeout=0.05)
        
        image_array = frame_data.get('image_array')
        
        canvas_width = self._canvas.winfo_width()
        canvas_height = self._canvas.winfo_height()
        
        # CPU-intensive: Create PIL Image and resize
        pil_image = Image.fromarray(image_array, mode='RGB')
        pil_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Throttle to target FPS
        now = time.time()
        if now - last_canvas_update >= min_frame_interval:
            # Queue for main thread (non-blocking, drops if full)
            self._canvas_update_queue.put({
                'pil_image': pil_image,
                'canvas_width': canvas_width,
                'canvas_height': canvas_height
            }, block=False)
            last_canvas_update = now
```

### 5. Main Thread Canvas Update (Polling)
**File**: `video_player_pane.py` lines 395-410, `pyav_video_player.py` lines 642-702

```python
# video_player_pane.py
def _start_update_timer(self) -> None:
    self._update_timecode()
    
    # Poll canvas update queue
    if hasattr(self.video_player, '_update_canvas_on_main_thread'):
        self.video_player._update_canvas_on_main_thread()
    
    self._update_timer_id = self.after(50, self._start_update_timer)  # 50ms = 20fps max

# pyav_video_player.py
def _update_canvas_on_main_thread(self) -> None:
    frame_data = self._canvas_update_queue.get_nowait()  # Non-blocking
    
    pil_image = frame_data.get('pil_image')
    
    # Must create PhotoImage on main thread (Tkinter requirement)
    photo_image = ImageTk.PhotoImage(pil_image)
    self._canvas_photo_image = photo_image
    
    self._canvas.delete("all")
    self._canvas.create_image(canvas_width // 2, canvas_height // 2, image=self._canvas_photo_image)
```

---

## Queue Architecture

```
┌────────────────┐     _frame_queue      ┌────────────────┐   _canvas_update_queue   ┌────────────────┐
│  Decode Thread │ ──────────────────▶   │  Render Thread │ ────────────────────────▶│  Main Thread   │
│                │     (maxsize=30)      │                │       (maxsize=1)        │                │
│  Produces:     │     BLOCKS if full    │  Produces:     │       DROP if full       │  Consumes:     │
│  numpy arrays  │     (timeout=0.1s)    │  PIL Images    │       (non-blocking)     │  PhotoImages   │
└────────────────┘                       └────────────────┘                          └────────────────┘
```

---

## Work that needs to be offloaded to other threads

### Critical Issues on Main Thread

| Issue | Location | Description | Impact |
|-------|----------|-------------|--------|
| **Timeline redraw on every time update** | `video_player_pane.py:366-385` `_update_timecode()` → `timeline.set_current_time()` → `_redraw()` | Every 50ms, the timeline canvas is completely redrawn (delete all, recreate all segments and playhead). At 20fps this is CPU-intensive. | High CPU usage on main thread, contributes to sluggishness |
| **PhotoImage creation** | `pyav_video_player.py:684` | Creating `ImageTk.PhotoImage()` on main thread is required by Tkinter but is CPU-intensive for 1280x720 frames | Necessary evil, but reduces available CPU for event handling |

### Critical Issues on Render Thread (blocking main thread indirectly)

| Issue | Location | Description | Impact |
|-------|----------|-------------|--------|
| **LANCZOS resampling** | `pyav_video_player.py:581` | `pil_image.resize(..., Image.Resampling.LANCZOS)` is CPU-intensive high-quality resampling. Done on every frame. | Render thread can't keep up with decode thread, causing massive frame drops |
| **Canvas dimension queries** | `pyav_video_player.py:542-543` | `self._canvas.winfo_width()` and `winfo_height()` called from render thread. While these are read-only, they may still block waiting for Tkinter's event loop. | Potential cross-thread synchronization issue |

### Critical Issues on Audio Thread

| Issue | Location | Description | Impact |
|-------|----------|-------------|--------|
| **Plays entire remaining audio at once** | `audio_player.py:248-277` | The audio thread plays ALL remaining audio from current position in a single `play_buffer()` call, then blocks with `wait_done()` | Audio plays correctly but: (1) Volume changes require stopping and restarting, (2) If video playback falls behind, audio is out of sync |
| **Volume scaling on full audio array** | `audio_player.py:263-264` | `frames_to_play = (frames_to_play * self._volume).astype(np.int16)` - applies volume to potentially millions of samples | CPU spike when playback starts or resumes |

### Decode Thread Issues

| Issue | Location | Description | Impact |
|-------|----------|-------------|--------|
| **RGB conversion on decode thread** | `pyav_video_player.py:443` | `frame.to_rgb().to_ndarray()` - converts YUV to RGB on decode thread | Necessary but CPU-intensive; decode thread spends most time here |
| **Blocking queue put** | `pyav_video_player.py:456` | `self._frame_queue.put(frame_data, block=True, timeout=0.1)` - blocks decode thread if render thread is slow | Causes frame drops when render thread can't keep up (100+ frames dropped per 10 seconds) |

---

## Root Cause Analysis: Why the UI Freezes

Based on the logs, here's what's happening:

1. **Play button clicked** at 09:31:52,761
2. **Decode thread starts** decoding frames immediately
3. **Render thread starts** at 09:31:52,973 and receives first frame
4. **Frame queue fills up** because render thread is too slow:
   - 09:31:54,222 - 10 frames dropped
   - 09:31:55,329 - 20 frames dropped
   - ... continues dropping 10 frames per second

5. **Main thread's canvas update queue remains empty** - the render thread logs `Frame #1` but never logs `*** CANVAS UPDATED SUCCESSFULLY ***`

**The smoking gun**: Looking at render thread code:
```python
# Line 604-612
try:
    self._canvas_update_queue.put({
        'pil_image': pil_image,
        ...
    }, block=False)
except queue.Full:
    pass  # Skip if UI thread is too slow
```

The render thread successfully creates PIL images but the `_canvas_update_queue.put()` is non-blocking and the queue has `maxsize=1`. If the main thread's polling (every 50ms) can't keep up, frames are silently dropped.

However, the main thread IS polling - it logs "Canvas update queue is empty" every ~60ms. This means:

**The render thread is not putting frames into the canvas update queue despite logging that it's processing them.**

Looking more carefully at the render thread flow:
1. It gets frames from `_frame_queue` ✓ (logged)
2. It creates PIL images ✓ (logged)
3. It should put into `_canvas_update_queue`... but the queue stays empty

**Hypothesis**: The render thread may be stuck in an earlier iteration or the throttle check at line 584-600 is preventing frames from being queued:

```python
if not should_render:
    frames_skipped_total += 1
    continue  # <-- Skipping the queue put!
```

Since `last_canvas_update` starts at `-float('inf')`, the first frame should pass. But if the LANCZOS resize is taking too long (>41ms at 24fps), subsequent frames might all be skipped due to the throttle check calculating incorrectly.

---

## Recommendations

### Debug Steps

- [x] Add logging at line 607 to confirm frames are being queued:
   ```python
   logger.info(f"Queued frame #{frames_rendered + 1} to canvas update queue")
   ```
- [x] Log `last_canvas_update` and timing values to verify throttle logic
- [x] Profile the LANCZOS resize to measure actual duration

### Immediate Fixes

- [ ] **Add more logging** - Log when frames are actually put into `_canvas_update_queue` vs skipped
- [ ] **Fix timeline redraw** - Only redraw the playhead marker, not all segments every frame
- [ ] **Increase canvas update queue size** - From 1 to 3-5 to buffer more frames
- [ ] **Remove or simplify LANCZOS resize** - Use `Image.Resampling.BILINEAR` or `NEAREST` instead

### Architecture Improvements

- [ ] **Chunk audio playback** - Play audio in 100ms chunks instead of all remaining audio at once
- [ ] **Consider using Tkinter's native video capabilities** or PyGame for rendering instead of Canvas
- [ ] **Implement proper A/V sync** - Currently audio and video are essentially independent; implement clock-based synchronization
