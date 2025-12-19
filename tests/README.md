# Testing Guide

This directory contains unit and integration tests for Video Censor Personal.

## Running Tests

### Run All Tests

```bash
./run-tests.sh
# or
python -m pytest tests/ -v
```

### Run with Coverage

```bash
python -m pytest tests/ -v --cov=video_censor_personal --cov-report=html
```

### Run Specific Test Files

```bash
# Unit tests only
python -m pytest tests/unit/ -v

# Integration tests only
python -m pytest tests/integration/ -v

# UI tests only
python -m pytest tests/ui/ -v

# Specific test file
python -m pytest tests/test_audio_remediator.py -v
```

### Skip Slow Tests

Some tests are marked as slow (e.g., tests requiring real AI models):

```bash
python -m pytest tests/ -v -m "not slow"
```

### Run by Marker

Tests can be selected by marker:

```bash
# Run only UI tests
python -m pytest -m ui -v

# Run UI tests with coverage
python -m pytest tests/ui/ -m ui --cov=video_censor_personal.ui --cov-report=term
```

## Test Structure

```
tests/
├── conftest.py                    # Shared project-wide fixtures
├── fixtures/                      # Test data files
├── unit/                          # Fast unit tests
├── integration/                   # Integration tests
├── ui/                            # UI tests (desktop application)
│   ├── conftest.py               # UI test fixtures
│   ├── test_app_bootstrap.py      # Application initialization tests
│   └── test_window_lifecycle.py   # Window lifecycle tests
├── test_audio_extractor.py        # Audio extraction tests
├── test_audio_remediator.py       # Audio remediation tests
├── test_audio_classification_detector.py  # Audio classifier tests
├── test_speech_profanity_detector.py      # Speech detector tests
├── test_video_muxer.py            # Video muxing tests
├── test_analysis_pipeline_audio.py # Pipeline audio integration
├── test_config_audio.py           # Audio config validation
└── ...
```

## Audio Tests and Model Downloads

### Required Dependencies

Audio tests require additional dependencies:

```bash
pip install librosa soundfile scipy transformers torch
```

### Model Downloads

Some tests may download AI models on first run:

- **Whisper model**: ~140 MB (for speech profanity tests)
- **Audio classification model**: ~300 MB (for audio classifier tests)

Models are cached in `~/.cache/huggingface/hub/` and persist across test runs.

### Skipping Tests Without Dependencies

Tests gracefully skip if dependencies are missing:

```python
# Example: test_audio_extractor.py
librosa = pytest.importorskip("librosa", reason="librosa not installed")
```

## Audio Remediation Tests

Audio remediation tests create temporary WAV files:

- Files are created in system temp directory
- Cleaned up automatically after tests
- Tests verify both silence and bleep modes

## Video Muxing Tests

Video muxing tests:

- Mock ffmpeg calls (no actual video processing)
- Verify correct command-line arguments
- Test error handling for missing files

### Running Real Muxing Tests

For integration tests with real ffmpeg:

```bash
# Ensure ffmpeg is installed
ffmpeg -version

# Run integration tests
python -m pytest tests/integration/ -v -m "not slow"
```

## UI Testing

UI tests validate the desktop application (CustomTkinter-based) and run in CI on Windows, macOS, and Linux.

### Running UI Tests Locally

```bash
# Run all UI tests
python -m pytest tests/ui/ -v

# Run specific UI test file
python -m pytest tests/ui/test_app_bootstrap.py -v

# Run with coverage
python -m pytest tests/ui/ --cov=video_censor_personal.ui --cov-report=term
```

### UI Testing on Linux (Headless)

On Linux CI environments without a display server, UI tests use a virtual display (xvfb):

```bash
# The CI workflow automatically wraps tests:
xvfb-run -a pytest tests/ui/ -v

# For local testing without display:
# Install pyvirtualdisplay (already in requirements.txt)
# Tests will automatically create virtual display if DISPLAY is not set
```

### UI Test Fixtures

Fixtures defined in `tests/ui/conftest.py`:

- `app`: Fresh DesktopApp instance with automatic cleanup
- `app_window`: Access to the root window widget
- Both fixtures ensure proper resource cleanup between tests

## Test Fixtures

Common fixtures are defined in `conftest.py`:

- `sample_video_path`: Path to a test video file
- `config_with_mock`: Config with mock detector
- `tmp_path`: Temporary directory (pytest built-in)
- `app` (UI tests): DesktopApp instance with cleanup
- `app_window` (UI tests): Window widget for testing

## Writing New Tests

### Audio Detector Test Pattern

```python
from unittest.mock import MagicMock, patch
import numpy as np
import pytest

# Skip if dependencies missing
pytest.importorskip("transformers")

from video_censor_personal.your_detector import YourDetector

class TestYourDetector:
    @patch("video_censor_personal.your_detector.pipeline")
    def test_detect_returns_results(self, mock_pipeline):
        mock_pipeline.return_value = MagicMock()
        
        detector = YourDetector({"categories": ["Violence"]})
        audio = np.random.randn(16000).astype(np.float32)
        
        results = detector.detect(audio_data=audio)
        assert isinstance(results, list)
```

### Integration Test Pattern

```python
import pytest

@pytest.mark.slow
def test_real_model_inference():
    """Test with real AI model (slow, requires download)."""
    # This test downloads and runs real model
    pass
```

## Coverage

Target coverage: >80%

Check coverage after running tests:

```bash
python -m pytest tests/ --cov=video_censor_personal --cov-report=term-missing
```

Coverage report is also generated in `htmlcov/` directory.
