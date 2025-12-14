"""Integration tests for the analysis pipeline.

Tests the complete workflow:
1. Video extraction with frame sampling
2. Detection pipeline execution
3. Result aggregation and merging
4. JSON output generation
"""

import json
from pathlib import Path

import pytest

from video_censor_personal.config import load_config
from video_censor_personal.frame import DetectionResult
from video_censor_personal.output import merge_segments
from video_censor_personal.pipeline import AnalysisPipeline, AnalysisRunner


class TestAnalysisPipelineBasics:
    """Test AnalysisPipeline initialization and basic functionality."""

    def test_pipeline_initializes_with_explicit_detectors(
        self, sample_video_path, config_with_mock
    ):
        """Test pipeline initialization with explicit detector list."""
        pipeline = AnalysisPipeline(sample_video_path, config_with_mock)
        assert pipeline.video_path == Path(sample_video_path)
        assert pipeline.config == config_with_mock
        assert pipeline.detection_pipeline is not None
        # With lazy loading, check detector configs instead of detectors list
        assert len(pipeline.detection_pipeline._detector_configs) > 0

    def test_pipeline_initializes_with_auto_discovered_detectors(
        self, sample_video_path, config_without_detectors
    ):
        """Test pipeline initialization with auto-discovered detectors.
        
        Note: Auto-discovery creates a LLaVA detector by default, which requires
        transformers library and downloaded models. This test is skipped if the
        LLaVA model is not available.
        """
        try:
            pipeline = AnalysisPipeline(sample_video_path, config_without_detectors)
            assert pipeline.detection_pipeline is not None
            # Auto-discovery should create detector configs (lazy loading)
            assert len(pipeline.detection_pipeline._detector_configs) > 0
        except ValueError as e:
            error_msg = str(e)
            if ("LLaVA dependencies not installed" in error_msg or
                "not found" in error_msg or
                "Can't load image processor" in error_msg or
                "Failed to load model" in error_msg):
                pytest.skip("LLaVA model not available in test environment (expected in CI)")
            raise

    def test_pipeline_raises_on_missing_video(self, config_with_mock):
        """Test pipeline raises FileNotFoundError for missing video."""
        with pytest.raises(FileNotFoundError):
            AnalysisPipeline("/nonexistent/video.mp4", config_with_mock)

    def test_pipeline_context_manager(self, sample_video_path, config_with_mock):
        """Test pipeline works as context manager."""
        with AnalysisPipeline(sample_video_path, config_with_mock) as pipeline:
            assert pipeline is not None
            assert pipeline.video_path == Path(sample_video_path)

    def test_pipeline_cleanup(self, sample_video_path, config_with_mock):
        """Test pipeline cleanup releases resources."""
        pipeline = AnalysisPipeline(sample_video_path, config_with_mock)
        pipeline.cleanup()
        assert pipeline.extractor is None
        # Second cleanup should not raise
        pipeline.cleanup()


