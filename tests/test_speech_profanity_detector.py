"""Tests for speech profanity detection module."""

from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import numpy as np
import pytest

# Skip all tests if transformers is not installed
pytest.importorskip("transformers", reason="transformers not installed")

from video_censor_personal.speech_profanity_detector import SpeechProfanityDetector


class TestSpeechProfanityDetectorInitialization:
    """Test SpeechProfanityDetector initialization."""

    @patch("video_censor_personal.speech_profanity_detector.get_device", return_value="cpu")
    @patch("transformers.pipeline")
    def test_init_with_default_config(self, mock_pipeline, mock_device):
        """Test initialization with default configuration."""
        mock_pipeline.return_value = MagicMock()
        
        config = {
            "name": "test-detector",
            "categories": ["Profanity"],
        }
        
        detector = SpeechProfanityDetector(config)
        
        assert detector.model_size == "base"
        assert detector.languages == ["en"]
        assert detector.confidence_threshold == 0.8
        assert detector.device == "cpu"

    @patch("video_censor_personal.speech_profanity_detector.get_device", return_value="cpu")
    @patch("transformers.pipeline")
    def test_init_with_custom_config(self, mock_pipeline, mock_device):
        """Test initialization with custom configuration."""
        mock_pipeline.return_value = MagicMock()
        
        config = {
            "name": "test-detector",
            "categories": ["Profanity"],
            "model": "large",
            "languages": ["en", "es"],
            "confidence_threshold": 0.9,
        }
        
        detector = SpeechProfanityDetector(config)
        
        assert detector.model_size == "large"
        assert detector.languages == ["en", "es"]
        assert detector.confidence_threshold == 0.9

    @patch("video_censor_personal.speech_profanity_detector.get_device", return_value="cpu")
    @patch("transformers.pipeline")
    def test_init_requires_profanity_category(self, mock_pipeline, mock_device):
        """Test that initialization requires Profanity category."""
        mock_pipeline.return_value = MagicMock()
        
        config = {
            "name": "test-detector",
            "categories": ["Violence"],  # Missing Profanity
        }
        
        with pytest.raises(ValueError, match="must include 'Profanity'"):
            SpeechProfanityDetector(config)

    @patch("video_censor_personal.speech_profanity_detector.get_device", return_value="cpu")
    @patch("transformers.pipeline")
    def test_init_requires_languages(self, mock_pipeline, mock_device):
        """Test that initialization requires at least one language."""
        mock_pipeline.return_value = MagicMock()
        
        config = {
            "name": "test-detector",
            "categories": ["Profanity"],
            "languages": [],
        }
        
        with pytest.raises(ValueError, match="At least one language"):
            SpeechProfanityDetector(config)


class TestProfanityKeywordLoading:
    """Test profanity keyword loading."""

    @patch("video_censor_personal.speech_profanity_detector.get_device", return_value="cpu")
    @patch("transformers.pipeline")
    def test_load_profanity_keywords_english(self, mock_pipeline, mock_device):
        """Test loading English profanity keywords."""
        mock_pipeline.return_value = MagicMock()
        
        config = {
            "name": "test-detector",
            "categories": ["Profanity"],
            "languages": ["en"],
        }
        
        detector = SpeechProfanityDetector(config)
        
        # Should have loaded English keywords
        assert "en" in detector.keywords
        # Keywords file should exist and have content
        # (exact keywords depend on profanity_en.txt file)

    @patch("video_censor_personal.speech_profanity_detector.get_device", return_value="cpu")
    @patch("transformers.pipeline")
    def test_load_keywords_missing_language(self, mock_pipeline, mock_device):
        """Test loading keywords for missing language file."""
        mock_pipeline.return_value = MagicMock()
        
        config = {
            "name": "test-detector",
            "categories": ["Profanity"],
            "languages": ["xyz"],  # Non-existent language
        }
        
        detector = SpeechProfanityDetector(config)
        
        # Should have empty set for missing language
        assert detector.keywords.get("xyz") == set()


