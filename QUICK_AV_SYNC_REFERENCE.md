# A/V Sync Logging - Quick Reference

## One-Minute Overview

Added logging to track how far apart audio and video are during playback. Run a video, look at logs, adjust sync parameters based on what you see.

## How to Use

### 1. Collect Logs (30 seconds)
```bash
python video_censor_personal.py
# Play video for 30 seconds
tail logs/video_censor_personal.log | grep "A/V DRIFT"
```

### 2. Identify Pattern

| Log Pattern | Problem | Fix |
|---|---|---|
| `drift=+20ms`, `avg=+20ms` (stable) | Video consistently 20ms ahead | Change `max_drift_ahead = 0.05` |
| `drift=+20ms` → `+100ms` (growing) | Audio too slow or video too fast | Check sample rates or use BILINEAR resize |
| `drift=+50ms`, `drift=-50ms` (oscillating) | Frames dropping/skipping | Change `maxsize=60` in frame queue |
| `drift=+1500ms` then discard | Seeking while playing | Normal, not an issue |

### 3. Make One Change
```python
# Edit pyav_video_player.py line 600-603

# For stable +20ms drift:
max_drift_ahead = 0.05  # was 0.03

# For oscillating drift:
# Edit line 58:
self._frame_queue = queue.Queue(maxsize=60)  # was 30

# For negative drift (video too slow):
# Edit line 737:
pil_image.resize(..., Image.Resampling.BILINEAR)  # was LANCZOS
```

### 4. Test Again
```bash
python video_censor_personal.py
# Play another 30 seconds
tail logs/video_censor_personal.log | grep "A/V DRIFT" | tail -20
```

Is drift better? If yes, keep change. If no, revert and try different fix.

---

## Log Format

```
A/V DRIFT: frame#24 video=1.042s audio=1.020s drift=+22.1ms (avg=+15.3ms)
           -------  ---------  ----------- -----------  ---------  --------
           Marker   Frame #    Video time  Audio time   This frame Average
```

- **drift=+22ms**: Video is 22ms ahead (positive = video ahead)
- **drift=-15ms**: Audio is 15ms ahead (negative = audio ahead)  
- **avg=+15.3ms**: Average of last 100 frames

---

## Drift Symptoms & Solutions

### Symptom: Consistent ±20ms (Good)
```
A/V DRIFT: frame#1 drift=+0.0ms (avg=+0.0ms)
A/V DRIFT: frame#25 drift=+18.0ms (avg=+9.2ms)
A/V DRIFT: frame#49 drift=+20.0ms (avg=+12.1ms)
A/V DRIFT: frame#73 drift=+22.0ms (avg=+14.6ms)
```
✅ **Status**: Acceptable
- Small, stable offset indicates good sync
- No action needed unless manually tested audio/video is out of sync

---

### Symptom: Growing Drift (Bad)
```
A/V DRIFT: frame#1 drift=+0.0ms (avg=+0.0ms)
A/V DRIFT: frame#49 drift=+25.0ms (avg=+18.5ms)
A/V DRIFT: frame#97 drift=+60.0ms (avg=+38.2ms)
A/V DRIFT: frame#145 drift=+105.0ms (avg=+62.3ms)
```
❌ **Status**: Problem - one stream is slower than the other

**Quick Fix** (try first):
```python
# Line 737: Use faster resize
Image.Resampling.BILINEAR  # instead of LANCZOS
```

If still grows, might be sample rate mismatch (harder to fix).

---

### Symptom: Oscillating Drift (Warning)
```
A/V DRIFT: frame#1 drift=+5.0ms (avg=+5.0ms)
A/V DRIFT: frame#25 drift=-45.0ms (avg=-20.1ms)
A/V DRIFT: frame#49 drift=+60.0ms (avg=+18.3ms)
A/V DRIFT: frame#73 drift=-30.0ms (avg=+5.2ms)
```
⚠️ **Status**: Frames being dropped/skipped

**Fix**:
```python
# Line 58: Larger buffer
self._frame_queue = queue.Queue(maxsize=60)  # was 30
```

---

### Symptom: Many "Stale Frame" Messages
```
A/V sync: discarding stale frame (drift=1542.0ms, likely seek)
```
✅ **Status**: Normal during seeking (NOT a problem)
- Happens when user seeks while playing
- Render thread discards old frames that no longer match audio position

---

## Tuning Parameters (3 Most Important)

### Parameter 1: Frame Queue Size
```python
# Line 58 in __init__
self._frame_queue: queue.Queue = queue.Queue(maxsize=30)
```
- **Increase to 60** if: Drift oscillates wildly
- **Keep at 30** if: Drift is stable
- **Decrease to 20** if: Low-latency output desired

### Parameter 2: Max Drift Ahead
```python
# Line 603 in _render_thread_main
max_drift_ahead = 0.03  # 30ms
```
- **Increase to 0.05** if: Video consistently 20-30ms ahead but sounds good
- **Decrease to 0.02** if: Want tighter sync for high-FPS video (60fps+)

### Parameter 3: Image Resize Method
```python
# Line 737 in _render_thread_main
Image.Resampling.LANCZOS  # High quality, slow
```
- **Change to BILINEAR** if: Drift is growing (video too slow)
- **Keep LANCZOS** if: Video is keeping up and you want best quality

---

## Performance Impact

Drift logging has **negligible** impact:
- ~0.1% CPU overhead
- Minimal memory (100 float values = ~800 bytes)
- To reduce noise in production:

```python
# Only log when drift is >100ms (major issues)
if abs(drift_ms) > 100:  # Instead of logging every 24 frames
    logger.info(...)
```

---

## Key Files

| File | What It Does |
|------|-------------|
| `pyav_video_player.py` | Render thread with A/V sync & drift logging |
| `audio_player.py` | Audio playback position logging |
| `AV_SYNC_LOGGING.md` | Detailed explanation of logging |
| `TEST_AV_SYNC.md` | Step-by-step testing guide |
| `AV_SYNC_TUNING.md` | In-depth tuning guide |

---

## Common Questions

**Q: What drift is "good"?**
A: ±5ms is excellent, ±20ms is acceptable, >50ms is noticeable.

**Q: Why is video always ahead by 20ms?**
A: Normal! Audio decoder might have slight latency. If playback sounds/looks good, leave it.

**Q: Drift growing - what do I do?**
A: Try BILINEAR resize first (faster). If still growing, might be sample rate issue (harder).

**Q: How do I know if my fix worked?**
A: Rerun with same test video. If avg drift is smaller or more stable, it worked.

**Q: Can I disable this logging?**
A: Yes, comment out line 658-662 in `pyav_video_player.py` to disable.

---

## Testing Checklist

- [ ] Can see drift logs with `grep "A/V DRIFT" logs/*.log`
- [ ] Logs show expected pattern (stable, growing, or oscillating)
- [ ] Make one parameter change
- [ ] Retest, compare statistics
- [ ] Video plays without visible audio/video sync issues
- [ ] Check multiple test videos to confirm fix is general

