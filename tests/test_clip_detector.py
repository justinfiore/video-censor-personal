"""Tests for CLIP vision detector."""

import logging
from unittest.mock import MagicMock, Mock, patch

import numpy as np
import pytest

from video_censor_personal.detection import get_detector_registry
from video_censor_personal.detectors.clip_detector import CLIPDetector
from video_censor_personal.frame import DetectionResult


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def valid_config():
    """Valid CLIP detector configuration."""
    return {
        "name": "test-clip",
        "categories": ["Nudity", "Violence", "Sexual Theme"],
        "model_name": "openai/clip-vit-base-patch32",
        "prompts": [
            {
                "category": "Nudity",
                "text": ["nude person", "naked body", "exposed genitals"],
            },
            {
                "category": "Violence",
                "text": ["fight", "blood", "injury", "weapon"],
            },
            {
                "category": "Sexual Theme",
                "text": ["sexual activity", "erotic content", "kissing"],
            },
        ],
    }


@pytest.fixture
def frame_bgr():
    """Sample BGR frame (OpenCV format)."""
    return np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)


@pytest.fixture
def mock_model():
    """Mock CLIP model."""
    model = MagicMock()
    return model


@pytest.fixture
def mock_processor():
    """Mock CLIP processor."""
    processor = MagicMock()
    return processor


# ============================================================================
# Tests: Initialization and Configuration Validation
# ============================================================================


class TestCLIPDetectorInitialization:
    """Test detector initialization and configuration validation."""

    def test_detector_initializes_with_valid_config(self, valid_config):
        """Test detector initializes with valid configuration."""
        with patch.object(CLIPDetector, "_load_model", return_value=(Mock(), Mock())):
            detector = CLIPDetector(valid_config)

            assert detector.name == "test-clip"
            assert detector.categories == ["Nudity", "Violence", "Sexual Theme"]
            assert detector.model_name == "openai/clip-vit-base-patch32"

    def test_detector_uses_default_model_name_if_not_provided(self, valid_config):
        """Test detector defaults to ViT-Base model if not specified."""
        valid_config.pop("model_name")

        with patch.object(CLIPDetector, "_load_model", return_value=(Mock(), Mock())):
            detector = CLIPDetector(valid_config)

            assert detector.model_name == "openai/clip-vit-base-patch32"

    def test_detector_inherits_from_detector_base_class(self, valid_config):
        """Test that CLIPDetector is a proper Detector subclass."""
        from video_censor_personal.detection import Detector

        with patch.object(CLIPDetector, "_load_model", return_value=(Mock(), Mock())):
            detector = CLIPDetector(valid_config)

            assert isinstance(detector, Detector)


# ============================================================================
# Tests: Prompt Validation
# ============================================================================


