# Quick Testing Guide

## TL;DR - Get Started in 60 Seconds

### 1. Verify Installation (30 seconds)
```bash
python3 test_video_playback.py
# Should see: "✓ All tests passed!"
```

### 2. Test Real Videos (15 seconds)
```bash
python3 test_real_video.py
# Should see: "✓ sample.mp4" and "✓ Psych1_1-clean.mp4"
```

### 3. Launch App & Test UI (15 seconds)
```bash
python3 video_censor_personal.py
# Then open preview editor and load a video file
```

## What to Look For

### ✅ Success Indicators
- Video displays in canvas (not black)
- Audio plays (you hear sound)
- Play/pause buttons work
- Timeline seeking works
- Volume slider works
- No crashes or error messages

### ⚠️ Known Issues (Not Critical)
- Audio-video sync may drift after 30+ minutes (Phase 2)
- Video may stutter if CPU is busy (Phase 2 optimization)
- Some rare codecs may not work (graceful error)

### ❌ Failure Indicators
- Application crashes (see console error)
- Video won't load (check file format)
- No audio at all (check if file has audio stream)
- Play button does nothing (threading issue)

## Quick Diagnostics

**Can't see video?**
```bash
# Check if PyAV works
python3 -c "import av; print(av.__version__)"
# Should show: 16.0.1
```

**No audio?**
```bash
# Check audio dependencies
python3 -c "import simpleaudio, pydub; print('Audio OK')"
# Should show: Audio OK
```

**Still broken?**
```bash
# Run with full logging
export PYTHONUNBUFFERED=1
python3 video_censor_personal.py 2>&1 | grep -E "ERROR|WARNING|PyAV"
```

## Test Video Files

These are already in your project:
- `/tests/fixtures/sample.mp4` (small, fast)
- `/output-video/Psych1_1-clean.mp4` (larger, realistic)

## Expected Console Output

### When playing starts:
```
video_censor_personal.ui - INFO - Loading video: /path/to/video.mp4
video_censor_personal.ui - INFO - Container opened
video_censor_personal.ui - INFO - Video stream found: h264 1280x720
video_censor_personal.ui - INFO - Audio stream found: aac
video_censor_personal.ui - INFO - Video loaded: duration=XXX.XXs
```

### During playback:
```
video_censor_personal.ui - INFO - Starting playback
video_censor_personal.ui - INFO - Initializing audio player
video_censor_personal.ui - INFO - Extracting audio: 44100Hz, 2 channels
```

## Checklist

- [ ] `test_video_playback.py` passes (5/5)
- [ ] `test_real_video.py` passes (2/2)
- [ ] App launches without crash
- [ ] Can load video in preview editor
- [ ] Video displays in canvas
- [ ] Audio plays
- [ ] Play/pause works
- [ ] Seeking works
- [ ] Volume control works
- [ ] Speed control works
- [ ] No crashes when seeking

## Common Issues & Fixes

| Issue | Solution |
|-------|----------|
| "ModuleNotFoundError: No module named 'av'" | Run: `pip3 install av` |
| "No audio" | Check file has audio (run test_real_video.py) |
| Video is black | Check canvas rendering (may need UI refresh) |
| App freezes on play | Threading issue - restart and try again |
| "simpleaudio not found" | Run: `pip3 install simpleaudio` |

## Need Help?

1. Check IMPLEMENTATION_STATUS.md (detailed status)
2. Check TESTING_GUIDE.md (comprehensive checklist)
3. Check PYAV_IMPLEMENTATION_SUMMARY.md (architecture)
4. Run tests with `PYTHONUNBUFFERED=1` for logging
5. Check console output for specific errors

---

**Summary**: If `test_video_playback.py` passes, the implementation is working. Any issues during UI testing are likely UI-specific (not core playback).
