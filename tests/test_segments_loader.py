"""Tests for segments JSON loading module."""

import json
import pytest
import tempfile
from pathlib import Path

from video_censor_personal.segments_loader import (
    load_segments_from_json,
    segments_to_detections,
    SegmentsLoadError,
)


class TestLoadSegmentsFromJson:
    """Test loading segments from JSON file."""

    def test_load_valid_segments_file(self, tmp_path):
        """Test loading a valid segments JSON file."""
        json_file = tmp_path / "segments.json"
        json_file.write_text(json.dumps({
            "metadata": {
                "file": "test.mp4",
                "duration": "00:10:00",
                "duration_seconds": 600.0,
            },
            "segments": [
                {
                    "start_time": "00:01:00",
                    "start_time_seconds": 60.0,
                    "end_time": "00:01:30",
                    "end_time_seconds": 90.0,
                    "labels": ["Profanity"],
                    "description": "Test segment",
                    "confidence": 0.95,
                    "allow": False,
                }
            ],
        }))

        result = load_segments_from_json(str(json_file))

        assert "segments" in result
        assert "metadata" in result
        assert len(result["segments"]) == 1
        assert result["segments"][0]["start_time"] == 60.0
        assert result["segments"][0]["end_time"] == 90.0
        assert result["segments"][0]["labels"] == ["Profanity"]
        assert result["segments"][0]["allow"] is False

    def test_load_segments_with_numeric_timestamps_only(self, tmp_path):
        """Test loading segments with only numeric timestamps."""
        json_file = tmp_path / "segments.json"
        json_file.write_text(json.dumps({
            "metadata": {"file": "test.mp4"},
            "segments": [
                {
                    "start_time_seconds": 10.0,
                    "end_time_seconds": 15.0,
                    "labels": ["Violence"],
                }
            ],
        }))

        result = load_segments_from_json(str(json_file))

        assert result["segments"][0]["start_time"] == 10.0
        assert result["segments"][0]["end_time"] == 15.0

    def test_load_segments_parses_time_string(self, tmp_path):
        """Test parsing HH:MM:SS time strings when numeric not available."""
        json_file = tmp_path / "segments.json"
        json_file.write_text(json.dumps({
            "metadata": {"file": "test.mp4"},
            "segments": [
                {
                    "start_time": "01:30:45",
                    "end_time": "01:31:00",
                    "labels": ["Nudity"],
                }
            ],
        }))

        result = load_segments_from_json(str(json_file))

        assert result["segments"][0]["start_time"] == 5445.0  # 1*3600 + 30*60 + 45
        assert result["segments"][0]["end_time"] == 5460.0    # 1*3600 + 31*60 + 0

    def test_load_segments_parses_time_string_with_milliseconds(self, tmp_path):
        """Test parsing HH:MM:SS.mmm time strings with milliseconds."""
        json_file = tmp_path / "segments.json"
        json_file.write_text(json.dumps({
            "metadata": {"file": "test.mp4"},
            "segments": [
                {
                    "start_time": "01:30:45.456",
                    "end_time": "01:31:00.789",
                    "labels": ["Nudity"],
                }
            ],
        }))

        result = load_segments_from_json(str(json_file))

        # 1*3600 + 30*60 + 45 + 0.456
        assert abs(result["segments"][0]["start_time"] - 5445.456) < 0.001
        # 1*3600 + 31*60 + 0 + 0.789
        assert abs(result["segments"][0]["end_time"] - 5460.789) < 0.001

    def test_load_segments_parses_mixed_millisecond_formats(self, tmp_path):
        """Test parsing time strings with varying millisecond precision."""
        json_file = tmp_path / "segments.json"
        json_file.write_text(json.dumps({
            "metadata": {"file": "test.mp4"},
            "segments": [
                {
                    "start_time": "00:00:01.1",    # Single digit
                    "end_time": "00:00:02.12",     # Two digits
                    "labels": ["Test"],
                },
                {
                    "start_time": "00:00:03.123",  # Three digits
                    "end_time": "00:00:04.0",      # Single zero
                    "labels": ["Test"],
                }
            ],
        }))

        result = load_segments_from_json(str(json_file))

        # First segment: 0.1 -> 0.100, 0.12 -> 0.120
        assert abs(result["segments"][0]["start_time"] - 1.1) < 0.001
        assert abs(result["segments"][0]["end_time"] - 2.12) < 0.001
        # Second segment: 0.123, 0.0 -> 0.000
        assert abs(result["segments"][1]["start_time"] - 3.123) < 0.001
        assert abs(result["segments"][1]["end_time"] - 4.0) < 0.001

    def test_load_segments_backward_compat_without_milliseconds(self, tmp_path):
        """Test backward compatibility with HH:MM:SS format (no milliseconds)."""
        json_file = tmp_path / "segments.json"
        json_file.write_text(json.dumps({
            "metadata": {"file": "test.mp4"},
            "segments": [
                {
                    "start_time": "00:01:23",  # Without milliseconds
                    "end_time": "00:01:45",
                    "labels": ["Violence"],
                }
            ],
        }))

        result = load_segments_from_json(str(json_file))

        # Should parse as integer seconds: 1*60 + 23 = 83, 1*60 + 45 = 105
        assert result["segments"][0]["start_time"] == 83.0
        assert result["segments"][0]["end_time"] == 105.0

    def test_load_segments_file_not_found(self):
        """Test error when file does not exist."""
        with pytest.raises(SegmentsLoadError, match="not found"):
            load_segments_from_json("/nonexistent/path.json")

    def test_load_segments_invalid_json(self, tmp_path):
        """Test error on invalid JSON."""
        json_file = tmp_path / "invalid.json"
        json_file.write_text("not valid json {{{")

        with pytest.raises(SegmentsLoadError, match="Invalid JSON"):
            load_segments_from_json(str(json_file))

    def test_load_segments_missing_segments_array(self, tmp_path):
        """Test error when segments array is missing."""
        json_file = tmp_path / "segments.json"
        json_file.write_text(json.dumps({
            "metadata": {"file": "test.mp4"},
        }))

        with pytest.raises(SegmentsLoadError, match="'segments' array"):
            load_segments_from_json(str(json_file))

    def test_load_segments_missing_metadata(self, tmp_path):
        """Test error when metadata is missing."""
        json_file = tmp_path / "segments.json"
        json_file.write_text(json.dumps({
            "segments": [],
        }))

        with pytest.raises(SegmentsLoadError, match="'metadata' object"):
            load_segments_from_json(str(json_file))

    def test_load_segments_warns_on_filename_mismatch(self, tmp_path, caplog):
        """Test warning when JSON filename doesn't match video."""
        json_file = tmp_path / "segments.json"
        json_file.write_text(json.dumps({
            "metadata": {"file": "original.mp4"},
            "segments": [],
        }))

        load_segments_from_json(str(json_file), video_path="/path/to/different.mp4")

        assert "original.mp4" in caplog.text
        assert "different.mp4" in caplog.text

    def test_load_segments_warns_on_duration_mismatch(self, tmp_path, caplog):
        """Test warning when duration doesn't match."""
        json_file = tmp_path / "segments.json"
        json_file.write_text(json.dumps({
            "metadata": {
                "file": "test.mp4",
                "duration_seconds": 600.0,
            },
            "segments": [],
        }))

        load_segments_from_json(str(json_file), video_duration=300.0)

        assert "duration mismatch" in caplog.text.lower()

    def test_load_segments_sorts_by_start_time(self, tmp_path):
        """Test that segments are sorted by start_time in chronological order."""
        json_file = tmp_path / "segments.json"
        json_file.write_text(json.dumps({
            "metadata": {"file": "test.mp4"},
            "segments": [
                {
                    "start_time": "00:00:30",  # Third segment
                    "end_time": "00:00:35",
                    "labels": ["C"],
                },
                {
                    "start_time": "00:00:10",  # First segment
                    "end_time": "00:00:15",
                    "labels": ["A"],
                },
                {
                    "start_time": "00:00:20",  # Second segment
                    "end_time": "00:00:25",
                    "labels": ["B"],
                },
            ],
        }))

        result = load_segments_from_json(str(json_file))

        segments = result["segments"]
        assert len(segments) == 3
        # Verify they're sorted
        assert segments[0]["start_time"] == 10.0
        assert segments[0]["labels"] == ["A"]
        assert segments[1]["start_time"] == 20.0
        assert segments[1]["labels"] == ["B"]
        assert segments[2]["start_time"] == 30.0
        assert segments[2]["labels"] == ["C"]

    def test_load_segments_sorts_with_numeric_timestamps(self, tmp_path):
        """Test sorting with numeric start_time_seconds."""
        json_file = tmp_path / "segments.json"
        json_file.write_text(json.dumps({
            "metadata": {"file": "test.mp4"},
            "segments": [
                {
                    "start_time_seconds": 50.0,
                    "end_time_seconds": 55.0,
                    "labels": ["Third"],
                },
                {
                    "start_time_seconds": 10.0,
                    "end_time_seconds": 15.0,
                    "labels": ["First"],
                },
                {
                    "start_time_seconds": 30.0,
                    "end_time_seconds": 35.0,
                    "labels": ["Second"],
                },
            ],
        }))

        result = load_segments_from_json(str(json_file))

        segments = result["segments"]
        assert segments[0]["start_time"] == 10.0
        assert segments[1]["start_time"] == 30.0
        assert segments[2]["start_time"] == 50.0

    def test_load_segments_sorts_with_float_precision(self, tmp_path):
        """Test sorting with millisecond precision."""
        json_file = tmp_path / "segments.json"
        json_file.write_text(json.dumps({
            "metadata": {"file": "test.mp4"},
            "segments": [
                {
                    "start_time": "00:00:10.500",
                    "end_time": "00:00:11",
                    "labels": ["Second"],
                },
                {
                    "start_time": "00:00:10.100",
                    "end_time": "00:00:10.500",
                    "labels": ["First"],
                },
                {
                    "start_time": "00:00:10.999",
                    "end_time": "00:00:11.500",
                    "labels": ["Third"],
                },
            ],
        }))

        result = load_segments_from_json(str(json_file))

        segments = result["segments"]
        assert segments[0]["start_time"] < segments[1]["start_time"]
        assert segments[1]["start_time"] < segments[2]["start_time"]


