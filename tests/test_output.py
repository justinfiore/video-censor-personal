"""Tests for output generation module."""

import json
import tempfile
from pathlib import Path
from typing import Any, Dict

import pytest

from video_censor_personal.frame import DetectionResult
from video_censor_personal.output import (
    calculate_summary,
    format_time,
    generate_json_output,
    merge_segments,
    write_output,
)


class TestFormatTime:
    """Test time formatting utility."""

    def test_format_time_hms_basic(self):
        """Format seconds to HH:MM:SS."""
        assert format_time(3661.0, "hms") == "01:01:01"

    def test_format_time_hms_zero(self):
        """Format 0 seconds."""
        assert format_time(0.0, "hms") == "00:00:00"

    def test_format_time_hms_large(self):
        """Format large time value."""
        assert format_time(36000.0, "hms") == "10:00:00"

    def test_format_time_seconds_basic(self):
        """Format to seconds string."""
        assert format_time(3661.5, "seconds") == "3661"

    def test_format_time_seconds_zero(self):
        """Format 0 to seconds."""
        assert format_time(0.0, "seconds") == "0"

    def test_format_time_default_hms(self):
        """Default format is HH:MM:SS."""
        assert format_time(3661.0) == "01:01:01"


class TestDetectionResultCreation:
    """Test DetectionResult data class."""

    def test_create_detection_result(self):
        """Create valid DetectionResult."""
        result = DetectionResult(
            start_time=10.0,
            end_time=15.0,
            label="Profanity",
            confidence=0.92,
            reasoning="Detected explicit language",
        )
        assert result.start_time == 10.0
        assert result.end_time == 15.0
        assert result.label == "Profanity"
        assert result.confidence == 0.92
        assert result.duration() == 5.0

    def test_detection_result_with_description(self):
        """DetectionResult with optional description."""
        result = DetectionResult(
            start_time=10.0,
            end_time=15.0,
            label="Violence",
            confidence=0.87,
            reasoning="Fight scene",
            description="Two characters fighting",
        )
        assert result.description == "Two characters fighting"

    def test_detection_result_with_frame_data(self):
        """DetectionResult with frame metadata."""
        frame_data = {
            "image": "iVBORw0KGgo...",
            "frame_index": 1234,
            "timecode_hms": "00:10:15",
            "timecode_seconds": 615.0,
        }
        result = DetectionResult(
            start_time=10.0,
            end_time=15.0,
            label="Nudity",
            confidence=0.95,
            reasoning="Detected nudity",
            frame_data=frame_data,
        )
        assert result.frame_data == frame_data

    def test_detection_result_invalid_confidence_low(self):
        """Confidence below 0.0 should raise error."""
        with pytest.raises(ValueError, match="confidence must be"):
            DetectionResult(
                start_time=10.0,
                end_time=15.0,
                label="Test",
                confidence=-0.1,
                reasoning="Test",
            )

    def test_detection_result_invalid_confidence_high(self):
        """Confidence above 1.0 should raise error."""
        with pytest.raises(ValueError, match="confidence must be"):
            DetectionResult(
                start_time=10.0,
                end_time=15.0,
                label="Test",
                confidence=1.1,
                reasoning="Test",
            )

    def test_detection_result_confidence_boundaries(self):
        """Confidence at boundaries should be valid."""
        result_min = DetectionResult(
            start_time=10.0,
            end_time=15.0,
            label="Test",
            confidence=0.0,
            reasoning="Test",
        )
        assert result_min.confidence == 0.0

        result_max = DetectionResult(
            start_time=10.0,
            end_time=15.0,
            label="Test",
            confidence=1.0,
            reasoning="Test",
        )
        assert result_max.confidence == 1.0

    def test_detection_result_invalid_time_order(self):
        """End time before start time should raise error."""
        with pytest.raises(ValueError, match="end_time.*must be >="):
            DetectionResult(
                start_time=15.0,
                end_time=10.0,
                label="Test",
                confidence=0.5,
                reasoning="Test",
            )

    def test_detection_result_same_start_end(self):
        """Start time equal to end time should be valid."""
        result = DetectionResult(
            start_time=10.0,
            end_time=10.0,
            label="Test",
            confidence=0.5,
            reasoning="Test",
        )
        assert result.duration() == 0.0


