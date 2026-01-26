# Design: Cross-Platform Video Playback Solution

## Context

The current implementation uses python-vlc bindings to play video within a tkinter widget. However, VLC's plugin architecture and tkinter's display model are fundamentally incompatible on macOS (and have compatibility issues on other platforms):

- **macOS**: VLC cannot render to a tkinter Canvas/Frame due to windowing system differences
- **Windows**: Windows Media Player backend adds platform-specific complexity
- **Linux**: X11 window embedding works but is fragile across distributions

User priorities for this solution:
1. Ease of use (everything bundled, no external setup)
2. Cross-platform consistency (single implementation)
3. Reliability (no crashes, audio/video always synchronized)
4. Open-source (permissive licenses)

## Goals

**Goals:**
- Enable full video+audio playback on macOS, Windows, Linux
- Eliminate VLC + tkinter integration issues
- Maintain VideoPlayer interface for backward compatibility
- Minimize user friction (bundled dependencies, no configuration)

**Non-Goals:**
- Advanced video effects or filters (playback only)
- Hardware acceleration optimization (defer to implementation phase if needed)
- Support for obscure video codecs (rely on ffmpeg/platform codec libraries)
- DRM-protected content (assume standard video formats)

## Decisions

### 1. Solution Selection: PyAV (FFmpeg Python Bindings)

**Decision: PyAV**

**Rationale:**
- **Cross-platform**: Works identically on macOS, Windows, Linux with single codebase
- **Audio+Video Synchronization**: FFmpeg handles both streams with guaranteed synchronization (no manual A/V sync code needed)
- **Tkinter-compatible**: Can render frames to Tkinter Canvas/PhotoImage without windowing conflicts
- **Codec support**: FFmpeg supports virtually all video formats (MP4, MKV, AVI, MOV, WebM, H.264, H.265, VP9, AAC, MP3, FLAC, Opus, etc.)
- **Packaging**: FFmpeg can be bundled (PyAV ships with 4.4.1+) or use system version (>= 4.0)
- **License**: LGPL is compatible with project goals
- **Community**: Active maintenance, well-documented, widely used in production video applications
- **No UI refactor needed**: VideoPlayer interface remains unchanged; PyAV replaces internal VLC implementation only

**Alternatives Evaluated:**
See `openspec/changes/other-video-playback-research-candidates/research-findings.md` for detailed evaluation of pygame, OpenCV, moviepy, VLC, Kivy, and why they were rejected. Key summary:
- pygame: Simpler API but legacy, fewer codecs, no A/V sync guarantee
- OpenCV: No audio support (frame extraction only)
- moviepy: Too slow for real-time playback
- Kivy: Would require wholesale UI refactor (out of scope)
- VLC: Already proven incompatible with macOS + tkinter

### 2. Integration Architecture

**Data Flow:**

```
FFmpeg (PyAV) → Frame + Audio Buffer
                    ↓
             TKinter Canvas (frame display)
             + Audio Backend (playback)
                    ↓
              Synchronized Output
```

**Implementation Approach:**
1. Use PyAV to read video stream (frame-by-frame)
2. Render frames to Tkinter Canvas via PhotoImage conversion
3. Use Tkinter's audio callback or pydub + simpleaudio for audio playback
4. Synchronize by tracking time offset between video and audio playback threads

**Threading Model:**
- Main UI thread: Handles user interactions (play, pause, seek)
- Video decode thread: Pulls frames from FFmpeg, updates Canvas
- Audio thread: Manages audio playback and sync signals
- Thread communication via thread-safe queues

### 3. Dependency Strategy

**Option A: Vendored FFmpeg (Recommended)**
- Bundle ffmpeg binaries with application
- Works offline, no external tool requirements
- Larger distribution size (~50-100MB)
- Simplest user experience

**Option B: System FFmpeg**
- User's system FFmpeg (via `brew install ffmpeg` on macOS, etc.)
- Smaller distribution, minimal footprint
- Requires user setup (acceptable if documented)

**Option C: Hybrid**
- Default to system FFmpeg, bundle fallback if not found
- Best of both worlds (UX + flexibility)

**Decision: Option C (Hybrid with Preference for Bundled)**
- Implement PyAV with `which ffmpeg` check
- If system FFmpeg unavailable, use bundled version (or error with setup instructions)
- For macOS app bundle: Embed ffmpeg in `.app/Contents/Resources`

### 4. Error Handling & Fallback Modes