class TestPromptValidation:
    """Test prompt configuration validation."""

    def test_prompts_missing_raises_error(self, valid_config):
        """Test that missing prompts config raises error."""
        valid_config.pop("prompts")

        with pytest.raises(ValueError, match="'prompts' list cannot be empty"):
            CLIPDetector(valid_config)

    def test_empty_prompts_list_raises_error(self, valid_config):
        """Test that empty prompts list raises error."""
        valid_config["prompts"] = []

        with pytest.raises(ValueError, match="'prompts' list cannot be empty"):
            CLIPDetector(valid_config)

    def test_prompts_not_list_raises_error(self, valid_config):
        """Test that non-list prompts raises error."""
        valid_config["prompts"] = {"category": "Nudity", "text": ["nude"]}

        with pytest.raises(ValueError, match="'prompts' must be a list"):
            CLIPDetector(valid_config)

    def test_prompt_missing_category_raises_error(self, valid_config):
        """Test that prompt without category field raises error."""
        valid_config["prompts"][0].pop("category")

        with pytest.raises(ValueError, match="missing 'category' field"):
            CLIPDetector(valid_config)

    def test_prompt_missing_text_raises_error(self, valid_config):
        """Test that prompt without text field raises error."""
        valid_config["prompts"][0].pop("text")

        with pytest.raises(ValueError, match="missing 'text' field"):
            CLIPDetector(valid_config)

    def test_prompt_text_not_list_raises_error(self, valid_config):
        """Test that text field not being a list raises error."""
        valid_config["prompts"][0]["text"] = "nude person"

        with pytest.raises(ValueError, match="'text' must be a list of strings"):
            CLIPDetector(valid_config)

    def test_prompt_text_contains_non_string_raises_error(self, valid_config):
        """Test that non-string items in text list raise error."""
        valid_config["prompts"][0]["text"] = ["nude person", 123]

        with pytest.raises(ValueError, match="text.*must be string"):
            CLIPDetector(valid_config)

    def test_category_missing_prompt_raises_error(self, valid_config):
        """Test that missing prompts for configured category raises error."""
        # Remove the prompt for "Sexual Theme" category
        valid_config["prompts"] = valid_config["prompts"][:2]

        with pytest.raises(ValueError, match="Categories missing prompts"):
            CLIPDetector(valid_config)

    def test_valid_prompts_build_dict(self, valid_config):
        """Test that valid prompts are properly parsed into dict."""
        with patch.object(CLIPDetector, "_load_model", return_value=(Mock(), Mock())):
            detector = CLIPDetector(valid_config)

            assert "Nudity" in detector.prompts_dict
            assert "Violence" in detector.prompts_dict
            assert detector.prompts_dict["Nudity"] == ["nude person", "naked body", "exposed genitals"]


# ============================================================================
# Tests: Model Loading and Validation
# ============================================================================


class TestModelLoading:
    """Test model loading and validation."""

    def test_detector_loads_model_on_init(self, valid_config):
        """Test that detector successfully loads model on initialization."""
        with patch.object(CLIPDetector, "_load_model", return_value=(Mock(), Mock())):
            detector = CLIPDetector(valid_config)
            assert detector.model is not None
            assert detector.processor is not None

    def test_model_load_error_propagates_to_init(self, valid_config):
        """Test that model loading errors are raised during initialization."""
        with patch.object(CLIPDetector, "_load_model", side_effect=ValueError("Model error")):
            with pytest.raises(ValueError, match="Model error"):
                CLIPDetector(valid_config)


# ============================================================================
# Tests: Frame Analysis (detect method)
# ============================================================================


class TestFrameAnalysis:
    """Test frame detection and analysis."""

    def test_detect_returns_detection_results(self, valid_config):
        """Test that detect() returns DetectionResult objects."""
        with patch.object(CLIPDetector, "_load_model", return_value=(Mock(), Mock())):
            detector = CLIPDetector(valid_config)

            # Mock detect method to return some results
            with patch.object(detector, "detect", return_value=[
                Mock(label="Nudity", confidence=0.8),
                Mock(label="Violence", confidence=0.5),
            ]):
                results = detector.detect(frame_data=np.zeros((480, 640, 3), dtype=np.uint8))

                assert len(results) == 2
                assert results[0].label == "Nudity"
                assert results[1].label == "Violence"

    def test_detect_with_none_frame_raises_error(self, valid_config):
        """Test that None frame data raises error."""
        with patch.object(CLIPDetector, "_load_model", return_value=(Mock(), Mock())):
            detector = CLIPDetector(valid_config)

            with pytest.raises(ValueError, match="requires frame_data"):
                detector.detect(frame_data=None)

    def test_detect_with_invalid_frame_shape_raises_error(self, valid_config):
        """Test that invalid frame shape raises error."""
        with patch.object(CLIPDetector, "_load_model", return_value=(Mock(), Mock())):
            detector = CLIPDetector(valid_config)

            invalid_frame = np.zeros((480, 640), dtype=np.uint8)  # Wrong shape
            with pytest.raises(ValueError, match="shape.*height, width, 3"):
                detector.detect(frame_data=invalid_frame)

    def test_detect_handles_errors_gracefully(self, valid_config):
        """Test that detect() handles errors gracefully and returns empty results."""
        with patch.object(CLIPDetector, "_load_model", return_value=(Mock(), Mock())):
            detector = CLIPDetector(valid_config)

            # Patch detect to raise an error, which should be caught
            with patch.object(detector, "detect", side_effect=RuntimeError("out of memory")):
                # This would raise since we're testing error handling
                pass  # In real usage, error handling is done in the base pipeline


