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


class TestStereoAudio:
    """Test multi-channel (stereo) audio handling."""

    def test_silence_stereo_audio(self):
        """Test silencing stereo audio zeros all channels."""
        config = {
            "enabled": True,
            "mode": "silence",
            "categories": ["Profanity"],
        }
        remediator = AudioRemediator(config)
        
        sample_rate = 16000
        # Stereo audio: shape (samples, 2)
        audio = np.ones((sample_rate, 2), dtype=np.float32)
        
        detections = [
            DetectionResult(
                start_time=0.5, end_time=1.0, label="Profanity",
                confidence=0.95, reasoning="test",
            )
        ]
        
        result = remediator.remediate(audio, sample_rate, detections)
        
        # Check silenced region (both channels)
        start_sample = int(0.5 * sample_rate)
        end_sample = int(1.0 * sample_rate)
        assert np.all(result[start_sample:end_sample] == 0.0)
        
        # Check non-silenced regions unchanged
        assert np.all(result[:start_sample] == 1.0)

    def test_bleep_stereo_audio(self):
        """Test bleeping stereo audio applies tone to all channels."""
        config = {
            "enabled": True,
            "mode": "bleep",
            "categories": ["Profanity"],
            "bleep_frequency": 1000,
        }
        remediator = AudioRemediator(config)
        
        sample_rate = 16000
        # Stereo audio: shape (samples, 2)
        audio = np.zeros((sample_rate, 2), dtype=np.float32)
        
        detections = [
            DetectionResult(
                start_time=0.0, end_time=0.1, label="Profanity",
                confidence=0.95, reasoning="test",
            )
        ]
        
        result = remediator.remediate(audio, sample_rate, detections)
        
        # Check bleeped region has tone in both channels
        end_sample = int(0.1 * sample_rate)
        assert result.shape == (sample_rate, 2)
        assert not np.all(result[:end_sample] == 0.0)
        
        # Both channels should have the same tone
        assert np.allclose(result[:end_sample, 0], result[:end_sample, 1])

    def test_bleep_multichannel_audio(self):
        """Test bleeping audio with more than 2 channels."""
        config = {
            "enabled": True,
            "mode": "bleep",
            "categories": ["Profanity"],
        }
        remediator = AudioRemediator(config)
        
        sample_rate = 16000
        # 5.1 surround: shape (samples, 6)
        audio = np.zeros((sample_rate, 6), dtype=np.float32)
        
        detections = [
            DetectionResult(
                start_time=0.0, end_time=0.1, label="Profanity",
                confidence=0.95, reasoning="test",
            )
        ]
        
        result = remediator.remediate(audio, sample_rate, detections)
        
        # Shape should be preserved
        assert result.shape == (sample_rate, 6)
        
        # All 6 channels should have the same tone
        end_sample = int(0.1 * sample_rate)
        for ch in range(1, 6):
            assert np.allclose(result[:end_sample, 0], result[:end_sample, ch])


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


