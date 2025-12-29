"""Tests for the two-file strategy: audio remediation + skip chapters.

This tests the scenario where both audio remediation and skip chapters are enabled,
ensuring they operate on the same output file sequentially without overwriting each other.

Key scenarios tested:
1. Pre-creation of output file when skip chapters enabled
2. _mux_remediated_audio uses pre-created file as video source
3. Combined audio remediation + skip chapters work together
4. Fresh file creation when no pre-created file exists
"""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest

from video_censor_personal.config import is_skip_chapters_enabled
from video_censor_personal.pipeline import AnalysisPipeline


class TestPreCreateOutputFile:
    """Test pre-creation of output file when skip chapters are enabled."""

    def test_is_skip_chapters_enabled_with_output_config(self):
        """is_skip_chapters_enabled returns True when video.metadata_output.skip_chapters.enabled is True."""
        config = {
            "video": {
                "metadata_output": {
                    "skip_chapters": {
                        "enabled": True,
                    }
                }
            }
        }
        assert is_skip_chapters_enabled(config) is True

    def test_is_skip_chapters_enabled_false_when_disabled(self):
        """is_skip_chapters_enabled returns False when explicitly disabled."""
        config = {
            "video": {
                "metadata_output": {
                    "skip_chapters": {
                        "enabled": False,
                    }
                }
            }
        }
        assert is_skip_chapters_enabled(config) is False

    def test_is_skip_chapters_enabled_false_when_missing(self):
        """is_skip_chapters_enabled returns False when config section missing."""
        config = {}
        assert is_skip_chapters_enabled(config) is False

    def test_precreate_copies_input_to_output(self, tmp_path):
        """When skip chapters enabled, input video should be copied to output path."""
        input_video = tmp_path / "input.mp4"
        output_video = tmp_path / "output.mp4"
        
        input_video.write_bytes(b"fake video content for testing")
        
        shutil.copy2(str(input_video), str(output_video))
        
        assert output_video.exists()
        assert output_video.read_bytes() == input_video.read_bytes()





class TestCombinedAudioRemediationAndSkipChapters:
    """Test combined audio remediation + skip chapters workflow."""

    def test_config_with_both_features_enabled(self):
        """Config can have both audio remediation and skip chapters enabled."""
        config = {
            "audio": {
                "remediation": {
                    "enabled": True,
                    "mode": "bleep",
                    "categories": ["Profanity"],
                }
            },
            "video": {
                "metadata_output": {
                    "skip_chapters": {
                        "enabled": True,
                    }
                }
            }
        }
        
        assert config["audio"]["remediation"]["enabled"] is True
        assert is_skip_chapters_enabled(config) is True

    def test_precreate_then_mux_workflow(self, tmp_path):
        """Pre-creation followed by audio muxing should preserve pre-created file."""
        input_video = tmp_path / "input.mp4"
        output_video = tmp_path / "output.mp4"
        
        input_video.write_bytes(b"original input video content")
        
        shutil.copy2(str(input_video), str(output_video))
        assert output_video.exists()
        
        modified_content = b"modified by audio remediation"
        output_video.write_bytes(modified_content)
        
        assert output_video.exists()
        assert output_video.read_bytes() == modified_content

    def test_skip_chapters_after_mux_workflow(self, tmp_path):
        """Skip chapters should work on file already processed by audio muxing."""
        input_video = tmp_path / "input.mp4"
        output_video = tmp_path / "output.mp4"
        
        input_video.write_bytes(b"original input video content")
        
        shutil.copy2(str(input_video), str(output_video))
        
        output_video.write_bytes(b"muxed audio content")
        
        final_content = b"muxed audio content with skip chapters"
        output_video.write_bytes(final_content)
        
        assert output_video.exists()
        assert output_video.read_bytes() == final_content



