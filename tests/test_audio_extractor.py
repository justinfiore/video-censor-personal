"""Tests for audio extraction module."""

import io
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

# Skip all tests if librosa is not installed
librosa = pytest.importorskip("librosa", reason="librosa not installed")

from video_censor_personal.audio_extractor import AudioExtractor, TARGET_SAMPLE_RATE


class TestAudioExtractorInitialization:
    """Test AudioExtractor initialization."""

    def test_init_creates_video_extractor(self):
        """Test that AudioExtractor creates VideoExtractor."""
        with patch(
            "video_censor_personal.audio_extractor.VideoExtractor"
        ) as mock_extractor:
            mock_extractor.return_value = MagicMock()
            extractor = AudioExtractor("/fake/video.mp4")

            assert extractor.video_path == "/fake/video.mp4"
            assert extractor._audio_data is None
            assert extractor._sample_rate == TARGET_SAMPLE_RATE
            mock_extractor.assert_called_once_with("/fake/video.mp4")

    def test_target_sample_rate_is_16khz(self):
        """Test that target sample rate is 16kHz for Whisper compatibility."""
        assert TARGET_SAMPLE_RATE == 16000


class TestAudioExtraction:
    """Test audio extraction functionality."""

    @patch("video_censor_personal.audio_extractor.VideoExtractor")
    @patch("video_censor_personal.audio_extractor.librosa")
    def test_extract_returns_cached_audio(self, mock_librosa, mock_video_extractor):
        """Test that extract() returns cached audio on subsequent calls."""
        mock_video_extractor.return_value = MagicMock()
        extractor = AudioExtractor("/fake/video.mp4")

        # Pre-populate cache
        cached_audio = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        extractor._audio_data = cached_audio

        audio, sr = extractor.extract()

        assert np.array_equal(audio, cached_audio)
        assert sr == TARGET_SAMPLE_RATE
        # VideoExtractor.extract_audio should NOT be called (cached)
        mock_video_extractor.return_value.extract_audio.assert_not_called()

    @patch("soundfile.read")
    @patch("video_censor_personal.audio_extractor.VideoExtractor")
    def test_extract_loads_audio_from_video(self, mock_video_extractor, mock_sf_read):
        """Test extraction from video file."""
        # Setup mock video extractor
        mock_extractor_instance = MagicMock()
        mock_audio_segment = MagicMock()
        mock_audio_segment.data = b"fake wav bytes"
        mock_audio_segment.duration.return_value = 1.0
        mock_extractor_instance.extract_audio.return_value = mock_audio_segment
        mock_video_extractor.return_value = mock_extractor_instance

        # Mock soundfile.read to return fake audio
        fake_audio = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        mock_sf_read.return_value = (fake_audio, 16000)

        extractor = AudioExtractor("/fake/video.mp4")
        audio, sr = extractor.extract()

        assert sr == TARGET_SAMPLE_RATE
        assert audio is not None
        mock_extractor_instance.extract_audio.assert_called_once()

    @patch("video_censor_personal.audio_extractor.librosa.resample")
    @patch("video_censor_personal.audio_extractor.VideoExtractor")
    def test_extract_resamples_to_16khz(
        self, mock_video_extractor, mock_resample
    ):
        """Test that audio is resampled to 16kHz if different."""
        mock_extractor_instance = MagicMock()
        mock_audio_segment = MagicMock()
        mock_audio_segment.data = b"fake wav bytes"
        mock_audio_segment.duration.return_value = 1.0
        mock_extractor_instance.extract_audio.return_value = mock_audio_segment
        mock_video_extractor.return_value = mock_extractor_instance

        # Return audio at 44100 Hz (needs resampling)
        fake_audio = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        mock_resample.return_value = np.array([0.1, 0.2], dtype=np.float32)

        with patch("soundfile.read", return_value=(fake_audio, 44100)):
            extractor = AudioExtractor("/fake/video.mp4")
            extractor.extract()

            mock_resample.assert_called_once()
            call_args = mock_resample.call_args
            assert call_args.kwargs["orig_sr"] == 44100
            assert call_args.kwargs["target_sr"] == TARGET_SAMPLE_RATE

    @patch("video_censor_personal.audio_extractor.VideoExtractor")
    def test_extract_converts_stereo_to_mono(self, mock_video_extractor):
        """Test stereo to mono conversion."""
        mock_extractor_instance = MagicMock()
        mock_audio_segment = MagicMock()
        mock_audio_segment.data = b"fake wav bytes"
        mock_audio_segment.duration.return_value = 1.0
        mock_extractor_instance.extract_audio.return_value = mock_audio_segment
        mock_video_extractor.return_value = mock_extractor_instance

        # Return stereo audio (2 channels)
        stereo_audio = np.array([[0.1, 0.3], [0.2, 0.4], [0.3, 0.5]], dtype=np.float32)

        with patch("soundfile.read", return_value=(stereo_audio, 16000)):
            extractor = AudioExtractor("/fake/video.mp4")
            audio, sr = extractor.extract()

            # Should be mono now
            assert len(audio.shape) == 1

    @patch("video_censor_personal.audio_extractor.VideoExtractor")
    def test_extract_raises_on_failure(self, mock_video_extractor):
        """Test RuntimeError on extraction failure."""
        mock_extractor_instance = MagicMock()
        mock_extractor_instance.extract_audio.side_effect = Exception("ffmpeg error")
        mock_video_extractor.return_value = mock_extractor_instance

        extractor = AudioExtractor("/fake/video.mp4")

        with pytest.raises(RuntimeError, match="Failed to extract audio"):
            extractor.extract()