class TestSegmentMerging:
    """Test segment merging logic."""

    def test_merge_empty_list(self):
        """Merging empty list should return empty."""
        merged = merge_segments([])
        assert merged == []

    def test_merge_single_detection(self):
        """Single detection should create one segment."""
        detection = DetectionResult(
            start_time=10.0,
            end_time=15.0,
            label="Profanity",
            confidence=0.92,
            reasoning="Test",
        )
        merged = merge_segments([detection])
        assert len(merged) == 1
        assert merged[0]["start_time"] == 10.0
        assert merged[0]["end_time"] == 15.0
        assert merged[0]["labels"] == ["Profanity"]

    def test_merge_overlapping_detections(self):
        """Overlapping detections should merge into one segment."""
        d1 = DetectionResult(10.0, 15.0, "Profanity", 0.90, "Test1")
        d2 = DetectionResult(14.0, 18.0, "Sexual Theme", 0.88, "Test2")
        merged = merge_segments([d1, d2])
        assert len(merged) == 1
        assert merged[0]["start_time"] == 10.0
        assert merged[0]["end_time"] == 18.0
        assert set(merged[0]["labels"]) == {"Profanity", "Sexual Theme"}

    def test_merge_nearby_detections_within_threshold(self):
        """Detections within threshold should merge."""
        d1 = DetectionResult(10.0, 12.0, "Profanity", 0.90, "Test1")
        d2 = DetectionResult(13.0, 15.0, "Violence", 0.85, "Test2")
        merged = merge_segments([d1, d2], threshold=2.0)
        assert len(merged) == 1
        assert merged[0]["start_time"] == 10.0
        assert merged[0]["end_time"] == 15.0

    def test_merge_distant_detections_beyond_threshold(self):
        """Detections beyond threshold should stay separate."""
        d1 = DetectionResult(10.0, 12.0, "Profanity", 0.90, "Test1")
        d2 = DetectionResult(15.0, 17.0, "Violence", 0.85, "Test2")
        merged = merge_segments([d1, d2], threshold=2.0)
        assert len(merged) == 2
        assert merged[0]["start_time"] == 10.0
        assert merged[1]["start_time"] == 15.0

    def test_merge_labels_aggregated(self):
        """Merged segment should include all unique labels."""
        d1 = DetectionResult(10.0, 12.0, "Profanity", 0.90, "Test1")
        d2 = DetectionResult(11.0, 13.0, "Profanity", 0.92, "Test2")
        d3 = DetectionResult(12.0, 14.0, "Sexual Theme", 0.88, "Test3")
        merged = merge_segments([d1, d2, d3])
        assert len(merged) == 1
        assert set(merged[0]["labels"]) == {"Profanity", "Sexual Theme"}

    def test_merge_confidence_averaged(self):
        """Merged segment confidence should be mean of group."""
        d1 = DetectionResult(10.0, 12.0, "Test", 0.90, "Test1")
        d2 = DetectionResult(11.0, 13.0, "Test", 0.94, "Test2")
        merged = merge_segments([d1, d2])
        assert abs(merged[0]["confidence"] - 0.92) < 0.001  # (0.90 + 0.94) / 2

    def test_merge_preserves_frame_data_from_first(self):
        """Frame data from first detection should be preserved."""
        frame_data = {
            "image": "iVBORw0KGgo...",
            "frame_index": 100,
            "timecode_hms": "00:10:15",
            "timecode_seconds": 615.0,
        }
        d1 = DetectionResult(
            10.0, 12.0, "Test", 0.90, "Test1", frame_data=frame_data
        )
        d2 = DetectionResult(11.0, 13.0, "Test", 0.94, "Test2")
        merged = merge_segments([d1, d2])
        assert merged[0]["frame_data"] == frame_data

    def test_merge_uses_first_description(self):
        """First detection's description should be used."""
        d1 = DetectionResult(
            10.0, 12.0, "Test", 0.90, "Test1", description="First desc"
        )
        d2 = DetectionResult(
            11.0, 13.0, "Test", 0.94, "Test2", description="Second desc"
        )
        merged = merge_segments([d1, d2])
        assert merged[0]["description"] == "First desc"

    def test_merge_generates_description_if_none(self):
        """Generated description should list labels."""
        d1 = DetectionResult(10.0, 12.0, "Profanity", 0.90, "Test1")
        d2 = DetectionResult(11.0, 13.0, "Violence", 0.94, "Test2")
        merged = merge_segments([d1, d2])
        assert "Profanity" in merged[0]["description"]
        assert "Violence" in merged[0]["description"]


