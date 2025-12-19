"""Pytest configuration and fixtures for integration tests.

This module includes:
- Project-wide fixtures for video and config handling
- Headless display setup for UI tests on Linux CI environments
- Pytest plugins and markers configuration
"""

import os
import sys
import tempfile
from pathlib import Path

import pytest

from video_censor_personal.config import load_config

# Setup headless display for Linux CI environments
# This initializes pyvirtualdisplay before any tests run
if sys.platform == "linux" and "DISPLAY" not in os.environ:
    try:
        from pyvirtualdisplay import Display
        _display = Display(visible=False, size=(1024, 768))
        _display.start()
    except ImportError:
        # pyvirtualdisplay not installed, tests requiring display will fail
        pass
    except Exception as e:
        # Virtual display setup failed, log but continue
        print(f"Warning: Could not start virtual display: {e}")


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for output files.

    Yields:
        Path to temporary directory (cleaned up after test).
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_video_path():
    """Get path to sample test video.

    Returns:
        Path to tests/fixtures/sample.mp4
    """
    video_path = Path(__file__).parent / "fixtures" / "sample.mp4"
    if not video_path.exists():
        pytest.skip(f"Sample video not found: {video_path}")
    return str(video_path)


@pytest.fixture
def config_with_mock():
    """Load configuration with mock detector.

    Returns:
        Configuration dictionary with mock detector.
    """
    config_path = Path(__file__).parent / "fixtures" / "config_with_mock.yaml"
    if not config_path.exists():
        pytest.skip(f"Config file not found: {config_path}")
    return load_config(str(config_path))


@pytest.fixture
def config_without_detectors():
    """Load configuration without explicit detectors section.

    Tests fallback behavior when detectors are auto-discovered.

    Returns:
        Configuration dictionary without detectors section.
    """
    config_path = Path(__file__).parent / "fixtures" / "config_without_detectors.yaml"
    if not config_path.exists():
        pytest.skip(f"Config file not found: {config_path}")
    return load_config(str(config_path))
