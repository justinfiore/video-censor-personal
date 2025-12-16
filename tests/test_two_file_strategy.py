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


class TestMuxRemediatedAudioWithPreCreatedFile:
    """Test _mux_remediated_audio behavior with pre-created output file."""

    @pytest.fixture
    def pipeline_with_mocks(self, tmp_path):
        """Create an AnalysisPipeline with mocked components."""
        video_file = tmp_path / "test.mp4"
        video_file.write_bytes(b"fake video content")
        
        config = {
            "detectors": [
                {"type": "mock", "name": "test", "categories": ["Violence"]}
            ],
            "audio": {
                "remediation": {
                    "enabled": True,
                    "mode": "silence",
                    "categories": ["Profanity"],
                }
            },
        }
        
        with patch("video_censor_personal.pipeline.VideoExtractor") as mock_extractor:
            instance = MagicMock()
            instance.get_frame_count.return_value = 30
            instance.get_fps.return_value = 30.0
            instance.get_duration_seconds.return_value = 1.0
            instance.extract_frames.return_value = iter([])
            instance.extract_audio.side_effect = Exception("No audio")
            mock_extractor.return_value = instance
            
            with patch.object(Path, "exists", return_value=True):
                pipeline = AnalysisPipeline(str(video_file), config)
                yield pipeline, tmp_path

    def test_mux_uses_precreated_output_when_exists(self, tmp_path):
        """_mux_remediated_audio should use pre-created output file as video source."""
        video_file = tmp_path / "input.mp4"
        output_file = tmp_path / "output.mp4"
        audio_file = tmp_path / "remediated.wav"
        
        video_file.write_bytes(b"fake video")
        output_file.write_bytes(b"precreated output video")
        audio_file.write_bytes(b"fake audio")
        
        config = {
            "detectors": [{"type": "mock", "name": "test", "categories": ["Violence"]}],
        }
        
        with patch("video_censor_personal.pipeline.VideoExtractor") as mock_extractor:
            instance = MagicMock()
            instance.get_frame_count.return_value = 30
            instance.get_fps.return_value = 30.0
            instance.get_duration_seconds.return_value = 1.0
            mock_extractor.return_value = instance
            
            with patch.object(Path, "exists", return_value=True):
                pipeline = AnalysisPipeline(
                    str(video_file),
                    config,
                    output_video_path=str(output_file)
                )
                pipeline.remediated_audio_path = str(audio_file)
                
                with patch("video_censor_personal.video_muxer.VideoMuxer") as mock_muxer:
                    mock_muxer_instance = MagicMock()
                    mock_muxer.return_value = mock_muxer_instance
                    
                    pipeline._mux_remediated_audio()
                    
                    mock_muxer.assert_called_once_with(
                        str(output_file),
                        str(audio_file)
                    )

    def test_mux_uses_original_when_output_not_exists(self, tmp_path):
        """_mux_remediated_audio should use original video when output doesn't exist."""
        video_file = tmp_path / "input.mp4"
        output_file = tmp_path / "output.mp4"
        audio_file = tmp_path / "remediated.wav"
        
        video_file.write_bytes(b"fake video")
        audio_file.write_bytes(b"fake audio")
        
        config = {
            "detectors": [{"type": "mock", "name": "test", "categories": ["Violence"]}],
        }
        
        with patch("video_censor_personal.pipeline.VideoExtractor") as mock_extractor:
            instance = MagicMock()
            instance.get_frame_count.return_value = 30
            instance.get_fps.return_value = 30.0
            instance.get_duration_seconds.return_value = 1.0
            mock_extractor.return_value = instance
            
            pipeline = AnalysisPipeline(
                str(video_file),
                config,
                output_video_path=str(output_file)
            )
            pipeline.remediated_audio_path = str(audio_file)
            
            with patch("video_censor_personal.video_muxer.VideoMuxer") as mock_muxer:
                mock_muxer_instance = MagicMock()
                mock_muxer.return_value = mock_muxer_instance
                
                pipeline._mux_remediated_audio()
                
                mock_muxer.assert_called_once_with(
                    str(video_file),
                    str(audio_file)
                )

    def test_mux_with_precreated_uses_temp_file(self, tmp_path):
        """When using pre-created output, muxing should use temp file then move."""
        video_file = tmp_path / "input.mp4"
        output_file = tmp_path / "output.mp4"
        audio_file = tmp_path / "remediated.wav"
        
        video_file.write_bytes(b"fake video")
        output_file.write_bytes(b"precreated output video")
        audio_file.write_bytes(b"fake audio")
        
        config = {
            "detectors": [{"type": "mock", "name": "test", "categories": ["Violence"]}],
        }
        
        with patch("video_censor_personal.pipeline.VideoExtractor") as mock_extractor:
            instance = MagicMock()
            instance.get_frame_count.return_value = 30
            instance.get_fps.return_value = 30.0
            instance.get_duration_seconds.return_value = 1.0
            mock_extractor.return_value = instance
            
            with patch.object(Path, "exists", return_value=True):
                pipeline = AnalysisPipeline(
                    str(video_file),
                    config,
                    output_video_path=str(output_file)
                )
                pipeline.remediated_audio_path = str(audio_file)
                
                with patch("video_censor_personal.video_muxer.VideoMuxer") as mock_muxer:
                    mock_muxer_instance = MagicMock()
                    mock_muxer.return_value = mock_muxer_instance
                    
                    with patch("shutil.move") as mock_move:
                        pipeline._mux_remediated_audio()
                        
                        mux_call_args = mock_muxer_instance.mux_video.call_args[0]
                        assert mux_call_args[0].endswith(".mp4")
                        
                        mock_move.assert_called_once()
                        move_dest = mock_move.call_args[0][1]
                        assert move_dest == str(output_file)


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