class TestCalculateSummary:
    """Test summary statistics calculation."""

    def test_summary_empty_segments(self):
        """Empty segments should produce zero summary."""
        summary = calculate_summary([])
        assert summary["total_segments_detected"] == 0
        assert summary["total_flagged_duration"] == 0
        assert summary["detection_counts"] == {}

    def test_summary_single_segment(self):
        """Single segment should calculate correctly."""
        segment = {
            "start_time": 10.0,
            "end_time": 15.0,
            "duration_seconds": 5.0,
            "labels": ["Profanity"],
            "detections": [],
        }
        summary = calculate_summary([segment])
        assert summary["total_segments_detected"] == 1
        assert summary["total_flagged_duration"] == 5.0
        assert summary["detection_counts"]["Profanity"] == 1

    def test_summary_multiple_segments(self):
        """Multiple segments should aggregate correctly."""
        segments = [
            {
                "start_time": 10.0,
                "end_time": 15.0,
                "duration_seconds": 5.0,
                "labels": ["Profanity"],
                "detections": [],
            },
            {
                "start_time": 20.0,
                "end_time": 30.0,
                "duration_seconds": 10.0,
                "labels": ["Violence"],
                "detections": [],
            },
        ]
        summary = calculate_summary(segments)
        assert summary["total_segments_detected"] == 2
        assert summary["total_flagged_duration"] == 15.0
        assert summary["detection_counts"]["Profanity"] == 1
        assert summary["detection_counts"]["Violence"] == 1

    def test_summary_multiple_labels_per_segment(self):
        """Labels should be counted per segment."""
        segments = [
            {
                "start_time": 10.0,
                "end_time": 15.0,
                "duration_seconds": 5.0,
                "labels": ["Profanity", "Sexual Theme"],
                "detections": [],
            }
        ]
        summary = calculate_summary(segments)
        assert summary["detection_counts"]["Profanity"] == 1
        assert summary["detection_counts"]["Sexual Theme"] == 1


class TestGenerateJsonOutput:
    """Test JSON output generation."""

    def test_generate_output_structure(self):
        """Generated output should have required structure."""
        segment = {
            "start_time": 10.0,
            "end_time": 15.0,
            "duration_seconds": 5.0,
            "labels": ["Profanity"],
            "description": "Test",
            "confidence": 0.92,
            "detections": [
                {
                    "label": "Profanity",
                    "confidence": 0.92,
                    "reasoning": "Detected explicit language",
                }
            ],
            "frame_data": None,
        }
        config = {"output": {"include_confidence": True, "include_frames": False}}
        output = generate_json_output(
            [segment], "test.mp4", 3661.0, "config.yaml", config
        )
        assert "metadata" in output
        assert "segments" in output
        assert "summary" in output

    def test_generate_output_metadata(self):
        """Metadata should include file, duration, config."""
        segment = {
            "start_time": 10.0,
            "end_time": 15.0,
            "duration_seconds": 5.0,
            "labels": ["Test"],
            "description": "Test",
            "confidence": 0.9,
            "detections": [],
            "frame_data": None,
        }
        config = {"output": {}}
        output = generate_json_output(
            [segment], "/path/to/test.mp4", 3661.0, "/path/to/config.yaml", config
        )
        metadata = output["metadata"]
        assert metadata["file"] == "test.mp4"
        assert metadata["duration"] == "01:01:01"
        assert metadata["config"] == "config.yaml"
        assert "processed_at" in metadata

    def test_generate_output_segment_time_formats(self):
        """Segments should include both HH:MM:SS and seconds."""
        segment = {
            "start_time": 10.0,
            "end_time": 15.0,
            "duration_seconds": 5.0,
            "labels": ["Test"],
            "description": "Test",
            "confidence": 0.9,
            "detections": [],
            "frame_data": None,
        }
        config = {"output": {}}
        output = generate_json_output([segment], "test.mp4", 100.0, "config.yaml", config)
        seg = output["segments"][0]
        assert seg["start_time"] == "00:00:10"
        assert seg["start_time_seconds"] == 10.0
        assert seg["end_time"] == "00:00:15"
        assert seg["end_time_seconds"] == 15.0

    def test_generate_output_exclude_confidence(self):
        """Confidence should be excluded when configured."""
        segment = {
            "start_time": 10.0,
            "end_time": 15.0,
            "duration_seconds": 5.0,
            "labels": ["Test"],
            "description": "Test",
            "confidence": 0.9,
            "detections": [
                {"label": "Test", "confidence": 0.9, "reasoning": "Test"}
            ],
            "frame_data": None,
        }
        config = {"output": {"include_confidence": False}}
        output = generate_json_output([segment], "test.mp4", 100.0, "config.yaml", config)
        seg = output["segments"][0]
        assert "confidence" not in seg
        assert "confidence" not in seg["detections"][0]

    def test_generate_output_include_frame_data(self):
        """Frame data should be included when configured."""
        frame_data = {
            "image": "iVBORw0KGgo...",
            "frame_index": 100,
            "timecode_hms": "00:00:10",
            "timecode_seconds": 10.0,
        }
        segment = {
            "start_time": 10.0,
            "end_time": 15.0,
            "duration_seconds": 5.0,
            "labels": ["Test"],
            "description": "Test",
            "confidence": 0.9,
            "detections": [],
            "frame_data": frame_data,
        }
        config = {"output": {"include_frames": True}}
        output = generate_json_output([segment], "test.mp4", 100.0, "config.yaml", config)
        assert output["segments"][0]["frame_data"] == frame_data

    def test_generate_output_exclude_frame_data(self):
        """Frame data should be excluded when configured."""
        frame_data = {
            "image": "iVBORw0KGgo...",
            "frame_index": 100,
            "timecode_hms": "00:00:10",
            "timecode_seconds": 10.0,
        }
        segment = {
            "start_time": 10.0,
            "end_time": 15.0,
            "duration_seconds": 5.0,
            "labels": ["Test"],
            "description": "Test",
            "confidence": 0.9,
            "detections": [],
            "frame_data": frame_data,
        }
        config = {"output": {"include_frames": False}}
        output = generate_json_output([segment], "test.mp4", 100.0, "config.yaml", config)
        assert "frame_data" not in output["segments"][0]