class TestProfanityDetection:
    """Test profanity detection functionality."""

    @patch("video_censor_personal.speech_profanity_detector.get_device", return_value="cpu")
    @patch("transformers.pipeline")
    def test_detect_returns_empty_when_no_audio(self, mock_pipeline, mock_device):
        """Test detection returns empty when no audio provided."""
        mock_pipeline.return_value = MagicMock()
        
        config = {
            "name": "test-detector",
            "categories": ["Profanity"],
        }
        
        detector = SpeechProfanityDetector(config)
        results = detector.detect(frame_data=np.zeros((100, 100, 3)), audio_data=None)
        
        assert results == []

    @patch("video_censor_personal.speech_profanity_detector.get_device", return_value="cpu")
    @patch("transformers.pipeline")
    def test_detect_finds_profanity_keyword(self, mock_pipeline, mock_device):
        """Test detection finds profanity in transcription."""
        mock_pipe = MagicMock()
        mock_pipe.return_value = {"text": "this is a test with damn word"}
        mock_pipeline.return_value = mock_pipe
        
        config = {
            "name": "test-detector",
            "categories": ["Profanity"],
        }
        
        detector = SpeechProfanityDetector(config)
        # Manually set a known keyword
        detector.keywords = {"en": {"damn"}}
        
        audio_data = np.random.randn(16000).astype(np.float32)
        results = detector.detect(audio_data=audio_data)
        
        assert len(results) == 1
        assert results[0].label == "Profanity"
        assert results[0].confidence == 0.95
        assert "damn" in results[0].reasoning.lower()

    @patch("video_censor_personal.speech_profanity_detector.get_device", return_value="cpu")
    @patch("transformers.pipeline")
    def test_detect_case_insensitive(self, mock_pipeline, mock_device):
        """Test detection is case-insensitive."""
        mock_pipe = MagicMock()
        mock_pipe.return_value = {"text": "This has DAMN word"}
        mock_pipeline.return_value = mock_pipe
        
        config = {
            "name": "test-detector",
            "categories": ["Profanity"],
        }
        
        detector = SpeechProfanityDetector(config)
        detector.keywords = {"en": {"damn"}}
        
        audio_data = np.random.randn(16000).astype(np.float32)
        results = detector.detect(audio_data=audio_data)
        
        assert len(results) == 1

    @patch("video_censor_personal.speech_profanity_detector.get_device", return_value="cpu")
    @patch("transformers.pipeline")
    def test_detect_no_match(self, mock_pipeline, mock_device):
        """Test detection returns empty when no profanity found."""
        mock_pipe = MagicMock()
        mock_pipe.return_value = {"text": "this is clean text"}
        mock_pipeline.return_value = mock_pipe
        
        config = {
            "name": "test-detector",
            "categories": ["Profanity"],
        }
        
        detector = SpeechProfanityDetector(config)
        detector.keywords = {"en": {"badword"}}
        
        audio_data = np.random.randn(16000).astype(np.float32)
        results = detector.detect(audio_data=audio_data)
        
        assert results == []

    @patch("video_censor_personal.speech_profanity_detector.get_device", return_value="cpu")
    @patch("transformers.pipeline")
    def test_detect_multiple_keywords(self, mock_pipeline, mock_device):
        """Test detection finds multiple profanity keywords."""
        mock_pipe = MagicMock()
        mock_pipe.return_value = {"text": "word1 here and word2 there"}
        mock_pipeline.return_value = mock_pipe
        
        config = {
            "name": "test-detector",
            "categories": ["Profanity"],
        }
        
        detector = SpeechProfanityDetector(config)
        detector.keywords = {"en": {"word1", "word2"}}
        
        audio_data = np.random.randn(16000).astype(np.float32)
        results = detector.detect(audio_data=audio_data)
        
        assert len(results) == 2

    @patch("video_censor_personal.speech_profanity_detector.get_device", return_value="cpu")
    @patch("transformers.pipeline")
    def test_detect_empty_transcription(self, mock_pipeline, mock_device):
        """Test detection handles empty transcription."""
        mock_pipe = MagicMock()
        mock_pipe.return_value = {"text": ""}
        mock_pipeline.return_value = mock_pipe
        
        config = {
            "name": "test-detector",
            "categories": ["Profanity"],
        }
        
        detector = SpeechProfanityDetector(config)
        
        audio_data = np.random.randn(16000).astype(np.float32)
        results = detector.detect(audio_data=audio_data)
        
        assert results == []

    @patch("video_censor_personal.speech_profanity_detector.get_device", return_value="cpu")
    @patch("transformers.pipeline")
    def test_detect_handles_transcription_error(self, mock_pipeline, mock_device):
        """Test detection handles transcription errors gracefully."""
        mock_pipe = MagicMock()
        mock_pipe.side_effect = Exception("Whisper error")
        mock_pipeline.return_value = mock_pipe
        
        config = {
            "name": "test-detector",
            "categories": ["Profanity"],
        }
        
        detector = SpeechProfanityDetector(config)
        
        audio_data = np.random.randn(16000).astype(np.float32)
        results = detector.detect(audio_data=audio_data)
        
        # Should return empty list on error, not raise
        assert results == []


class TestMultiLanguageSupport:
    """Test multi-language profanity detection."""

    @patch("video_censor_personal.speech_profanity_detector.get_device", return_value="cpu")
    @patch("transformers.pipeline")
    def test_detect_multi_language_keywords(self, mock_pipeline, mock_device):
        """Test detection across multiple languages."""
        mock_pipe = MagicMock()
        mock_pipe.return_value = {"text": "english word1 spanish palabra1"}
        mock_pipeline.return_value = mock_pipe
        
        config = {
            "name": "test-detector",
            "categories": ["Profanity"],
            "languages": ["en", "es"],
        }
        
        detector = SpeechProfanityDetector(config)
        detector.keywords = {
            "en": {"word1"},
            "es": {"palabra1"},
        }
        
        audio_data = np.random.randn(16000).astype(np.float32)
        results = detector.detect(audio_data=audio_data)
        
        assert len(results) == 2


class TestCleanup:
    """Test resource cleanup."""

    @patch("video_censor_personal.speech_profanity_detector.get_device", return_value="cpu")
    @patch("transformers.pipeline")
    def test_cleanup_releases_model(self, mock_pipeline, mock_device):
        """Test cleanup releases Whisper model."""
        mock_pipeline.return_value = MagicMock()
        
        config = {
            "name": "test-detector",
            "categories": ["Profanity"],
        }
        
        detector = SpeechProfanityDetector(config)
        assert hasattr(detector, "pipeline")
        
        detector.cleanup()
        
        assert not hasattr(detector, "pipeline")

    @patch("video_censor_personal.speech_profanity_detector.get_device", return_value="cpu")
    @patch("transformers.pipeline")
    def test_cleanup_handles_missing_pipeline(self, mock_pipeline, mock_device):
        """Test cleanup handles case where pipeline doesn't exist."""
        mock_pipeline.return_value = MagicMock()
        
        config = {
            "name": "test-detector",
            "categories": ["Profanity"],
        }
        
        detector = SpeechProfanityDetector(config)
        del detector.pipeline
        
        # Should not raise
        detector.cleanup()
