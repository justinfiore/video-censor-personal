"""Tests for progress bar and debug output utilities."""

import io
import sys
import pytest

from video_censor_personal.progress import VideoProgressBar, DebugOutput


class TestVideoProgressBar:
    """Test VideoProgressBar functionality."""

    def test_init_with_duration(self):
        """Should initialize with video duration."""
        pbar = VideoProgressBar(total_duration=120.0)
        assert pbar.total_duration == 120.0
        assert pbar.description == "Processing"
        assert pbar.disable is False

    def test_init_with_custom_description(self):
        """Should accept custom description."""
        pbar = VideoProgressBar(total_duration=60.0, description="Analyzing")
        assert pbar.description == "Analyzing"

    def test_init_with_disable(self):
        """Should accept disable flag."""
        pbar = VideoProgressBar(total_duration=60.0, disable=True)
        assert pbar.disable is True

    def test_format_time_seconds(self):
        """Should format time as MM:SS for short durations."""
        assert VideoProgressBar._format_time(65) == "01:05"
        assert VideoProgressBar._format_time(0) == "00:00"
        assert VideoProgressBar._format_time(59) == "00:59"

    def test_format_time_hours(self):
        """Should format time as HH:MM:SS for long durations."""
        assert VideoProgressBar._format_time(3661) == "01:01:01"
        assert VideoProgressBar._format_time(7200) == "02:00:00"

    def test_format_time_negative(self):
        """Should handle negative time."""
        assert VideoProgressBar._format_time(-5) == "00:00"

    def test_context_manager_disabled(self):
        """Should work as context manager when disabled."""
        with VideoProgressBar(total_duration=60.0, disable=True) as pbar:
            pbar.update(30.0)

    def test_update_progress(self):
        """Should update progress without error."""
        pbar = VideoProgressBar(total_duration=100.0, disable=True)
        pbar.start()
        pbar.update(25.0)
        pbar.update(50.0)
        pbar.update(75.0)
        pbar.close()

    def test_update_zero_duration(self):
        """Should handle zero duration gracefully."""
        pbar = VideoProgressBar(total_duration=0.0, disable=True)
        pbar.start()
        pbar.update(0.0)
        pbar.close()


class TestDebugOutput:
    """Test DebugOutput functionality."""

    def test_init_disabled(self):
        """Should initialize as disabled by default."""
        debug = DebugOutput()
        assert debug.enabled is False

    def test_init_enabled(self):
        """Should initialize as enabled when requested."""
        debug = DebugOutput(enabled=True)
        assert debug.enabled is True

    def test_section_disabled_no_output(self, capsys):
        """Should not output when disabled."""
        debug = DebugOutput(enabled=False)
        debug.section("Test Section")
        captured = capsys.readouterr()
        assert captured.err == ""

    def test_section_enabled_outputs(self, capsys):
        """Should output section header when enabled."""
        debug = DebugOutput(enabled=True)
        debug.section("Test Section")
        captured = capsys.readouterr()
        assert "Test Section" in captured.err
        assert "=" in captured.err

    def test_subsection_enabled_outputs(self, capsys):
        """Should output subsection header when enabled."""
        debug = DebugOutput(enabled=True)
        debug.subsection("Test Subsection")
        captured = capsys.readouterr()
        assert "Test Subsection" in captured.err
        assert "-" in captured.err

    def test_info_enabled_outputs(self, capsys):
        """Should output info message when enabled."""
        debug = DebugOutput(enabled=True)
        debug.info("Test info message")
        captured = capsys.readouterr()
        assert "Test info message" in captured.err
        assert "[DEBUG]" in captured.err

    def test_detail_enabled_outputs(self, capsys):
        """Should output key-value detail when enabled."""
        debug = DebugOutput(enabled=True)
        debug.detail("Key", "Value")
        captured = capsys.readouterr()
        assert "Key:" in captured.err
        assert "Value" in captured.err

    def test_frame_info_enabled_outputs(self, capsys):
        """Should output frame info when enabled."""
        debug = DebugOutput(enabled=True)
        debug.frame_info(frame_index=5, timestamp=10.5, detections=2)
        captured = capsys.readouterr()
        assert "Frame" in captured.err
        assert "5" in captured.err
        assert "2 detection" in captured.err

    def test_detector_result_enabled_outputs(self, capsys):
        """Should output detector result when enabled."""
        debug = DebugOutput(enabled=True)
        debug.detector_result(
            detector_name="TestDetector",
            category="profanity",
            confidence=0.95,
        )
        captured = capsys.readouterr()
        assert "TestDetector" in captured.err
        assert "profanity" in captured.err
        assert "95" in captured.err  # 95%

    def test_step_enabled_outputs(self, capsys):
        """Should output step description when enabled."""
        debug = DebugOutput(enabled=True)
        debug.step("Processing audio...")
        captured = capsys.readouterr()
        assert "Processing audio" in captured.err
        assert "→" in captured.err

    def test_all_methods_disabled_no_output(self, capsys):
        """All methods should be silent when disabled."""
        debug = DebugOutput(enabled=False)
        debug.section("Test")
        debug.subsection("Test")
        debug.info("Test")
        debug.detail("Key", "Value")
        debug.frame_info(1, 0.5, 0)
        debug.detector_result("det", "cat", 0.5)
        debug.step("Test")
        captured = capsys.readouterr()
        assert captured.err == ""
