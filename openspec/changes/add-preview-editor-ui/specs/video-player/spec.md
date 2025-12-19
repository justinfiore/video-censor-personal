## ADDED Requirements

### Requirement: Video Player Component Interface

The system SHALL provide a VideoPlayer abstraction that encapsulates video playback logic and enables easy substitution of different video playback backends. The component SHALL expose a consistent interface for loading, playing, seeking, and controlling volume.

#### Scenario: Load video file into player
- **WHEN** VideoPlayer.load("/path/to/video.mp4") is called
- **THEN** video file is loaded and ready to play
- **AND** duration is determined and available via VideoPlayer API
- **AND** subsequent play() calls start playback from time 0

#### Scenario: Play video from current position
- **WHEN** VideoPlayer.play() is called after load()
- **THEN** video begins playing
- **AND** audio plays in sync with video
- **AND** playback can be paused with pause()

#### Scenario: Pause video playback
- **WHEN** VideoPlayer.pause() is called during playback
- **THEN** video stops at current frame
- **AND** seeking works from paused state
- **AND** calling play() resumes from paused position

#### Scenario: Seek to arbitrary timestamp
- **WHEN** VideoPlayer.seek(45.5) is called (45.5 seconds)
- **THEN** video jumps to 45.5 seconds
- **AND** playback continues from new position (if was playing)
- **AND** audio remains synchronized with video
- **AND** seeking latency is <500ms

#### Scenario: Control volume
- **WHEN** VideoPlayer.set_volume(0.75) is called (0.0-1.0 range)
- **THEN** audio volume is set to 75%
- **AND** muting (0.0) silences audio completely
- **AND** max volume (1.0) plays at full strength

#### Scenario: Get current playback time
- **WHEN** VideoPlayer.get_current_time() is called during playback
- **THEN** current position in seconds is returned (e.g., 45.5)
- **AND** accuracy is within 100ms
- **AND** value updates continuously as video plays

#### Scenario: Register time-change callback
- **WHEN** VideoPlayer.on_time_changed(callback) is registered
- **THEN** callback is invoked periodically during playback (e.g., every 50ms)
- **AND** callback receives current time as parameter
- **AND** UI can synchronize visual elements (timeline, timecode) based on callback

#### Scenario: Clean up resources
- **WHEN** VideoPlayer.cleanup() is called
- **THEN** video file handle is closed
- **AND** audio resources are released
- **AND** subsequent load() calls work correctly (can load new file)

### Requirement: Video Player Widget Integration

The system SHALL integrate the VideoPlayer component into a UI widget that can be embedded in the three-pane layout. The widget SHALL render video frames and provide interactive controls.

#### Scenario: Video player widget displayed in UI
- **WHEN** VideoPlayerPane is initialized with a loaded VideoPlayer
- **THEN** video player widget appears in the center of the three-pane layout
- **AND** video frames are rendered correctly
- **AND** widget size is responsive to layout resizing

#### Scenario: Video player displays current timecode
- **WHEN** video is playing or paused
- **THEN** current timecode is displayed in HH:MM:SS.mmm format (e.g., "00:01:30.500")
- **AND** timecode updates with playback or seeks
- **AND** timecode visible in UI (not obscured)

#### Scenario: Playback controls enabled when video loaded
- **WHEN** video file is successfully loaded
- **THEN** play/pause button, seek buttons, volume slider are enabled
- **AND** clicking controls triggers appropriate VideoPlayer methods
- **AND** button states reflect playback state (play shows when paused, pause shows when playing)

#### Scenario: Playback controls disabled when no video loaded
- **WHEN** application starts or user closes video
- **THEN** all playback controls (play/pause, seek, volume) are disabled/grayed out
- **AND** attempting interaction shows friendly message or is ignored

#### Scenario: Timeline visualization with segment markers
- **WHEN** VideoPlayerPane is initialized with segments
- **THEN** timeline displays visual markers for segment boundaries
- **AND** markers are color-coded: green for allowed, red for not-allowed
- **AND** hovering over marker shows segment details (time range, labels)

#### Scenario: Current playback position marked on timeline
- **WHEN** video is playing or paused
- **THEN** timeline shows current playback position with visual indicator (e.g., vertical line, dot)
- **AND** indicator updates as video plays or is seeked

### Requirement: Synchronization with UI Segment Highlighting

The system SHALL ensure video playback time is continuously communicated to other UI components so that the segment list highlights the currently-playing segment.

#### Scenario: Current segment auto-highlights during playback
- **WHEN** video plays through a detected segment (e.g., 00:30:45–00:30:50)
- **THEN** segment list automatically highlights the current segment
- **AND** as playback moves between segments, highlighting updates
- **AND** when playback is between segments, no segment is highlighted

#### Scenario: Seeking updates segment highlight
- **WHEN** user clicks seek button or timeline (seeking to 00:40:00)
- **THEN** segment list updates to highlight segment containing 00:40:00
- **AND** if no segment at that time, highlighting is cleared

#### Scenario: Highlighting works with paused playback
- **WHEN** user pauses video and seeks to different position
- **THEN** segment list highlights segment at paused position
- **AND** highlighting remains accurate as user seeks while paused

### Requirement: Seek Button Controls

The system SHALL provide skip forward and skip backward buttons that seek the video by a fixed duration (10 seconds recommended).

#### Scenario: Skip backward 10 seconds
- **WHEN** user clicks skip backward button or presses left arrow key
- **THEN** video seeks backward 10 seconds
- **AND** if current position < 10s, seeks to 0:00:00 (beginning)
- **AND** seeking works from any playback state (playing or paused)

#### Scenario: Skip forward 10 seconds
- **WHEN** user clicks skip forward button or presses right arrow key
- **THEN** video seeks forward 10 seconds
- **AND** if current position + 10s > duration, seeks to video end
- **AND** seeking works from any playback state

#### Scenario: Seek amount configurable (optional)
- **WHEN** developer modifies skip_duration parameter (e.g., 5s, 15s)
- **THEN** skip buttons use new duration
- **AND** behavior remains identical
