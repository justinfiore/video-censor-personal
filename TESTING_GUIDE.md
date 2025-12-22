# Manual Testing Guide for PyAV Video Playback

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Integration Tests
```bash
python3 test_video_playback.py
```

Expected output: All tests should pass (✓)

### 3. Launch the Application
```bash
python3 video_censor_personal.py
```

Then navigate to the preview editor UI to load and test videos.

## Testing Checklist

### Basic Functionality

- [ ] **Play/Pause Controls**
  - Click play button → video starts
  - Click pause button → video pauses
  - Play/pause button text updates correctly

- [ ] **Seeking**
  - Click on timeline → video seeks to that position
  - Use seek buttons (-10s, +10s) → video seeks correctly
  - Seek to beginning → video starts from frame 1
  - Seek to end → video shows last frame

- [ ] **Volume Control**
  - Volume slider adjusts from 0-100%
  - Mute (0%) → no audio
  - Max (100%) → full volume

- [ ] **Playback Speed**
  - Speed dropdown changes: 0.5x, 0.75x, 1.0x, 1.25x, 1.5x, 2.0x
  - Video plays at selected speed
  - Speed changes are smooth

- [ ] **Timecode Display**
  - Shows current time and duration in HH:MM:SS.mmm format
  - Updates in real-time during playback
  - Updates when seeking

### Video Format Support

Test with these video formats (if available):

- [ ] MP4 with H.264 + AAC (most common)
- [ ] MKV with H.265 + Opus
- [ ] MOV (macOS QuickTime format)
- [ ] AVI (legacy format)
- [ ] WebM with VP9 + Vorbis

### Audio-Video Synchronization

- [ ] **Long Video Test** (15+ minutes)
  - Play full video without seeking
  - Audio and video stay synchronized throughout
  - No audio drifting ahead or behind video
  - No audio underruns (playback pauses)

- [ ] **Seeking Test**
  - Seek to random positions throughout video
  - Audio and video sync immediately after seek
  - No audio gaps or stutters after seek

- [ ] **Multiple Seeks**
  - Rapid seeks forward/backward
  - Playback resumes smoothly each time
  - No crashes or hung threads

### Error Handling

- [ ] **Invalid File**
  - Select non-existent file → clear error message
  - Application doesn't crash
  - Can load another file after error

- [ ] **Corrupt Video File**
  - Load partially damaged MP4 → plays what it can
  - No crash or hang
  - Error logged in console

- [ ] **Missing Audio Stream**
  - Load video without audio track → video plays in video-only mode
  - No audio controls needed
  - Clear console message about missing audio

- [ ] **Missing Video Stream**
  - Load audio-only file (if available) → audio plays
  - Canvas shows black/empty
  - No crash

- [ ] **Unsupported Codec**
  - Load video with rare/unsupported codec → graceful error
  - Error message indicates codec issue
  - Can try different file

### UI Responsiveness

- [ ] **During Playback**
  - Controls respond immediately (no lag)
  - Seek is smooth and fast (<500ms)
  - No UI freezing during playback

- [ ] **Heavy Operations**
  - Seeking doesn't freeze UI
  - Volume changes are immediate
  - Speed changes don't stutter

### Platform-Specific Tests (as applicable)

#### macOS
- [ ] Play video on Intel Mac
- [ ] Play video on Apple Silicon Mac (if available)
- [ ] CustomTkinter styling looks correct
- [ ] No graphics glitches or artifacts

#### Windows
- [ ] Play video on Windows 10/11
- [ ] Test with multiple audio devices
- [ ] Check DirectShow integration

#### Linux
- [ ] Play video on Ubuntu 20.04/22.04 (if applicable)
- [ ] Test with PulseAudio/ALSA audio backends

## Debugging

### Enable Debug Logging
Edit the application startup to increase logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Console Output

Expected messages during playback:
```
video_censor_personal.ui - INFO - Using PyAVVideoPlayer
video_censor_personal.ui - INFO - Loading video: /path/to/video.mp4
video_censor_personal.ui - INFO - Container opened
video_censor_personal.ui - INFO - Video stream found: h264 1920x1080
video_censor_personal.ui - INFO - Audio stream found: aac
video_censor_personal.ui - INFO - Video loaded: duration=123.45s
```

### Common Issues & Solutions

**Issue**: "PyAV not available" error
- **Solution**: `pip install PyAV>=10.0.0`
- **Check**: `python3 -c "import av; print(av.__version__)"`

**Issue**: "No audio" during playback
- **Solution**: Check if video has audio stream (see console output)
- **Check**: Verify simpleaudio and pydub are installed
- **Debug**: Run `test_video_playback.py` to test audio player

**Issue**: Video plays but no audio
- **Likely cause**: Audio decoding error (check logs)
- **Debug**: Run `python3 poc_pyav.py` to test audio extraction

**Issue**: Seeking causes audio/video desync
- **Known limitation**: Advanced sync not yet implemented
- **Workaround**: Pause, seek, then resume
- **Expected in Phase 2**: Periodic sync checks

**Issue**: Video plays slowly or stutters
- **Likely cause**: Frame render is slow
- **Debug**: Check console for "Frame queue full" messages
- **Workaround**: Try smaller resolution video

**Issue**: Application crashes on specific file
- **Solution**: Check console error message
- **Debug**: Try `poc_pyav.py` with same file
- **Report**: Note file format, codec, and error

## Performance Metrics to Record

During testing, if you notice performance issues:

1. **Frame Decode Latency**
   - Should be <50ms per frame
   - Note if higher, which format

2. **Memory Usage**
   - Monitor memory during long playback
   - Check for memory leaks (steadily increasing memory)

3. **CPU Usage**
   - Should be <50% on modern CPU
   - Note if higher, which codec

4. **Audio-Video Sync Drift**
   - Should be <200ms over 30 minutes
   - Measure and note any drift

## Reporting Issues

If you find issues, include:

1. **File Details**
   - Path to video file
   - Format (MP4, MKV, etc.)
   - Video codec (H.264, H.265, etc.)
   - Audio codec (AAC, Opus, etc.)
   - Resolution and frame rate

2. **Error Messages**
   - Exact error text from console
   - Timestamp when it occurred

3. **Reproduction Steps**
   - Exact steps to reproduce the issue
   - Does it happen every time?

4. **System Info**
   - OS and version (macOS 13.0, Windows 11, etc.)
   - Python version: `python3 --version`
   - Installed packages: `pip list | grep -E "PyAV|pydub|simpleaudio"`

## Success Indicators

✓ **All tests pass** (`test_video_playback.py`)
✓ **Video plays with audio** (multiple formats)
✓ **Seeking works smoothly** (no audio/video drift)
✓ **Controls are responsive** (no UI lag)
✓ **Errors are handled gracefully** (no crashes)
✓ **No "audio-only mode" message** (macOS now supports full video!)

## Next Steps After Testing

If manual testing passes:

1. Document any platform-specific issues
2. Record performance metrics
3. Create a summary of results
4. Note any deferred improvements for Phase 2
5. Proceed with Phase 2 (platform testing, optimization)

---

**Test Date**: ________________
**Tester**: ________________
**Platform**: ________________
**Result**: ✓ Pass  ☐ Fail

Notes:
_________________________________________________________________
_________________________________________________________________
