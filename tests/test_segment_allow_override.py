"""Tests for segment allow override feature."""

import pytest

from video_censor_personal.audio_remediator import AudioRemediator
from video_censor_personal.output import _build_merged_segment
from video_censor_personal.frame import DetectionResult
from video_censor_personal.video_metadata_writer import _build_skip_chapters
import numpy as np


class TestOutputSchemaAllow:
    """Test allow property in output schema."""

    def test_merged_segment_has_allow_property(self):
        """Test that merged segments include allow property defaulting to false."""
        detection = DetectionResult(
            start_time=10.0,
            end_time=12.0,
            label="Profanity",
            confidence=0.95,
            reasoning="Contains profanity",
        )

        segment = _build_merged_segment([detection])

        assert "allow" in segment
        assert segment["allow"] is False

    def test_merged_segment_allow_false_by_default(self):
        """Test that new merged segments default to allow=false."""
        detection = DetectionResult(
            start_time=5.0,
            end_time=7.0,
            label="Violence",
            confidence=0.85,
            reasoning="Contains violence",
        )

        segment = _build_merged_segment([detection])

        assert segment.get("allow", False) is False


class TestAudioRemediationWithAllow:
    """Test audio remediation respects allow flag."""

    def test_remediate_skips_allowed_segment(self):
        """Test that segments marked with allow=true are skipped during remediation."""
        config = {
            "enabled": True,
            "mode": "silence",
            "categories": ["Profanity"],
            "bleep_frequency": 1000,
        }
        remediator = AudioRemediator(config)

        # Create audio with 44100 Hz sample rate, 2 seconds duration
        audio_data = np.random.randn(44100 * 2).astype(np.float32)
        sample_rate = 44100

        # Create detection that should be silenced
        detection = DetectionResult(
            start_time=0.5,
            end_time=1.0,
            label="Profanity",
            confidence=0.95,
            reasoning="Test profanity",
        )

        # Create segment marked as allowed
        segment = {
            "start_time": 0.5,
            "end_time": 1.0,
            "allow": True,
        }

        # Remediate with allow flag
        result = remediator.remediate(audio_data, sample_rate, [detection], [segment])

        # Audio should be unchanged (not silenced) because segment is allowed
        expected_start_sample = int(0.5 * sample_rate)
        expected_end_sample = int(1.0 * sample_rate)
        
        # Check that the detection region is NOT all zeros (wasn't silenced)
        region = result[expected_start_sample:expected_end_sample]
        assert not np.allclose(region, 0.0), "Allowed segment should not be remediated"

    def test_remediate_processes_disallowed_segment(self):
        """Test that segments not marked as allowed are remediated."""
        config = {
            "enabled": True,
            "mode": "silence",
            "categories": ["Profanity"],
            "bleep_frequency": 1000,
        }
        remediator = AudioRemediator(config)

        # Create audio with 44100 Hz sample rate, 2 seconds duration
        audio_data = np.random.randn(44100 * 2).astype(np.float32)
        sample_rate = 44100

        # Create detection
        detection = DetectionResult(
            start_time=0.5,
            end_time=1.0,
            label="Profanity",
            confidence=0.95,
            reasoning="Test profanity",
        )

        # Create segment NOT marked as allowed
        segment = {
            "start_time": 0.5,
            "end_time": 1.0,
            "allow": False,
        }

        # Remediate with disallowed segment
        result = remediator.remediate(audio_data, sample_rate, [detection], [segment])

        # Audio should be silenced in the detection region
        expected_start_sample = int(0.5 * sample_rate)
        expected_end_sample = int(1.0 * sample_rate)
        
        region = result[expected_start_sample:expected_end_sample]
        assert np.allclose(region, 0.0), "Disallowed segment should be remediated (silenced)"

    def test_remediate_without_segments_param_processes_all(self):
        """Test that remediate works without segments param (backward compatibility)."""
        config = {
            "enabled": True,
            "mode": "silence",
            "categories": ["Profanity"],
            "bleep_frequency": 1000,
        }
        remediator = AudioRemediator(config)

        # Create audio
        audio_data = np.random.randn(44100 * 2).astype(np.float32)
        sample_rate = 44100

        # Create detection
        detection = DetectionResult(
            start_time=0.5,
            end_time=1.0,
            label="Profanity",
            confidence=0.95,
            reasoning="Test profanity",
        )

        # Remediate WITHOUT segments parameter (backward compatibility)
        result = remediator.remediate(audio_data, sample_rate, [detection])

        # Audio should be silenced since no allow flag
        expected_start_sample = int(0.5 * sample_rate)
        expected_end_sample = int(1.0 * sample_rate)
        
        region = result[expected_start_sample:expected_end_sample]
        assert np.allclose(region, 0.0), "Detection should be remediated without segments param"


class TestChapterGenerationWithAllow:
    """Test chapter generation respects allow flag."""

    def test_skip_chapters_exclude_allowed_segments(self):
        """Test that segments marked with allow=true are excluded from chapters."""
        segments = [
            {
                "start_time": 5.0,
                "end_time": 10.0,
                "labels": ["Profanity"],
                "confidence": 0.95,
                "allow": True,  # Allowed - should not create chapter
            },
            {
                "start_time": 15.0,
                "end_time": 20.0,
                "labels": ["Violence"],
                "confidence": 0.85,
                "allow": False,  # Not allowed - should create chapter
            },
        ]

        chapters = _build_skip_chapters(segments)

        # Should have only 1 chapter (for disallowed segment)
        assert len(chapters) == 1
        assert chapters[0]["start"] == 15.0
        assert chapters[0]["end"] == 20.0
        assert "Violence" in chapters[0]["title"]

    def test_skip_chapters_include_disallowed_segments(self):
        """Test that segments marked with allow=false are included in chapters."""
        segments = [
            {
                "start_time": 5.0,
                "end_time": 10.0,
                "labels": ["Nudity"],
                "confidence": 0.9,
                "allow": False,
            },
        ]

        chapters = _build_skip_chapters(segments)

        assert len(chapters) == 1
        assert chapters[0]["start"] == 5.0
        assert chapters[0]["end"] == 10.0
        assert "Nudity" in chapters[0]["title"]

    def test_skip_chapters_with_all_allowed(self):
        """Test that no chapters are created when all segments are allowed."""
        segments = [
            {
                "start_time": 5.0,
                "end_time": 10.0,
                "labels": ["Profanity"],
                "confidence": 0.95,
                "allow": True,
            },
            {
                "start_time": 15.0,
                "end_time": 20.0,
                "labels": ["Violence"],
                "confidence": 0.85,
                "allow": True,
            },
        ]

        chapters = _build_skip_chapters(segments)

        assert len(chapters) == 0

    def test_skip_chapters_default_allow_false(self):
        """Test that segments without allow property default to false."""
        segments = [
            {
                "start_time": 5.0,
                "end_time": 10.0,
                "labels": ["Sexual Theme"],
                "confidence": 0.8,
                # No 'allow' property - should default to False
            },
        ]

        chapters = _build_skip_chapters(segments)

        assert len(chapters) == 1
        assert chapters[0]["start"] == 5.0
