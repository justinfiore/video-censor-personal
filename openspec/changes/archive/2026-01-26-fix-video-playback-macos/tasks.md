# Implementation Tasks: Fix Video Playback on macOS

## 1. Research & Proof of Concept (PyAV Only)

- [x] 1.1 Research PyAV library: installation, API, platform-specific notes, threading model
- [x] 1.2 Create minimal proof-of-concept script: load video with PyAV, decode frames, extract timing (PTS)
- [x] 1.3 Measure PyAV frame decode performance (current platform)
- [x] 1.4 Test PyAV frame rendering to Tkinter Canvas (numpy array → PIL Image → PhotoImage conversion)
- [x] 1.5 Test PyAV audio stream reading: extract, resample, format conversion
- [x] 1.6 Test pydub + simpleaudio audio playback backend on current platform
- [x] 1.7 Document findings and confirm PyAV is viable for production (pass/fail checkpoint)

## 2. Dependency Management

- [x] 2.1 Add PyAV (>= 10.0.0), pydub (>= 0.25.1), simpleaudio (>= 1.1.20) to requirements.txt
- [x] 2.2 Remove python-vlc from requirements.txt (being replaced by PyAV)
- [ ] 2.3 Test pip install on current platform to verify all dependencies resolve
- [ ] 2.4 Verify PyAV wheels include bundled FFmpeg 4.4.1+
- [ ] 2.5 Implement hybrid FFmpeg detection: check system ffmpeg (>= 4.0) first, fall back to PyAV's bundled version
- [ ] 2.6 Create installation guide for users: explain hybrid strategy, what to do if system ffmpeg check fails
- [ ] 2.7 Document minimum FFmpeg version requirement: 4.0+ (for codec support)

## 3. Audio Backend Implementation

- [x] 3.1 Create abstract `AudioPlayer` base class (parallel to VideoPlayer)
- [x] 3.2 Implement `SimpleAudioPlayer` using simpleaudio (playback) + pydub (format conversion)
- [x] 3.3 Add methods: play(), pause(), stop(), set_volume(), get_current_time(), is_playing()
- [x] 3.4 Implement audio stream reading with PyAV: extract audio frames, resample to target format (16-bit PCM, 48kHz)
- [x] 3.5 Use pydub to handle format conversion (PyAV → WAV/PCM → simpleaudio playback)
- [x] 3.6 Implement time tracking for audio (elapsed time for A/V sync, using samples played)
- [x] 3.7 Handle edge cases: no audio stream, mono/stereo/multi-channel audio, variable sample rates
- [ ] 3.8 Test audio callback integration with main thread (ensure no UI blocking)
- [ ] 3.9 Unit test AudioPlayer implementation (test audio loading, playback, volume, timing)

## 4. Video Rendering Implementation

- [x] 4.1 Create `PyAVVideoPlayer` subclass implementing VideoPlayer interface
- [x] 4.2 Implement PyAV container and stream management: open file, detect video stream, handle no-video case
- [x] 4.3 Implement frame decoding with PyAV: decode to RGB24 or YUV420P, extract frame timing (PTS)
- [x] 4.4 Implement frame → Tkinter Canvas rendering: numpy array → PIL Image → PhotoImage (via PIL)
- [x] 4.5 Implement seek functionality: seek to timestamp, flush decoder buffers, sync audio position
- [x] 4.6 Cache decoded frames intelligently: buffer ~30 frames ahead to smooth playback
- [ ] 4.7 Measure frame decode and render latency (target <50ms); benchmark decode vs. render overhead
- [ ] 4.8 Unit test frame decoding and rendering with various video formats (MP4 H.264, MKV H.265, WebM VP9)

## 5. Audio-Video Synchronization

- [x] 5.1 Implement A/V sync mechanism: track PTS (presentation timestamp) for both streams
- [x] 5.2 Implement frame drop logic: if video behind audio, skip frames to catch up
- [x] 5.3 Implement audio underrun handling: if audio runs dry, pause video temporarily
- [ ] 5.4 Implement periodic sync check (every 100 frames) to prevent drift accumulation
- [ ] 5.5 Document acceptable sync drift tolerance (recommend <200ms)
- [ ] 5.6 Unit test sync mechanisms with synthetic video/audio (predictable timing)

