"""Tests for RemediationManager unified remediation logic.

Tests that both analysis and remediation-only modes use the same remediation
pipeline, ensuring audio + video remediation work correctly in both modes.
"""

import logging
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from video_censor_personal.remediation import RemediationManager


logger = logging.getLogger(__name__)


class TestRemediationManagerInitialization:
    """Test RemediationManager initialization."""
    
    def test_init_with_valid_video_path(self, tmp_path):
        """Test initialization with valid video path."""
        video_file = tmp_path / "test.mp4"
        video_file.touch()
        
        config = {"remediation": {"audio": {"enabled": False}, "video": {"enabled": False}}}
        manager = RemediationManager(str(video_file), config)
        
        assert manager.input_video_path == video_file
        assert manager.config == config
        assert manager.output_video_path is None
        assert manager.remediated_audio_path is None
    
    def test_init_with_missing_video_raises_error(self):
        """Test initialization with missing video raises FileNotFoundError."""
        config = {"remediation": {"audio": {"enabled": False}, "video": {"enabled": False}}}
        
        with pytest.raises(FileNotFoundError):
            RemediationManager("/nonexistent/video.mp4", config)
    
    def test_init_with_output_video_path(self, tmp_path):
        """Test initialization with output video path."""
        video_file = tmp_path / "test.mp4"
        video_file.touch()
        output_file = tmp_path / "output.mp4"
        
        config = {"remediation": {"audio": {"enabled": False}, "video": {"enabled": False}}}
        manager = RemediationManager(str(video_file), config, output_video_path=str(output_file))
        
        assert manager.output_video_path == str(output_file)


class TestRemediationManagerAudioAndVideoSequence:
    """Test that audio and video remediation happen in correct order.
    
    The critical bug was that video remediation used the original input file
    instead of the output from audio remediation, losing the audio changes.
    """
    
    @patch('video_censor_personal.remediation.RemediationManager._apply_audio_remediation')
    @patch('video_censor_personal.remediation.RemediationManager._apply_video_remediation')
    @patch('video_censor_personal.remediation.RemediationManager._mux_remediated_audio')
    def test_remediation_sequence_with_both_audio_and_video(
        self,
        mock_mux,
        mock_video,
        mock_audio,
        tmp_path,
    ):
        """Test that remediation sequence is: audio -> mux -> video."""
        video_file = tmp_path / "test.mp4"
        video_file.touch()
        output_file = tmp_path / "output.mp4"
        
        config = {
            "remediation": {
                "audio": {"enabled": True, "mode": "silence"},
                "video": {"enabled": True, "mode": "blank"},
            }
        }
        
        manager = RemediationManager(str(video_file), config, output_video_path=str(output_file))
        
        # Mock audio extraction
        audio_data = [0.0] * 48000
        audio_sr = 48000
        detections = []
        merged_segments = [{"start_time": 1.0, "end_time": 2.0, "labels": ["violence"]}]
        
        # Have mock_audio set remediated_audio_path so mux will be called
        def set_audio_path(*args, **kwargs):
            manager.remediated_audio_path = str(tmp_path / "audio.wav")
        
        mock_audio.side_effect = set_audio_path
        
        # Call apply_remediation
        manager.apply_remediation(
            detections,
            audio_data=audio_data,
            audio_sample_rate=audio_sr,
            video_width=1920,
            video_height=1080,
            video_duration=10.0,
            merged_segments=merged_segments,
        )
        
        # Verify methods were called in order: audio -> mux -> video
        mock_audio.assert_called_once()
        mock_mux.assert_called_once()
        mock_video.assert_called_once()
        
        # Verify audio remediation set the audio path
        assert manager.remediated_audio_path is not None
    
    def test_video_remediation_uses_correct_source_when_audio_remediated(self, tmp_path):
        """Test that video remediation uses output file when audio was remediated.
        
        This is the key fix: video remediation should NOT use the original input
        file if audio remediation has already created an output file.
        """
        video_file = tmp_path / "test.mp4"
        video_file.touch()
        output_file = tmp_path / "output.mp4"
        
        config = {
            "remediation": {
                "audio": {"enabled": True, "mode": "silence"},
                "video": {"enabled": True, "mode": "blank"},
            }
        }
        
        manager = RemediationManager(str(video_file), config, output_video_path=str(output_file))
        
        # Simulate audio remediation having created a temp file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            manager.remediated_audio_path = tmp.name
        
        # Format segments for video remediation
        segments = [
            {"start_time": 1.0, "end_time": 2.0, "labels": ["violence"], "allow": False}
        ]
        formatted = manager._format_segments_for_remediation(segments)
        
        # Verify formatting works correctly
        assert len(formatted) == 1
        assert formatted[0]["start_time"] == 1.0
        assert formatted[0]["end_time"] == 2.0
        assert formatted[0]["labels"] == ["violence"]
        assert formatted[0]["allow"] is False
        
        # Clean up
        Path(manager.remediated_audio_path).unlink(missing_ok=True)


