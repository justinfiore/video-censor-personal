# video-playback Specification

## ADDED Requirements

### Requirement: Cross-Platform Video Playback with Audio and Video Synchronization

The system SHALL support synchronized video and audio playback on macOS, Windows, and Linux. Playback SHALL be provided via a pluggable VideoPlayer interface that abstracts the underlying implementation. The system SHALL support seeking to arbitrary timestamps and SHALL handle audio and video streams in perfect synchronization.

#### Scenario: Video playback on macOS with full video and audio output
- **WHEN** a user loads a video file (MP4, MKV, AVI) in the preview editor UI on macOS
- **THEN** the video displays in the video player canvas with clear, undistorted video frames
- **AND** audio plays simultaneously with the video (both streams start at the same time)
- **AND** audio and video remain synchronized throughout playback (drift <200ms over 30-minute duration)
- **AND** the video can be played, paused, and resumed without loss of sync

#### Scenario: Video playback on Windows with full video and audio output
- **WHEN** a user loads a video file on Windows
- **THEN** the video displays in the video player with synchronized audio output
- **AND** all playback controls function identically to macOS behavior
- **AND** supported formats (MP4, MKV, WebM, etc.) play without external setup or dependencies

#### Scenario: Video playback on Linux with full video and audio output
- **WHEN** a user loads a video file on Linux (Ubuntu, Fedora, or similar distribution)
- **THEN** the video plays with synchronized audio
- **AND** audio output uses the system's default audio backend (PulseAudio, ALSA, PipeWire)
- **AND** no external configuration or VLC installation is required

#### Scenario: Seeking to an arbitrary timestamp
- **WHEN** user clicks on a segment in the segment list to jump to a specific time
- **THEN** the video player seeks to the specified timestamp
- **AND** the new frame is rendered within 500ms of the seek command
- **AND** audio resumes playback from the same timestamp
- **AND** audio and video remain synchronized after seek

#### Scenario: Support for common video formats
- **WHEN** a user attempts to load a video file in any of these formats: MP4, MKV, AVI, MOV, WebM
- **THEN** the video loads successfully and plays without errors
- **AND** video codec support includes: H.264 (AVC), H.265 (HEVC), VP9, ProRes (where applicable)
- **AND** audio codec support includes: AAC, MP3, FLAC, Opus, Vorbis

#### Scenario: Graceful handling of unsupported codecs
- **WHEN** user attempts to load a video file with an unsupported or corrupted video stream
- **THEN** the system logs detailed codec information (via ffmpeg introspection)
- **AND** an error message is displayed to the user: "Video format not supported. Codec: [codec name]"
- **AND** the application does NOT crash
- **AND** the user can attempt to load a different video file

#### Scenario: Video playback with missing audio stream
- **WHEN** user loads a video file that contains only video stream (no audio track)
- **THEN** the video plays normally without errors
- **AND** the system logs a warning: "No audio stream detected in video file"
- **AND** playback continues in video-only mode (no audio output expected)
- **AND** all video controls (play, pause, seek) function normally

#### Scenario: Video playback with missing video stream
- **WHEN** user loads a file that contains only an audio stream (e.g., WAV, MP3 file mistakenly opened)
- **THEN** the system logs an error: "No video stream detected"
- **AND** an error message is displayed to the user
- **AND** the application does NOT crash
- **AND** playback does NOT begin

### Requirement: Audio-Video Synchronization

The system SHALL maintain synchronization between audio and video streams during playback, seeking, and pause/resume operations. Synchronization drift SHALL be measured and monitored to ensure user experience is not degraded.

#### Scenario: Audio and video stay synchronized during extended playback
- **WHEN** a user plays a 30-minute video file
- **THEN** audio and video remain in sync from start to finish
- **AND** A/V sync drift does NOT exceed 200ms at any point during playback
- **AND** no manual sync adjustment by user is required

#### Scenario: Sync recovery after seek operation
- **WHEN** user seeks to a new timestamp in the video
- **THEN** audio and video both resume from the same timestamp
- **AND** they remain synchronized immediately following the seek (within first 1 second after seek)
- **AND** no audio stutter or video frame skip is visible to the user

#### Scenario: Sync is maintained after pause and resume
- **WHEN** user pauses playback and then resumes after 5+ seconds of pause
- **THEN** audio and video resume at the same position
- **AND** no sync drift is introduced by the pause/resume cycle

### Requirement: Frame Rendering Performance

The system SHALL render video frames smoothly to the UI without visible stuttering. Frame rendering latency SHALL be optimized to accommodate the screen refresh rate while maintaining audio sync.