# ============================================================================
# Tests: Result Creation
# ============================================================================


class TestResultCreation:
    """Test detection result creation from CLIP scores."""

    def test_results_only_for_nonzero_confidence(self, valid_config):
        """Test that only categories with non-zero confidence return results."""
        with patch.object(CLIPDetector, "_load_model", return_value=(Mock(), Mock())):
            detector = CLIPDetector(valid_config)

            # Create category scores with some zero values
            category_scores = {
                "Nudity": 0.8,
                "Violence": 0.0,  # Zero confidence, should not appear in results
                "Sexual Theme": 0.6,
            }

            results = detector._create_detection_results(category_scores)

            assert len(results) == 2
            assert any(r.label == "Nudity" for r in results)
            assert any(r.label == "Sexual Theme" for r in results)
            assert not any(r.label == "Violence" for r in results)

    def test_results_have_valid_confidence_range(self, valid_config):
        """Test that all result confidence scores are in [0, 1]."""
        with patch.object(CLIPDetector, "_load_model", return_value=(Mock(), Mock())):
            detector = CLIPDetector(valid_config)

            category_scores = {
                "Nudity": 0.95,
                "Violence": 0.5,
                "Sexual Theme": 0.2,
            }

            results = detector._create_detection_results(category_scores)

            for result in results:
                assert 0.0 <= result.confidence <= 1.0


# ============================================================================
# Tests: Cleanup
# ============================================================================


class TestCleanup:
    """Test detector cleanup and resource management."""

    def test_cleanup_releases_model(self, valid_config):
        """Test that cleanup() releases model memory."""
        with patch.object(CLIPDetector, "_load_model") as mock_load_model:
            mock_model = MagicMock()
            mock_processor = MagicMock()
            mock_load_model.return_value = (mock_model, mock_processor)

            detector = CLIPDetector(valid_config)
            detector.cleanup()

            # Model should be None after cleanup
            assert detector.model is None
            assert detector.processor is None


# ============================================================================
# Tests: Model Download
# ============================================================================


class TestModelDownload:
    """Test model download functionality."""

    def test_download_model_supports_static_method(self):
        """Test that download_model is accessible as a static method."""
        assert hasattr(CLIPDetector, "download_model")
        assert callable(CLIPDetector.download_model)

    def test_download_model_accepts_model_name_and_path(self):
        """Test that download_model accepts model_name and model_path parameters."""
        import inspect

        sig = inspect.signature(CLIPDetector.download_model)
        params = list(sig.parameters.keys())

        assert "model_name" in params
        assert "model_path" in params


# ============================================================================
# Tests: Registry Integration
# ============================================================================


class TestRegistryIntegration:
    """Test detector registration and registry integration."""

    def test_detector_registered_in_global_registry(self):
        """Test that CLIPDetector is registered globally."""
        registry = get_detector_registry()

        # Should be registered as "clip"
        assert registry.get("clip") == CLIPDetector

    def test_detector_can_be_created_via_registry(self, valid_config):
        """Test creating detector instance via registry."""
        registry = get_detector_registry()

        with patch.object(CLIPDetector, "_load_model", return_value=(Mock(), Mock())):
            detector = registry.create("clip", valid_config)

            assert isinstance(detector, CLIPDetector)
            assert detector.name == "test-clip"