## 6. Threading & Concurrency

- [x] 6.1 Design thread architecture: main UI, decode thread, audio thread, render thread
- [x] 6.2 Implement thread-safe queues for frame and audio buffer passing (queue.Queue)
- [x] 6.3 Implement condition variables for sync signaling between threads
- [x] 6.4 Implement graceful thread shutdown: catch exceptions, clean up on error
- [ ] 6.5 Test thread safety under stress: rapid seek, play/pause, multiple format changes
- [ ] 6.6 Avoid deadlocks: use timeout on all blocking operations (queue.get, lock.acquire)

## 7. Error Handling & Fallback Modes

- [x] 7.1 Add graceful error handling: file not found, unsupported codec, corrupt file
- [x] 7.2 Implement fallback modes: video-only (no audio), audio-only (no video), paused with error
- [x] 7.3 Add codec detection: use ffmpeg to introspect stream information on load
- [x] 7.4 Implement user-facing error messages: "Video format not supported", "Audio unavailable"
- [x] 7.5 Log detailed diagnostics: ffmpeg output, stream info, decode errors
- [ ] 7.6 Test error handling with corrupted/invalid video files
- [ ] 7.7 Unit test error path code coverage

## 8. Integration with Existing UI

- [x] 8.1 Update `VideoPlayerPane` to use new PyAVVideoPlayer (backward compatible with VideoPlayer interface)
- [ ] 8.2 Test integration with segment list, details panel (verify no UI regressions)
- [ ] 8.3 Test seek from segment list: click segment → video plays at that timestamp
- [ ] 8.4 Test play/pause, volume control, playback speed with existing UI controls
- [ ] 8.5 Verify CustomTkinter styling preserved (no visual regressions)

## 9. Platform-Specific Testing

- [ ] 9.1 macOS testing: Intel and Apple Silicon (M1/M2/M3), various OS versions
- [ ] 9.2 Windows testing: Windows 10/11, both 64-bit
- [ ] 9.3 Linux testing: Ubuntu 20.04, 22.04; Fedora; elementary OS (if time permits)
- [ ] 9.4 Test PyAV frame decoding performance on each platform
- [ ] 9.5 Test pydub + simpleaudio audio playback: MP3, AAC, FLAC, Opus formats on each platform
- [ ] 9.6 Test A/V sync with test videos: measure drift over 5, 15, 30 minute durations on each platform
- [ ] 9.7 Test PyAVVideoPlayer with CustomTkinter Canvas widget on each platform
- [ ] 9.8 Integration test full preview editor UI workflow on macOS, Windows, Linux
- [ ] 9.9 Test common video formats on each platform: MP4, MKV, AVI, MOV, WebM
- [ ] 9.10 Test codec combinations: H.264 + AAC, H.265 + Opus, VP9 + Vorbis on each platform
- [ ] 9.11 Integration test multithreaded playback on all platforms
- [ ] 9.12 Document platform-specific issues or workarounds found

## 10. Performance Optimization

- [ ] 10.1 Profile frame decode latency: identify bottlenecks (decode vs. render vs. sync)
- [ ] 10.2 Profile memory usage with large video files (check for memory leaks)
- [ ] 10.3 Benchmark seek performance: measure time to render first frame at new position
- [ ] 10.4 Optimize if frame render >30ms: consider OpenGL rendering (defer if not needed)
- [ ] 10.5 Optimize if A/V sync drift >200ms over 30 minutes: adjust sync frequency
- [ ] 10.6 Document performance characteristics and optimization tips

## 11. Documentation & Examples

- [ ] 11.1 Update `VideoPlayer` interface docstring (if needed)
- [ ] 11.2 Document `PyAVVideoPlayer` class: constructor, methods, error handling
- [ ] 11.3 Document `AudioPlayer` and implementations
- [ ] 11.4 Write integration guide: how to use new video player with CustomTkinter
- [ ] 11.5 Create troubleshooting guide: common issues and solutions (codec not found, slow render, etc.)
- [ ] 11.6 Create example script: standalone video player (non-UI) using PyAVVideoPlayer for testing
- [ ] 11.7 Document platform-specific build/deployment steps

