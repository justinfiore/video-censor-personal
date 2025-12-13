"""Tests for detection framework, detectors, and detection pipeline."""

import logging
from typing import Any, Dict, List, Optional

import numpy as np
import pytest

from video_censor_personal.detection import (
    Detector,
    DetectionPipeline,
    DetectorRegistry,
    get_detector_registry,
    register_detector,
)
from video_censor_personal.frame import DetectionResult, Frame


# ============================================================================
# Stub Detector Implementation for Testing
# ============================================================================


class StubDetector(Detector):
    """Stub detector for testing that returns predictable results."""

    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize stub detector with test mode configuration.

        Args:
            config: Configuration dict with optional 'mode' and 'results' fields.
                   - mode: 'success' (default), 'failure', or 'empty'
                   - results: List of DetectionResult dicts to return
        """
        super().__init__(config)
        self.mode = config.get("mode", "success")
        self.cleanup_called = False
        self.detect_call_count = 0

    def detect(
        self,
        frame_data: Optional[np.ndarray] = None,
        audio_data: Optional[Any] = None,
    ) -> List[DetectionResult]:
        """Return stub detection results based on mode.

        Args:
            frame_data: Frame pixel data (ignored in stub).
            audio_data: Audio data (ignored in stub).

        Returns:
            List of DetectionResult objects or empty list.

        Raises:
            RuntimeError: If mode is 'failure'.
        """
        self.detect_call_count += 1

        if self.mode == "failure":
            raise RuntimeError(f"Stub detector '{self.name}' simulated failure")

        if self.mode == "empty":
            return []

        # Success mode: return results for each category
        results = []
        for category in self.categories:
            results.append(
                DetectionResult(
                    start_time=0.0,
                    end_time=0.033,
                    label=category,
                    confidence=0.9,
                    reasoning=f"Stub detection for {category}",
                )
            )
        return results

    def cleanup(self) -> None:
        """Mark cleanup as called."""
        self.cleanup_called = True


class FailingDetector(Detector):
    """Detector that always fails on detect()."""

    def detect(
        self,
        frame_data: Optional[np.ndarray] = None,
        audio_data: Optional[Any] = None,
    ) -> List[DetectionResult]:
        """Always raise exception."""
        raise RuntimeError("Detector always fails")


# ============================================================================
# Tests: Detector Interface
# ============================================================================


class TestDetectorInterface:
    """Test abstract Detector interface and lifecycle."""

    def test_detector_abstract_class_cannot_instantiate(self):
        """Test that Detector is abstract and cannot be instantiated directly."""
        with pytest.raises(TypeError):
            Detector({"name": "test", "categories": ["Test"]})

    def test_detector_requires_dict_config(self):
        """Test that detector config must be a dictionary."""
        with pytest.raises(ValueError, match="config must be a dictionary"):
            StubDetector("not a dict")

    def test_detector_requires_categories(self):
        """Test that detector must declare at least one category."""
        with pytest.raises(ValueError, match="must declare at least one category"):
            StubDetector({"name": "test"})

    def test_detector_categories_must_be_list(self):
        """Test that categories must be a list."""
        with pytest.raises(ValueError, match="categories must be a list"):
            StubDetector({"name": "test", "categories": "Profanity"})

    def test_detector_with_valid_config(self):
        """Test detector initialization with valid config."""
        config = {"name": "test-detector", "categories": ["Profanity", "Violence"]}
        detector = StubDetector(config)
        assert detector.name == "test-detector"
        assert detector.categories == ["Profanity", "Violence"]

    def test_detector_uses_class_name_if_no_name_provided(self):
        """Test that detector uses class name if 'name' not in config."""
        config = {"categories": ["Test"]}
        detector = StubDetector(config)
        assert detector.name == "StubDetector"

    def test_detector_cleanup_default_implementation(self):
        """Test that detector.cleanup() is provided by default."""
        config = {"name": "test", "categories": ["Test"]}
        detector = StubDetector(config)
        # Should not raise
        detector.cleanup()

    def test_detector_detect_must_be_implemented_by_subclass(self):
        """Test that abstract detect() method must be implemented."""

        class MinimalDetector(Detector):
            def detect(
                self,
                frame_data: Optional[np.ndarray] = None,
                audio_data: Optional[Any] = None,
            ) -> List[DetectionResult]:
                return []

        # Should not raise (detect is implemented)
        detector = MinimalDetector({"name": "test", "categories": ["Test"]})
        results = detector.detect()
        assert results == []


# ============================================================================
# Tests: Multi-Category Detection
# ============================================================================


class TestMultiCategoryDetection:
    """Test detectors identifying multiple categories in single pass."""

    def test_detector_returns_multiple_category_results(self):
        """Test detector can return results for multiple categories."""
        config = {
            "name": "multi-category",
            "categories": ["Profanity", "Nudity", "Violence"],
            "mode": "success",
        }
        detector = StubDetector(config)
        results = detector.detect(frame_data=np.zeros((480, 640, 3), dtype=np.uint8))

        assert len(results) == 3
        labels = {r.label for r in results}
        assert labels == {"Profanity", "Nudity", "Violence"}

    def test_each_category_result_has_independent_confidence(self):
        """Test that each category can have different confidence."""

        class MultiConfidenceDetector(Detector):
            def detect(
                self,
                frame_data: Optional[np.ndarray] = None,
                audio_data: Optional[Any] = None,
            ) -> List[DetectionResult]:
                return [
                    DetectionResult(
                        start_time=0.0,
                        end_time=0.033,
                        label="Profanity",
                        confidence=0.95,
                        reasoning="High confidence profanity",
                    ),
                    DetectionResult(
                        start_time=0.0,
                        end_time=0.033,
                        label="Violence",
                        confidence=0.65,
                        reasoning="Lower confidence violence",
                    ),
                ]

        detector = MultiConfidenceDetector(
            {"name": "test", "categories": ["Profanity", "Violence"]}
        )
        results = detector.detect(frame_data=np.zeros((480, 640, 3), dtype=np.uint8))

        assert len(results) == 2
        profanity_result = next(r for r in results if r.label == "Profanity")
        violence_result = next(r for r in results if r.label == "Violence")
        assert profanity_result.confidence == 0.95
        assert violence_result.confidence == 0.65

    def test_detector_returns_empty_list_for_no_detections(self):
        """Test detector returns empty list if nothing detected."""
        config = {
            "name": "empty",
            "categories": ["Profanity"],
            "mode": "empty",
        }
        detector = StubDetector(config)
        results = detector.detect(frame_data=np.zeros((480, 640, 3), dtype=np.uint8))
        assert results == []


# ============================================================================
# Tests: Detector Registry
# ============================================================================


class TestDetectorRegistry:
    """Test detector registration and instantiation."""

    def test_registry_register_detector(self):
        """Test registering a detector type."""
        registry = DetectorRegistry()
        registry.register("stub", StubDetector)
        assert registry.get("stub") == StubDetector

    def test_registry_register_non_detector_raises_error(self):
        """Test that registering non-Detector class raises TypeError."""
        registry = DetectorRegistry()

        class NotADetector:
            pass

        with pytest.raises(TypeError, match="must be subclass of Detector"):
            registry.register("bad", NotADetector)

    def test_registry_get_unknown_detector_returns_none(self):
        """Test getting unknown detector returns None."""
        registry = DetectorRegistry()
        assert registry.get("unknown") is None

    def test_registry_create_detector_with_config(self):
        """Test creating detector instance with config."""
        registry = DetectorRegistry()
        registry.register("stub", StubDetector)

        config = {"name": "test-instance", "categories": ["Test"]}
        detector = registry.create("stub", config)

        assert isinstance(detector, StubDetector)
        assert detector.name == "test-instance"

    def test_registry_create_unknown_detector_raises_error(self):
        """Test creating unknown detector type raises ValueError."""
        registry = DetectorRegistry()
        with pytest.raises(ValueError, match="Unknown detector type"):
            registry.create("unknown", {})

    def test_registry_error_message_includes_available_types(self):
        """Test error message lists available detector types."""
        registry = DetectorRegistry()
        registry.register("stub", StubDetector)
        registry.register("failing", FailingDetector)

        with pytest.raises(
            ValueError, match="Available types.*failing.*stub"
        ):
            registry.create("unknown", {})

    def test_registry_registered_types_returns_sorted_list(self):
        """Test getting list of registered detector types."""
        registry = DetectorRegistry()
        registry.register("zebra", StubDetector)
        registry.register("alpha", FailingDetector)
        registry.register("beta", StubDetector)

        types = registry.registered_types()
        assert types == ["alpha", "beta", "zebra"]

    def test_global_register_detector(self):
        """Test global register_detector function."""
        # Use global registry
        register_detector("test-stub", StubDetector)
        registry = get_detector_registry()
        assert registry.get("test-stub") == StubDetector

    def test_global_get_detector_registry(self):
        """Test get_detector_registry returns the global instance."""
        registry1 = get_detector_registry()
        registry2 = get_detector_registry()
        assert registry1 is registry2


# ============================================================================
# Tests: Detection Pipeline
# ============================================================================


class TestDetectionPipeline:
    """Test detection pipeline orchestration and error handling."""

    def setup_method(self):
        """Set up test fixtures."""
        # Register stub detector for tests
        register_detector("stub", StubDetector)
        register_detector("failing", FailingDetector)

    def test_pipeline_initializes_with_empty_config(self):
        """Test pipeline with no detectors configured."""
        config = {"detectors": []}
        pipeline = DetectionPipeline(config)
        assert pipeline.detectors == []

    def test_pipeline_initializes_single_detector(self):
        """Test pipeline initializes single detector from config."""
        config = {
            "detectors": [
                {"type": "stub", "name": "primary", "categories": ["Test"]}
            ]
        }
        pipeline = DetectionPipeline(config)
        assert len(pipeline.detectors) == 1
        assert pipeline.detectors[0].name == "primary"

    def test_pipeline_initializes_multiple_detectors(self):
        """Test pipeline initializes multiple detectors."""
        config = {
            "detectors": [
                {"type": "stub", "name": "detector-1", "categories": ["Profanity"]},
                {"type": "stub", "name": "detector-2", "categories": ["Violence"]},
            ]
        }
        pipeline = DetectionPipeline(config)
        assert len(pipeline.detectors) == 2
        assert pipeline.detectors[0].name == "detector-1"
        assert pipeline.detectors[1].name == "detector-2"

    def test_pipeline_config_detectors_missing_type_raises_error(self):
        """Test that missing 'type' in detector config raises ValueError."""
        config = {"detectors": [{"name": "bad", "categories": ["Test"]}]}
        with pytest.raises(ValueError, match="missing required 'type' field"):
            DetectionPipeline(config)

    def test_pipeline_config_invalid_detector_type_raises_error(self):
        """Test that unknown detector type raises ValueError."""
        config = {
            "detectors": [
                {"type": "unknown-type", "name": "bad", "categories": ["Test"]}
            ]
        }
        with pytest.raises(ValueError, match="Unknown detector type"):
            DetectionPipeline(config)

    def test_pipeline_detectors_must_be_list(self):
        """Test that 'detectors' config must be a list."""
        config = {"detectors": "not a list"}
        with pytest.raises(ValueError, match="detectors.*must be a list"):
            DetectionPipeline(config)

    def test_pipeline_each_detector_config_must_be_dict(self):
        """Test that each detector config must be a dictionary."""
        config = {"detectors": ["not a dict"]}
        with pytest.raises(ValueError, match="detector config must be a dictionary"):
            DetectionPipeline(config)

    def test_pipeline_analyze_frame_with_no_detectors(self):
        """Test analyzing frame with no detectors returns empty list."""
        config = {"detectors": []}
        pipeline = DetectionPipeline(config)

        frame = Frame(index=0, timecode=1.0, data=np.zeros((480, 640, 3), dtype=np.uint8))
        results = pipeline.analyze_frame(frame)
        assert results == []

    def test_pipeline_analyze_frame_with_single_detector(self):
        """Test analyzing frame runs detector and returns results."""
        config = {
            "detectors": [
                {"type": "stub", "name": "detector", "categories": ["Test"]}
            ]
        }
        pipeline = DetectionPipeline(config)

        frame = Frame(index=0, timecode=1.5, data=np.zeros((480, 640, 3), dtype=np.uint8))
        results = pipeline.analyze_frame(frame)

        assert len(results) == 1
        assert results[0].label == "Test"
        assert results[0].confidence == 0.9

    def test_pipeline_assigns_frame_timecode_to_results(self):
        """Test that pipeline assigns frame timecode to results."""
        config = {
            "detectors": [
                {
                    "type": "stub",
                    "name": "detector",
                    "categories": ["Profanity", "Violence"],
                }
            ]
        }
        pipeline = DetectionPipeline(config)

        frame = Frame(index=0, timecode=5.0, data=np.zeros((480, 640, 3), dtype=np.uint8))
        results = pipeline.analyze_frame(frame)

        assert all(r.start_time == 5.0 for r in results)
        assert all(r.end_time == pytest.approx(5.033) for r in results)

    def test_pipeline_aggregates_results_from_multiple_detectors(self):
        """Test pipeline runs all detectors and aggregates results."""
        config = {
            "detectors": [
                {"type": "stub", "name": "detector-1", "categories": ["Profanity"]},
                {"type": "stub", "name": "detector-2", "categories": ["Violence"]},
            ]
        }
        pipeline = DetectionPipeline(config)

        frame = Frame(index=0, timecode=2.0, data=np.zeros((480, 640, 3), dtype=np.uint8))
        results = pipeline.analyze_frame(frame)

        # Should have results from both detectors
        assert len(results) == 2
        labels = {r.label for r in results}
        assert labels == {"Profanity", "Violence"}

    def test_pipeline_handles_detector_failure_gracefully(self):
        """Test that detector failure doesn't stop pipeline."""
        config = {
            "detectors": [
                {"type": "failing", "name": "failing-detector", "categories": ["Test"]},
                {"type": "stub", "name": "stub-detector", "categories": ["Success"]},
            ]
        }
        pipeline = DetectionPipeline(config)

        frame = Frame(index=0, timecode=1.0, data=np.zeros((480, 640, 3), dtype=np.uint8))
        results = pipeline.analyze_frame(frame)

        # Should only have results from stub detector
        assert len(results) == 1
        assert results[0].label == "Success"

    def test_pipeline_logs_detector_failure(self, caplog):
        """Test that detector failure is logged."""
        config = {
            "detectors": [
                {"type": "failing", "name": "bad", "categories": ["Test"]},
            ]
        }
        pipeline = DetectionPipeline(config)

        with caplog.at_level(logging.ERROR):
            frame = Frame(index=0, timecode=1.0, data=np.zeros((480, 640, 3), dtype=np.uint8))
            pipeline.analyze_frame(frame)

        assert "bad" in caplog.text
        assert "failed" in caplog.text.lower()

    def test_pipeline_cleanup_calls_all_detectors(self):
        """Test that pipeline.cleanup() calls cleanup on all detectors."""
        config = {
            "detectors": [
                {"type": "stub", "name": "detector-1", "categories": ["Test"]},
                {"type": "stub", "name": "detector-2", "categories": ["Test"]},
            ]
        }
        pipeline = DetectionPipeline(config)

        pipeline.cleanup()

        for detector in pipeline.detectors:
            assert isinstance(detector, StubDetector)
            assert detector.cleanup_called

    def test_pipeline_cleanup_error_handling(self, caplog):
        """Test that pipeline cleanup logs errors but continues."""

        class FailingCleanupDetector(Detector):
            def __init__(self, config: Dict[str, Any]) -> None:
                super().__init__(config)
                self.order_id = config.get("order_id")

            def detect(
                self,
                frame_data: Optional[np.ndarray] = None,
                audio_data: Optional[Any] = None,
            ) -> List[DetectionResult]:
                return []

            def cleanup(self) -> None:
                if self.order_id == 1:
                    raise RuntimeError("Cleanup failed")

        register_detector("failing-cleanup", FailingCleanupDetector)

        config = {
            "detectors": [
                {"type": "failing-cleanup", "name": "bad", "categories": ["Test"], "order_id": 1},
                {"type": "stub", "name": "good", "categories": ["Test"]},
            ]
        }
        pipeline = DetectionPipeline(config)

        with caplog.at_level(logging.ERROR):
            pipeline.cleanup()

        # Should log error but continue
        assert "Error cleaning up" in caplog.text

    def test_pipeline_cleanup_in_reverse_order(self):
        """Test that pipeline cleans up detectors in reverse order."""
        cleanup_order = []

        class OrderTrackingDetector(Detector):
            def __init__(self, config: Dict[str, Any]) -> None:
                super().__init__(config)
                self.order_id = config.get("order_id")

            def detect(
                self,
                frame_data: Optional[np.ndarray] = None,
                audio_data: Optional[Any] = None,
            ) -> List[DetectionResult]:
                return []

            def cleanup(self) -> None:
                cleanup_order.append(self.order_id)

        register_detector("order-tracker", OrderTrackingDetector)

        config = {
            "detectors": [
                {"type": "order-tracker", "name": "first", "categories": ["Test"], "order_id": 1},
                {"type": "order-tracker", "name": "second", "categories": ["Test"], "order_id": 2},
                {"type": "order-tracker", "name": "third", "categories": ["Test"], "order_id": 3},
            ]
        }
        pipeline = DetectionPipeline(config)
        pipeline.cleanup()

        assert cleanup_order == [3, 2, 1]

    def test_pipeline_analyze_frame_with_audio_data(self):
        """Test pipeline passes audio data to detectors."""

        class AudioCapturingDetector(Detector):
            def __init__(self, config: Dict[str, Any]) -> None:
                super().__init__(config)
                self.received_audio = None

            def detect(
                self,
                frame_data: Optional[np.ndarray] = None,
                audio_data: Optional[Any] = None,
            ) -> List[DetectionResult]:
                self.received_audio = audio_data
                return []

        register_detector("audio-capture", AudioCapturingDetector)

        config = {
            "detectors": [
                {"type": "audio-capture", "name": "audio-detector", "categories": ["Test"]}
            ]
        }
        pipeline = DetectionPipeline(config)

        frame = Frame(index=0, timecode=1.0, data=np.zeros((480, 640, 3), dtype=np.uint8))
        audio = np.zeros((16000,), dtype=np.float32)

        pipeline.analyze_frame(frame, audio_data=audio)

        # Verify audio was passed
        detector = pipeline.detectors[0]
        assert detector.received_audio is not None
        assert np.array_equal(detector.received_audio, audio)


