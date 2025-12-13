"""Tests for LLaVA vision-language detector."""

import json
import logging
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import numpy as np
import pytest

from video_censor_personal.detection import get_detector_registry
from video_censor_personal.detectors.llava_detector import LLaVADetector
from video_censor_personal.frame import DetectionResult, Frame


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def valid_config():
    """Valid LLaVA detector configuration."""
    return {
        "name": "test-llava",
        "categories": ["Nudity", "Profanity", "Violence", "Sexual Theme"],
        "model_name": "liuhaotian/llava-v1.5-7b",
        "prompt_file": "./prompts/llava-detector.txt",
    }


@pytest.fixture
def frame_bgr():
    """Sample BGR frame (OpenCV format)."""
    return np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)


@pytest.fixture
def mock_model():
    """Mock LLaVA model."""
    model = MagicMock()
    model.generate = MagicMock()
    return model


@pytest.fixture
def mock_processor():
    """Mock LLaVA processor."""
    processor = MagicMock()
    processor.decode = MagicMock(return_value="mock response")
    return processor


# ============================================================================
# Tests: Initialization and Model Loading
# ============================================================================


class TestLLaVADetectorInitialization:
    """Test detector initialization and model loading."""

    def test_detector_initializes_with_valid_config(self, valid_config):
        """Test detector initializes with valid configuration."""
        with patch("video_censor_personal.detectors.llava_detector.Path.exists", return_value=True):
            with patch("builtins.open", create=True):
                with patch.object(LLaVADetector, "_load_model", return_value=(Mock(), Mock())):
                    detector = LLaVADetector(valid_config)

                    assert detector.name == "test-llava"
                    assert detector.categories == [
                        "Nudity",
                        "Profanity",
                        "Violence",
                        "Sexual Theme",
                    ]
                    assert detector.model_name == "liuhaotian/llava-v1.5-7b"

    def test_detector_uses_default_model_name_if_not_provided(self, valid_config):
        """Test detector defaults to 7B model if not specified."""
        valid_config.pop("model_name")

        with patch("video_censor_personal.detectors.llava_detector.Path.exists", return_value=True):
            with patch("builtins.open", create=True):
                with patch.object(LLaVADetector, "_load_model", return_value=(Mock(), Mock())):
                    detector = LLaVADetector(valid_config)

                    assert detector.model_name == "liuhaotian/llava-v1.5-7b"

    def test_detector_prompt_file_missing_raises_error(self, valid_config):
        """Test that missing prompt file raises helpful error."""
        with patch("video_censor_personal.detectors.llava_detector.Path.exists", return_value=False):
            with pytest.raises(ValueError, match="Prompt file not found"):
                LLaVADetector(valid_config)

    def test_detector_prompt_file_read_error_raises_error(self, valid_config):
        """Test that prompt file read errors are handled."""
        with patch("video_censor_personal.detectors.llava_detector.Path.exists", return_value=True):
            with patch("builtins.open", side_effect=IOError("Read error")):
                with pytest.raises(ValueError, match="Failed to read prompt file"):
                    LLaVADetector(valid_config)

    def test_detector_inherits_from_detector_base_class(self, valid_config):
        """Test that LLaVADetector is a proper Detector subclass."""
        from video_censor_personal.detection import Detector

        with patch("video_censor_personal.detectors.llava_detector.Path.exists", return_value=True):
            with patch("builtins.open", create=True):
                with patch.object(LLaVADetector, "_load_model", return_value=(Mock(), Mock())):
                    detector = LLaVADetector(valid_config)

                    assert isinstance(detector, Detector)


# ============================================================================
# Tests: Model Loading and Validation
# ============================================================================


class TestModelLoading:
    """Test model loading and validation."""

    def test_model_load_missing_transformers_dependency_raises_error(self, valid_config):
        """Test helpful error when transformers not installed."""
        with patch(
            "video_censor_personal.detectors.llava_detector.Path.exists",
            return_value=True,
        ):
            with patch("builtins.open", create=True):
                with patch(
                    "video_censor_personal.detectors.llava_detector.Detector.__init__",
                ):
                    detector = LLaVADetector.__new__(LLaVADetector)
                    detector.name = "test"
                    detector.model_name = "liuhaotian/llava-v1.5-7b"
                    detector.prompt_file = "./prompts/llava-detector.txt"

                    with patch(
                        "builtins.__import__",
                        side_effect=ImportError("No module named transformers"),
                    ):
                        with pytest.raises(ValueError, match="dependencies not installed"):
                            detector._load_model()

    def test_model_load_missing_model_raises_error_with_instructions(self, valid_config):
        """Test helpful error when model file not found."""
        with patch("video_censor_personal.detectors.llava_detector.Path.exists", return_value=True):
            with patch("builtins.open", create=True):
                with patch(
                    "video_censor_personal.detectors.llava_detector.Detector.__init__",
                ):
                    detector = LLaVADetector.__new__(LLaVADetector)
                    detector.name = "test"
                    detector.model_name = "liuhaotian/llava-v1.5-7b"
                    detector.model_path = None
                    detector.prompt_file = "./prompts/llava-detector.txt"

                    # Mock the transformers module import to succeed, but from_pretrained to fail
                    def mock_import(*args, **kwargs):
                        if args[0] == "transformers":
                            mock_module = MagicMock()
                            mock_module.AutoProcessor.from_pretrained.side_effect = FileNotFoundError("Model not found")
                            return mock_module
                        return __import__(*args, **kwargs)
                    
                    with patch("builtins.__import__", side_effect=mock_import):
                        with pytest.raises(ValueError, match="not found") as exc_info:
                            detector._load_model()

                        # Check error message has download instructions
                        assert "Download command" in str(exc_info.value)
                        assert "QUICK_START.md" in str(exc_info.value)