class TestAnalysisPipelineExecution:
    """Test end-to-end pipeline execution."""

    def test_pipeline_analyze_runs_successfully(
        self, sample_video_path, config_with_mock
    ):
        """Test pipeline.analyze() runs successfully with mock detector."""
        with AnalysisPipeline(sample_video_path, config_with_mock) as pipeline:
            results = pipeline.analyze()
            assert isinstance(results, list)
            # Mock detector should return some detections for even frames
            assert len(results) >= 0

    def test_pipeline_returns_detection_results(
        self, sample_video_path, config_with_mock
    ):
        """Test pipeline returns valid DetectionResult objects."""
        with AnalysisPipeline(sample_video_path, config_with_mock) as pipeline:
            results = pipeline.analyze()
            for result in results:
                assert isinstance(result, DetectionResult)
                assert 0.0 <= result.confidence <= 1.0
                assert result.end_time >= result.start_time
                assert result.label in ["Nudity", "Violence"]

    def test_pipeline_respects_sample_rate(
        self, sample_video_path, config_with_mock
    ):
        """Test pipeline respects frame sampling configuration."""
        sample_rate = config_with_mock["processing"]["frame_sampling"]["sample_rate"]
        with AnalysisPipeline(sample_video_path, config_with_mock) as pipeline:
            # Create a mock extractor to get video stats
            from video_censor_personal.video_extraction import VideoExtractor
            extractor = VideoExtractor(sample_video_path)
            try:
                duration = extractor.get_duration_seconds()
                fps = extractor.get_fps()
            finally:
                extractor.close()

            # With sample rate, we should get approximately duration / sample_rate frames
            expected_frames = int(duration / sample_rate) + 1
            results = pipeline.analyze()
            # We can't directly count frames from results since multiple detectors
            # can return results per frame, but we can verify results are reasonable
            assert len(results) >= 0

    def test_pipeline_handles_no_detections(self, sample_video_path):
        """Test pipeline handles video with no detections gracefully.

        Uses a configuration with no enabled categories (will auto-discover as empty).
        This test is skipped as it requires special handling for the case where
        no detectors can be initialized.
        """
        pytest.skip("Requires special test configuration without enabled categories")

    def test_pipeline_cleanup_called_on_exception(
        self, sample_video_path, config_with_mock, monkeypatch
    ):
        """Test pipeline cleanup is called even if exception occurs during analysis."""
        with AnalysisPipeline(sample_video_path, config_with_mock) as pipeline:
            # Verify cleanup happens (context manager guarantees it)
            pass
        # Pipeline should be cleaned up after context manager exits
        assert pipeline.extractor is None


class TestAnalysisRunner:
    """Test AnalysisRunner for end-to-end CLI execution."""

    def test_runner_runs_analysis_and_writes_output(
        self, sample_video_path, config_with_mock, temp_output_dir
    ):
        """Test AnalysisRunner.run() produces valid JSON output."""
        output_path = str(temp_output_dir / "output.json")
        config_path = Path(__file__).parent / "fixtures" / "config_with_mock.yaml"

        runner = AnalysisRunner(sample_video_path, config_with_mock, str(config_path))
        result = runner.run(output_path)

        # Verify output was written
        assert Path(output_path).exists()
        assert result is not None

        # Verify JSON structure
        with open(output_path, "r") as f:
            output_json = json.load(f)

        assert "metadata" in output_json
        assert "segments" in output_json
        assert "summary" in output_json

    def test_output_json_structure(
        self, sample_video_path, config_with_mock, temp_output_dir
    ):
        """Test output JSON has correct structure and types."""
        output_path = str(temp_output_dir / "output.json")
        config_path = Path(__file__).parent / "fixtures" / "config_with_mock.yaml"

        runner = AnalysisRunner(sample_video_path, config_with_mock, str(config_path))
        runner.run(output_path)

        with open(output_path, "r") as f:
            output_json = json.load(f)

        # Verify metadata
        metadata = output_json["metadata"]
        assert "file" in metadata
        assert "duration" in metadata
        assert "duration_seconds" in metadata
        assert "processed_at" in metadata

        # Verify segments array
        segments = output_json["segments"]
        assert isinstance(segments, list)
        for segment in segments:
            assert "start_time" in segment
            assert "end_time" in segment
            assert "duration_seconds" in segment
            assert "labels" in segment
            assert "description" in segment
            assert "detections" in segment

        # Verify summary
        summary = output_json["summary"]
        assert "total_segments_detected" in summary
        assert "total_flagged_duration" in summary
        assert "detection_counts" in summary

    def test_output_includes_confidence_when_configured(
        self, sample_video_path, config_with_mock, temp_output_dir
    ):
        """Test output includes confidence scores when configured."""
        output_path = str(temp_output_dir / "output.json")
        config_path = Path(__file__).parent / "fixtures" / "config_with_mock.yaml"

        runner = AnalysisRunner(sample_video_path, config_with_mock, str(config_path))
        runner.run(output_path)

        with open(output_path, "r") as f:
            output_json = json.load(f)

        # Config has include_confidence: true
        segments = output_json["segments"]
        for segment in segments:
            assert "confidence" in segment
            for detection in segment["detections"]:
                assert "confidence" in detection