# ============================================================================
# Tests: Configuration Support
# ============================================================================


class TestConfigurationSupport:
    """Test detector configuration parsing and validation."""

    def setup_method(self):
        """Set up test fixtures."""
        register_detector("stub", StubDetector)

    def test_detector_config_with_custom_parameters(self):
        """Test detector receives custom parameters in config."""

        class ParameterizedDetector(Detector):
            def __init__(self, config: Dict[str, Any]) -> None:
                super().__init__(config)
                self.threshold = config.get("threshold", 0.5)
                self.model_path = config.get("model_path")

            def detect(
                self,
                frame_data: Optional[np.ndarray] = None,
                audio_data: Optional[Any] = None,
            ) -> List[DetectionResult]:
                return []

        register_detector("parameterized", ParameterizedDetector)

        config = {
            "detectors": [
                {
                    "type": "parameterized",
                    "name": "custom",
                    "categories": ["Test"],
                    "threshold": 0.8,
                    "model_path": "/path/to/model",
                }
            ]
        }
        pipeline = DetectionPipeline(config)
        detector = pipeline.detectors[0]

        assert detector.threshold == 0.8
        assert detector.model_path == "/path/to/model"

    def test_multiple_detectors_with_different_configs(self):
        """Test multiple detectors can have different configurations."""
        config = {
            "detectors": [
                {
                    "type": "stub",
                    "name": "detector-1",
                    "categories": ["Profanity", "Violence"],
                    "mode": "success",
                },
                {
                    "type": "stub",
                    "name": "detector-2",
                    "categories": ["Nudity"],
                    "mode": "empty",
                },
            ]
        }
        pipeline = DetectionPipeline(config)

        assert len(pipeline.detectors) == 2
        assert pipeline.detectors[0].mode == "success"
        assert pipeline.detectors[1].mode == "empty"


