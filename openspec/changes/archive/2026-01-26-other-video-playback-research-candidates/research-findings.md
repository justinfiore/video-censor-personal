# Research Findings: Video Playback Solutions Evaluation

## Evaluation Criteria

Solutions were evaluated against these requirements:
1. Cross-platform support (macOS, Windows, Linux with single codebase)
2. Audio + video synchronization guarantee
3. Seeking to arbitrary timestamps
4. CustomTkinter UI integration without stability compromise
5. Open-source with permissive licenses (MIT, Apache 2.0, LGPL)
6. Ease of use (minimal user configuration, bundled dependencies preferred)
7. Active maintenance and community support

## Candidate Evaluation Matrix

| Solution | Pros | Cons | License | Status |
|----------|------|------|---------|--------|
| **PyAV** (FFmpeg binding) | Cross-platform, full codec support, Tkinter-compatible, audio+video sync guaranteed, FFmpeg can be bundled | Steeper learning curve for maintainers, larger binary footprint (~50-100MB with bundled FFmpeg) | LGPL (compatible) | ✅ **SELECTED** |
| **pygame** | Simple API, cross-platform, lightweight, good Tkinter integration | Older project, less active maintenance, fewer video codecs, audio sync issues | LGPL (compatible) | ❌ Rejected |
| **OpenCV (cv2)** | Fast frame extraction, video reading, widely used | Does NOT support audio playback (frame-by-frame extraction only, unsuitable for real-time playback), no A/V sync | BSD (compatible) | ❌ Rejected |
| **moviepy** | High-level Python API, handles audio+video, good for quick prototypes | Much slower than needed (unsuitable for real-time playback), heavy dependencies (ImageIO, librosa, etc.), not designed for streaming playback | MIT (compatible) | ❌ Rejected |
| **VLC (python-vlc)** | Full-featured, most codec support, works on all platforms | macOS + tkinter incompatible (VLC window embedding fails), complex windowing model, Windows Media Player backend adds platform-specific complexity, already proven broken in this project | LGPL (current, known broken) | ❌ Rejected (current solution, proven incompatible) |
| **Kivy** | Modern UI framework with built-in video support, active community | Would require complete UI refactor (replacing CustomTkinter), massive scope expansion (out of scope for video player fix), steep learning curve for team | MIT (compatible) | ❌ Rejected (architectural mismatch) |

## Detailed Analysis

### PyAV (Selected)

**Why chosen:**
- Cross-platform: Identical code path on macOS, Windows, Linux
- Audio+Video: FFmpeg handles both streams with guaranteed synchronization (no manual A/V sync code needed)
- Tkinter-compatible: Can render frames to Tkinter Canvas/PhotoImage without windowing conflicts
- Codec support: FFmpeg supports virtually all video formats (MP4, MKV, AVI, MOV, WebM, etc.)
- Packaging: FFmpeg can be bundled (PyAV ships with 4.4.1+) or use system version
- License: LGPL compatible with project
- Community: Active maintenance, widely used in production

**Known challenges:**
- Learning curve: FFmpeg API is more complex than VLC, requires careful threading/buffering
- Binary size: Bundled FFmpeg adds 50-100MB to distribution
- Mitigation: Wrap FFmpeg in simple abstraction, provide documentation; compress distribution if needed

### pygame (Rejected)

**Why rejected:**
- Legacy project: Less active than PyAV, smaller community
- Fewer codecs: Relies on platform-specific codecs, unreliable on some systems
- A/V sync: No built-in synchronization guarantee; requires manual implementation
- Performance: Adequate for simple games, but not optimized for video playback

### OpenCV (Rejected)

**Why rejected:**
- **Critical limitation**: Does NOT provide audio playback capabilities
- Frame-by-frame extraction only: Designed for computer vision (frame analysis), not playback
- Would require separate audio library: Doubles complexity without clear benefit over PyAV
- Performance: Optimized for frame extraction/processing, not continuous playback

### moviepy (Rejected)

**Why rejected:**
- **Performance blocker**: Much slower than needed for real-time playback
- Heavy dependencies: Brings in large dependency tree (ImageIO, librosa, scipy, etc.)
- Design mismatch: Built for video editing/composition, not streaming playback
- Not designed for Tkinter integration: Would require significant adaptation

### VLC (Current, Proven Broken)

**Why rejected (already confirmed in project):**
- **macOS + tkinter incompatibility**: VLC's plugin architecture cannot render to tkinter Canvas/Frame on macOS
- Windows complexity: Relies on Windows Media Player backend (platform-specific fragility)
- Linux fragility: X11 window embedding works but breaks across distributions
- Already proven in codebase: Line 122 of `video_player.py` explicitly disables video output on macOS

### Kivy (Rejected)

**Why rejected:**
- **Architectural mismatch**: Kivy is a complete UI framework; replacing CustomTkinter is out of scope
- Scope explosion: Would require rewriting entire UI layer (preview editor, segment list, details panel, etc.)
- Team fit: No prior Kivy experience, steep learning curve
- Not justified: Problem is video playback, not UI framework

## Conclusion

**PyAV** is the optimal choice because:
1. ✅ Solves the immediate problem: cross-platform video playback on macOS, Windows, Linux
2. ✅ Minimal scope: No UI refactor needed, VideoPlayer interface unchanged
3. ✅ Future-proof: FFmpeg is industry standard (used in VLC, OBS, ffmpeg-python, etc.)
4. ✅ Maintainable: Clear separation of concerns (decode + render + audio)
5. ✅ Proven: Thousands of applications use PyAV successfully

## Fallback Strategy

If PyAV implementation encounters blockers:
1. **Short-term fallback**: pygame (simpler API, lower performance acceptable as fallback)
2. **Long-term fallback**: Kivy (requires UI refactor, deferred if needed)

## Research Archive

This document preserves the evaluation for future reference. No action items; this is documentation-only.