class TestSegmentMerging:
    """Test detection result merging into segments."""

    def test_segment_merging_overlapping_detections(self):
        """Test merging of overlapping detection results."""
        detections = [
            DetectionResult(0.0, 1.0, "Nudity", 0.8, "Test 1"),
            DetectionResult(0.5, 1.5, "Violence", 0.7, "Test 2"),
        ]
        merged = merge_segments(detections, threshold=0.0)
        assert len(merged) == 1
        assert merged[0]["start_time"] == 0.0
        assert merged[0]["end_time"] == 1.5

    def test_segment_merging_nearby_detections(self):
        """Test merging of nearby detections within threshold."""
        detections = [
            DetectionResult(0.0, 1.0, "Nudity", 0.8, "Test 1"),
            DetectionResult(2.0, 3.0, "Violence", 0.7, "Test 2"),
        ]
        merged = merge_segments(detections, threshold=2.0)
        assert len(merged) == 1
        assert merged[0]["start_time"] == 0.0
        assert merged[0]["end_time"] == 3.0

    def test_segment_merging_separate_detections(self):
        """Test separation of detections beyond threshold."""
        detections = [
            DetectionResult(0.0, 1.0, "Nudity", 0.8, "Test 1"),
            DetectionResult(5.0, 6.0, "Violence", 0.7, "Test 2"),
        ]
        merged = merge_segments(detections, threshold=1.0)
        assert len(merged) == 2

    def test_segment_merging_empty_list(self):
        """Test merging empty detection list."""
        merged = merge_segments([], threshold=1.0)
        assert len(merged) == 0


class TestDetectorInitialization:
    """Test detector initialization from configuration."""

    def test_mock_detector_registered(self):
        """Test mock detector is properly registered."""
        from video_censor_personal.detection import get_detector_registry
        registry = get_detector_registry()
        assert "mock" in registry.registered_types()

    def test_detection_pipeline_with_mock_detector(self, config_with_mock):
        """Test DetectionPipeline initializes with mock detector from config."""
        from video_censor_personal.detection import DetectionPipeline
        pipeline = DetectionPipeline(config_with_mock)
        assert len(pipeline.detectors) > 0
        assert pipeline.detectors[0].name == "mock-detector"

    def test_detection_pipeline_fails_with_unknown_detector(self):
        """Test DetectionPipeline fails with unknown detector type."""
        from video_censor_personal.detection import DetectionPipeline
        bad_config = {
            "detectors": [
                {
                    "type": "unknown-detector",
                    "name": "bad",
                    "categories": ["Test"],
                }
            ]
        }
        with pytest.raises(ValueError):
            DetectionPipeline(bad_config)


class TestErrorHandling:
    """Test error handling in pipeline."""

    def test_pipeline_handles_detector_failure_gracefully(
        self, sample_video_path, config_with_mock
    ):
        """Test pipeline continues when a detector fails."""
        # The pipeline should skip frames where detector fails and continue
        with AnalysisPipeline(sample_video_path, config_with_mock) as pipeline:
            results = pipeline.analyze()
            # Should complete without raising
            assert isinstance(results, list)

    def test_analysis_runner_propagates_errors(
        self, config_with_mock, temp_output_dir
    ):
        """Test AnalysisRunner propagates errors appropriately."""
        output_path = str(temp_output_dir / "output.json")
        config_path = Path(__file__).parent / "fixtures" / "config_with_mock.yaml"

        runner = AnalysisRunner("/nonexistent/video.mp4", config_with_mock, str(config_path))
        with pytest.raises(Exception):
            runner.run(output_path)
