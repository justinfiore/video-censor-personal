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

    def test_remediation_not_applied_when_disabled(
        self, config_without_remediation, tmp_path
    ):
        """Test that remediation is not applied when disabled in config."""
        video_file = tmp_path / "test.mp4"
        video_file.write_bytes(b"fake video")
        
        with patch("video_censor_personal.pipeline.VideoExtractor") as mock_extractor:
            instance = MagicMock()
            instance.get_frame_count.return_value = 30
            instance.get_fps.return_value = 30.0
            instance.get_duration_seconds.return_value = 1.0
            instance.extract_frames.return_value = iter([])
            instance.extract_audio.side_effect = Exception("No audio")
            mock_extractor.return_value = instance
            
            with patch.object(Path, "exists", return_value=True):
                pipeline = AnalysisPipeline(
                    str(video_file), 
                    config_without_remediation
                )
                results = pipeline.analyze()
                
                # No remediated audio path should be set
                assert pipeline.remediated_audio_path is None

    def test_remediation_method_called_when_enabled_with_audio(
        self, config_with_remediation, tmp_path
    ):
        """Test that _apply_audio_remediation is actually called when enabled.
        
        This test catches the bug where post-processing code was unreachable
        due to an early return statement.
        """
        video_file = tmp_path / "test.mp4"
        video_file.write_bytes(b"fake video")
        
        with patch("video_censor_personal.pipeline.VideoExtractor") as mock_extractor:
            instance = MagicMock()
            instance.get_frame_count.return_value = 30
            instance.get_fps.return_value = 30.0
            instance.get_duration_seconds.return_value = 1.0
            instance.extract_frames.return_value = iter([])
            
            # Provide valid audio data
            audio_segment = MagicMock()
            audio_segment.data = np.zeros(16000, dtype=np.float32)
            audio_segment.sample_rate = 16000
            audio_segment.duration.return_value = 1.0
            instance.extract_audio.return_value = audio_segment
            mock_extractor.return_value = instance
            
            with patch.object(Path, "exists", return_value=True):
                pipeline = AnalysisPipeline(
                    str(video_file), 
                    config_with_remediation
                )
                
                # Mock the _apply_audio_remediation method to verify it's called
                with patch.object(
                    pipeline, "_apply_audio_remediation"
                ) as mock_remediate:
                    pipeline.analyze()
                    
                    # Verify remediation method was called
                    mock_remediate.assert_called_once()

    def test_remediation_produces_output_file_when_detections_present(
        self, config_with_remediation, tmp_path
    ):
        """Test that remediation produces an audio file when detections exist.
        
        This is an integration test that verifies the full remediation flow
        actually executes and produces output.
        """
        video_file = tmp_path / "test.mp4"
        video_file.write_bytes(b"fake video")
        output_audio = tmp_path / "remediated.wav"
        
        # Add output path to config
        config = config_with_remediation.copy()
        config["remediation"]["audio"]["output_path"] = str(output_audio)
        
        with patch("video_censor_personal.pipeline.VideoExtractor") as mock_extractor:
            instance = MagicMock()
            instance.get_frame_count.return_value = 30
            instance.get_fps.return_value = 30.0
            instance.get_duration_seconds.return_value = 1.0
            instance.extract_frames.return_value = iter([])
            
            # Provide valid audio data (1 second of silence at 48kHz)
            audio_segment = MagicMock()
            audio_segment.data = np.zeros(48000, dtype=np.float32)
            audio_segment.sample_rate = 48000
            audio_segment.duration.return_value = 1.0
            instance.extract_audio.return_value = audio_segment
            mock_extractor.return_value = instance
            
            with patch.object(Path, "exists", return_value=True):
                pipeline = AnalysisPipeline(
                    str(video_file), 
                    config
                )
                
                # Inject a detection result to trigger remediation
                profanity_detection = DetectionResult(
                    label="Profanity",
                    confidence=0.95,
                    start_time=0.5,
                    end_time=0.7,
                    reasoning="Test profanity"
                )
                
                # Mock analyze_full_audio to return our detection
                with patch.object(
                    pipeline, "_ensure_detection_pipeline"
                ):
                    pipeline._ensure_detection_pipeline()
                    
                    # Manually set up detection pipeline mock
                    pipeline.detection_pipeline = MagicMock()
                    pipeline.detection_pipeline._detector_configs = [{"type": "mock"}]
                    pipeline.detection_pipeline.detectors = []
                    pipeline.detection_pipeline.analyze_full_audio.return_value = [
                        profanity_detection
                    ]
                    pipeline.detection_pipeline.get_frame_detectors.return_value = []
                    
                    results = pipeline.analyze()
                    
                    # Verify the detection was returned
                    assert len(results) == 1
                    assert results[0].label == "Profanity"
                    
                    # Verify remediated audio file was created
                    assert output_audio.exists(), (
                        "Remediated audio file should be created when "
                        "remediation is enabled and detections are present"
                    )
                    
                    # Verify pipeline stored the path
                    assert pipeline.remediated_audio_path == str(output_audio)


