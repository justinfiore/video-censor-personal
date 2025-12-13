# Implementation Tasks: Video Extraction

## 1. Core Data Structures

- [x] 1.1 Create `Frame` data class in `video_censor_personal/frame.py`
  - Fields: `index` (int), `timecode` (float, seconds), `data` (numpy array, BGR uint8)
  - Methods: `to_rgb()` for converting BGR to RGB, `timestamp_str()` for formatted output
  
- [x] 1.2 Create `AudioSegment` data class in `video_censor_personal/frame.py`
  - Fields: `start_time` (float), `end_time` (float), `data` (bytes or numpy array)
  - Methods: `duration()`, `sample_rate` property (default 16kHz)

## 2. Video Processing Module

- [x] 2.1 Create `VideoExtractor` class in `video_censor_personal/video_extraction.py`
  - Method: `__init__(video_path: str)` - validates file exists, opens with OpenCV
  - Method: `get_frame_count() -> int` - returns total frame count
  - Method: `get_duration_seconds() -> float` - calculates video duration
  - Method: `get_fps() -> float` - returns frames per second from metadata
  
- [x] 2.2 Implement `extract_frames()` generator in `VideoExtractor`
  - Signature: `extract_frames(sample_rate: float = 1.0) -> Generator[Frame, None, None]`
  - Respects `sample_rate` from config (e.g., 1.0 = every 1 second)
  - Yields `Frame` objects with correct timecode and index
  - Handles EOF and missing frames gracefully
  
- [x] 2.3 Implement `extract_audio()` method in `VideoExtractor`
  - Signature: `extract_audio() -> AudioSegment`
  - Uses ffmpeg subprocess to extract audio stream to temporary file
  - Reads audio and stores as numpy array
  - Caches result to avoid re-extraction
  - Returns `AudioSegment` with metadata

- [x] 2.4 Implement `extract_audio_segment()` method in `VideoExtractor`
  - Signature: `extract_audio_segment(start_sec: float, end_sec: float) -> AudioSegment`
  - Extracts audio for specified time range
  - Uses cached full audio if available, else extracts segment directly
  
- [x] 2.5 Add resource cleanup in `VideoExtractor`
  - Method: `close()` - releases OpenCV VideoCapture and removes temp files
  - Context manager support: `__enter__` and `__exit__` for `with` statement

## 3. Configuration Integration

- [x] 3.1 Verify `processing.frame_sampling` config options are accessible
  - Config keys: `strategy` (uniform|scene_based|all), `sample_rate` (float, seconds)
  - Validate values in config parsing (already in `config.py`)

- [x] 3.2 Add helper function `get_sample_rate_from_config(config: dict) -> float`
  - Reads `processing.frame_sampling.sample_rate` or defaults to 1.0

## 4. Testing & Validation

- [x] 4.1 Create unit tests in `tests/test_video_extraction.py`
  - Test `Frame` data class serialization
  - Test `VideoExtractor` initialization with valid/invalid file paths
  - Test frame extraction at different sample rates
  - Test audio extraction (mock ffmpeg if needed)
  - Test edge cases: empty video, single-frame video, corrupted files
  
- [x] 4.2 Create integration test
  - Test end-to-end extraction with a small sample video
  - Verify frame count matches expected sample rate
  - Verify audio extraction produces valid output
  - Validate temporal metadata accuracy
  
- [x] 4.3 Add documentation in docstrings (Google-style)
  - All public methods in `VideoExtractor`
  - `Frame` and `AudioSegment` classes
  - Examples of usage in docstrings

## 5. Documentation & Examples

- [x] 5.1 Update `README.md`
  - Add section: "Video Extraction" explaining supported formats (MP4, MKV, AVI, etc.)
  - Document frame extraction behavior and sample rates
  - Mention audio extraction and supported audio codecs
  
- [x] 5.2 Add code example in docstring or QUICK_START.md
  - Show usage of `VideoExtractor` with context manager
  - Example of iterating through frames at 1-second intervals
  - Example of extracting audio segment

## 6. Dependency & Environment

- [x] 6.1 Verify ffmpeg is available at runtime
  - Add check in `video_censor_personal/video_extraction.py:_check_ffmpeg_available()`
  - Raise informative error if ffmpeg not found
  
- [x] 6.2 Update `requirements.txt` if needed
  - Verify `opencv-python` is listed (already present)
  - Document any new dependencies (none expected beyond opencv)

## Validation Checklist

- [x] All code passes `ruff` linting (PEP 8 + type hints)
- [x] Type hints present on all function signatures
- [x] Docstrings complete (Google-style) for public API
- [x] No hardcoded paths; use `pathlib.Path`
- [x] Tests achieve ≥80% coverage for new module
- [x] Handles missing/corrupted files gracefully with informative errors
- [x] Resource cleanup works (no lingering temp files or open file handles)
