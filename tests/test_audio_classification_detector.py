"""Tests for audio classification detection module."""

from pathlib import Path
from unittest.mock import MagicMock, patch
import json

import numpy as np
import pytest

# Skip all tests if transformers is not installed
pytest.importorskip("transformers", reason="transformers not installed")

from video_censor_personal.audio_classification_detector import AudioClassificationDetector


class TestAudioClassificationDetectorInitialization:
    """Test AudioClassificationDetector initialization."""

    @patch("video_censor_personal.audio_classification_detector.get_device", return_value="cpu")
    @patch("transformers.AutoModelForAudioClassification")
    @patch("transformers.AutoFeatureExtractor")
    def test_init_with_default_config(self, mock_extractor, mock_model, mock_device):
        """Test initialization with default configuration."""
        mock_model_instance = MagicMock()
        mock_extractor.from_pretrained.return_value = MagicMock()
        mock_model.from_pretrained.return_value = mock_model_instance
        
        config = {
            "name": "test-detector",
            "categories": ["Violence"],
        }
        
        detector = AudioClassificationDetector(config)
        
        assert detector.model_name == "MIT/ast-finetuned-audioset-10-10-0.4593"
        assert detector.confidence_threshold == 0.6
        assert "Violence" in detector.target_categories

    @patch("video_censor_personal.audio_classification_detector.get_device", return_value="cpu")
    @patch("transformers.AutoModelForAudioClassification")
    @patch("transformers.AutoFeatureExtractor")
    def test_init_with_custom_config(self, mock_extractor, mock_model, mock_device):
        """Test initialization with custom configuration."""
        mock_model_instance = MagicMock()
        mock_extractor.from_pretrained.return_value = MagicMock()
        mock_model.from_pretrained.return_value = mock_model_instance
        
        config = {
            "name": "test-detector",
            "categories": ["Violence", "Sexual Theme"],
            "model": "custom-audio-model",
            "confidence_threshold": 0.8,
        }
        
        detector = AudioClassificationDetector(config)
        
        assert detector.model_name == "custom-audio-model"
        assert detector.confidence_threshold == 0.8
        mock_extractor.from_pretrained.assert_called_with("custom-audio-model")
        mock_model.from_pretrained.assert_called_with("custom-audio-model")

    @patch("video_censor_personal.audio_classification_detector.get_device", return_value="cpu")
    @patch("transformers.AutoModelForAudioClassification")
    @patch("transformers.AutoFeatureExtractor")
    def test_init_loads_category_mapping(self, mock_extractor, mock_model, mock_device):
        """Test that initialization loads category mapping."""
        mock_model_instance = MagicMock()
        mock_extractor.from_pretrained.return_value = MagicMock()
        mock_model.from_pretrained.return_value = mock_model_instance
        
        config = {
            "name": "test-detector",
            "categories": ["Violence"],
        }
        
        detector = AudioClassificationDetector(config)
        
        # Should have default mapping
        assert "gunshot" in detector.category_mapping
        assert detector.category_mapping["gunshot"] == "Violence"


class TestCategoryMapping:
    """Test category mapping functionality."""

    @patch("video_censor_personal.audio_classification_detector.get_device", return_value="cpu")
    @patch("transformers.AutoModelForAudioClassification")
    @patch("transformers.AutoFeatureExtractor")
    def test_default_violence_mappings(self, mock_extractor, mock_model, mock_device):
        """Test default Violence category mappings."""
        mock_model_instance = MagicMock()
        mock_extractor.from_pretrained.return_value = MagicMock()
        mock_model.from_pretrained.return_value = mock_model_instance
        
        config = {
            "name": "test-detector",
            "categories": ["Violence"],
        }
        
        detector = AudioClassificationDetector(config)
        
        violence_sounds = ["gunshot", "explosion", "scream", "crash"]
        for sound in violence_sounds:
            assert sound in detector.category_mapping
            assert detector.category_mapping[sound] == "Violence"

    @patch("video_censor_personal.audio_classification_detector.get_device", return_value="cpu")
    @patch("transformers.AutoModelForAudioClassification")
    @patch("transformers.AutoFeatureExtractor")
    def test_default_sexual_theme_mappings(self, mock_extractor, mock_model, mock_device):
        """Test default Sexual Theme category mappings."""
        mock_model_instance = MagicMock()
        mock_extractor.from_pretrained.return_value = MagicMock()
        mock_model.from_pretrained.return_value = mock_model_instance
        
        config = {
            "name": "test-detector",
            "categories": ["Sexual Theme"],
        }
        
        detector = AudioClassificationDetector(config)
        
        sexual_sounds = ["moan", "moaning"]
        for sound in sexual_sounds:
            assert sound in detector.category_mapping
            assert detector.category_mapping[sound] == "Sexual Theme"


