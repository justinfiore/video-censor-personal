"""Tests for video metadata writing functionality."""

import argparse
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from video_censor_personal.cli import validate_cli_args
from video_censor_personal.config import validate_config, is_skip_chapters_enabled
from video_censor_personal.video_metadata_writer import (
    VideoMetadataError,
    _format_chapter_name,
    _parse_ffmetadata_chapters,
    _build_skip_chapters,
    _merge_chapters,
    _generate_ffmetadata,
)


@pytest.fixture
def valid_config_with_skip_chapters():
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
def valid_config_without_skip_chapters():
    """Configuration without skip chapters."""
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
    }


@pytest.fixture
def sample_merged_segments():
    """Sample merged detection segments."""
    return [
        {
            "start_time": 10.0,
            "end_time": 15.0,
            "duration": 5.0,
            "labels": ["Nudity"],
            "confidence": 0.92,
        },
        {
            "start_time": 30.0,
            "end_time": 35.5,
            "duration": 5.5,
            "labels": ["Violence", "Sexual Theme"],
            "confidence": 0.85,
        },
    ]


class TestConfigSchema:
    """Test video metadata config schema validation."""

    def test_skip_chapters_enabled_config_valid(self, valid_config_with_skip_chapters):
        """Valid skip chapters config should pass validation."""
        validate_config(valid_config_with_skip_chapters)

    def test_skip_chapters_disabled_config_valid(self, valid_config_without_skip_chapters):
        """Config without skip chapters should still be valid."""
        validate_config(valid_config_without_skip_chapters)

    def test_skip_chapters_enabled_field_must_be_bool(self, valid_config_with_skip_chapters):
        """skip_chapters.enabled must be boolean."""
        valid_config_with_skip_chapters["video"]["metadata_output"]["skip_chapters"]["enabled"] = "yes"
        with pytest.raises(Exception):
            validate_config(valid_config_with_skip_chapters)

    def test_skip_chapters_name_format_field_must_be_string(self, valid_config_with_skip_chapters):
        """skip_chapters.name_format must be string if provided."""
        valid_config_with_skip_chapters["video"]["metadata_output"]["skip_chapters"]["name_format"] = 123
        with pytest.raises(Exception):
            validate_config(valid_config_with_skip_chapters)

    def test_is_skip_chapters_enabled_true(self, valid_config_with_skip_chapters):
        """is_skip_chapters_enabled should return True when enabled."""
        assert is_skip_chapters_enabled(valid_config_with_skip_chapters) is True

    def test_is_skip_chapters_enabled_false(self, valid_config_without_skip_chapters):
        """is_skip_chapters_enabled should return False when not configured."""
        assert is_skip_chapters_enabled(valid_config_without_skip_chapters) is False

    def test_is_skip_chapters_enabled_explicitly_false(self, valid_config_with_skip_chapters):
        """is_skip_chapters_enabled should return False when explicitly disabled."""
        valid_config_with_skip_chapters["video"]["metadata_output"]["skip_chapters"]["enabled"] = False
        assert is_skip_chapters_enabled(valid_config_with_skip_chapters) is False


class TestCLIValidation:
    """Test CLI argument validation."""

    def test_skip_chapters_enabled_requires_output_video(self, valid_config_with_skip_chapters):
        """Skip chapters enabled without --output-video should raise error."""
        args = argparse.Namespace(
            input="test.mp4",
            output="results.json",
            config="config.yaml",
            output_video=None,
            download_models=False,
            log_level="INFO",
        )
        
        with pytest.raises(SystemExit) as exc_info:
            validate_cli_args(args, valid_config_with_skip_chapters)
        assert exc_info.value.code == 1

    def test_skip_chapters_enabled_with_output_video_passes(self, valid_config_with_skip_chapters, tmp_path):
        """Skip chapters enabled with --output-video should pass."""
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
        
        # Should not raise
        validate_cli_args(args, valid_config_with_skip_chapters)

    def test_output_video_without_skip_chapters_warns(self, valid_config_without_skip_chapters, tmp_path, caplog):
        """Providing --output-video without skip chapters should warn."""
        import logging
        caplog.set_level(logging.WARNING)
        
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
        
        # Should warn but not fail
        validate_cli_args(args, valid_config_without_skip_chapters)
        assert "skip chapters and audio remediation are both disabled" in caplog.text

    @patch("builtins.input", return_value="n")
    def test_input_output_path_match_prompts_user_no(self, mock_input, valid_config_with_skip_chapters, tmp_path):
        """Same input/output paths should prompt user, exit if they say no."""
        same_file = tmp_path / "video.mp4"
        same_file.touch()
        
        args = argparse.Namespace(
            input=str(same_file),
            output="results.json",
            config="config.yaml",
            output_video=str(same_file),
            download_models=False,
            log_level="INFO",
        )
        
        with pytest.raises(SystemExit) as exc_info:
            validate_cli_args(args, valid_config_with_skip_chapters)
        assert exc_info.value.code == 0

    @patch("builtins.input", return_value="y")
    def test_input_output_path_match_prompts_user_yes(self, mock_input, valid_config_with_skip_chapters, tmp_path):
        """Same input/output paths with user confirmation should continue."""
        same_file = tmp_path / "video.mp4"
        same_file.touch()
        
        args = argparse.Namespace(
            input=str(same_file),
            output="results.json",
            config="config.yaml",
            output_video=str(same_file),
            download_models=False,
            log_level="INFO",
        )
        
        # Should not raise
        validate_cli_args(args, valid_config_with_skip_chapters)


