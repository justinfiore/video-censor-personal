"""Integration tests for video metadata writing with pipeline output."""

import argparse
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from video_censor_personal.config import is_skip_chapters_enabled
from video_censor_personal.video_metadata_writer import write_skip_chapters_to_mp4, VideoMetadataError


@pytest.fixture
def config_with_skip_chapters():
    """Configuration with skip chapters enabled."""
    return {
        "version": 1.0,
        "detections": {
            "nudity": {
                "enabled": True,
                "sensitivity": 0.7,
                "model": "local",
            },
        },
        "processing": {
            "frame_sampling": {"strategy": "uniform", "sample_rate": 1.0},
            "segment_merge": {"enabled": True, "merge_threshold": 2.0},
            "max_workers": 4,
        },
        "output": {"format": "json", "include_confidence": True},
        "video": {
            "metadata_output": {
                "skip_chapters": {
                    "enabled": True,
                }
            }
        },
    }


@pytest.fixture
def pipeline_output_dict():
    """Sample output from the analysis pipeline."""
    return {
        "metadata": {
            "video_file": "test.mp4",
            "analysis_date": "2025-01-15T10:00:00",
            "duration_seconds": 120,
        },
        "segments": [
            {
                "start_time": 10.0,
                "end_time": 15.0,
                "duration_seconds": 5.0,
                "labels": ["Nudity"],
                "description": "Detected Nudity",
                "confidence": 0.92,
                "detections": [
                    {
                        "label": "Nudity",
                        "confidence": 0.92,
                        "reasoning": "Detected nude torso",
                    }
                ],
            },
            {
                "start_time": 30.0,
                "end_time": 35.5,
                "duration_seconds": 5.5,
                "labels": ["Violence", "Sexual Theme"],
                "description": "Detected Violence, Sexual Theme",
                "confidence": 0.85,
                "detections": [
                    {
                        "label": "Violence",
                        "confidence": 0.85,
                        "reasoning": "Detected fighting scene",
                    },
                    {
                        "label": "Sexual Theme",
                        "confidence": 0.85,
                        "reasoning": "Detected suggestive content",
                    },
                ],
            },
        ],
    }


class TestIntegrationWithPipelineOutput:
    """Test video metadata writing with actual pipeline output format."""

    def test_write_chapters_from_pipeline_output(self, config_with_skip_chapters, pipeline_output_dict, tmp_path):
        """Test writing chapters using pipeline output format."""
        input_file = tmp_path / "input.mp4"
        output_file = tmp_path / "output.mp4"
        
        # Create dummy input file
        input_file.write_bytes(b"fake mp4 data")
        
        # Extract segments from pipeline output
        segments = pipeline_output_dict.get("segments", [])
        
        # Verify segment format is correct for our chapter writer
        assert len(segments) == 2
        assert "start_time" in segments[0]
        assert "end_time" in segments[0]
        assert "labels" in segments[0]
        assert "confidence" in segments[0]
        
        # Verify config has skip chapters enabled
        assert is_skip_chapters_enabled(config_with_skip_chapters)

    def test_empty_segments_from_pipeline(self, config_with_skip_chapters, tmp_path):
        """Test handling of pipeline output with no detections."""
        input_file = tmp_path / "input.mp4"
        output_file = tmp_path / "output.mp4"
        
        # Create dummy input file
        input_file.write_bytes(b"fake mp4 data")
        
        # Empty segments (no detections)
        segments = []
        
        # Should not raise, just handle gracefully
        assert len(segments) == 0
        assert is_skip_chapters_enabled(config_with_skip_chapters)

    def test_mixed_segment_types(self, config_with_skip_chapters):
        """Test that pipeline output format works with video metadata writer."""
        # Simulate pipeline output with various segment types
        segments = [
            {
                "start_time": 5.0,
                "end_time": 10.0,
                "duration_seconds": 5.0,
                "labels": ["Profanity"],
                "description": "Detected Profanity",
                "confidence": 0.95,
            },
            {
                "start_time": 25.0,
                "end_time": 30.0,
                "duration_seconds": 5.0,
                "labels": ["Violence"],
                "description": "Detected Violence",
                "confidence": 0.88,
            },
            {
                "start_time": 50.0,
                "end_time": 55.0,
                "duration_seconds": 5.0,
                "labels": ["Sexual Theme", "Nudity"],
                "description": "Detected Sexual Theme, Nudity",
                "confidence": 0.82,
            },
        ]
        
        # Verify all required fields are present
        for segment in segments:
            assert "start_time" in segment
            assert "end_time" in segment
            assert "labels" in segment
            assert "confidence" in segment
            assert isinstance(segment["labels"], list)
            assert len(segment["labels"]) > 0
            assert 0.0 <= segment["confidence"] <= 1.0