# ============================================================================
# Tests: Prompt Loading
# ============================================================================


class TestPromptLoading:
    """Test prompt loading from files."""

    def test_load_prompt_from_file(self, valid_config, tmp_path):
        """Test loading prompt from file."""
        prompt_content = "Analyze this image for bad content."
        prompt_file = tmp_path / "test_prompt.txt"
        prompt_file.write_text(prompt_content)

        valid_config["prompt_file"] = str(prompt_file)

        with patch.object(LLaVADetector, "_load_model", return_value=(Mock(), Mock())):
            detector = LLaVADetector(valid_config)

            assert detector.prompt_template == prompt_content

    def test_load_prompt_file_not_found(self, valid_config):
        """Test error when prompt file doesn't exist."""
        valid_config["prompt_file"] = "/nonexistent/prompt.txt"

        with pytest.raises(ValueError, match="Prompt file not found"):
            detector = LLaVADetector.__new__(LLaVADetector)
            detector.prompt_file = "/nonexistent/prompt.txt"
            detector._load_prompt()


# ============================================================================
# Tests: Frame Analysis (detect method)
# ============================================================================


class TestFrameAnalysis:
    """Test frame detection and analysis."""

    def test_detect_with_valid_frame(self, valid_config, frame_bgr):
        """Test detect() with valid frame data."""
        with patch("video_censor_personal.detectors.llava_detector.Path.exists", return_value=True):
            with patch("builtins.open", create=True):
                with patch.object(LLaVADetector, "_load_model") as mock_load_model:
                    mock_model = MagicMock()
                    mock_processor = MagicMock()

                    # Mock the generation output
                    mock_output = MagicMock()
                    mock_output.__getitem__ = MagicMock(return_value=np.array([1, 2, 3]))
                    mock_model.generate.return_value = mock_output

                    # Mock the decode output with valid JSON
                    valid_response = json.dumps({
                        "nudity": {"detected": True, "confidence": 0.95, "reasoning": "Nude body detected"},
                        "profanity": {"detected": False, "confidence": 0.1, "reasoning": "No profanity"},
                        "violence": {"detected": True, "confidence": 0.8, "reasoning": "Fighting scene"},
                        "sexual_theme": {"detected": False, "confidence": 0.2, "reasoning": "No sexual content"},
                    })
                    mock_processor.decode.return_value = valid_response
                    mock_processor.return_value = {"test": "input"}

                    mock_load_model.return_value = (mock_model, mock_processor)

                    # Mock PIL Image which is imported inside detect method
                    with patch("PIL.Image.fromarray") as mock_from_array:
                        mock_from_array.return_value = MagicMock()
                        detector = LLaVADetector(valid_config)
                        results = detector.detect(frame_data=frame_bgr)

                        # Should return results for detected categories (nudity, violence)
                        assert len(results) == 2
                        assert any(r.label == "Nudity" for r in results)
                        assert any(r.label == "Violence" for r in results)

    def test_detect_with_none_frame_raises_error(self, valid_config):
        """Test that None frame data raises error."""
        with patch("video_censor_personal.detectors.llava_detector.Path.exists", return_value=True):
            with patch("builtins.open", create=True):
                with patch.object(LLaVADetector, "_load_model", return_value=(Mock(), Mock())):
                    detector = LLaVADetector(valid_config)

                    with pytest.raises(ValueError, match="requires frame_data"):
                        detector.detect(frame_data=None)

    def test_detect_with_invalid_frame_shape_raises_error(self, valid_config):
        """Test that invalid frame shape raises error."""
        with patch("video_censor_personal.detectors.llava_detector.Path.exists", return_value=True):
            with patch("builtins.open", create=True):
                with patch.object(LLaVADetector, "_load_model", return_value=(Mock(), Mock())):
                    detector = LLaVADetector(valid_config)

                    invalid_frame = np.zeros((480, 640), dtype=np.uint8)  # Wrong shape
                    with pytest.raises(ValueError, match="shape.*height, width, 3"):
                        detector.detect(frame_data=invalid_frame)

    def test_detect_malformed_json_response_returns_empty_results(self, valid_config, frame_bgr):
        """Test graceful handling of malformed JSON response."""
        with patch("video_censor_personal.detectors.llava_detector.Path.exists", return_value=True):
            with patch("builtins.open", create=True):
                with patch.object(LLaVADetector, "_load_model") as mock_load_model:
                    mock_model = MagicMock()
                    mock_processor = MagicMock()
                    mock_output = MagicMock()
                    mock_output.__getitem__ = MagicMock(return_value=np.array([1]))

                    # Return invalid JSON
                    mock_processor.decode.return_value = "This is not JSON at all"
                    mock_processor.return_value = {"test": "input"}
                    mock_model.generate.return_value = mock_output

                    mock_load_model.return_value = (mock_model, mock_processor)

                    detector = LLaVADetector(valid_config)
                    results = detector.detect(frame_data=frame_bgr)

                    # Should return empty results, not raise
                    assert results == []

    def test_detect_oom_error_returns_empty_results(self, valid_config, frame_bgr):
        """Test that OOM errors during inference return empty results."""
        with patch("video_censor_personal.detectors.llava_detector.Path.exists", return_value=True):
            with patch("builtins.open", create=True):
                with patch.object(LLaVADetector, "_load_model") as mock_load_model:
                    mock_model = MagicMock()
                    mock_processor = MagicMock()
                    mock_processor.return_value = {"test": "input"}

                    # Make generate raise OOM error
                    mock_model.generate.side_effect = RuntimeError("out of memory")

                    mock_load_model.return_value = (mock_model, mock_processor)

                    detector = LLaVADetector(valid_config)
                    results = detector.detect(frame_data=frame_bgr)

                    assert results == []


