"""Tests for analysis pipeline audio integration.

Tests audio extraction, detection, and remediation within the pipeline.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock
import tempfile

import numpy as np
import pytest

from video_censor_personal.frame import DetectionResult
from video_censor_personal.pipeline import AnalysisPipeline


class TestPipelineAudioExtraction:
    """Test audio extraction in the analysis pipeline."""

    @pytest.fixture
    def mock_video_extractor(self):
        """Create a mock VideoExtractor."""
        with patch("video_censor_personal.pipeline.VideoExtractor") as mock:
            instance = MagicMock()
            instance.get_frame_count.return_value = 30
            instance.get_fps.return_value = 30.0
            instance.get_duration_seconds.return_value = 1.0
            instance.extract_frames.return_value = iter([])
            
            # Mock audio extraction
            audio_segment = MagicMock()
            audio_segment.data = b"fake wav data"
            audio_segment.sample_rate = 44100
            audio_segment.duration.return_value = 1.0
            instance.extract_audio.return_value = audio_segment
            
            mock.return_value = instance
            yield mock, instance

    @pytest.fixture
    def config_with_mock_detector(self):
        """Config with a mock detector (frame-based, no audio)."""
        return {
            "detectors": [
                {
                    "type": "mock",
                    "name": "test-mock",
                    "categories": ["Nudity", "Violence"],
                }
            ],
            "processing": {
                "frame_sampling": {"sample_rate": 1.0},
            },
        }

    @pytest.fixture
    def config_with_audio_detector(self):
        """Config with an audio detector to trigger audio extraction."""
        return {
            "detectors": [
                {
                    "type": "speech-profanity",
                    "name": "test-audio",
                    "categories": ["Profanity"],
                }
            ],
            "processing": {
                "frame_sampling": {"sample_rate": 1.0},
            },
        }

    def test_audio_extraction_called_when_detectors_present(
        self, mock_video_extractor, config_with_mock_detector, tmp_path
    ):
        """Test that audio extraction is called when detectors are present."""
        mock_class, mock_instance = mock_video_extractor
        
        # Create a fake video file
        video_file = tmp_path / "test.mp4"
        video_file.write_bytes(b"fake video")
        
        with patch.object(Path, "exists", return_value=True):
            pipeline = AnalysisPipeline(str(video_file), config_with_mock_detector)
            
            # Mock soundfile and librosa at the point of import
            with patch.dict("sys.modules", {"soundfile": MagicMock(), "librosa": MagicMock()}):
                try:
                    pipeline.analyze()
                except Exception:
                    pass  # May fail due to mocking, but audio extraction should be called
            
            # Verify audio extraction was attempted
            mock_instance.extract_audio.assert_called()

    def test_audio_extraction_failure_continues_analysis(
        self, mock_video_extractor, config_with_mock_detector, tmp_path
    ):
        """Test that audio extraction failure doesn't stop analysis."""
        mock_class, mock_instance = mock_video_extractor
        mock_instance.extract_audio.side_effect = Exception("No audio track")
        
        video_file = tmp_path / "test.mp4"
        video_file.write_bytes(b"fake video")
        
        with patch.object(Path, "exists", return_value=True):
            pipeline = AnalysisPipeline(str(video_file), config_with_mock_detector)
            
            # Should not raise even though audio extraction failed
            results = pipeline.analyze()
            assert isinstance(results, list)


class TestPipelineAudioRemediation:
    """Test audio remediation in the analysis pipeline."""

    @pytest.fixture
    def config_with_remediation(self):
        """Config with audio remediation enabled."""
        return {
            "detectors": [
                {
                    "type": "mock",
                    "name": "test-mock",
                    "categories": ["Profanity"],
                }
            ],
            "audio": {
                "detection": {"enabled": False},
            },
            "remediation": {
                "audio": {
                    "enabled": True,
                    "mode": "silence",
                    "categories": ["Profanity"],
                }
            },
            "processing": {
                "frame_sampling": {"sample_rate": 1.0},
            },
        }

    @pytest.fixture
    def config_without_remediation(self):
        """Config with audio remediation disabled."""
        return {
            "detectors": [
                {
                    "type": "mock",
                    "name": "test-mock",
                    "categories": ["Profanity"],
                }
            ],
            "audio": {
                "remediation": {
                    "enabled": False,
                }
            },
            "processing": {
                "frame_sampling": {"sample_rate": 1.0},
            },
        }







class TestPipelineCleanup:
    """Test pipeline cleanup with audio resources."""

    def test_cleanup_releases_audio_resources(self, tmp_path):
        """Test that cleanup releases audio-related resources."""
        video_file = tmp_path / "test.mp4"
        video_file.write_bytes(b"fake video")
        
        config = {
            "detectors": [
                {"type": "mock", "name": "test", "categories": ["Violence"]}
            ],
        }
        
        with patch("video_censor_personal.pipeline.VideoExtractor") as mock_extractor:
            instance = MagicMock()
            instance.get_frame_count.return_value = 30
            instance.get_fps.return_value = 30.0
            instance.get_duration_seconds.return_value = 1.0
            mock_extractor.return_value = instance
            
            with patch.object(Path, "exists", return_value=True):
                pipeline = AnalysisPipeline(str(video_file), config)
                pipeline.extractor = instance
                
                pipeline.cleanup()
                
                # Extractor should be cleaned up
                instance.close.assert_called()
                assert pipeline.extractor is None
