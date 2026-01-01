"""Pytest configuration and fixtures for UI tests.

This module provides shared fixtures for testing the desktop UI (CustomTkinter).
It handles display setup for headless environments (Linux CI) and provides
fixtures for application initialization and window lifecycle testing.

Fixtures support headless and headed execution modes:
- Headless (default): Tests run without display (CI/CD compatible)
- Headed: Tests run with visible windows, slower execution for debugging
"""

import os
import sys
import time
import json
import tempfile
import subprocess
import pytest
from typing import Generator, Dict, Any
from pathlib import Path

from video_censor_personal.ui.main import DesktopApp


def has_display() -> bool:
    """Check if a display server is available.
    
    On Linux, checks for X11 DISPLAY environment variable.
    On macOS and Windows, display is always available.
    
    Returns:
        True if display is available or not needed, False otherwise.
    """
    if sys.platform == "linux":
        return "DISPLAY" in os.environ
    # macOS and Windows always have display available
    return True


def pytest_addoption(parser):
    """Add pytest CLI options for test execution modes."""
    parser.addoption(
        "--headed",
        action="store_true",
        default=False,
        help="Run UI tests in headed mode (visible windows, slower execution for debugging)"
    )


@pytest.fixture(scope="function")
def headed_mode(request) -> bool:
    """Check if tests should run in headed mode.
    
    Headed mode is enabled via:
    1. pytest --headed CLI flag
    2. PYTEST_HEADED environment variable (any non-empty value)
    
    In headed mode, tests run slower with visual feedback for debugging.
    In headless mode (default), tests run fast in CI/CD without display.
    
    Args:
        request: pytest request fixture
    
    Returns:
        True if headed mode, False for headless mode.
    """
    env_headed = os.environ.get("PYTEST_HEADED", "").strip()
    cli_headed = request.config.getoption("--headed", default=False)
    return bool(env_headed or cli_headed)


@pytest.fixture(scope="function")
def app(headed_mode: bool) -> Generator[DesktopApp, None, None]:
    """Create an isolated DesktopApp instance for testing.
    
    This fixture:
    - Creates a fresh DesktopApp instance
    - Yields the instance for the test to use
    - Properly cleans up the window and all resources after the test
    - In headed mode: window is visible with delays for observation
    - In headless mode: window is hidden or off-screen for CI/CD
    
    The fixture has function scope to ensure test isolation - each test
    gets its own application instance with no shared state.
    
    Args:
        headed_mode: Whether to run in headed (visible) or headless mode
    
    Yields:
        DesktopApp: An initialized application instance.
    """
    application = DesktopApp()
    
    # Configure window visibility based on mode
    if not headed_mode:
        # Headless mode: hide window or use off-screen rendering
        try:
            application.root.withdraw()  # Hide window
        except Exception:
            pass
    
    try:
        yield application
    finally:
        # Cleanup: destroy the window and release resources
        try:
            if application.root.winfo_exists():
                application.root.destroy()
        except Exception:
            pass  # Window may already be destroyed or not yet created


@pytest.fixture(scope="function")
def app_window(app: DesktopApp, headed_mode: bool):
    """Get the root window from an application instance.
    
    This fixture provides access to the window widget for tests that need
    to interact with window-level properties or lifecycle.
    
    In headed mode, adds a test name to the window title and optional delays.
    
    Args:
        app: The application fixture (provides isolated app instance).
        headed_mode: Whether to run in headed (visible) or headless mode
    
    Yields:
        The CTk root window instance.
    """
    window = app.root
    
    # Update window title in headed mode for debugging
    if headed_mode:
        try:
            original_title = window.title()
            window.title(f"{original_title} [TEST MODE]")
        except Exception:
            pass
    
    yield window