**Graceful Degradation:**
1. **Video decode fails**: Log error, display static frame, play audio only
2. **Audio unavailable**: Play video without sound, show user warning
3. **Frame render lag**: Drop frames to maintain audio sync (audio is priority)
4. **Seek out of bounds**: Clamp to valid range, notify user
5. **File format unsupported**: Display error dialog with codec info, user can try different file

**Diagnostics:**
- Log codec information on load (`ffmpeg -i file.mp4` equivalent)
- Report available vs required streams (video, audio)
- Measure decode/render latency and report issues

### 5. Codec & Format Support

**Guaranteed Support (FFmpeg bundled):**
- **Video**: H.264 (AVC), H.265 (HEVC), VP9, ProRes, DNxHD
- **Audio**: AAC, MP3, FLAC, Opus, Vorbis
- **Containers**: MP4, MKV, AVI, MOV, WebM, FLV

**Best Effort (system-dependent codecs):**
- MPEG-2, VC-1, RealMedia, others (rely on system codec libraries)

### 6. Performance Considerations

**Frame Render Optimization:**
- Use `numpy` to avoid memory copies: `ffmpeg → numpy array → PhotoImage`
- Cache PhotoImage objects to reduce GC overhead
- Drop duplicate frames if display refresh rate is slower than decode rate

**Latency Targets:**
- Frame decode: <50ms (acceptable for 20 fps UI updates)
- Frame render: <16ms (60 fps display)
- Seek latency: <500ms (reasonable for UI responsiveness)

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|-----------|
| **FFmpeg library complexity** | Slow learning curve for maintainers | Wrap FFmpeg in simple abstraction, extensive documentation |
| **Large binary size (bundled FFmpeg)** | Installation size bloat | Use builds with minimal codec support, compress, document download time |
| **Thread safety issues** (decode + render + audio) | Crashes, A/V sync loss | Use proven patterns: thread-safe queues, condition variables, careful state management |
| **macOS app signing** (if bundled ffmpeg) | Code signature breaks on M1/Intel | Use notarization for bundled binaries, document process |
| **Tkinter Canvas rendering bottleneck** | Frame rendering too slow, video stutter | Benchmark early; fallback to OpenGL if needed (advanced, defer) |
| **Audio format incompatibility** (system audio API) | Audio won't play on some Linux distros | Test on common distros (Ubuntu, Fedora); use system audio backend detection |

## Migration Plan

### Phase 1: Prototype & Research (this spec)
- Evaluate PyAV, pygame, and other candidates with proof-of-concept code
- Test on macOS, Windows, Linux (physical or VMs)
- Benchmark frame rendering and A/V sync latency
- Confirm CustomTkinter integration works

### Phase 2: Implementation (in apply stage, tracked by tasks.md)
- Implement PyAV-based VideoPlayer subclass
- Add audio playback backend (pydub + simpleaudio or PyAudio)
- Implement frame rendering to Tkinter Canvas
- Implement seeking and sync mechanisms
- Write comprehensive unit and integration tests
- Document platform-specific build/packaging steps
- Use the already installed `ffmpeg` if it is available AND a sufficient version. If it isn't available, use the bundled version.
- The installation should always include the bundled version so the application can "just work" on any platform.

### Phase 3: Validation & Deployment
- End-to-end testing on all platforms
- Performance benchmarking
- Create bundled distributions (macOS .app, Windows installer, Linux AppImage)
- User testing with preview editor UI
- Document troubleshooting and codec support

### Rollback Plan
- Remove VLC implementation (we already checked that in on a separate branch if we want to get back to it.)
- If PyAV integration fails, abort and let me know.


## Open Questions

1. Should bundled FFmpeg be statically or dynamically linked? Static
   - Static: Larger binary, zero dependencies, simpler deployment
   
2. What's the acceptable application bundle size for users?
   - Bundled FFmpeg alone adds 50-100MB; is this acceptable? Yes

3. Should we support HW acceleration (VA-API on Linux, NVENC on Windows, VideoToolbox on macOS)?
   - Deferred to Phase 2 if performance is acceptable without it

4. For audio playback, should we use pydub+simpleaudio or PyAudio? pydub + simpleaudio

## Success Criteria

- [ ] Video plays on macOS with audio and video synchronized
- [ ] Video plays on Windows with audio and video synchronized
- [ ] Video plays on Linux with audio and video synchronized
- [ ] Seeking to arbitrary timestamps works reliably
- [ ] No crashes when loading incompatible codecs (graceful error)
- [ ] Frame rendering is smooth (no visible stuttering) at 30+ fps
- [ ] A/V sync drift is <200ms over 30-minute video
- [ ] Integration tests pass on all three platforms
- [ ] User can play typical MP4/MKV files without external setup