class TestChapterFormatting:
    """Test chapter name formatting."""

    def test_format_chapter_name_single_label(self):
        """Format chapter with single label."""
        result = _format_chapter_name(["Nudity"], 0.92)
        assert result == "skip: Nudity [92%]"

    def test_format_chapter_name_multiple_labels(self):
        """Format chapter with multiple labels."""
        result = _format_chapter_name(["Violence", "Sexual Theme"], 0.85)
        assert result == "skip: Violence, Sexual Theme [85%]"

    def test_format_chapter_name_low_confidence(self):
        """Format chapter with low confidence."""
        result = _format_chapter_name(["Profanity"], 0.15)
        assert result == "skip: Profanity [15%]"

    def test_format_chapter_name_high_confidence(self):
        """Format chapter with high confidence."""
        result = _format_chapter_name(["Nudity"], 0.99)
        assert result == "skip: Nudity [99%]"

    def test_format_chapter_name_rounded_confidence(self):
        """Format chapter with confidence that needs rounding."""
        result = _format_chapter_name(["Nudity"], 0.545)
        assert result == "skip: Nudity [55%]" or result == "skip: Nudity [54%]"  # rounding


class TestChapterParsing:
    """Test FFMETADATA chapter parsing."""

    def test_parse_empty_ffmetadata(self):
        """Parsing empty metadata returns empty list."""
        result = _parse_ffmetadata_chapters("")
        assert result == []

    def test_parse_single_chapter(self):
        """Parse single chapter from FFMETADATA."""
        ffmetadata = """[CHAPTER01]
TIMEBASE=1/1000
START=5000
END=10000
title=Chapter 1
"""
        result = _parse_ffmetadata_chapters(ffmetadata)
        assert len(result) == 1
        assert result[0]["start"] == 5.0
        assert result[0]["end"] == 10.0
        assert result[0]["title"] == "Chapter 1"

    def test_parse_multiple_chapters(self):
        """Parse multiple chapters from FFMETADATA."""
        ffmetadata = """[CHAPTER01]
TIMEBASE=1/1000
START=5000
END=10000
title=Chapter 1

[CHAPTER02]
TIMEBASE=1/1000
START=20000
END=30000
title=Chapter 2
"""
        result = _parse_ffmetadata_chapters(ffmetadata)
        assert len(result) == 2
        assert result[0]["title"] == "Chapter 1"
        assert result[1]["title"] == "Chapter 2"


class TestSkipChapterBuilding:
    """Test building skip chapters from segments."""

    def test_build_skip_chapters_from_segments(self, sample_merged_segments):
        """Build skip chapters from merged segments."""
        result = _build_skip_chapters(sample_merged_segments)
        
        assert len(result) == 2
        assert result[0]["start"] == 10.0
        assert result[0]["end"] == 15.0
        assert "Nudity" in result[0]["title"]
        assert "[92%]" in result[0]["title"]
        
        assert result[1]["start"] == 30.0
        assert result[1]["end"] == 35.5
        assert "Violence" in result[1]["title"]
        assert "Sexual Theme" in result[1]["title"]

    def test_build_skip_chapters_empty_segments(self):
        """Building skip chapters from empty segments returns empty list."""
        result = _build_skip_chapters([])
        assert result == []


class TestChapterMerging:
    """Test merging existing and skip chapters."""

    def test_merge_no_existing_chapters(self, sample_merged_segments):
        """Merge when no existing chapters."""
        skip_chapters = _build_skip_chapters(sample_merged_segments)
        result = _merge_chapters(None, skip_chapters)
        
        assert len(result) == 2
        assert result[0]["start"] == 10.0

    def test_merge_with_existing_chapters(self, sample_merged_segments):
        """Merge with existing chapters."""
        existing = [
            {"start": 0, "end": 5, "title": "Original Chapter 1"},
            {"start": 60, "end": 70, "title": "Original Chapter 2"},
        ]
        skip_chapters = _build_skip_chapters(sample_merged_segments)
        result = _merge_chapters(existing, skip_chapters)
        
        assert len(result) == 4
        # Should be sorted by start time
        assert result[0]["start"] == 0
        assert result[1]["start"] == 10.0
        assert result[2]["start"] == 30.0
        assert result[3]["start"] == 60

    def test_merge_empty_skip_chapters(self):
        """Merge with empty skip chapters preserves existing."""
        existing = [
            {"start": 0, "end": 5, "title": "Original Chapter"},
        ]
        result = _merge_chapters(existing, [])
        
        assert len(result) == 1
        assert result[0]["title"] == "Original Chapter"


class TestFFMetadataGeneration:
    """Test FFMETADATA string generation."""

    def test_generate_ffmetadata_single_chapter(self):
        """Generate FFMETADATA for single chapter."""
        chapters = [
            {"start": 10.0, "end": 15.0, "title": "skip: Nudity [92%]"},
        ]
        result = _generate_ffmetadata(chapters)
        
        assert ";FFMETADATA1" in result
        assert "[CHAPTER01]" in result
        assert "START=10000" in result
        assert "END=15000" in result
        assert "title=skip: Nudity [92%]" in result

    def test_generate_ffmetadata_multiple_chapters(self, sample_merged_segments):
        """Generate FFMETADATA for multiple chapters."""
        chapters = _build_skip_chapters(sample_merged_segments)
        result = _generate_ffmetadata(chapters)
        
        assert ";FFMETADATA1" in result
        assert "[CHAPTER01]" in result
        assert "[CHAPTER02]" in result
        assert "START=10000" in result  # 10.0 seconds
        assert "START=30000" in result  # 30.0 seconds

    def test_generate_ffmetadata_preserves_titles(self):
        """Generated FFMETADATA preserves chapter titles."""
        chapters = [
            {"start": 5, "end": 10, "title": "Chapter One"},
            {"start": 20, "end": 25, "title": "Chapter Two"},
        ]
        result = _generate_ffmetadata(chapters)
        
        assert "title=Chapter One" in result
        assert "title=Chapter Two" in result