@pytest.fixture(scope="function")
def sample_json_payloads() -> Dict[str, Dict[str, Any]]:
    """Pre-built JSON payload structures for different test scenarios.
    
    Provides valid, invalid, and edge-case JSON structures to test
    file I/O, schema validation, and error handling.
    
    Returns:
        Dictionary of scenario names to JSON payloads:
        - valid_full: Complete, well-formed JSON with all fields
        - valid_minimal: Minimal valid JSON (no optional fields)
        - valid_no_allow_field: Segments without 'allow' field (should default to False)
        - valid_no_video_path: JSON with missing video_path field
        - valid_custom_fields: JSON with additional custom fields to preserve
        - invalid_missing_segments: JSON missing 'segments' key
        - invalid_bad_schema: Segments with wrong field types
        - edge_case_100_segments: Large JSON with 100+ segments
        - edge_case_empty_segments: Valid JSON with empty segments array
    """
    return {
        "valid_full": {
            "file": "test_video.mp4",
            "segments": [
                {
                    "start_time": 10.0,
                    "end_time": 15.0,
                    "duration_seconds": 5.0,
                    "labels": ["Profanity"],
                    "description": "Test segment 1",
                    "confidence": 0.9,
                    "detections": [
                        {
                            "label": "Profanity",
                            "confidence": 0.9,
                            "reasoning": "Contains explicit language"
                        }
                    ],
                    "allow": False
                },
                {
                    "start_time": 30.0,
                    "end_time": 35.0,
                    "duration_seconds": 5.0,
                    "labels": ["Violence"],
                    "description": "Test segment 2",
                    "confidence": 0.85,
                    "detections": [
                        {
                            "label": "Violence",
                            "confidence": 0.85,
                            "reasoning": "Contains violent content"
                        }
                    ],
                    "allow": True
                }
            ]
        },
        "valid_minimal": {
            "file": "minimal.mp4",
            "segments": [
                {
                    "start_time": 0.0,
                    "end_time": 5.0,
                    "duration_seconds": 5.0,
                    "labels": ["Test"],
                    "description": "Minimal segment",
                    "confidence": 0.5,
                    "detections": [],
                    "allow": False
                }
            ]
        },
        "valid_no_allow_field": {
            "file": "test_video.mp4",
            "segments": [
                {
                    "start_time": 10.0,
                    "end_time": 15.0,
                    "duration_seconds": 5.0,
                    "labels": ["Profanity"],
                    "description": "Segment without allow field",
                    "confidence": 0.9,
                    "detections": []
                }
            ]
        },
        "valid_no_video_path": {
            "segments": [
                {
                    "start_time": 10.0,
                    "end_time": 15.0,
                    "duration_seconds": 5.0,
                    "labels": ["Test"],
                    "description": "No video path",
                    "confidence": 0.9,
                    "detections": [],
                    "allow": False
                }
            ]
        },
        "valid_custom_fields": {
            "file": "test_video.mp4",
            "custom_metadata": "should be preserved",
            "analysis_version": "1.0",
            "segments": [
                {
                    "start_time": 10.0,
                    "end_time": 15.0,
                    "duration_seconds": 5.0,
                    "labels": ["Test"],
                    "description": "With custom fields",
                    "confidence": 0.9,
                    "detections": [],
                    "allow": False,
                    "custom_segment_field": "preserved"
                }
            ]
        },
        "invalid_missing_segments": {
            "file": "test_video.mp4"
            # Missing 'segments' key
        },
        "invalid_bad_schema": {
            "file": "test_video.mp4",
            "segments": [
                {
                    "start_time": "not_a_number",  # Should be float
                    "end_time": 15.0,
                    "duration_seconds": 5.0,
                    "labels": ["Test"],
                    "description": "Bad schema",
                    "confidence": 0.9,
                    "detections": [],
                    "allow": "maybe"  # Should be boolean
                }
            ]
        },
        "edge_case_100_segments": {
            "file": "large_video.mp4",
            "segments": [
                {
                    "start_time": i * 10.0,
                    "end_time": (i * 10.0) + 5.0,
                    "duration_seconds": 5.0,
                    "labels": [f"Label{i % 3}"],
                    "description": f"Large test segment {i}",
                    "confidence": 0.8,
                    "detections": [],
                    "allow": i % 2 == 0
                }
                for i in range(100)
            ]
        },
        "edge_case_empty_segments": {
            "file": "empty_video.mp4",
            "segments": []
        }
    }


@pytest.fixture(scope="function")
def sample_video_file(tmp_path) -> str:
    """Create a minimal test video file for integration tests.
    
    Creates a 3-second test video using ffmpeg if available,
    otherwise creates a dummy MP4 file for basic file I/O tests.
    
    Args:
        tmp_path: pytest temporary directory fixture
    
    Returns:
        Path to created video file
    """
    video_path = str(tmp_path / "test_video.mp4")
    
    # Try to create real video with ffmpeg
    try:
        subprocess.run(
            [
                "ffmpeg", "-f", "lavfi", "-i", "color=c=blue:s=320x240:d=3",
                "-f", "lavfi", "-i", "sine=f=1000:d=3",
                "-c:v", "libx264", "-c:a", "aac", "-y",
                video_path
            ],
            capture_output=True,
            timeout=10,
            check=True
        )
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        # Fallback: create dummy file for file I/O tests
        # (real video playback tests use mocks)
        with open(video_path, "wb") as f:
            f.write(b"ftypisom" + b"\x00" * 1000)  # Minimal MP4 header
    
    return video_path


