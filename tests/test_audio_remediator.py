"""Tests for audio remediation module."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from video_censor_personal.audio_remediator import AudioRemediator
from video_censor_personal.frame import DetectionResult


class TestAudioRemediatorInitialization:
    """Test AudioRemediator initialization."""

    def test_init_with_default_config(self):
        """Test initialization with default configuration."""
        config = {}
        
        remediator = AudioRemediator(config)
        
        assert remediator.enabled is False
        assert remediator.mode == "silence"
        assert remediator.categories == set()
        assert remediator.bleep_frequency == 1000

    def test_init_with_custom_config(self):
        """Test initialization with custom configuration."""
        config = {
            "enabled": True,
            "mode": "bleep",
            "categories": ["Profanity", "Violence"],
            "bleep_frequency": 800,
        }
        
        remediator = AudioRemediator(config)
        
        assert remediator.enabled is True
        assert remediator.mode == "bleep"
        assert remediator.categories == {"Profanity", "Violence"}
        assert remediator.bleep_frequency == 800

    def test_init_invalid_mode(self):
        """Test initialization rejects invalid mode."""
        config = {
            "mode": "invalid",
        }
        
        with pytest.raises(ValueError, match="Invalid remediation mode"):
            AudioRemediator(config)

    def test_init_negative_frequency(self):
        """Test initialization rejects negative frequency."""
        config = {
            "bleep_frequency": -100,
        }
        
        with pytest.raises(ValueError, match="must be positive"):
            AudioRemediator(config)

    def test_init_zero_frequency(self):
        """Test initialization rejects zero frequency."""
        config = {
            "bleep_frequency": 0,
        }
        
        with pytest.raises(ValueError, match="must be positive"):
            AudioRemediator(config)


class TestSilenceMode:
    """Test silence remediation mode."""

    def test_silence_zeros_out_samples(self):
        """Test that silence mode zeros out audio samples."""
        config = {
            "enabled": True,
            "mode": "silence",
            "categories": ["Profanity"],
        }
        remediator = AudioRemediator(config)
        
        # Create audio with known values
        sample_rate = 16000
        audio = np.ones(sample_rate * 2, dtype=np.float32)  # 2 seconds
        
        # Detection from 0.5s to 1.0s
        detections = [
            DetectionResult(
                start_time=0.5,
                end_time=1.0,
                label="Profanity",
                confidence=0.95,
                reasoning="test",
            )
        ]
        
        result = remediator.remediate(audio, sample_rate, detections)
        
        # Check silenced region
        start_sample = int(0.5 * sample_rate)
        end_sample = int(1.0 * sample_rate)
        assert np.all(result[start_sample:end_sample] == 0.0)
        
        # Check non-silenced regions are unchanged
        assert np.all(result[:start_sample] == 1.0)
        assert np.all(result[end_sample:] == 1.0)

    def test_silence_multiple_detections(self):
        """Test silencing multiple detection segments."""
        config = {
            "enabled": True,
            "mode": "silence",
            "categories": ["Profanity"],
        }
        remediator = AudioRemediator(config)
        
        sample_rate = 16000
        audio = np.ones(sample_rate * 3, dtype=np.float32)  # 3 seconds
        
        detections = [
            DetectionResult(
                start_time=0.0, end_time=0.5, label="Profanity",
                confidence=0.95, reasoning="test1",
            ),
            DetectionResult(
                start_time=2.0, end_time=2.5, label="Profanity",
                confidence=0.95, reasoning="test2",
            ),
        ]
        
        result = remediator.remediate(audio, sample_rate, detections)
        
        # Check both regions silenced
        assert np.all(result[0:8000] == 0.0)
        assert np.all(result[32000:40000] == 0.0)
        
        # Check middle region unchanged
        assert np.all(result[8000:32000] == 1.0)


class TestBleepMode:
    """Test bleep remediation mode."""

    def test_bleep_generates_tone(self):
        """Test that bleep mode generates sine wave tone."""
        config = {
            "enabled": True,
            "mode": "bleep",
            "categories": ["Profanity"],
            "bleep_frequency": 1000,
        }
        remediator = AudioRemediator(config)
        
        sample_rate = 16000
        audio = np.zeros(sample_rate, dtype=np.float32)  # 1 second
        
        detections = [
            DetectionResult(
                start_time=0.0,
                end_time=0.1,
                label="Profanity",
                confidence=0.95,
                reasoning="test",
            )
        ]
        
        result = remediator.remediate(audio, sample_rate, detections)
        
        # Check bleeped region is not zero
        end_sample = int(0.1 * sample_rate)
        assert not np.all(result[:end_sample] == 0.0)
        
        # Check amplitude is reasonable (0.2 * sin = max 0.2)
        assert np.max(np.abs(result[:end_sample])) <= 0.21

    def test_bleep_frequency_affects_tone(self):
        """Test that bleep frequency affects generated tone."""
        sample_rate = 16000
        audio = np.zeros(sample_rate, dtype=np.float32)
        
        detections = [
            DetectionResult(
                start_time=0.0, end_time=0.1, label="Profanity",
                confidence=0.95, reasoning="test",
            )
        ]
        
        # Low frequency bleep
        config_low = {
            "enabled": True,
            "mode": "bleep",
            "categories": ["Profanity"],
            "bleep_frequency": 500,
        }
        result_low = AudioRemediator(config_low).remediate(audio.copy(), sample_rate, detections)
        
        # High frequency bleep
        config_high = {
            "enabled": True,
            "mode": "bleep",
            "categories": ["Profanity"],
            "bleep_frequency": 2000,
        }
        result_high = AudioRemediator(config_high).remediate(audio.copy(), sample_rate, detections)
        
        # Results should be different (different frequencies)
        assert not np.allclose(result_low[:1600], result_high[:1600])


class TestCategoryFiltering:
    """Test per-category remediation filtering."""

    def test_skips_non_matching_categories(self):
        """Test that remediation skips detections not in categories list."""
        config = {
            "enabled": True,
            "mode": "silence",
            "categories": ["Profanity"],  # Only Profanity
        }
        remediator = AudioRemediator(config)
        
        sample_rate = 16000
        audio = np.ones(sample_rate, dtype=np.float32)
        
        detections = [
            DetectionResult(
                start_time=0.0, end_time=0.5, label="Violence",  # Not in categories
                confidence=0.95, reasoning="test",
            )
        ]
        
        result = remediator.remediate(audio, sample_rate, detections)
        
        # Audio should be unchanged (Violence not in categories)
        assert np.all(result == 1.0)

    def test_remediates_matching_categories_only(self):
        """Test that only matching categories are remediated."""
        config = {
            "enabled": True,
            "mode": "silence",
            "categories": ["Profanity"],
        }
        remediator = AudioRemediator(config)
        
        sample_rate = 16000
        audio = np.ones(sample_rate, dtype=np.float32)
        
        detections = [
            DetectionResult(
                start_time=0.0, end_time=0.25, label="Profanity",
                confidence=0.95, reasoning="test1",
            ),
            DetectionResult(
                start_time=0.5, end_time=0.75, label="Violence",
                confidence=0.95, reasoning="test2",
            ),
        ]
        
        result = remediator.remediate(audio, sample_rate, detections)
        
        # Profanity section silenced
        assert np.all(result[0:4000] == 0.0)
        
        # Violence section unchanged
        assert np.all(result[8000:12000] == 1.0)


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_disabled_remediation_returns_original(self):
        """Test that disabled remediation returns original audio."""
        config = {
            "enabled": False,
            "mode": "silence",
            "categories": ["Profanity"],
        }
        remediator = AudioRemediator(config)
        
        audio = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        
        detections = [
            DetectionResult(
                start_time=0.0, end_time=0.1, label="Profanity",
                confidence=0.95, reasoning="test",
            )
        ]
        
        result = remediator.remediate(audio, 16000, detections)
        
        assert np.array_equal(result, audio)

    def test_empty_detections_returns_original(self):
        """Test that empty detections returns original audio."""
        config = {
            "enabled": True,
            "mode": "silence",
            "categories": ["Profanity"],
        }
        remediator = AudioRemediator(config)
        
        audio = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        
        result = remediator.remediate(audio, 16000, [])
        
        assert np.array_equal(result, audio)

    def test_clamps_to_valid_range(self):
        """Test that sample indices are clamped to valid range."""
        config = {
            "enabled": True,
            "mode": "silence",
            "categories": ["Profanity"],
        }
        remediator = AudioRemediator(config)
        
        sample_rate = 16000
        audio = np.ones(sample_rate, dtype=np.float32)  # 1 second
        
        # Detection extends beyond audio
        detections = [
            DetectionResult(
                start_time=0.8, end_time=2.0, label="Profanity",
                confidence=0.95, reasoning="test",
            )
        ]
        
        result = remediator.remediate(audio, sample_rate, detections)
        
        # Should silence from 0.8s to end
        start_sample = int(0.8 * sample_rate)
        assert np.all(result[start_sample:] == 0.0)
        assert np.all(result[:start_sample] == 1.0)

    def test_handles_invalid_range(self):
        """Test handling of invalid sample range."""
        config = {
            "enabled": True,
            "mode": "silence",
            "categories": ["Profanity"],
        }
        remediator = AudioRemediator(config)
        
        audio = np.ones(16000, dtype=np.float32)
        
        # Detection with start >= end after conversion
        detections = [
            DetectionResult(
                start_time=10.0, end_time=10.0, label="Profanity",
                confidence=0.95, reasoning="test",
            )
        ]
        
        result = remediator.remediate(audio, 16000, detections)
        
        # Should return audio unchanged
        assert np.all(result == 1.0)


class TestAudioFileWriting:
    """Test audio file writing functionality."""

    def test_write_audio_creates_file(self, tmp_path):
        """Test that write_audio creates WAV file."""
        config = {}
        remediator = AudioRemediator(config)
        
        audio = np.array([0.1, 0.2, 0.3, 0.4, 0.5], dtype=np.float32)
        output_path = str(tmp_path / "test_output.wav")
        
        remediator.write_audio(audio, 16000, output_path)
        
        assert Path(output_path).exists()

    def test_write_audio_readable(self, tmp_path):
        """Test that written audio file is readable."""
        import soundfile as sf
        
        config = {}
        remediator = AudioRemediator(config)
        
        audio = np.random.randn(16000).astype(np.float32) * 0.5
        output_path = str(tmp_path / "test_output.wav")
        
        remediator.write_audio(audio, 16000, output_path)
        
        # Read back and verify
        read_audio, read_sr = sf.read(output_path)
        assert read_sr == 16000
        assert len(read_audio) == len(audio)

    @patch("soundfile.write")
    def test_write_audio_handles_error(self, mock_write):
        """Test that write_audio handles errors gracefully."""
        mock_write.side_effect = Exception("Write error")
        
        config = {}
        remediator = AudioRemediator(config)
        
        audio = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        
        with pytest.raises(RuntimeError, match="Failed to write audio"):
            remediator.write_audio(audio, 16000, "/fake/path.wav")
