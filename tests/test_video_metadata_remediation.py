"""Tests for video metadata remediation (title and custom tags).

Tests the video_metadata module which provides functions for:
- Extracting original titles from video files
- Creating censored titles with "(Censored)" suffix
- Building remediation metadata tags
- Formatting metadata for ffmpeg
- Logging metadata changes
"""

import json
import logging
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

import pytest

from video_censor_personal.video_metadata import (
    extract_original_title,
    create_censored_title,
    build_remediation_metadata,
    format_metadata_for_ffmpeg,
    log_metadata,
)


class TestExtractOriginalTitle:
    """Tests for extract_original_title function."""

    def test_extract_title_from_video_with_title(self):
        """Test extracting title from a video that has title metadata."""
        mock_output = {
            "format": {
                "tags": {
                    "title": "Family Video",
                    "encoder": "Lavf62.3.100"
                }
            }
        }
        
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(
                returncode=0,
                stdout=json.dumps(mock_output)
            )
            
            title = extract_original_title("/path/to/video.mp4")
            
            assert title == "Family Video"
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            assert "ffprobe" in args[0]

    def test_extract_title_from_video_without_title(self):
        """Test extracting title from a video without title metadata."""
        mock_output = {
            "format": {
                "tags": {
                    "encoder": "Lavf62.3.100"
                }
            }
        }
        
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(
                returncode=0,
                stdout=json.dumps(mock_output)
            )
            
            title = extract_original_title("/path/to/video.mp4")
            
            assert title is None

    def test_extract_title_ffprobe_error(self):
        """Test handling when ffprobe returns an error."""
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = mock.Mock(
                returncode=1,
                stderr="ffprobe error"
            )
            
            title = extract_original_title("/path/to/video.mp4")
            
            assert title is None

    def test_extract_title_ffprobe_timeout(self):
        """Test handling when ffprobe times out."""
        with mock.patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("ffprobe", 10)
            
            title = extract_original_title("/path/to/video.mp4")
            
            assert title is None

    def test_extract_title_ffprobe_not_found(self):
        """Test error when ffprobe is not available."""
        with mock.patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("ffprobe not found")
            
            with pytest.raises(RuntimeError, match="ffprobe not available"):
                extract_original_title("/path/to/video.mp4")


class TestCreateCensoredTitle:
    """Tests for create_censored_title function."""

    def test_create_censored_title_from_original(self):
        """Test appending (Censored) to an original title."""
        title = create_censored_title("Family Video", "/path/to/video.mp4")
        assert title == "Family Video (Censored)"

    def test_create_censored_title_already_censored(self):
        """Test that (Censored) is not doubled if already present."""
        title = create_censored_title("Family Video (Censored)", "/path/to/video.mp4")
        assert title == "Family Video (Censored)"

    def test_create_censored_title_from_filename_when_no_title(self):
        """Test using filename when no original title exists."""
        title = create_censored_title(None, "/path/to/family_video.mp4")
        assert title == "family_video (Censored)"

    def test_create_censored_title_with_special_chars(self):
        """Test preserving special characters in title."""
        title = create_censored_title("La Película: Noche & Día", "/path/to/video.mp4")
        assert title == "La Película: Noche & Día (Censored)"

    def test_create_censored_title_unicode_chars(self):
        """Test handling unicode characters."""
        title = create_censored_title("日本語ビデオ", "/path/to/video.mp4")
        assert title == "日本語ビデオ (Censored)"

    def test_create_censored_title_quotes(self):
        """Test title with quotes."""
        title = create_censored_title('Video "My Event"', "/path/to/video.mp4")
        assert title == 'Video "My Event" (Censored)'