# ============================================================================
# Tests: Response Parsing and Result Creation
# ============================================================================


class TestResponseParsing:
    """Test LLaVA response parsing and result creation."""

    def test_parse_response_with_extra_text(self, valid_config):
        """Test parsing JSON from response with surrounding text."""
        with patch("video_censor_personal.detectors.llava_detector.Path.exists", return_value=True):
            with patch("builtins.open", create=True):
                with patch.object(LLaVADetector, "_load_model", return_value=(Mock(), Mock())):
                    detector = LLaVADetector(valid_config)

                    response = 'Some preamble {"nudity": {"detected": true}} Some postamble'
                    result = detector._parse_response(response)

                    assert "nudity" in result
                    assert result["nudity"]["detected"] is True

    def test_confidence_clamped_to_range(self, valid_config, frame_bgr):
        """Test that confidence scores are clamped to [0.0, 1.0]."""
        with patch("video_censor_personal.detectors.llava_detector.Path.exists", return_value=True):
            with patch("builtins.open", create=True):
                with patch.object(LLaVADetector, "_load_model") as mock_load_model:
                    mock_model = MagicMock()
                    mock_processor = MagicMock()
                    mock_output = MagicMock()
                    mock_output.__getitem__ = MagicMock(return_value=np.array([1]))

                    # Return JSON with out-of-range confidence
                    response_data = {
                        "nudity": {"detected": True, "confidence": 1.5, "reasoning": "test"},
                        "profanity": {"detected": True, "confidence": -0.5, "reasoning": "test"},
                        "violence": {"detected": False, "confidence": 0.5, "reasoning": "test"},
                        "sexual_theme": {"detected": False, "confidence": 0.5, "reasoning": "test"},
                    }
                    mock_processor.decode.return_value = json.dumps(response_data)
                    mock_processor.return_value = {"test": "input"}
                    mock_model.generate.return_value = mock_output

                    mock_load_model.return_value = (mock_model, mock_processor)

                    detector = LLaVADetector(valid_config)
                    results = detector.detect(frame_data=frame_bgr)

                    for result in results:
                        assert 0.0 <= result.confidence <= 1.0


# ============================================================================
# Tests: Cleanup
# ============================================================================


class TestCleanup:
    """Test detector cleanup and resource management."""

    def test_cleanup_releases_model(self, valid_config):
        """Test that cleanup() releases model memory."""
        with patch("video_censor_personal.detectors.llava_detector.Path.exists", return_value=True):
            with patch("builtins.open", create=True):
                with patch.object(LLaVADetector, "_load_model") as mock_load_model:
                    mock_model = MagicMock()
                    mock_processor = MagicMock()
                    mock_load_model.return_value = (mock_model, mock_processor)

                    detector = LLaVADetector(valid_config)
                    detector.cleanup()

                    # Model should be None after cleanup
                    assert detector.model is None
                    assert detector.processor is None


# ============================================================================
# Tests: Registry Integration
# ============================================================================


class TestRegistryIntegration:
    """Test detector registration and registry integration."""

    def test_detector_registered_in_global_registry(self):
        """Test that LLaVADetector is registered globally."""
        registry = get_detector_registry()

        # Should be registered as "llava"
        assert registry.get("llava") == LLaVADetector

    def test_detector_can_be_created_via_registry(self, valid_config):
        """Test creating detector instance via registry."""
        registry = get_detector_registry()

        with patch("video_censor_personal.detectors.llava_detector.Path.exists", return_value=True):
            with patch("builtins.open", create=True):
                with patch.object(LLaVADetector, "_load_model", return_value=(Mock(), Mock())):
                    detector = registry.create("llava", valid_config)

                    assert isinstance(detector, LLaVADetector)
                    assert detector.name == "test-llava"
