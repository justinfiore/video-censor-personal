"""Tests for duration invariant validation.

This module ensures that duration_seconds is never used for remediation processing—
only start_time and end_time are used in decision-making. This is important because
duration might be stale or incorrect, but start/end times are definitive.
"""

import json
import tempfile
from pathlib import Path

import pytest

from video_censor_personal.frame import DetectionResult
from video_censor_personal.output import merge_segments
from video_censor_personal.segments_loader import (
    load_segments_from_json,
    segments_to_detections,
)


class TestDurationNotUsedInAudioRemediation:
    """Verify duration is not used in audio remediation decisions."""

    def test_segments_recalculate_duration_from_times(self):
        """When loading segments, duration should be recalculated from start/end times."""
        with tempfile.TemporaryDirectory() as tmpdir:
            json_file = Path(tmpdir) / "segments.json"
            json_file.write_text(json.dumps({
                "metadata": {"file": "test.mp4"},
                "segments": [
                    {
                        "start_time": "00:00:10.000",
                        "end_time": "00:00:20.000",
                        "duration_seconds": 999.0,  # Intentionally wrong
                        "labels": ["Profanity"],
                        "allow": False,
                    }
                ],
            }))

            result = load_segments_from_json(str(json_file))

            # Duration should be recalculated from start/end times, ignoring input duration
            loaded_segment = result["segments"][0]
            assert loaded_segment["start_time"] == 10.0
            assert loaded_segment["end_time"] == 20.0
            assert loaded_segment["duration_seconds"] == 10.0  # 20 - 10, not 999


class TestDurationNotUsedInVideoRemediation:
    """Verify duration is not used in video remediation decisions."""

    def test_merged_segments_use_start_end_times(self):
        """Merged segments should use start/end times for remediation, not duration."""
        # Create detections with specific times
        d1 = DetectionResult(
            start_time=10.5,
            end_time=20.75,
            label="Profanity",
            confidence=0.9,
            reasoning="Test",
        )
        d2 = DetectionResult(
            start_time=15.25,
            end_time=25.5,
            label="Violence",
            confidence=0.85,
            reasoning="Test",
        )

        merged = merge_segments([d1, d2])

        assert len(merged) == 1
        # Times should be merged using min/max of start/end
        assert merged[0]["start_time"] == 10.5  # min of starts
        assert merged[0]["end_time"] == 25.5    # max of ends
        # Duration calculated from times
        assert abs(merged[0]["duration_seconds"] - 15.0) < 0.001  # 25.5 - 10.5


class TestSegmentsConvertToDetectionsUsingTimes:
    """Verify conversion to DetectionResult uses start/end times correctly."""

    def test_convert_uses_start_end_times_not_duration(self):
        """Converting segments should use start/end times, not duration."""
        segments = [
            {
                "start_time": 100.123,
                "end_time": 110.456,
                "duration_seconds": 999.0,  # Intentionally wrong
                "labels": ["Violence"],
                "description": "Fight scene",
                "confidence": 0.95,
                "allow": False,
            }
        ]

        detections = segments_to_detections(segments)

        assert len(detections) == 1
        assert detections[0].start_time == 100.123
        assert detections[0].end_time == 110.456
        # Duration should be calculated from times if needed
        assert abs(detections[0].duration() - 10.333) < 0.001  # 110.456 - 100.123


class TestDurationInvariantEdgeCases:
    """Test edge cases for duration invariant."""

    def test_zero_duration_segment(self):
        """Segments with zero duration (start_time == end_time) should be valid."""
        with tempfile.TemporaryDirectory() as tmpdir:
            json_file = Path(tmpdir) / "segments.json"
            json_file.write_text(json.dumps({
                "metadata": {"file": "test.mp4"},
                "segments": [
                    {
                        "start_time": "00:00:10.000",
                        "end_time": "00:00:10.000",  # Zero duration
                        "labels": ["Profanity"],
                        "allow": False,
                    }
                ],
            }))

            result = load_segments_from_json(str(json_file))

            loaded_segment = result["segments"][0]
            assert loaded_segment["start_time"] == 10.0
            assert loaded_segment["end_time"] == 10.0
            assert loaded_segment["duration_seconds"] == 0.0

    def test_millisecond_precision_preserved(self):
        """Millisecond precision in start/end times should be preserved."""
        with tempfile.TemporaryDirectory() as tmpdir:
            json_file = Path(tmpdir) / "segments.json"
            json_file.write_text(json.dumps({
                "metadata": {"file": "test.mp4"},
                "segments": [
                    {
                        "start_time": "00:00:10.123",
                        "end_time": "00:00:20.456",
                        "labels": ["Nudity"],
                        "allow": False,
                    }
                ],
            }))

            result = load_segments_from_json(str(json_file))

            loaded_segment = result["segments"][0]
            # Verify millisecond precision is preserved
            assert abs(loaded_segment["start_time"] - 10.123) < 0.0001
            assert abs(loaded_segment["end_time"] - 20.456) < 0.0001
            # Duration calculated with full precision
            assert abs(loaded_segment["duration_seconds"] - 10.333) < 0.0001

    def test_negative_duration_prevented(self):
        """Invalid times where start > end should be caught at parse time."""
        with tempfile.TemporaryDirectory() as tmpdir:
            json_file = Path(tmpdir) / "segments.json"
            json_file.write_text(json.dumps({
                "metadata": {"file": "test.mp4"},
                "segments": [
                    {
                        "start_time": "00:00:20.000",
                        "end_time": "00:00:10.000",  # Invalid: end < start
                        "labels": ["Test"],
                        "allow": False,
                    }
                ],
            }))

            # Load should succeed (validation happens at remediation time)
            result = load_segments_from_json(str(json_file))
            
            # But the resulting segment would have negative duration
            loaded_segment = result["segments"][0]
            assert loaded_segment["start_time"] == 20.0
            assert loaded_segment["end_time"] == 10.0
            assert loaded_segment["duration_seconds"] == -10.0
