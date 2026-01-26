# Change: Fix Video Playback on macOS and Ensure Cross-Platform Compatibility

## Why

Video playback is currently broken on macOS due to VLC + tkinter integration issues. Line 122 of `video_censor_personal/ui/video_player.py` explicitly disables video output on macOS, falling back to audio-only mode. This breaks a critical user-facing feature: the preview editor UI cannot display video content on the primary development platform.

Beyond macOS, we need a robust, cross-platform solution that works on Windows, macOS, and Linux with synchronized audio and video, seeking support, and proper error handling.

**Why PyAV:** We evaluated multiple video playback solutions (pygame, OpenCV, moviepy, VLC, Kivy) and determined PyAV (FFmpeg Python bindings) is optimal. See `openspec/changes/other-video-playback-research-candidates/research-findings.md` for detailed analysis. PyAV provides:
- Cross-platform identical implementation (macOS, Windows, Linux)
- Guaranteed audio+video synchronization (FFmpeg handles both streams)
- Tkinter Canvas compatibility (no windowing conflicts)
- Industry-standard FFmpeg backend (widely used, reliable, actively maintained)
- No UI refactor needed (VideoPlayer interface unchanged)

## What Changes

- **Replace VLC with PyAV (FFmpeg Python bindings)** for cross-platform video decoding and frame extraction
- **Implement audio playback backend** using pydub + simpleaudio for synchronized audio output
- **Create video-playback capability spec** documenting cross-platform video+audio playback requirements
- **Update video player implementation** to support full video+audio playback on macOS, Windows, and Linux
- **Add robust error handling** with graceful fallback modes (video-only, audio-only, paused with error)
- **Implement A/V synchronization mechanism** using presentation timestamps (PTS) and frame-drop logic
- **Design multi-threaded architecture** with decode, audio, and render threads using thread-safe queues
- **Ensure backward compatibility** with existing UI code (VideoPlayer interface contract unchanged)
- **Establish hybrid FFmpeg dependency strategy**: prefer system FFmpeg if available (>= 4.0), fall back to PyAV's bundled version
- **Document platform-specific bundling** (macOS .app, Windows installer, Linux AppImage with embedded ffmpeg)

## Impact

- **Affected specs**: `desktop-ui`, `segment-review` (implied by preview editor UI change)
- **Affected code**:
  - `video_censor_personal/ui/video_player.py` (primary implementation, replace VLC with PyAV)
  - `video_censor_personal/ui/video_player_pane.py` (integration point, no changes to interface)
  - `requirements.txt` (add PyAV, pydub, simpleaudio; remove python-vlc)
  - `setup.py` or equivalent (packaging and platform-specific dependencies)
- **Breaking changes**: None (VideoPlayer abstract interface remains stable; internal VLC implementation replaced with PyAV)
- **New dependencies**:
  - `PyAV >= 10.0.0` (FFmpeg Python bindings)
  - `pydub >= 0.25.1` (audio processing)
  - `simpleaudio >= 1.1.20` (cross-platform audio playback)
  - Bundled FFmpeg 4.4.1+ (included in PyAV wheels)
- **Removed dependencies**:
  - `python-vlc` (being replaced)
- **Platform-specific deployment**: 
  - Hybrid strategy: system FFmpeg if available (>= 4.0), otherwise use PyAV's bundled version
  - macOS .app: embed ffmpeg in `.app/Contents/Resources` (Optional; PyAV wheels handle this)
  - Windows installer: include ffmpeg binary (~50-100MB) or rely on bundled PyAV version
  - Linux AppImage: bundle ffmpeg or specify system dependency documentation

## Goals

1. Video playback MUST work on macOS, Windows, and Linux
2. Solution MUST be platform-independent (single code path where feasible)
3. MUST use open-source libraries with compatible licenses (MIT, Apache 2.0, LGPL, etc.)
4. MUST prioritize ease of use for end-users (minimal configuration, bundled dependencies)
5. Audio and video MUST be synchronized and play together
6. Seeking to arbitrary timestamps MUST be supported
7. Solution MUST integrate seamlessly with CustomTkinter UI without compromising stability
