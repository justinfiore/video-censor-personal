# Logging Optimization Detail

## Problem

The current logs from loading a 1.5-hour video contain **2000+ dense log lines** and produce a **540KB log file**. This is primarily due to frame-by-frame logging during audio extraction:

```
2026-01-01 15:15:15,701 - video_censor_personal.ui - DEBUG - Audio frame #227300: shape=(2, 1024), dtype=float32
2026-01-01 15:15:15,702 - video_censor_personal.ui - DEBUG - Audio frame #227350: shape=(2, 1024), dtype=float32
2026-01-01 15:15:15,703 - video_censor_personal.ui - DEBUG - Audio frame #227400: shape=(2, 1024), dtype=float32
... (repeated ~2000 times)
```

While this detail is useful during development and troubleshooting, it:
1. **Increases logging overhead** during normal operation
2. **Inflates log files** making them harder to store and analyze
3. **Masks important diagnostics** by burying phase transitions in noise

## Solution: Log Level Stratification

Implement a 3-level logging strategy:

### INFO Level (Minimal)
- Only errors and critical state changes
- Example: "Error: Failed to load video", "Video loaded successfully"
- **Use case**: Production/user-facing scenarios where detailed logs are not needed

### DEBUG Level (Standard, Default)
- Phase transitions and high-level progress
- Examples:
  - "Loading video: /path/to/video.mp4"
  - "Audio extraction started"
  - "Audio extraction complete: 236894 frames"
  - "Segment list population started"
  - "Segment list population complete: 206 segments"
  - "UI initialization complete in 2.5s"
- **Use case**: Normal development and user support (logs for understanding what happened)
- **Target log file size**: <100KB for 206-segment video

### TRACE Level (Detailed)
- Frame-by-frame details, widget creation, layout calculations
- Examples:
  - "Audio frame #227300: shape=(2, 1024), dtype=float32"
  - "Creating SegmentListItem widget #5"
  - "Layout calculation for segment list: 206 items"
- **Use case**: Deep troubleshooting when performance issues are unclear
- **Activation**: Environment variable `VIDEO_CENSOR_LOG_LEVEL=TRACE` or config file

## Implementation Strategy

### 1. Refactor Existing Logs

**Before** (all DEBUG):
```python
for i, frame in enumerate(audio_frames):
    logger.debug(f"Audio frame #{i}: shape={frame.shape}, dtype={frame.dtype}")
```

**After** (frame-level is TRACE):
```python
# Phase logging at DEBUG
if starting_batch:
    logger.debug(f"Audio extraction started: extracting {total_frames} frames")

# Dense logs at TRACE
for i, frame in enumerate(audio_frames):
    logger.debug(f"Audio frame #{i}: shape={frame.shape}, dtype={frame.dtype}")  # ← Changed to TRACE
```

Or better:
```python
# Use separate loggers for different components
audio_logger = logging.getLogger("video_censor_personal.ui.audio")
ui_logger = logging.getLogger("video_censor_personal.ui")

# Phase transitions at DEBUG
ui_logger.debug(f"Audio extraction started")

# Frame-level details at TRACE
for i, frame in enumerate(audio_frames):
    audio_logger.debug(f"Audio frame #{i}: shape={frame.shape}, dtype={frame.dtype}")  # ← Still DEBUG, but on sub-logger
```

### 2. Logging Configuration

Add environment variable support:

```python
# In app initialization
import os
import logging

log_level = os.getenv("VIDEO_CENSOR_LOG_LEVEL", "DEBUG").upper()
logging.basicConfig(level=log_level, ...)

# User can now run:
# VIDEO_CENSOR_LOG_LEVEL=TRACE ./launch-ui.sh output.json    # Detailed logs
# ./launch-ui.sh output.json                                   # Standard DEBUG logs
# VIDEO_CENSOR_LOG_LEVEL=INFO ./launch-ui.sh output.json      # Minimal logs
```

Or via logger configuration:

```yaml
# video_censor_logging.yaml
version: 1
root:
  level: DEBUG
loggers:
  video_censor_personal.ui.audio:
    level: TRACE  # Very chatty
  video_censor_personal.ui.segment_list:
    level: DEBUG  # Less chatty
```

### 3. Measurable Impact

**Current State** (540KB with all logs at DEBUG):
```
15:15:04 - App launch
15:15:18 - Audio loaded
...
```
Log file: 540KB, ~2000+ audio frame lines

**After Optimization** (default DEBUG):
- Audio frame lines moved to TRACE level (hidden by default)
- Phase transitions remain at DEBUG
- Log file size: ~50-100KB (90%+ reduction)
- Same diagnostic information available when needed (run with TRACE)

**With TRACE enabled**:
- Same detail as before (540KB, ~2000+ lines)
- Available on demand for deep troubleshooting

## Why This Matters for Scaling

1. **Performance**: Reduced logging overhead means more CPU/IO resources available for UI rendering
2. **Diagnostics**: Easier to spot actual bottlenecks when logs aren't buried in frame-level noise
3. **User Experience**: Smaller log files, faster disk I/O during execution
4. **Development**: Developers can enable TRACE when investigating specific issues, disabled for normal workflows

## Acceptance Criteria

- ✅ Frame-by-frame logs (audio, widgets, layout) are at TRACE or controlled sub-logger level
- ✅ Phase transitions remain visible at DEBUG level
- ✅ Default log level (DEBUG) produces <100KB for 206-segment video
- ✅ TRACE level produces full detail (540KB+) when needed
- ✅ Log level configurable via environment variable or config file
- ✅ No code changes needed to enable/disable TRACE logging