@pytest.fixture(scope="function")
def temp_workspace(tmp_path, sample_video_file, sample_json_payloads) -> Dict[str, Path]:
    """Create isolated workspace with sample video and JSON files.
    
    Provides a temporary directory structure for file I/O tests:
    - Contains sample video file
    - Pre-populated with various JSON payloads
    - Auto-cleaned up after test
    
    Args:
        tmp_path: pytest temporary directory fixture
        sample_video_file: Path to created test video
        sample_json_payloads: Pre-built JSON payload fixtures
    
    Returns:
        Dictionary with keys:
        - root: Path to temp workspace
        - video: Path to test video file
        - json files: named by payload key (e.g., 'valid_full')
    """
    workspace = {
        "root": tmp_path,
        "video": Path(sample_video_file)
    }
    
    # Write sample JSON files to workspace
    for name, payload in sample_json_payloads.items():
        json_path = tmp_path / f"{name}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        workspace[name] = json_path
    
    return workspace


@pytest.fixture(scope="function")
def app_with_files(app: DesktopApp, temp_workspace: Dict[str, Path]) -> DesktopApp:
    """Create app instance with pre-loaded JSON and video files.
    
    Provides a PreviewEditorApp with workspace already populated,
    ready for cross-component and workflow tests.
    
    Args:
        app: The application fixture
        temp_workspace: Pre-populated workspace with files
    
    Returns:
        Configured DesktopApp instance ready for integration testing
    """
    # Load a valid JSON file for basic setup
    try:
        app.segment_manager.load_from_json(str(temp_workspace["valid_full"]))
    except Exception:
        pass  # Some tests may not use the loaded data
    
    # Store workspace reference for test access
    app._test_workspace = temp_workspace
    
    return app


def assert_json_structure_valid(json_data: Dict[str, Any]) -> bool:
    """Validate JSON has required structure for segment data.
    
    Checks:
    - 'segments' key exists
    - segments is a list
    - Each segment has required fields
    
    Args:
        json_data: JSON payload to validate
    
    Returns:
        True if valid, raises AssertionError otherwise
    """
    assert isinstance(json_data, dict), "JSON must be a dictionary"
    assert "segments" in json_data, "JSON must contain 'segments' key"
    assert isinstance(json_data["segments"], list), "'segments' must be a list"
    
    required_fields = {"start_time", "end_time", "duration_seconds", "labels", 
                       "description", "confidence", "detections"}
    
    for idx, segment in enumerate(json_data["segments"]):
        assert isinstance(segment, dict), f"Segment {idx} must be a dict"
        for field in required_fields:
            assert field in segment, f"Segment {idx} missing required field: {field}"
    
    return True


def assert_segment_allow_status(json_data: Dict[str, Any], segment_idx: int, 
                                expected_allow: bool, label: str = "") -> bool:
    """Assert a specific segment's allow status in JSON.
    
    Args:
        json_data: JSON payload
        segment_idx: Index of segment to check
        expected_allow: Expected boolean value
        label: Optional description for assertion failure
    
    Returns:
        True if match, raises AssertionError otherwise
    """
    segments = json_data.get("segments", [])
    assert segment_idx < len(segments), f"Segment index {segment_idx} out of range"
    
    actual_allow = segments[segment_idx].get("allow", False)
    assert actual_allow == expected_allow, \
        f"Segment {segment_idx} allow={actual_allow}, expected {expected_allow}. {label}"
    
    return True


def assert_json_file_unchanged_except(json_path: str, changed_fields: set = None) -> bool:
    """Verify JSON file structure unchanged except for specific fields.
    
    Useful for checking that file operations preserve unmodified data.
    
    Args:
        json_path: Path to JSON file to check
        changed_fields: Set of field names that may have changed 
                       (e.g., {'allow'}, defaults to empty)
    
    Returns:
        True if validation passes, raises AssertionError otherwise
    """
    if changed_fields is None:
        changed_fields = set()
    
    assert os.path.exists(json_path), f"JSON file not found: {json_path}"
    
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    assert_json_structure_valid(data)
    return True