# ============================================================================
# Tests: Error Handling and Resilience
# ============================================================================


class TestErrorHandling:
    """Test error handling and resilience."""

    def setup_method(self):
        """Set up test fixtures."""
        register_detector("stub", StubDetector)
        register_detector("failing", FailingDetector)

    def test_detector_initialization_failure_raises_before_analysis(self):
        """Test that detector initialization failure raises immediately."""

        class FailOnInitDetector(Detector):
            def __init__(self, config: Dict[str, Any]) -> None:
                super().__init__(config)
                raise RuntimeError("Init failed")

            def detect(
                self,
                frame_data: Optional[np.ndarray] = None,
                audio_data: Optional[Any] = None,
            ) -> List[DetectionResult]:
                return []

        register_detector("fail-init", FailOnInitDetector)

        config = {
            "detectors": [
                {"type": "fail-init", "name": "failing", "categories": ["Test"]}
            ]
        }

        with pytest.raises(ValueError, match="Failed to initialize detector"):
            DetectionPipeline(config)

    def test_detector_exception_with_clear_error_message(self):
        """Test that detector exceptions include detector name in message."""

        class CustomFailDetector(Detector):
            def detect(
                self,
                frame_data: Optional[np.ndarray] = None,
                audio_data: Optional[Any] = None,
            ) -> List[DetectionResult]:
                raise ValueError("Custom error message")

        register_detector("custom-fail", CustomFailDetector)

        config = {
            "detectors": [
                {"type": "custom-fail", "name": "my-detector", "categories": ["Test"]}
            ]
        }
        pipeline = DetectionPipeline(config)

        frame = Frame(index=0, timecode=1.0, data=np.zeros((480, 640, 3), dtype=np.uint8))
        results = pipeline.analyze_frame(frame)

        # Pipeline should continue and return empty results
        assert results == []

    def test_partial_results_from_detector_accepted(self):
        """Test that detectors can return partial results."""

        class PartialDetector(Detector):
            def detect(
                self,
                frame_data: Optional[np.ndarray] = None,
                audio_data: Optional[Any] = None,
            ) -> List[DetectionResult]:
                # Only return result for some of configured categories
                return [
                    DetectionResult(
                        start_time=0.0,
                        end_time=0.033,
                        label="Profanity",
                        confidence=0.9,
                        reasoning="Found profanity",
                    )
                ]

        register_detector("partial", PartialDetector)

        config = {
            "detectors": [
                {
                    "type": "partial",
                    "name": "detector",
                    "categories": ["Profanity", "Violence", "Nudity"],
                }
            ]
        }
        pipeline = DetectionPipeline(config)

        frame = Frame(index=0, timecode=1.0, data=np.zeros((480, 640, 3), dtype=np.uint8))
        results = pipeline.analyze_frame(frame)

        # Should have only the partial results
        assert len(results) == 1
        assert results[0].label == "Profanity"


