"""Tests for video extraction module."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import cv2
import numpy as np
import pytest

from video_censor_personal.frame import AudioSegment, Frame
from video_censor_personal.video_extraction import (
    VideoExtractor,
    _check_ffmpeg_available,
)


class TestFrame:
    """Test Frame data class."""

    def test_frame_creation(self):
        """Test creating a Frame object."""
        data = np.zeros((480, 640, 3), dtype=np.uint8)
        frame = Frame(index=0, timecode=1.5, data=data)

        assert frame.index == 0
        assert frame.timecode == 1.5
        assert frame.data.shape == (480, 640, 3)

    def test_frame_to_rgb(self):
        """Test BGR to RGB conversion."""
        bgr_data = np.array([[[255, 0, 0]]], dtype=np.uint8)  # Blue in BGR
        frame = Frame(index=0, timecode=0.0, data=bgr_data)

        rgb_data = frame.to_rgb()
        assert rgb_data[0, 0, 0] == 0  # Red channel = 0
        assert rgb_data[0, 0, 2] == 255  # Blue channel = 255

    def test_frame_timestamp_str(self):
        """Test timestamp formatting."""
        frame = Frame(index=0, timecode=3661.0, data=np.zeros((1, 1, 3)))
        assert frame.timestamp_str() == "01:01:01"

        frame = Frame(index=0, timecode=0.0, data=np.zeros((1, 1, 3)))
        assert frame.timestamp_str() == "00:00:00"

        frame = Frame(index=0, timecode=7322.0, data=np.zeros((1, 1, 3)))
        assert frame.timestamp_str() == "02:02:02"


class TestAudioSegment:
    """Test AudioSegment data class."""

    def test_audio_segment_creation(self):
        """Test creating an AudioSegment object."""
        audio_data = b"fake audio data"
        segment = AudioSegment(
            start_time=0.0, end_time=1.0, data=audio_data, sample_rate=16000
        )

        assert segment.start_time == 0.0
        assert segment.end_time == 1.0
        assert segment.data == audio_data
        assert segment.sample_rate == 16000

    def test_audio_segment_duration(self):
        """Test duration calculation."""
        segment = AudioSegment(
            start_time=10.0, end_time=15.5, data=b"audio", sample_rate=16000
        )
        assert segment.duration() == 5.5

    def test_audio_segment_default_sample_rate(self):
        """Test default sample rate."""
        segment = AudioSegment(start_time=0.0, end_time=1.0, data=b"audio")
        assert segment.sample_rate == 16000


class TestCheckFfmpegAvailable:
    """Test ffmpeg availability check."""

    def test_ffmpeg_available(self):
        """Test when ffmpeg is available."""
        with patch("shutil.which", return_value="/usr/bin/ffmpeg"):
            assert _check_ffmpeg_available() is True

    def test_ffmpeg_not_available(self):
        """Test when ffmpeg is not available."""
        with patch("shutil.which", return_value=None):
            assert _check_ffmpeg_available() is False


class TestVideoExtractorInitialization:
    """Test VideoExtractor initialization."""

    def test_file_not_found(self):
        """Test initialization with non-existent file."""
        with pytest.raises(FileNotFoundError):
            VideoExtractor("/nonexistent/file.mp4")

    def test_invalid_file_format(self, tmp_path):
        """Test initialization with invalid file."""
        invalid_file = tmp_path / "invalid.mp4"
        invalid_file.write_text("not a video")

        with pytest.raises(RuntimeError, match="Failed to open video file"):
            VideoExtractor(str(invalid_file))

    def test_valid_initialization(self, tmp_path):
        """Test initialization with valid video file."""
        # Create a minimal valid video file
        video_file = tmp_path / "test.mp4"

        # Create a simple video using OpenCV
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(str(video_file), fourcc, 30.0, (640, 480))
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        out.write(frame)
        out.release()

        extractor = VideoExtractor(str(video_file))
        assert extractor.video_path == video_file
        extractor.close()


class TestVideoExtractorMetadata:
    """Test VideoExtractor metadata methods."""

    def test_get_fps(self, tmp_path):
        """Test getting FPS from video."""
        video_file = tmp_path / "test.mp4"
        fps = 30.0

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(str(video_file), fourcc, fps, (640, 480))
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        for _ in range(30):
            out.write(frame)
        out.release()

        extractor = VideoExtractor(str(video_file))
        assert extractor.get_fps() == pytest.approx(fps, abs=1)
        extractor.close()

    def test_get_duration_seconds(self, tmp_path):
        """Test getting duration from video."""
        video_file = tmp_path / "test.mp4"
        fps = 30.0
        num_frames = 60

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(str(video_file), fourcc, fps, (640, 480))
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        for _ in range(num_frames):
            out.write(frame)
        out.release()

        extractor = VideoExtractor(str(video_file))
        duration = extractor.get_duration_seconds()
        expected_duration = num_frames / fps
        assert duration == pytest.approx(expected_duration, abs=1)
        extractor.close()

    def test_get_frame_count(self, tmp_path):
        """Test getting frame count from video."""
        video_file = tmp_path / "test.mp4"
        num_frames = 60

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(str(video_file), fourcc, 30.0, (640, 480))
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        for _ in range(num_frames):
            out.write(frame)
        out.release()

        extractor = VideoExtractor(str(video_file))
        assert extractor.get_frame_count() >= num_frames - 1
        extractor.close()


class TestExtractFrames:
    """Test frame extraction."""

    def test_extract_frames_basic(self, tmp_path):
        """Test basic frame extraction."""
        video_file = tmp_path / "test.mp4"

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(str(video_file), fourcc, 30.0, (640, 480))
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        for _ in range(30):
            out.write(frame)
        out.release()

        extractor = VideoExtractor(str(video_file))
        frames = list(extractor.extract_frames(sample_rate=1.0))

        assert len(frames) > 0
        assert all(isinstance(f, Frame) for f in frames)
        assert frames[0].index == 0
        assert frames[0].data.shape[2] == 3  # BGR
        extractor.close()

    def test_extract_all_frames(self, tmp_path):
        """Test extracting all frames."""
        video_file = tmp_path / "test.mp4"

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(str(video_file), fourcc, 30.0, (640, 480))
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        for _ in range(30):
            out.write(frame)
        out.release()

        extractor = VideoExtractor(str(video_file))
        frames = list(extractor.extract_frames(sample_rate=0))

        assert len(frames) > 20  # Should have many frames
        extractor.close()


class TestAudioExtraction:
    """Test audio extraction."""

    @patch("video_censor_personal.video_extraction._check_ffmpeg_available")
    def test_extract_audio_ffmpeg_not_available(
        self, mock_ffmpeg, tmp_path
    ):
        """Test audio extraction when ffmpeg not available."""
        mock_ffmpeg.return_value = False

        video_file = tmp_path / "test.mp4"
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(str(video_file), fourcc, 30.0, (640, 480))
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        out.write(frame)
        out.release()

        extractor = VideoExtractor(str(video_file))
        with pytest.raises(RuntimeError, match="ffmpeg is not available"):
            extractor.extract_audio()
        extractor.close()


class TestContextManager:
    """Test context manager functionality."""

    def test_context_manager(self, tmp_path):
        """Test VideoExtractor as context manager."""
        video_file = tmp_path / "test.mp4"

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(str(video_file), fourcc, 30.0, (640, 480))
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        out.write(frame)
        out.release()

        with VideoExtractor(str(video_file)) as extractor:
            assert extractor.video_path == video_file

        # After exiting context, should be closed
        # (we don't check capture state directly as it's internal)


class TestResourceCleanup:
    """Test resource cleanup."""

    def test_close_releases_resources(self, tmp_path):
        """Test that close() releases resources."""
        video_file = tmp_path / "test.mp4"

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(str(video_file), fourcc, 30.0, (640, 480))
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        out.write(frame)
        out.release()

        extractor = VideoExtractor(str(video_file))
        extractor.close()

        # Should not raise error when closing twice
        extractor.close()