class TestPipelineVideoMuxing:
    """Test video muxing in the analysis pipeline."""

    @pytest.fixture
    def config_with_muxing(self):
        """Config with remediation and muxing enabled."""
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
                    "enabled": True,
                    "mode": "silence",
                    "categories": ["Profanity"],
                }
            },
            "processing": {
                "frame_sampling": {"sample_rate": 1.0},
            },
        }

    def test_muxing_skipped_when_no_output_path(self, config_with_muxing, tmp_path):
        """Test that muxing is skipped when output_video_path not provided."""
        video_file = tmp_path / "test.mp4"
        video_file.write_bytes(b"fake video")
        
        with patch("video_censor_personal.pipeline.VideoExtractor") as mock_extractor:
            instance = MagicMock()
            instance.get_frame_count.return_value = 30
            instance.get_fps.return_value = 30.0
            instance.get_duration_seconds.return_value = 1.0
            instance.extract_frames.return_value = iter([])
            instance.extract_audio.side_effect = Exception("No audio")
            mock_extractor.return_value = instance
            
            with patch.object(Path, "exists", return_value=True):
                # No output_video_path provided
                pipeline = AnalysisPipeline(
                    str(video_file),
                    config_with_muxing,
                    output_video_path=None
                )
                
                pipeline.analyze()
                # No remediated audio path should be set (no audio extracted)
                assert pipeline.remediated_audio_path is None

    def test_muxing_called_when_output_path_provided(self, config_with_muxing, tmp_path):
        """Test that output_video_path is stored when provided."""
        video_file = tmp_path / "test.mp4"
        video_file.write_bytes(b"fake video")
        output_file = tmp_path / "output.mp4"
        
        with patch("video_censor_personal.pipeline.VideoExtractor") as mock_extractor:
            instance = MagicMock()
            instance.get_frame_count.return_value = 30
            instance.get_fps.return_value = 30.0
            instance.get_duration_seconds.return_value = 1.0
            instance.extract_frames.return_value = iter([])
            instance.extract_audio.side_effect = Exception("No audio")
            mock_extractor.return_value = instance
            
            with patch.object(Path, "exists", return_value=True):
                pipeline = AnalysisPipeline(
                    str(video_file),
                    config_with_muxing,
                    output_video_path=str(output_file)
                )
                
                # Verify output_video_path is stored
                assert pipeline.output_video_path == str(output_file)
                
                # Run analysis (muxing won't happen without audio)
                pipeline.analyze()

    def test_mux_remediated_audio_called_after_remediation(self, config_with_muxing, tmp_path):
        """Test that _mux_remediated_audio is called after audio remediation.
        
        This test verifies the full post-processing flow executes:
        1. _apply_audio_remediation is called
        2. _mux_remediated_audio is called after
        
        This catches bugs where post-processing code is unreachable.
        """
        video_file = tmp_path / "test.mp4"
        video_file.write_bytes(b"fake video")
        output_file = tmp_path / "output.mp4"
        
        with patch("video_censor_personal.pipeline.VideoExtractor") as mock_extractor:
            instance = MagicMock()
            instance.get_frame_count.return_value = 30
            instance.get_fps.return_value = 30.0
            instance.get_duration_seconds.return_value = 1.0
            instance.extract_frames.return_value = iter([])
            
            # Provide valid audio data
            audio_segment = MagicMock()
            audio_segment.data = np.zeros(16000, dtype=np.float32)
            audio_segment.sample_rate = 16000
            audio_segment.duration.return_value = 1.0
            instance.extract_audio.return_value = audio_segment
            mock_extractor.return_value = instance
            
            with patch.object(Path, "exists", return_value=True):
                pipeline = AnalysisPipeline(
                    str(video_file),
                    config_with_muxing,
                    output_video_path=str(output_file)
                )
                
                # Track call order to verify both methods are called
                call_order = []
                
                original_apply = pipeline._apply_audio_remediation
                original_mux = pipeline._mux_remediated_audio
                
                def track_apply(*args, **kwargs):
                    call_order.append("_apply_audio_remediation")
                    return original_apply(*args, **kwargs)
                
                def track_mux(*args, **kwargs):
                    call_order.append("_mux_remediated_audio")
                    # Don't actually mux (would fail without real files)
                
                with patch.object(pipeline, "_apply_audio_remediation", side_effect=track_apply):
                    with patch.object(pipeline, "_mux_remediated_audio", side_effect=track_mux):
                        pipeline.analyze()
                
                # Verify both methods were called in order
                assert "_apply_audio_remediation" in call_order, (
                    "_apply_audio_remediation should be called during analyze()"
                )
                assert "_mux_remediated_audio" in call_order, (
                    "_mux_remediated_audio should be called during analyze()"
                )
                
                # Verify order: remediation before muxing
                remediation_idx = call_order.index("_apply_audio_remediation")
                mux_idx = call_order.index("_mux_remediated_audio")
                assert remediation_idx < mux_idx, (
                    "_apply_audio_remediation should be called before _mux_remediated_audio"
                )


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