class TestWriteOutput:
    """Test output file writing."""

    def test_write_output_creates_file(self):
        """Write should create output file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.json"
            output_dict = {
                "metadata": {"file": "test.mp4"},
                "segments": [],
                "summary": {},
            }
            config = {"output": {"pretty_print": True}}
            write_output(output_dict, str(output_path), config)
            assert output_path.exists()

    def test_write_output_creates_directory(self):
        """Write should create missing directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "subdir" / "nested" / "output.json"
            output_dict = {
                "metadata": {"file": "test.mp4"},
                "segments": [],
                "summary": {},
            }
            config = {"output": {"pretty_print": True}}
            write_output(output_dict, str(output_path), config)
            assert output_path.exists()
            assert output_path.parent.exists()

    def test_write_output_valid_json(self):
        """Written file should contain valid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.json"
            output_dict = {
                "metadata": {"file": "test.mp4"},
                "segments": [{"label": "Test"}],
                "summary": {"total": 1},
            }
            config = {"output": {"pretty_print": True}}
            write_output(output_dict, str(output_path), config)
            with open(output_path) as f:
                loaded = json.load(f)
            assert loaded == output_dict

    def test_write_output_pretty_print_enabled(self):
        """Pretty print should format with indentation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.json"
            output_dict = {"key": "value"}
            config = {"output": {"pretty_print": True}}
            write_output(output_dict, str(output_path), config)
            content = output_path.read_text()
            assert "\n" in content  # Should have newlines

    def test_write_output_pretty_print_disabled(self):
        """Pretty print disabled should be compact."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.json"
            output_dict = {"key": "value"}
            config = {"output": {"pretty_print": False}}
            write_output(output_dict, str(output_path), config)
            content = output_path.read_text()
            # Compact JSON shouldn't have unnecessary formatting
            assert content == '{"key": "value"}'

    def test_write_output_permission_error(self):
        """Write to non-writable path should raise IOError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a non-writable directory
            readonly_dir = Path(tmpdir) / "readonly"
            readonly_dir.mkdir()
            readonly_dir.chmod(0o444)

            output_path = readonly_dir / "output.json"
            output_dict = {"key": "value"}
            config = {"output": {"pretty_print": True}}

            try:
                with pytest.raises(IOError):
                    write_output(output_dict, str(output_path), config)
            finally:
                # Clean up: restore write permissions
                readonly_dir.chmod(0o755)


class TestIntegration:
    """Integration tests combining multiple components."""

    def test_end_to_end_pipeline(self):
        """Full pipeline: create → merge → output → write."""
        # Create detections
        d1 = DetectionResult(10.0, 12.0, "Profanity", 0.90, "Explicit word")
        d2 = DetectionResult(11.0, 13.0, "Sexual Theme", 0.88, "Sexual context")
        d3 = DetectionResult(50.0, 52.0, "Violence", 0.85, "Fight scene")

        # Merge
        merged = merge_segments([d1, d2, d3], threshold=2.0)
        assert len(merged) == 2

        # Generate output
        config = {
            "output": {
                "include_confidence": True,
                "include_frames": False,
                "pretty_print": True,
            }
        }
        output = generate_json_output(
            merged, "test.mp4", 3661.0, "config.yaml", config
        )

        # Verify structure
        assert output["summary"]["total_segments_detected"] == 2
        assert output["summary"]["total_flagged_duration"] == 5.0  # (13-10) + (52-50) = 3 + 2 = 5
        assert "Profanity" in output["summary"]["detection_counts"]
        assert "Violence" in output["summary"]["detection_counts"]

        # Write to file
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "results.json"
            write_output(output, str(output_path), config)
            assert output_path.exists()
            with open(output_path) as f:
                loaded = json.load(f)
            assert loaded == output