# ============================================================================
# Tests: Frame and Audio Analysis
# ============================================================================


class TestFrameAndAudioAnalysis:
    """Test frame and audio handling."""

    def setup_method(self):
        """Set up test fixtures."""
        register_detector("stub", StubDetector)

    def test_detector_receives_frame_data(self):
        """Test detector receives frame pixel data."""

        class FrameCapturingDetector(Detector):
            def __init__(self, config: Dict[str, Any]) -> None:
                super().__init__(config)
                self.received_frame = None

            def detect(
                self,
                frame_data: Optional[np.ndarray] = None,
                audio_data: Optional[Any] = None,
            ) -> List[DetectionResult]:
                self.received_frame = frame_data
                return []

        register_detector("frame-capture", FrameCapturingDetector)

        config = {
            "detectors": [
                {"type": "frame-capture", "name": "detector", "categories": ["Test"]}
            ]
        }
        pipeline = DetectionPipeline(config)

        frame_data = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
        frame = Frame(index=0, timecode=1.0, data=frame_data)

        pipeline.analyze_frame(frame)

        detector = pipeline.detectors[0]
        assert detector.received_frame is not None
        assert np.array_equal(detector.received_frame, frame_data)

    def test_detector_receives_audio_data(self):
        """Test detector receives audio data when provided."""

        class AudioCapturingDetector(Detector):
            def __init__(self, config: Dict[str, Any]) -> None:
                super().__init__(config)
                self.received_audio = None

            def detect(
                self,
                frame_data: Optional[np.ndarray] = None,
                audio_data: Optional[Any] = None,
            ) -> List[DetectionResult]:
                self.received_audio = audio_data
                return []

        register_detector("audio-capture", AudioCapturingDetector)

        config = {
            "detectors": [
                {"type": "audio-capture", "name": "detector", "categories": ["Test"]}
            ]
        }
        pipeline = DetectionPipeline(config)

        frame = Frame(index=0, timecode=1.0, data=np.zeros((480, 640, 3), dtype=np.uint8))
        audio = b"audio data"

        pipeline.analyze_frame(frame, audio_data=audio)

        detector = pipeline.detectors[0]
        assert detector.received_audio == audio

    def test_detector_handles_none_audio_gracefully(self):
        """Test detector can handle None audio data."""

        class AudioOptionalDetector(Detector):
            def detect(
                self,
                frame_data: Optional[np.ndarray] = None,
                audio_data: Optional[Any] = None,
            ) -> List[DetectionResult]:
                # Should handle None audio
                if audio_data is None:
                    return [
                        DetectionResult(
                            start_time=0.0,
                            end_time=0.033,
                            label="Visual",
                            confidence=0.8,
                            reasoning="Frame only",
                        )
                    ]
                return []

        register_detector("audio-optional", AudioOptionalDetector)

        config = {
            "detectors": [
                {"type": "audio-optional", "name": "detector", "categories": ["Visual"]}
            ]
        }
        pipeline = DetectionPipeline(config)

        frame = Frame(index=0, timecode=1.0, data=np.zeros((480, 640, 3), dtype=np.uint8))
        results = pipeline.analyze_frame(frame, audio_data=None)

        assert len(results) == 1
        assert results[0].label == "Visual"