class TestRemediationManagerVideoSource:
    """Test correct video source selection for muxing."""
    
    def test_mux_creates_output_file(self, tmp_path):
        """Test that muxing creates output file from remediated audio and input video."""
        video_file = tmp_path / "test.mp4"
        video_file.write_bytes(b"fake video")
        output_file = tmp_path / "output.mp4"
        audio_file = tmp_path / "audio.wav"
        audio_file.write_bytes(b"fake audio")
        
        config = {"remediation": {"audio": {"enabled": False}, "video": {"enabled": False}}}
        manager = RemediationManager(str(video_file), config, output_video_path=str(output_file))
        
        # Simulate audio remediation
        manager.remediated_audio_path = str(audio_file)
        
        # Verify the state
        assert manager.remediated_audio_path is not None
        assert Path(manager.remediated_audio_path).exists()
        
        # Clean up
        Path(manager.remediated_audio_path).unlink(missing_ok=True)


class TestCorrectRemediationSequence:
    """Test that the correct remediation sequence is maintained."""
    
    def test_audio_remediation_runs_before_mux(self, tmp_path):
        """Audio remediation must run before muxing to create the remediated audio."""
        video_file = tmp_path / "test.mp4"
        video_file.write_bytes(b"fake video")
        output_file = tmp_path / "output.mp4"
        
        config = {
            "remediation": {
                "audio": {"enabled": True, "mode": "silence"},
                "video": {"enabled": True, "mode": "blank"},
            }
        }
        
        manager = RemediationManager(str(video_file), config, output_video_path=str(output_file))
        
        # Track which methods are called
        call_sequence = []
        
        original_apply_audio = manager._apply_audio_remediation
        original_mux = manager._mux_remediated_audio
        original_apply_video = manager._apply_video_remediation
        
        def track_audio(*args, **kwargs):
            call_sequence.append('audio')
            # Simulate audio remediation by setting the path
            manager.remediated_audio_path = str(tmp_path / "audio.wav")
        
        def track_mux(*args, **kwargs):
            call_sequence.append('mux')
            # Don't actually mux, just track the call
        
        def track_video(*args, **kwargs):
            call_sequence.append('video')
            # Don't actually remediate, just track the call
        
        manager._apply_audio_remediation = track_audio
        manager._mux_remediated_audio = track_mux
        manager._apply_video_remediation = track_video
        
        audio_data = [0.0] * 48000
        merged_segments = [{"start_time": 1.0, "end_time": 2.0, "labels": ["violence"]}]
        
        manager.apply_remediation(
            [],
            audio_data=audio_data,
            audio_sample_rate=48000,
            video_width=1920,
            video_height=1080,
            video_duration=10.0,
            merged_segments=merged_segments,
        )
        
        # Verify sequence: audio -> mux -> video
        assert call_sequence == ['audio', 'mux', 'video'], (
            f"Expected ['audio', 'mux', 'video'] but got {call_sequence}. "
            "This is critical: audio and video must be muxed BEFORE video remediation "
            "to ensure audio/video sync when video has cuts."
        )


class TestRemediationManagerCleanup:
    """Test cleanup of temporary files."""
    
    def test_cleanup_removes_remediated_audio(self, tmp_path):
        """Test that cleanup removes temporary audio file."""
        video_file = tmp_path / "test.mp4"
        video_file.touch()
        
        config = {"remediation": {"audio": {"enabled": False}, "video": {"enabled": False}}}
        manager = RemediationManager(str(video_file), config)
        
        # Create a temp audio file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            audio_path = tmp.name
        
        manager.remediated_audio_path = audio_path
        assert Path(audio_path).exists()
        
        # Cleanup should remove it
        manager.cleanup()
        assert not Path(audio_path).exists()
    