class TestAudioSegmentSlicing:
    """Test audio segment extraction by time."""

    @patch("video_censor_personal.audio_extractor.VideoExtractor")
    def test_get_audio_segment_returns_none_when_no_audio(self, mock_video_extractor):
        """Test segment extraction with no cached audio."""
        mock_video_extractor.return_value = MagicMock()
        extractor = AudioExtractor("/fake/video.mp4")

        segment = extractor.get_audio_segment(start_time=0.0, duration=1.0)

        assert segment is None

    @patch("video_censor_personal.audio_extractor.VideoExtractor")
    def test_get_audio_segment_returns_correct_slice(self, mock_video_extractor):
        """Test segment extraction returns correct time slice."""
        mock_video_extractor.return_value = MagicMock()
        extractor = AudioExtractor("/fake/video.mp4")

        # Pre-populate with 2 seconds of audio at 16kHz
        sample_rate = 16000
        duration_sec = 2.0
        num_samples = int(sample_rate * duration_sec)
        extractor._audio_data = np.arange(num_samples, dtype=np.float32)

        # Get segment from 0.5s to 1.0s (0.5s duration)
        segment = extractor.get_audio_segment(start_time=0.5, duration=0.5)

        expected_start = int(0.5 * sample_rate)
        expected_length = int(0.5 * sample_rate)
        assert len(segment) == expected_length
        assert segment[0] == expected_start

    @patch("video_censor_personal.audio_extractor.VideoExtractor")
    def test_get_audio_segment_clamps_to_range(self, mock_video_extractor):
        """Test segment extraction clamps to available audio range."""
        mock_video_extractor.return_value = MagicMock()
        extractor = AudioExtractor("/fake/video.mp4")

        # Pre-populate with 1 second of audio at 16kHz
        sample_rate = 16000
        num_samples = sample_rate
        extractor._audio_data = np.arange(num_samples, dtype=np.float32)

        # Request segment that extends beyond available audio
        segment = extractor.get_audio_segment(start_time=0.8, duration=0.5)

        # Should clamp to end of available audio
        assert len(segment) < int(0.5 * sample_rate)

    @patch("video_censor_personal.audio_extractor.VideoExtractor")
    def test_get_audio_segment_returns_none_beyond_range(self, mock_video_extractor):
        """Test segment extraction returns None when start is beyond audio."""
        mock_video_extractor.return_value = MagicMock()
        extractor = AudioExtractor("/fake/video.mp4")

        extractor._audio_data = np.array([0.1, 0.2, 0.3], dtype=np.float32)

        # Request segment starting beyond available audio
        segment = extractor.get_audio_segment(start_time=10.0, duration=1.0)

        assert segment is None


class TestAudioExtractorCleanup:
    """Test resource cleanup."""

    @patch("video_censor_personal.audio_extractor.VideoExtractor")
    def test_cleanup_releases_audio_data(self, mock_video_extractor):
        """Test cleanup releases cached audio."""
        mock_extractor_instance = MagicMock()
        mock_video_extractor.return_value = mock_extractor_instance

        extractor = AudioExtractor("/fake/video.mp4")
        extractor._audio_data = np.array([0.1, 0.2, 0.3])

        extractor.cleanup()

        assert extractor._audio_data is None
        mock_extractor_instance.close.assert_called_once()

    @patch("video_censor_personal.audio_extractor.VideoExtractor")
    def test_cleanup_handles_close_error(self, mock_video_extractor):
        """Test cleanup handles VideoExtractor close errors gracefully."""
        mock_extractor_instance = MagicMock()
        mock_extractor_instance.close.side_effect = Exception("close error")
        mock_video_extractor.return_value = mock_extractor_instance

        extractor = AudioExtractor("/fake/video.mp4")

        # Should not raise
        extractor.cleanup()


class TestContextManager:
    """Test context manager functionality."""

    @patch("video_censor_personal.audio_extractor.VideoExtractor")
    def test_context_manager_calls_cleanup(self, mock_video_extractor):
        """Test context manager calls cleanup on exit."""
        mock_extractor_instance = MagicMock()
        mock_video_extractor.return_value = mock_extractor_instance

        with AudioExtractor("/fake/video.mp4") as extractor:
            extractor._audio_data = np.array([0.1, 0.2, 0.3])

        # After exiting context, cleanup should have been called
        mock_extractor_instance.close.assert_called()