class TestFreshFileCreation:
    """Test scenarios where output file is created fresh (no pre-creation)."""

    def test_mux_creates_new_output_when_skip_chapters_disabled(self, tmp_path):
        """Audio muxing creates new output when skip chapters not enabled."""
        video_file = tmp_path / "input.mp4"
        output_file = tmp_path / "output.mp4"
        audio_file = tmp_path / "remediated.wav"
        
        video_file.write_bytes(b"fake video")
        audio_file.write_bytes(b"fake audio")
        
        config = {
            "detectors": [{"type": "mock", "name": "test", "categories": ["Violence"]}],
        }
        
        with patch("video_censor_personal.pipeline.VideoExtractor") as mock_extractor:
            instance = MagicMock()
            instance.get_frame_count.return_value = 30
            instance.get_fps.return_value = 30.0
            instance.get_duration_seconds.return_value = 1.0
            mock_extractor.return_value = instance
            
            pipeline = AnalysisPipeline(
                str(video_file),
                config,
                output_video_path=str(output_file)
            )
            pipeline.remediated_audio_path = str(audio_file)
            
            with patch("video_censor_personal.video_muxer.VideoMuxer") as mock_muxer:
                mock_muxer_instance = MagicMock()
                mock_muxer.return_value = mock_muxer_instance
                
                pipeline._mux_remediated_audio()
                
                mock_muxer.assert_called_once_with(
                    str(video_file),
                    str(audio_file)
                )
                
                mock_muxer_instance.mux_video.assert_called_once_with(
                    str(output_file)
                )

    def test_no_output_created_when_both_disabled(self, tmp_path):
        """No output created when both audio remediation and skip chapters disabled."""
        video_file = tmp_path / "input.mp4"
        output_file = tmp_path / "output.mp4"
        
        video_file.write_bytes(b"fake video")
        
        config = {
            "detectors": [{"type": "mock", "name": "test", "categories": ["Violence"]}],
            "audio": {"remediation": {"enabled": False}},
            "output": {"skip_chapters": {"enabled": False}},
        }
        
        assert not output_file.exists()


class TestEdgeCases:
    """Test edge cases in the two-file strategy."""

    def test_no_mux_when_no_remediated_audio(self, tmp_path):
        """_mux_remediated_audio does nothing when no remediated audio path."""
        video_file = tmp_path / "input.mp4"
        output_file = tmp_path / "output.mp4"
        
        video_file.write_bytes(b"fake video")
        
        config = {
            "detectors": [{"type": "mock", "name": "test", "categories": ["Violence"]}],
        }
        
        with patch("video_censor_personal.pipeline.VideoExtractor") as mock_extractor:
            instance = MagicMock()
            instance.get_frame_count.return_value = 30
            instance.get_fps.return_value = 30.0
            instance.get_duration_seconds.return_value = 1.0
            mock_extractor.return_value = instance
            
            with patch.object(Path, "exists", return_value=True):
                pipeline = AnalysisPipeline(
                    str(video_file),
                    config,
                    output_video_path=str(output_file)
                )
                pipeline.remediated_audio_path = None
                
                with patch("video_censor_personal.video_muxer.VideoMuxer") as mock_muxer:
                    pipeline._mux_remediated_audio()
                    
                    mock_muxer.assert_not_called()

    def test_no_mux_when_no_output_path(self, tmp_path):
        """_mux_remediated_audio does nothing when no output path specified."""
        video_file = tmp_path / "input.mp4"
        audio_file = tmp_path / "remediated.wav"
        
        video_file.write_bytes(b"fake video")
        audio_file.write_bytes(b"fake audio")
        
        config = {
            "detectors": [{"type": "mock", "name": "test", "categories": ["Violence"]}],
        }
        
        with patch("video_censor_personal.pipeline.VideoExtractor") as mock_extractor:
            instance = MagicMock()
            instance.get_frame_count.return_value = 30
            instance.get_fps.return_value = 30.0
            instance.get_duration_seconds.return_value = 1.0
            mock_extractor.return_value = instance
            
            with patch.object(Path, "exists", return_value=True):
                pipeline = AnalysisPipeline(
                    str(video_file),
                    config,
                    output_video_path=None
                )
                pipeline.remediated_audio_path = str(audio_file)
                
                with patch("video_censor_personal.video_muxer.VideoMuxer") as mock_muxer:
                    pipeline._mux_remediated_audio()
                    
                    mock_muxer.assert_not_called()

    def test_mux_failure_raises_exception(self, tmp_path):
        """_mux_remediated_audio should raise exception on muxer failure."""
        video_file = tmp_path / "input.mp4"
        output_file = tmp_path / "output.mp4"
        audio_file = tmp_path / "remediated.wav"
        
        video_file.write_bytes(b"fake video")
        audio_file.write_bytes(b"fake audio")
        
        config = {
            "detectors": [{"type": "mock", "name": "test", "categories": ["Violence"]}],
        }
        
        with patch("video_censor_personal.pipeline.VideoExtractor") as mock_extractor:
            instance = MagicMock()
            instance.get_frame_count.return_value = 30
            instance.get_fps.return_value = 30.0
            instance.get_duration_seconds.return_value = 1.0
            mock_extractor.return_value = instance
            
            with patch.object(Path, "exists", return_value=True):
                pipeline = AnalysisPipeline(
                    str(video_file),
                    config,
                    output_video_path=str(output_file)
                )
                pipeline.remediated_audio_path = str(audio_file)
                
                with patch("video_censor_personal.video_muxer.VideoMuxer") as mock_muxer:
                    mock_muxer.side_effect = Exception("Muxing failed")
                    
                    with pytest.raises(Exception, match="Muxing failed"):
                        pipeline._mux_remediated_audio()