class TestBuildRemediationMetadata:
    """Tests for build_remediation_metadata function."""

    def test_build_metadata_all_fields(self):
        """Test building complete remediation metadata."""
        config_file = "/path/to/video-censor.yaml"
        segment_file = "/path/to/results-2025-12-29.json"
        timestamp = datetime(2025, 12, 29, 14, 30, 45, 123000, tzinfo=timezone.utc)
        
        metadata = build_remediation_metadata(
            config_file=config_file,
            segment_file=segment_file,
            processed_timestamp=timestamp,
            audio_remediation_enabled=True,
            video_remediation_enabled=False,
        )
        
        assert metadata["video_censor_personal_config_file"] == "video-censor.yaml"
        assert metadata["video_censor_personal_segment_file"] == "results-2025-12-29.json"
        assert metadata["video_censor_personal_processed_date"] == "2025-12-29T14:30:45.123000+00:00"
        assert metadata["video_censor_personal_audio_remediation_enabled"] == "true"
        assert metadata["video_censor_personal_video_remediation_enabled"] == "false"

    def test_build_metadata_basename_extraction(self):
        """Test that full paths are reduced to basenames."""
        config_file = "/very/long/path/to/config.yaml"
        segment_file = "/another/long/path/segments.json"
        timestamp = datetime.now()
        
        metadata = build_remediation_metadata(
            config_file=config_file,
            segment_file=segment_file,
            processed_timestamp=timestamp,
            audio_remediation_enabled=False,
            video_remediation_enabled=True,
        )
        
        assert metadata["video_censor_personal_config_file"] == "config.yaml"
        assert metadata["video_censor_personal_segment_file"] == "segments.json"

    def test_build_metadata_both_remediation_disabled(self):
        """Test metadata when both audio and video remediation are disabled."""
        metadata = build_remediation_metadata(
            config_file="config.yaml",
            segment_file="segments.json",
            processed_timestamp=datetime.now(),
            audio_remediation_enabled=False,
            video_remediation_enabled=False,
        )
        
        assert metadata["video_censor_personal_audio_remediation_enabled"] == "false"
        assert metadata["video_censor_personal_video_remediation_enabled"] == "false"

    def test_build_metadata_timestamp_with_timezone(self):
        """Test ISO8601 timestamp formatting with timezone."""
        # Create timestamp with PST timezone (UTC-8)
        timestamp = datetime(
            2025, 12, 29, 14, 30, 45, 123000,
            tzinfo=timezone(timezone.utc.utcoffset(None) - __import__('datetime').timedelta(hours=8))
        )
        
        metadata = build_remediation_metadata(
            config_file="config.yaml",
            segment_file="segments.json",
            processed_timestamp=timestamp,
            audio_remediation_enabled=True,
            video_remediation_enabled=True,
        )
        
        # Should include timezone offset in ISO8601 format
        date_value = metadata["video_censor_personal_processed_date"]
        assert "2025-12-29T14:30:45" in date_value
        assert "+" in date_value or "-" in date_value


class TestFormatMetadataForFfmpeg:
    """Tests for format_metadata_for_ffmpeg function."""

    def test_format_empty_metadata(self):
        """Test formatting empty metadata dict."""
        result = format_metadata_for_ffmpeg({})
        assert result == []

    def test_format_single_metadata(self):
        """Test formatting a single metadata tag."""
        metadata = {"title": "My Video"}
        result = format_metadata_for_ffmpeg(metadata)
        
        assert result == ["-metadata", "title=My Video"]

    def test_format_multiple_metadata(self):
        """Test formatting multiple metadata tags."""
        metadata = {
            "title": "My Video",
            "config_file": "config.yaml",
            "timestamp": "2025-12-29T14:30:45Z",
        }
        result = format_metadata_for_ffmpeg(metadata)
        
        # Result should have 3 pairs of arguments
        assert len(result) == 6
        assert "-metadata" in result
        # Check that all metadata values are present
        formatted_string = " ".join(result)
        assert "title=My Video" in formatted_string
        assert "config_file=config.yaml" in formatted_string
        assert "timestamp=2025-12-29T14:30:45Z" in formatted_string

    def test_format_metadata_special_chars(self):
        """Test that special characters in values are preserved."""
        metadata = {
            "video_censor_personal_config_file": "config (2025).yaml",
            "video_censor_personal_segment_file": "results-2025-12-29.json",
        }
        result = format_metadata_for_ffmpeg(metadata)
        
        formatted_string = " ".join(result)
        assert "config (2025).yaml" in formatted_string
        assert "results-2025-12-29.json" in formatted_string


class TestLogMetadata:
    """Tests for log_metadata function."""

    def test_log_metadata_with_title(self, caplog):
        """Test logging metadata including title."""
        metadata = {
            "video_censor_personal_config_file": "config.yaml",
            "video_censor_personal_segment_file": "segments.json",
        }
        
        with caplog.at_level(logging.DEBUG):
            log_metadata(metadata, title="Family Video (Censored)")
        
        log_text = caplog.text
        assert "Setting video metadata: title = 'Family Video (Censored)'" in log_text
        assert "video_censor_personal_config_file = 'config.yaml'" in log_text
        assert "video_censor_personal_segment_file = 'segments.json'" in log_text

    def test_log_metadata_without_title(self, caplog):
        """Test logging metadata without title."""
        metadata = {
            "video_censor_personal_config_file": "config.yaml",
        }
        
        with caplog.at_level(logging.DEBUG):
            log_metadata(metadata)
        
        log_text = caplog.text
        assert "title" not in log_text
        assert "video_censor_personal_config_file = 'config.yaml'" in log_text

    def test_log_metadata_empty(self, caplog):
        """Test logging empty metadata."""
        with caplog.at_level(logging.DEBUG):
            log_metadata({})
        
        # Should not produce any log entries
        assert caplog.text == ""

    def test_log_metadata_all_remediation_flags(self, caplog):
        """Test logging all remediation flag metadata."""
        metadata = {
            "video_censor_personal_audio_remediation_enabled": "true",
            "video_censor_personal_video_remediation_enabled": "false",
            "video_censor_personal_processed_date": "2025-12-29T14:30:45.123-08:00",
        }
        
        with caplog.at_level(logging.DEBUG):
            log_metadata(metadata)
        
        log_text = caplog.text
        assert "video_censor_personal_audio_remediation_enabled = 'true'" in log_text
        assert "video_censor_personal_video_remediation_enabled = 'false'" in log_text
        assert "2025-12-29T14:30:45.123-08:00" in log_text
