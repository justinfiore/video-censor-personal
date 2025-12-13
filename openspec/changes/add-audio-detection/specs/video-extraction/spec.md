## MODIFIED Requirements

### Requirement: Audio Extraction and Caching

The system SHALL extract audio from video files and cache the result to enable efficient reuse across detection modules.

#### Scenario: Extract full audio from video
- **WHEN** a user calls `extract_audio()` on a `VideoExtractor` instance
- **THEN** the system:
  - Uses ffmpeg to extract the audio stream to a temporary file
  - Reads and decodes the audio into a numpy array using librosa at 16kHz sample rate
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
  - Preserves audio quality and ensures 16kHz resampling

#### Scenario: Audio segment includes temporal metadata
- **WHEN** an audio segment is returned
- **THEN** the segment object includes:
  - `start_time`: start timecode in seconds
  - `end_time`: end timecode in seconds
  - `duration()`: method returning duration in seconds
  - `sample_rate`: audio sample rate (16 kHz standard)
  - `data`: raw audio data as numpy array (mono, float32)

#### Scenario: Missing audio stream
- **WHEN** input video has no audio track
- **THEN** the system returns an empty `AudioSegment` with None data; detectors handle gracefully

#### Scenario: Automatic audio resampling to 16kHz
- **WHEN** audio is extracted from video with different sample rate (44.1kHz, 48kHz, etc.)
- **THEN** audio is resampled to 16kHz using librosa.resample() for compatibility with Whisper and audio classifiers

#### Scenario: Audio segment slicing for frame-level analysis
- **WHEN** `extract_audio_segment()` is called for a frame duration (e.g., start=10.0, end=10.033)
- **THEN** audio slice is returned without re-extraction; uses cached full audio

#### Scenario: Handle corrupted audio gracefully
- **WHEN** audio extraction fails due to corruption or unsupported codec
- **THEN** error is logged and empty AudioSegment returned; pipeline continues with visual-only detection
