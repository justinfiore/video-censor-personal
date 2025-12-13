"""Tests for video muxing module."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from video_censor_personal.video_muxer import VideoMuxer


class TestVideoMuxerInitialization:
    """Test VideoMuxer initialization."""

    def test_init_validates_video_exists(self, tmp_path):
        """Test that initialization validates video file exists."""
        audio_file = tmp_path / "audio.wav"
        audio_file.write_bytes(b"fake audio")
        
        with pytest.raises(FileNotFoundError, match="Original video not found"):
            VideoMuxer("/nonexistent/video.mp4", str(audio_file))

    def test_init_validates_audio_exists(self, tmp_path):
        """Test that initialization validates audio file exists."""
        video_file = tmp_path / "video.mp4"
        video_file.write_bytes(b"fake video")
        
        with pytest.raises(FileNotFoundError, match="Remediated audio not found"):
            VideoMuxer(str(video_file), "/nonexistent/audio.wav")

    def test_init_success_with_valid_files(self, tmp_path):
        """Test successful initialization with valid files."""
        video_file = tmp_path / "video.mp4"
        video_file.write_bytes(b"fake video")
        audio_file = tmp_path / "audio.wav"
        audio_file.write_bytes(b"fake audio")
        
        muxer = VideoMuxer(str(video_file), str(audio_file))
        
        assert muxer.original_video_path == video_file
        assert muxer.remediated_audio_path == audio_file


class TestFfmpegCheck:
    """Test ffmpeg availability check."""

    @patch("shutil.which", return_value="/usr/bin/ffmpeg")
    def test_check_ffmpeg_available(self, mock_which):
        """Test when ffmpeg is available."""
        assert VideoMuxer._check_ffmpeg() is True
        mock_which.assert_called_with("ffmpeg")

    @patch("shutil.which", return_value=None)
    def test_check_ffmpeg_not_available(self, mock_which):
        """Test when ffmpeg is not available."""
        assert VideoMuxer._check_ffmpeg() is False


class TestVideoMuxing:
    """Test video muxing functionality."""

    @patch("subprocess.run")
    @patch.object(VideoMuxer, "_check_ffmpeg", return_value=True)
    def test_mux_video_calls_ffmpeg(self, mock_check, mock_run, tmp_path):
        """Test that mux_video calls ffmpeg with correct arguments."""
        video_file = tmp_path / "video.mp4"
        video_file.write_bytes(b"fake video")
        audio_file = tmp_path / "audio.wav"
        audio_file.write_bytes(b"fake audio")
        output_file = tmp_path / "output.mp4"
        
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        
        muxer = VideoMuxer(str(video_file), str(audio_file))
        muxer.mux_video(str(output_file))
        
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        
        # Verify command structure
        assert call_args[0] == "ffmpeg"
        assert "-i" in call_args
        assert str(video_file) in call_args
        assert str(audio_file) in call_args
        assert "-c:v" in call_args
        assert "copy" in call_args
        assert "-c:a" in call_args
        assert "aac" in call_args
        assert "-map" in call_args
        assert "-shortest" in call_args
        assert "-y" in call_args
        assert str(output_file) in call_args

    @patch.object(VideoMuxer, "_check_ffmpeg", return_value=False)
    def test_mux_video_raises_when_ffmpeg_missing(self, mock_check, tmp_path):
        """Test that mux_video raises when ffmpeg not available."""
        video_file = tmp_path / "video.mp4"
        video_file.write_bytes(b"fake video")
        audio_file = tmp_path / "audio.wav"
        audio_file.write_bytes(b"fake audio")
        
        muxer = VideoMuxer(str(video_file), str(audio_file))
        
        with pytest.raises(RuntimeError, match="ffmpeg not available"):
            muxer.mux_video(str(tmp_path / "output.mp4"))

    @patch("subprocess.run")
    @patch.object(VideoMuxer, "_check_ffmpeg", return_value=True)
    def test_mux_video_raises_on_ffmpeg_failure(self, mock_check, mock_run, tmp_path):
        """Test that mux_video raises on ffmpeg failure."""
        video_file = tmp_path / "video.mp4"
        video_file.write_bytes(b"fake video")
        audio_file = tmp_path / "audio.wav"
        audio_file.write_bytes(b"fake audio")
        
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="ffmpeg error: invalid codec"
        )
        
        muxer = VideoMuxer(str(video_file), str(audio_file))
        
        with pytest.raises(RuntimeError, match="ffmpeg muxing failed"):
            muxer.mux_video(str(tmp_path / "output.mp4"))

    @patch("subprocess.run")
    @patch.object(VideoMuxer, "_check_ffmpeg", return_value=True)
    def test_mux_video_handles_subprocess_exception(
        self, mock_check, mock_run, tmp_path
    ):
        """Test that mux_video handles subprocess exceptions."""
        video_file = tmp_path / "video.mp4"
        video_file.write_bytes(b"fake video")
        audio_file = tmp_path / "audio.wav"
        audio_file.write_bytes(b"fake audio")
        
        mock_run.side_effect = Exception("subprocess error")
        
        muxer = VideoMuxer(str(video_file), str(audio_file))
        
        with pytest.raises(RuntimeError, match="Video muxing failed"):
            muxer.mux_video(str(tmp_path / "output.mp4"))


class TestMuxVideoMapFlags:
    """Test correct mapping flags in ffmpeg command."""

    @patch("subprocess.run")
    @patch.object(VideoMuxer, "_check_ffmpeg", return_value=True)
    def test_map_flags_correct(self, mock_check, mock_run, tmp_path):
        """Test that -map flags are correctly set for video and audio."""
        video_file = tmp_path / "video.mp4"
        video_file.write_bytes(b"fake video")
        audio_file = tmp_path / "audio.wav"
        audio_file.write_bytes(b"fake audio")
        
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        
        muxer = VideoMuxer(str(video_file), str(audio_file))
        muxer.mux_video(str(tmp_path / "output.mp4"))
        
        call_args = mock_run.call_args[0][0]
        
        # Find -map arguments
        map_indices = [i for i, arg in enumerate(call_args) if arg == "-map"]
        assert len(map_indices) == 2
        
        # Verify video map (0:v:0 - first video stream from first input)
        video_map_idx = map_indices[0]
        assert call_args[video_map_idx + 1] == "0:v:0"
        
        # Verify audio map (1:a:0 - first audio stream from second input)
        audio_map_idx = map_indices[1]
        assert call_args[audio_map_idx + 1] == "1:a:0"