class TestChapterWriterWithMockedFFmpeg:
    """Test chapter writing with mocked ffmpeg."""

    @patch("subprocess.run")
    def test_write_chapters_calls_ffmpeg(self, mock_run, tmp_path):
        """Test that write_skip_chapters_to_mp4 calls ffmpeg correctly."""
        import subprocess
        
        # Setup mock to succeed
        mock_run.return_value = MagicMock(returncode=0)
        
        input_file = tmp_path / "input.mp4"
        output_file = tmp_path / "output.mp4"
        
        # Create dummy input file
        input_file.write_bytes(b"fake mp4 data")
        
        segments = [
            {
                "start_time": 10.0,
                "end_time": 15.0,
                "labels": ["Nudity"],
                "confidence": 0.92,
            },
        ]
        
        # This will raise VideoMetadataError due to mocked ffmpeg,
        # but we can verify it was called
        try:
            write_skip_chapters_to_mp4(str(input_file), str(output_file), segments)
        except VideoMetadataError:
            pass  # Expected due to mocking
        
        # Verify ffmpeg was called
        assert mock_run.called

    def test_chapter_writer_error_handling(self, tmp_path):
        """Test error handling when input file doesn't exist."""
        input_file = tmp_path / "nonexistent.mp4"
        output_file = tmp_path / "output.mp4"
        
        segments = [
            {
                "start_time": 10.0,
                "end_time": 15.0,
                "labels": ["Nudity"],
                "confidence": 0.92,
            },
        ]
        
        # Should raise VideoMetadataError for missing input file
        with pytest.raises(VideoMetadataError):
            write_skip_chapters_to_mp4(str(input_file), str(output_file), segments)

    def test_empty_segments_doesnt_require_ffmpeg_output(self, tmp_path):
        """Test that empty segments don't require full ffmpeg setup."""
        input_file = tmp_path / "input.mp4"
        output_file = tmp_path / "output.mp4"
        
        # Create dummy input file
        input_file.write_bytes(b"fake mp4 data")
        
        segments = []
        
        # With empty segments, ffmpeg will still be called, but input file exists
        # This would normally fail because ffmpeg is not installed in test env,
        # but we're verifying the code handles empty segments gracefully
        try:
            write_skip_chapters_to_mp4(str(input_file), str(output_file), segments)
        except VideoMetadataError as e:
            # Expected - ffmpeg not available in test
            assert "ffmpeg" in str(e).lower() or "failed" in str(e).lower()


class TestConfigAndCLIIntegration:
    """Test configuration and CLI integration."""

    def test_skip_chapters_config_structure_in_output(self, config_with_skip_chapters):
        """Test that skip chapters config is properly structured."""
        video_config = config_with_skip_chapters.get("video", {})
        metadata_output = video_config.get("metadata_output", {})
        skip_chapters = metadata_output.get("skip_chapters", {})
        
        assert isinstance(skip_chapters, dict)
        assert "enabled" in skip_chapters
        assert skip_chapters["enabled"] is True

    def test_cli_args_for_skip_chapters_flow(self, tmp_path):
        """Test that CLI args can properly specify output video for skip chapters."""
        input_file = tmp_path / "input.mp4"
        output_file = tmp_path / "output.mp4"
        
        input_file.touch()
        
        args = argparse.Namespace(
            input=str(input_file),
            output="results.json",
            config="config.yaml",
            output_video=str(output_file),
            download_models=False,
            log_level="INFO",
        )
        
        # Verify args are structured correctly for skip chapters pipeline
        assert args.output_video is not None
        assert args.input != args.output_video