class TestAudioClassification:
    """Test audio classification detection."""

    @patch("video_censor_personal.audio_classification_detector.get_device", return_value="cpu")
    @patch("transformers.AutoModelForAudioClassification")
    @patch("transformers.AutoFeatureExtractor")
    def test_detect_returns_empty_when_no_audio(
        self, mock_extractor, mock_model, mock_device
    ):
        """Test detection returns empty when no audio provided."""
        mock_model_instance = MagicMock()
        mock_extractor.from_pretrained.return_value = MagicMock()
        mock_model.from_pretrained.return_value = mock_model_instance
        
        config = {
            "name": "test-detector",
            "categories": ["Violence"],
        }
        
        detector = AudioClassificationDetector(config)
        results = detector.detect(frame_data=np.zeros((100, 100, 3)), audio_data=None)
        
        assert results == []

    @patch("video_censor_personal.audio_classification_detector.get_device", return_value="cpu")
    @patch("transformers.AutoModelForAudioClassification")
    @patch("transformers.AutoFeatureExtractor")
    def test_detect_maps_audio_label_to_category(
        self, mock_extractor, mock_model, mock_device
    ):
        """Test detection maps audio labels to content categories."""
        import torch
        
        # Setup processor mock that returns a dict with a tensor
        mock_processor = MagicMock()
        mock_input_tensor = torch.zeros(1, 1024)
        mock_processor.return_value = {"input_values": mock_input_tensor}
        mock_extractor.from_pretrained.return_value = mock_processor
        
        # Setup model mock - needs to be properly callable
        mock_model_instance = MagicMock()
        mock_model_instance.config.id2label = {0: "gunshot", 1: "other", 2: "noise"}
        mock_model_instance.to.return_value = mock_model_instance  # .to(device) returns self
        
        # Create actual tensors for logits - index 0 (gunshot) should be max
        # Use larger difference to ensure softmax gives confidence > 0.6
        mock_logits = torch.tensor([[5.0, 0.0, 0.0]])
        mock_outputs = MagicMock()
        mock_outputs.logits = mock_logits
        mock_model_instance.return_value = mock_outputs
        mock_model.from_pretrained.return_value = mock_model_instance
        
        config = {
            "name": "test-detector",
            "categories": ["Violence"],
        }
        
        detector = AudioClassificationDetector(config)
        
        audio_data = np.random.randn(16000).astype(np.float32)
        results = detector.detect(audio_data=audio_data)
        
        assert len(results) == 1
        assert results[0].label == "Violence"
        assert "gunshot" in results[0].reasoning

    @patch("video_censor_personal.audio_classification_detector.get_device", return_value="cpu")
    @patch("video_censor_personal.audio_classification_detector.torch")
    @patch("transformers.AutoModelForAudioClassification")
    @patch("transformers.AutoFeatureExtractor")
    def test_detect_skips_below_confidence_threshold(
        self, mock_extractor, mock_model, mock_torch, mock_device
    ):
        """Test detection skips results below confidence threshold."""
        mock_processor = MagicMock()
        mock_processor.return_value = {"input_values": MagicMock()}
        mock_extractor.from_pretrained.return_value = mock_processor
        
        mock_model_instance = MagicMock()
        mock_model_instance.config.id2label = {0: "gunshot"}
        
        mock_outputs = MagicMock()
        mock_logits = MagicMock()
        mock_logits.argmax.return_value.item.return_value = 0
        mock_logits.softmax.return_value.max.return_value.item.return_value = 0.3  # Below threshold
        mock_outputs.logits = mock_logits
        mock_model_instance.return_value = mock_outputs
        mock_model.from_pretrained.return_value = mock_model_instance
        
        config = {
            "name": "test-detector",
            "categories": ["Violence"],
            "confidence_threshold": 0.6,
        }
        
        detector = AudioClassificationDetector(config)
        
        audio_data = np.random.randn(16000).astype(np.float32)
        results = detector.detect(audio_data=audio_data)
        
        assert results == []

    @patch("video_censor_personal.audio_classification_detector.get_device", return_value="cpu")
    @patch("video_censor_personal.audio_classification_detector.torch")
    @patch("transformers.AutoModelForAudioClassification")
    @patch("transformers.AutoFeatureExtractor")
    def test_detect_skips_unmapped_labels(
        self, mock_extractor, mock_model, mock_torch, mock_device
    ):
        """Test detection skips audio labels not in mapping."""
        mock_processor = MagicMock()
        mock_processor.return_value = {"input_values": MagicMock()}
        mock_extractor.from_pretrained.return_value = mock_processor
        
        mock_model_instance = MagicMock()
        mock_model_instance.config.id2label = {0: "unknown_sound"}  # Not in mapping
        
        mock_outputs = MagicMock()
        mock_logits = MagicMock()
        mock_logits.argmax.return_value.item.return_value = 0
        mock_logits.softmax.return_value.max.return_value.item.return_value = 0.9
        mock_outputs.logits = mock_logits
        mock_model_instance.return_value = mock_outputs
        mock_model.from_pretrained.return_value = mock_model_instance
        
        config = {
            "name": "test-detector",
            "categories": ["Violence"],
        }
        
        detector = AudioClassificationDetector(config)
        
        audio_data = np.random.randn(16000).astype(np.float32)
        results = detector.detect(audio_data=audio_data)
        
        assert results == []

    @patch("video_censor_personal.audio_classification_detector.get_device", return_value="cpu")
    @patch("video_censor_personal.audio_classification_detector.torch")
    @patch("transformers.AutoModelForAudioClassification")
    @patch("transformers.AutoFeatureExtractor")
    def test_detect_skips_non_target_categories(
        self, mock_extractor, mock_model, mock_torch, mock_device
    ):
        """Test detection skips categories not in target list."""
        mock_processor = MagicMock()
        mock_processor.return_value = {"input_values": MagicMock()}
        mock_extractor.from_pretrained.return_value = mock_processor
        
        mock_model_instance = MagicMock()
        mock_model_instance.config.id2label = {0: "moan"}  # Maps to Sexual Theme
        
        mock_outputs = MagicMock()
        mock_logits = MagicMock()
        mock_logits.argmax.return_value.item.return_value = 0
        mock_logits.softmax.return_value.max.return_value.item.return_value = 0.9
        mock_outputs.logits = mock_logits
        mock_model_instance.return_value = mock_outputs
        mock_model.from_pretrained.return_value = mock_model_instance
        
        config = {
            "name": "test-detector",
            "categories": ["Violence"],  # Only targeting Violence, not Sexual Theme
        }
        
        detector = AudioClassificationDetector(config)
        
        audio_data = np.random.randn(16000).astype(np.float32)
        results = detector.detect(audio_data=audio_data)
        
        assert results == []

    @patch("video_censor_personal.audio_classification_detector.get_device", return_value="cpu")
    @patch("transformers.AutoModelForAudioClassification")
    @patch("transformers.AutoFeatureExtractor")
    def test_detect_handles_model_error(
        self, mock_extractor, mock_model, mock_device
    ):
        """Test detection handles model errors gracefully."""
        mock_processor = MagicMock()
        mock_processor.side_effect = Exception("Processing error")
        mock_extractor.from_pretrained.return_value = mock_processor
        mock_model_instance = MagicMock()
        mock_model.from_pretrained.return_value = mock_model_instance
        
        config = {
            "name": "test-detector",
            "categories": ["Violence"],
        }
        
        detector = AudioClassificationDetector(config)
        
        audio_data = np.random.randn(16000).astype(np.float32)
        results = detector.detect(audio_data=audio_data)
        
        # Should return empty list on error, not raise
        assert results == []