class TestSegmentsToDetections:
    """Test converting segments to DetectionResult objects."""

    def test_convert_single_segment(self):
        """Test converting a single segment to detections."""
        segments = [
            {
                "start_time": 10.0,
                "end_time": 15.0,
                "labels": ["Profanity"],
                "description": "Test profanity",
                "confidence": 0.95,
                "allow": False,
            }
        ]

        detections = segments_to_detections(segments)

        assert len(detections) == 1
        assert detections[0].start_time == 10.0
        assert detections[0].end_time == 15.0
        assert detections[0].label == "Profanity"
        assert detections[0].confidence == 0.95

    def test_convert_multi_label_segment(self):
        """Test converting segment with multiple labels."""
        segments = [
            {
                "start_time": 10.0,
                "end_time": 15.0,
                "labels": ["Profanity", "Violence"],
                "description": "Multiple issues",
                "confidence": 0.9,
                "allow": False,
            }
        ]

        detections = segments_to_detections(segments)

        assert len(detections) == 2
        labels = {d.label for d in detections}
        assert labels == {"Profanity", "Violence"}

    def test_skip_allowed_segments(self):
        """Test that allowed segments are not converted."""
        segments = [
            {
                "start_time": 10.0,
                "end_time": 15.0,
                "labels": ["Profanity"],
                "allow": True,  # Allowed - should be skipped
            },
            {
                "start_time": 20.0,
                "end_time": 25.0,
                "labels": ["Violence"],
                "allow": False,
            },
        ]

        detections = segments_to_detections(segments)

        assert len(detections) == 1
        assert detections[0].label == "Violence"
        assert detections[0].start_time == 20.0

    def test_empty_segments(self):
        """Test converting empty segments list."""
        detections = segments_to_detections([])

        assert detections == []

    def test_all_allowed_segments(self):
        """Test converting all allowed segments."""
        segments = [
            {
                "start_time": 10.0,
                "end_time": 15.0,
                "labels": ["Profanity"],
                "allow": True,
            },
        ]

        detections = segments_to_detections(segments)

        assert detections == []

    def test_default_values(self):
        """Test default values when optional fields missing."""
        segments = [
            {
                "start_time": 10.0,
                "end_time": 15.0,
            }
        ]

        detections = segments_to_detections(segments)

        assert len(detections) == 1
        assert detections[0].label == "Unknown"
        assert detections[0].confidence == 1.0

    def test_detections_preserve_chronological_order(self):
        """Test that detections maintain chronological order from sorted segments."""
        segments = [
            {
                "start_time": 30.0,
                "end_time": 35.0,
                "labels": ["Profanity"],
                "allow": False,
            },
            {
                "start_time": 10.0,
                "end_time": 15.0,
                "labels": ["Violence"],
                "allow": False,
            },
            {
                "start_time": 20.0,
                "end_time": 25.0,
                "labels": ["Nudity"],
                "allow": False,
            },
        ]

        detections = segments_to_detections(segments)

        # Detections should follow the segment order (already sorted)
        assert len(detections) == 3
        assert detections[0].start_time == 30.0
        assert detections[1].start_time == 10.0
        assert detections[2].start_time == 20.0
