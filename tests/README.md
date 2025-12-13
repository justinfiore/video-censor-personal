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

# Specific test file
python -m pytest tests/test_audio_remediator.py -v
```

### Skip Slow Tests

Some tests are marked as slow (e.g., tests requiring real AI models):

```bash
python -m pytest tests/ -v -m "not slow"
```

## Test Structure

```
tests/
├── conftest.py                    # Shared fixtures
├── fixtures/                      # Test data files
├── unit/                          # Fast unit tests
├── integration/                   # Integration tests
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

## Test Fixtures

Common fixtures are defined in `conftest.py`:

- `sample_video_path`: Path to a test video file
- `config_with_mock`: Config with mock detector
- `tmp_path`: Temporary directory (pytest built-in)

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