class TestCleanup:
    """Test resource cleanup."""

    @patch("video_censor_personal.audio_classification_detector.get_device", return_value="cpu")
    @patch("transformers.AutoModelForAudioClassification")
    @patch("transformers.AutoFeatureExtractor")
    def test_cleanup_releases_model(self, mock_extractor, mock_model, mock_device):
        """Test cleanup releases model and processor."""
        mock_model_instance = MagicMock()
        mock_extractor.from_pretrained.return_value = MagicMock()
        mock_model.from_pretrained.return_value = mock_model_instance
        
        config = {
            "name": "test-detector",
            "categories": ["Violence"],
        }
        
        detector = AudioClassificationDetector(config)
        assert hasattr(detector, "model")
        assert hasattr(detector, "processor")
        
        detector.cleanup()
        
        assert not hasattr(detector, "model")
        assert not hasattr(detector, "processor")

    @patch("video_censor_personal.audio_classification_detector.get_device", return_value="cpu")
    @patch("transformers.AutoModelForAudioClassification")
    @patch("transformers.AutoFeatureExtractor")
    def test_cleanup_handles_missing_attributes(self, mock_extractor, mock_model, mock_device):
        """Test cleanup handles case where attributes don't exist."""
        mock_model_instance = MagicMock()
        mock_extractor.from_pretrained.return_value = MagicMock()
        mock_model.from_pretrained.return_value = mock_model_instance
        
        config = {
            "name": "test-detector",
            "categories": ["Violence"],
        }
        
        detector = AudioClassificationDetector(config)
        del detector.model
        del detector.processor
        
        # Should not raise
        detector.cleanup()