# ============================================================================
# Integration Tests
# ============================================================================


class TestIntegration:
    """End-to-end integration tests."""

    def setup_method(self):
        """Set up test fixtures."""
        register_detector("stub", StubDetector)

    def test_end_to_end_frame_to_multi_category_results(self):
        """Test complete flow: frame → pipeline → multi-category results."""
        config = {
            "detectors": [
                {
                    "type": "stub",
                    "name": "vision-model",
                    "categories": ["Profanity", "Nudity", "Violence", "Sexual Theme"],
                }
            ]
        }
        pipeline = DetectionPipeline(config)

        frame = Frame(index=5, timecode=10.5, data=np.zeros((480, 640, 3), dtype=np.uint8))
        results = pipeline.analyze_frame(frame)

        # Verify multi-category results
        assert len(results) == 4
        assert all(r.start_time == 10.5 for r in results)
        assert all(r.end_time == pytest.approx(10.533) for r in results)
        labels = {r.label for r in results}
        assert labels == {"Profanity", "Nudity", "Violence", "Sexual Theme"}

    def test_end_to_end_with_multiple_frames(self):
        """Test analyzing multiple frames in sequence."""
        config = {
            "detectors": [
                {
                    "type": "stub",
                    "name": "detector",
                    "categories": ["Profanity"],
                }
            ]
        }
        pipeline = DetectionPipeline(config)

        frames = [
            Frame(index=0, timecode=0.0, data=np.zeros((480, 640, 3), dtype=np.uint8)),
            Frame(index=1, timecode=0.033, data=np.zeros((480, 640, 3), dtype=np.uint8)),
            Frame(index=2, timecode=0.066, data=np.zeros((480, 640, 3), dtype=np.uint8)),
        ]

        all_results = []
        for frame in frames:
            results = pipeline.analyze_frame(frame)
            all_results.extend(results)

        # Should have results from all frames
        assert len(all_results) == 3
        timecodes = [r.start_time for r in all_results]
        assert timecodes == [0.0, 0.033, 0.066]

        pipeline.cleanup()

    def test_end_to_end_with_frame_and_audio(self):
        """Test analyzing frames with audio data."""

        class DualModalityDetector(Detector):
            def detect(
                self,
                frame_data: Optional[np.ndarray] = None,
                audio_data: Optional[Any] = None,
            ) -> List[DetectionResult]:
                results = []
                if frame_data is not None:
                    results.append(
                        DetectionResult(
                            start_time=0.0,
                            end_time=0.033,
                            label="Visual Content",
                            confidence=0.9,
                            reasoning="Detected from visual",
                        )
                    )
                if audio_data is not None:
                    results.append(
                        DetectionResult(
                            start_time=0.0,
                            end_time=0.033,
                            label="Audio Content",
                            confidence=0.85,
                            reasoning="Detected from audio",
                        )
                    )
                return results

        register_detector("dual-modal", DualModalityDetector)

        config = {
            "detectors": [
                {
                    "type": "dual-modal",
                    "name": "multimodal",
                    "categories": ["Visual Content", "Audio Content"],
                }
            ]
        }
        pipeline = DetectionPipeline(config)

        frame = Frame(index=0, timecode=1.0, data=np.zeros((480, 640, 3), dtype=np.uint8))
        audio = np.zeros((16000,), dtype=np.float32)

        results = pipeline.analyze_frame(frame, audio_data=audio)

        assert len(results) == 2
        labels = {r.label for r in results}
        assert labels == {"Visual Content", "Audio Content"}