#### Scenario: Smooth video playback at 30+ frames per second
- **WHEN** user plays a video file on any supported platform
- **THEN** video playback is smooth with no visible stuttering, lag, or frame skipping
- **AND** frame rendering latency is <50ms per frame on typical hardware
- **AND** audio does NOT buffer or skip due to rendering delays

#### Scenario: Performance degrades gracefully on slower systems
- **WHEN** frame rendering takes longer than expected due to CPU/system constraints
- **THEN** the system prioritizes audio playback (audio continues uninterrupted)
- **AND** video frames are dropped if necessary to maintain audio sync
- **AND** user sees a warning indicator (e.g., "Performance: frame drops detected")
- **AND** playback does NOT pause or crash

### Requirement: Playback Control Interface

The system SHALL provide a consistent VideoPlayer interface that abstracts the underlying implementation. All playback controls (play, pause, seek, volume) SHALL function identically across platforms.

#### Scenario: VideoPlayer interface supports all required operations
- **WHEN** the VideoPlayer implementation is used (either directly or via UI)
- **THEN** the following methods MUST work correctly on macOS, Windows, and Linux:
  - `load(video_path)` - Load a video file
  - `play()` - Start or resume playback
  - `pause()` - Pause playback
  - `seek(seconds)` - Jump to a specific timestamp
  - `set_volume(level)` - Set volume (0.0 to 1.0)
  - `get_current_time()` - Get current position in seconds
  - `get_duration()` - Get total video duration
  - `is_playing()` - Check if video is currently playing

#### Scenario: Backward compatibility with existing UI code
- **WHEN** the UI code (segment list, details panel, video player pane) uses the VideoPlayer interface
- **THEN** no changes to the UI code are required beyond implementation switching
- **AND** the interface contract remains unchanged (same method signatures, return types)
- **AND** all existing functionality (preview editor UI) works with the new VideoPlayer implementation

### Requirement: Cross-Platform Ease of Use (Dependency Management)

The system SHALL minimize setup friction for end-users by providing a simple installation experience. External dependencies (FFmpeg, system libraries) SHALL be automatically detected or bundled.

#### Scenario: User can play video without external setup (pip install - development)
- **WHEN** developer installs via `pip install video-censor-personal`
- **THEN** video playback works with PyAV's bundled FFmpeg (or system FFmpeg if >= 4.0)
- **AND** no additional `ffmpeg` installation steps required
- **AND** all audio/video dependencies (pydub, simpleaudio) automatically installed

#### Scenario: User can play video without any setup (standalone installers)
- **WHEN** end-user downloads and installs using platform-specific installer
  - Windows: `video-censor-personal-setup.exe`
  - macOS: `Video-Censor-Personal.dmg`
  - Linux: `video-censor-personal-x86_64.AppImage`
- **THEN** all dependencies (FFmpeg, audio libraries, Python, models) are bundled
- **AND** video playback works immediately after installation
- **AND** no external tool installation required
- **AND** see openspec/changes/installer/ spec for installer-specific details and requirements

#### Scenario: Clear error messages if dependencies are missing
- **WHEN** a required dependency (FFmpeg library) is not available on the system
- **THEN** an error message displays explaining which dependency is missing
- **AND** installation instructions are provided (e.g., "Run: brew install ffmpeg")
- **AND** the application does NOT crash with an obscure import error

### Requirement: Error Handling and Diagnostics

The system SHALL provide comprehensive error handling for file loading, codec detection, and playback failures. Diagnostic information SHALL be logged to assist troubleshooting.

#### Scenario: File not found error is handled gracefully
- **WHEN** user attempts to load a video file that does not exist
- **THEN** an error message displays: "File not found: [path]"
- **AND** the application does NOT crash
- **AND** the user can select a different file

#### Scenario: Detailed diagnostics logged for codec issues
- **WHEN** a video file with unsupported or corrupted codec is loaded
- **THEN** the system logs detailed information using ffmpeg introspection:
  - Video codec name (e.g., "mpeg2video")
  - Audio codec name (e.g., "ac3")
  - Resolution and frame rate
  - Duration
  - Any decode errors encountered
- **AND** this information is available in the application log file for debugging

#### Scenario: Corrupted file is handled without crash
- **WHEN** user attempts to play a corrupted or invalid video file
- **THEN** an error message displays: "Failed to read video file. File may be corrupted."
- **AND** the application does NOT crash
- **AND** the user can attempt to load a different file