## 12. FFmpeg Dependency Strategy (Development, Not Packaging)

- [ ] 12.1 Implement hybrid FFmpeg detection: check system `ffmpeg` (>= 4.0) via `which`, set env var or use bundled PyAV version
- [ ] 12.2 Document decision: use PyAV's bundled FFmpeg 4.4.1+ as primary, system ffmpeg as optional override
- [ ] 12.3 Test that PyAV wheels include bundled FFmpeg: verify `import av` works on current platform
- [ ] 12.4 Create user-facing error messages: "FFmpeg not found. Bundled version may be corrupted. Install ffmpeg or reinstall application."
- [ ] 12.5 Document FFmpeg version requirements: minimum 4.0+ for codec support
- [ ] 12.6 Coordinate with installer spec: packaging handles FFmpeg bundling in installers
- [ ] 12.7 For development (pip install), assume PyAV wheels handle FFmpeg; document system fallback

## 13. Testing & Quality Assurance

- [ ] 13.1 Write unit tests for `PyAVVideoPlayer`: load, play, pause, seek, cleanup
- [ ] 13.2 Write unit tests for `AudioPlayer`: load audio, play, volume, timing
- [ ] 13.3 Write unit tests for A/V sync logic with mocked audio/video streams
- [ ] 13.4 Write integration tests: full playback workflow (open file, play, seek, stop)
- [ ] 13.5 Write regression tests: verify VideoPlayer interface compatibility, UI still works
- [ ] 13.6 Achieve minimum 80% code coverage for new video_player.py code

## 14. Cleanup & Deprecation (Phase 3)

- [x] 14.1 Remove VLC-related code paths: delete VLCVideoPlayer class from video_player.py
- [x] 14.2 Verify requirements.txt: remove python-vlc (already done in section 2.2)
- [x] 14.3 Remove VLC import checks from codebase: simplify error handling (no fallback to VLC)
- [ ] 14.4 Remove VLC installation from CI/CD pipelines if present
- [ ] 14.5 Remove or archive VLC-related troubleshooting docs
- [ ] 14.6 Update CHANGELOG documenting: "Replaced VLC with PyAV for cross-platform video playback support on macOS, Windows, Linux"
- [ ] 14.7 Verify no lingering imports: grep for "vlc" and "VLC" in codebase (done, only in docs/spec/archives)

## 15. Final Validation

- [ ] 15.1 Review design.md decisions against implementation: PyAV ✓, pydub+simpleaudio ✓, hybrid FFmpeg ✓, threading model ✓
- [ ] 15.2 Verify all requirements from spec.md are implemented and tested
- [ ] 15.3 Review Section 9 results: all platform-specific testing complete, no blocking issues
- [ ] 15.4 Run full test suite: unit + integration + UI tests passing on all platforms (from Section 9)
- [ ] 15.5 Verify all success criteria from design.md met:
  - [ ] Video plays on macOS with audio/video synchronized (from Section 9.1, 9.8)
  - [ ] Video plays on Windows with audio/video synchronized (from Section 9.2, 9.8)
  - [ ] Video plays on Linux with audio/video synchronized (from Section 9.3, 9.8)
  - [ ] Seeking to arbitrary timestamps works reliably (from Section 9.8)
  - [ ] No crashes when loading incompatible codecs (graceful error)
  - [ ] Frame rendering smooth (30+ fps, <50ms latency) (from Section 9.4)
  - [ ] A/V sync drift <200ms over 30-minute video (from Section 9.6)
  - [ ] FFmpeg accessible (bundled in PyAV wheels or system fallback)
- [ ] 15.6 Conduct manual end-to-end testing with real video files (various formats, codecs, resolutions)
- [ ] 15.7 Document final status, performance metrics, known limitations, codec support matrix
- [ ] 15.8 Verify pip install works: `pip install video-censor-personal` with PyAV, all deps, video playback functional
- [ ] 15.9 Coordinate with installer spec: installers (separate spec) will bundle everything
- [ ] 15.10 Prepare for archival: move `changes/fix-video-playback-macos/` → `changes/archive/YYYY-MM-DD-fix-video-playback-macos/`
