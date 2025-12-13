# Video Extraction Specification

## ADDED Requirements

### Requirement: Frame Extraction from Video

The system SHALL extract individual frames from video files at a configurable sampling rate and provide them as numeric arrays with temporal metadata.

#### Scenario: Extract frames at uniform 1-second intervals
- **WHEN** a user initializes `VideoExtractor` with a video file and calls `extract_frames(sample_rate=1.0)`
- **THEN** the system yields one frame per second of video duration, each with correct timecode and index

#### Scenario: Extract all frames from video
- **WHEN** a user calls `extract_frames(sample_rate=0)` or uses strategy `"all"`
- **THEN** the system yields every frame in the video file in sequence

#### Scenario: Extract frames at custom intervals
- **WHEN** a user calls `extract_frames(sample_rate=2.5)` (e.g., every 2.5 seconds)
- **THEN** the system yields frames at precisely the requested interval throughout the video duration

#### Scenario: Frame data includes metadata
- **WHEN** a frame is extracted and yielded from `extract_frames()`
- **THEN** the frame object includes:
  - `index`: frame number in sequence (0-indexed)
  - `timecode`: exact timestamp in seconds as a float
  - `data`: frame pixel data as numpy array (BGR format, uint8 dtype)
  - `timestamp_str()`: method to format timecode as HH:MM:SS

#### Scenario: Handle video with variable frame rate
- **WHEN** input video has variable frame rate (VFR)
- **THEN** extraction respects the requested sample rate (by time, not frame count) and produces accurate timecode metadata

#### Scenario: Handle end of video
- **WHEN** extraction reaches the final frame
- **THEN** the generator cleanly terminates without raising exceptions

### Requirement: Audio Extraction and Caching

The system SHALL extract audio from video files and cache the result to enable efficient reuse across detection modules.

#### Scenario: Extract full audio from video
- **WHEN** a user calls `extract_audio()` on a `VideoExtractor` instance
- **THEN** the system:
  - Uses ffmpeg to extract the audio stream to a temporary file
  - Reads and decodes the audio into a numpy array or bytes object
  - Caches the result internally to avoid re-extraction
  - Returns an `AudioSegment` object with metadata

#### Scenario: Reuse cached audio
- **WHEN** a user calls `extract_audio()` multiple times on the same `VideoExtractor` instance
- **THEN** the system returns the cached audio without re-invoking ffmpeg

#### Scenario: Extract audio segment by time range
- **WHEN** a user calls `extract_audio_segment(start_sec=10.5, end_sec=15.2)`
- **THEN** the system:
  - Returns an `AudioSegment` object covering the specified time range
  - Uses cached full audio if available, or extracts the segment directly
  - Preserves audio quality (sample rate, bit depth)

#### Scenario: Audio segment includes temporal metadata
- **WHEN** an audio segment is returned
- **THEN** the segment object includes:
  - `start_time`: start timecode in seconds
  - `end_time`: end timecode in seconds
  - `duration()`: method returning duration in seconds
  - `sample_rate`: audio sample rate (default 16 kHz, or detected from source)
  - `data`: raw audio data as bytes or numpy array

#### Scenario: Missing audio stream
- **WHEN** input video has no audio track
- **THEN** the system returns an empty `AudioSegment` or raises a descriptive error indicating audio unavailable

### Requirement: Video Metadata Access

The system SHALL provide metadata about the input video to enable sampling strategy decisions and result mapping.

#### Scenario: Get video duration
- **WHEN** a user calls `get_duration_seconds()` on a `VideoExtractor`
- **THEN** the system returns the total duration as a float in seconds

#### Scenario: Get video frame count
- **WHEN** a user calls `get_frame_count()` on a `VideoExtractor`
- **THEN** the system returns the total number of frames as an integer

#### Scenario: Get frames per second
- **WHEN** a user calls `get_fps()` on a `VideoExtractor`
- **THEN** the system returns the video frame rate as a float (frames per second)

#### Scenario: Metadata available immediately after initialization
- **WHEN** a `VideoExtractor` is initialized with a valid video file
- **THEN** metadata methods can be called without reading frames first

### Requirement: Sampling Strategy Configuration

The system SHALL support multiple frame sampling strategies configurable via YAML to balance coverage and performance.

#### Scenario: Uniform sampling strategy
- **WHEN** config specifies `processing.frame_sampling.strategy = "uniform"` and `sample_rate = 1.0`
- **THEN** the system extracts frames evenly spaced by time across the entire video

#### Scenario: Scene-based sampling strategy
- **WHEN** config specifies `processing.frame_sampling.strategy = "scene_based"`
- **THEN** the system identifies scene changes and extracts frames at scene boundaries (future enhancement; current default to uniform)

#### Scenario: All frames strategy
- **WHEN** config specifies `processing.frame_sampling.strategy = "all"`
- **THEN** the system extracts every frame in the video file

#### Scenario: Sample rate configuration
- **WHEN** config specifies `processing.frame_sampling.sample_rate = 2.0`
- **THEN** extraction uses this value (e.g., 2.0 seconds = one frame every 2 seconds)

#### Scenario: Respect max_workers for parallelization
- **WHEN** config specifies `processing.max_workers = 4`
- **THEN** frame extraction respects this setting if frame processing is parallelized in future enhancement

### Requirement: Resource Management and Cleanup

The system SHALL properly manage file handles, temporary files, and memory to avoid resource leaks.

#### Scenario: Close video file after extraction
- **WHEN** a user calls `close()` on a `VideoExtractor` instance
- **THEN** the system:
  - Releases the underlying video file handle (OpenCV VideoCapture)
  - Cleans up any temporary files (e.g., extracted audio)
  - Subsequent calls to extract methods raise a descriptive error

#### Scenario: Context manager usage
- **WHEN** a user utilizes `VideoExtractor` as a context manager (`with VideoExtractor(...) as ve:`)
- **THEN** the system:
  - Automatically calls `close()` when exiting the context
  - Ensures cleanup happens even if exceptions occur within the block

#### Scenario: Temporary file cleanup on error
- **WHEN** an error occurs during audio extraction or frame processing
- **THEN** the system:
  - Removes any partial or temporary files created
  - Leaves the `VideoExtractor` in a usable state for retry attempts

#### Scenario: Memory efficiency with frame generation
- **WHEN** a user iterates through frames using the `extract_frames()` generator
- **THEN** the system:
  - Yields frames one at a time rather than loading all into memory
  - Does not retain references to previously yielded frames (enabling garbage collection)

### Requirement: Error Handling and Validation

The system SHALL validate input files and provide informative error messages for common failure cases.

#### Scenario: Invalid video file path
- **WHEN** a user initializes `VideoExtractor` with a non-existent file path
- **THEN** the system raises a descriptive error (FileNotFoundError or similar) indicating the file is not found

#### Scenario: Unsupported video format
- **WHEN** a user initializes `VideoExtractor` with a file in an unsupported format
- **THEN** the system raises a descriptive error indicating the format is not supported

#### Scenario: Corrupted video file
- **WHEN** a user attempts to extract frames from a corrupted video file
- **THEN** the system:
  - Raises a descriptive error when corruption is detected
  - Or gracefully skips corrupted frames with a warning (configurable)

#### Scenario: ffmpeg not available
- **WHEN** the system initializes and ffmpeg is required but not installed
- **THEN** the system raises an error pointing users to installation instructions

#### Scenario: Insufficient permissions
- **WHEN** a user attempts to read a video file without read permissions
- **THEN** the system raises a PermissionError with guidance on file access