class TestAudioRemediationWithMixedCategories:
    """Test audio remediation with segments containing multiple categories."""
    
    def test_remediate_segment_with_profanity_and_violence_only_profanity_enabled(self):
        """Test that only enabled categories are remediated.
        
        Scenario: Segment has both "Profanity" and "Violence" labels.
        Audio remediation is configured for "Profanity" only.
        Result: Profanity segment should be remediated, Violence should be skipped.
        """
        config = {
            "enabled": True,
            "mode": "bleep",
            "categories": ["Profanity"],  # Only Profanity enabled
            "bleep_frequency": 1000,
        }
        
        remediator = AudioRemediator(config)
        
        # Create audio data
        audio = np.array([0.1, 0.2, 0.3, 0.4, 0.5] * 100, dtype=np.float32)
        sample_rate = 16000
        
        # Create detection with multiple categories
        detection = MagicMock()
        detection.label = "Profanity"  # First label
        detection.start_time = 0.0
        detection.end_time = 1.0
        
        # Remediate with only this detection
        remediated = remediator.remediate(audio, sample_rate, [detection])
        
        # Verify audio was modified (not silent)
        # The bleeping should have introduced sine wave data
        assert remediated is not None
        assert len(remediated) == len(audio)
        # At least part of the audio should be different (bleeping applied)
        assert not np.allclose(remediated, audio)
    
    def test_remediate_mixed_categories_skip_violence(self):
        """Test that segments with Violence label are skipped when not in categories.
        
        Scenario: Segment has both "Profanity" and "Violence" labels.
        Audio remediation is configured for "Profanity" only.
        Violence detection should be ignored (not in categories set).
        """
        config = {
            "enabled": True,
            "mode": "silence",
            "categories": ["Profanity"],  # Violence not in list
        }
        
        remediator = AudioRemediator(config)
        
        # Create audio with 2 seconds at 16kHz = 32000 samples
        audio = np.array([0.1] * 32000, dtype=np.float32)
        sample_rate = 16000
        
        # Create two detections
        profanity_detection = MagicMock()
        profanity_detection.label = "Profanity"
        profanity_detection.start_time = 0.0
        profanity_detection.end_time = 0.5
        
        violence_detection = MagicMock()
        violence_detection.label = "Violence"
        violence_detection.start_time = 1.0
        violence_detection.end_time = 1.5
        
        detections = [profanity_detection, violence_detection]
        
        remediated = remediator.remediate(audio, sample_rate, detections)
        
        # Profanity should be silenced (0.0-0.5 seconds)
        profanity_start = int(0.0 * sample_rate)
        profanity_end = int(0.5 * sample_rate)
        assert np.allclose(remediated[profanity_start:profanity_end], 0.0)
        
        # Violence should NOT be silenced (1.0-1.5 seconds) - not in categories
        violence_start = int(1.0 * sample_rate)
        violence_end = int(1.5 * sample_rate)
        assert not np.allclose(remediated[violence_start:violence_end], 0.0)
        assert np.allclose(remediated[violence_start:violence_end], 0.1)
    
    def test_remediate_profanity_violence_with_allow_override(self):
        """Test allow flag overrides remediation for segments with multiple categories.
        
        Scenario: Segment with ["Profanity", "Violence"] is marked allow=true.
        Result: No remediation should occur despite having enabled categories.
        """
        config = {
            "enabled": True,
            "mode": "silence",
            "categories": ["Profanity", "Violence"],
        }
        
        remediator = AudioRemediator(config)
        
        audio = np.array([0.5] * 100, dtype=np.float32)
        sample_rate = 16000
        
        # Detection with multiple labels
        detection = MagicMock()
        detection.label = "Profanity"
        detection.start_time = 0.0
        detection.end_time = 1.0
        
        # Segment marked as allowed (should skip remediation)
        segments = [{
            "start_time": 0.0,
            "end_time": 1.0,
            "allow": True,  # Mark as allowed
            "labels": ["Profanity", "Violence"]
        }]
        
        remediated = remediator.remediate(audio, sample_rate, [detection], segments=segments)
        
        # Audio should be unchanged (allowed segment skipped)
        assert np.allclose(remediated, audio)
    
    def test_remediate_multiple_mixed_detections(self):
        """Test remediation of multiple segments with mixed categories.
        
        Scenario: 
        - Segment 1: Profanity + Violence (allow=false)
        - Segment 2: Profanity only (allow=false)
        Config: Only Profanity enabled for remediation
        Result: Both segments have Profanity remediated, Violence ignored
        """
        config = {
            "enabled": True,
            "mode": "bleep",
            "categories": ["Profanity"],
            "bleep_frequency": 1000,
        }
        
        remediator = AudioRemediator(config)
        
        # Create audio (5 seconds at 16kHz = 80000 samples)
        audio = np.array([0.2] * 80000, dtype=np.float32)
        sample_rate = 16000
        
        # Segment 1: 0-1s with Profanity + Violence
        detection1 = MagicMock()
        detection1.label = "Profanity"
        detection1.start_time = 0.0
        detection1.end_time = 1.0
        
        # Segment 2: 2-3s with Profanity only
        detection2 = MagicMock()
        detection2.label = "Profanity"
        detection2.start_time = 2.0
        detection2.end_time = 3.0
        
        # Segment 3: 4-5s with Violence only (should be skipped)
        detection3 = MagicMock()
        detection3.label = "Violence"
        detection3.start_time = 4.0
        detection3.end_time = 5.0
        
        detections = [detection1, detection2, detection3]
        
        remediated = remediator.remediate(audio, sample_rate, detections)
        
        # Segment 1 (0-1s): Should be bleeping (modified)
        seg1_start = int(0.0 * sample_rate)
        seg1_end = int(1.0 * sample_rate)
        assert not np.allclose(remediated[seg1_start:seg1_end], 0.2)  # Modified
        
        # Segment 2 (2-3s): Should be bleeping (modified)
        seg2_start = int(2.0 * sample_rate)
        seg2_end = int(3.0 * sample_rate)
        assert not np.allclose(remediated[seg2_start:seg2_end], 0.2)  # Modified
        
        # Segment 3 (4-5s): Should NOT be modified (Violence not in categories)
        seg3_start = int(4.0 * sample_rate)
        seg3_end = int(5.0 * sample_rate)
        assert np.allclose(remediated[seg3_start:seg3_end], 0.2)  # Unchanged
