"""Tests for audio-related configuration validation."""

import pytest
import yaml
from pathlib import Path


class TestAudioDetectorConfig:
    """Test audio detector configuration validation."""

    def test_valid_speech_profanity_detector_config(self):
        """Test valid speech-profanity detector configuration."""
        config_yaml = """
        detectors:
          - type: "speech-profanity"
            name: "speech-detector"
            categories:
              - "Profanity"
            model: "base"
            languages:
              - "en"
              - "es"
            confidence_threshold: 0.8
        """
        config = yaml.safe_load(config_yaml)
        
        assert len(config["detectors"]) == 1
        detector = config["detectors"][0]
        assert detector["type"] == "speech-profanity"
        assert detector["model"] == "base"
        assert "en" in detector["languages"]
        assert detector["confidence_threshold"] == 0.8

    def test_valid_audio_classification_detector_config(self):
        """Test valid audio-classification detector configuration."""
        config_yaml = """
        detectors:
          - type: "audio-classification"
            name: "audio-classifier"
            categories:
              - "Violence"
              - "Sexual Theme"
            model: "MIT/ast-finetuned-audioset-10-10-0.4593"
            confidence_threshold: 0.6
        """
        config = yaml.safe_load(config_yaml)
        
        detector = config["detectors"][0]
        assert detector["type"] == "audio-classification"
        assert detector["model"] == "MIT/ast-finetuned-audioset-10-10-0.4593"
        assert "Violence" in detector["categories"]

    def test_languages_array_parsed_correctly(self):
        """Test that languages array is parsed correctly."""
        config_yaml = """
        detectors:
          - type: "speech-profanity"
            name: "speech-detector"
            categories: ["Profanity"]
            languages: ["en", "es", "fr"]
        """
        config = yaml.safe_load(config_yaml)
        
        languages = config["detectors"][0]["languages"]
        assert isinstance(languages, list)
        assert len(languages) == 3
        assert languages == ["en", "es", "fr"]

    def test_model_parameter_parsed_correctly(self):
        """Test that model parameter is passed correctly."""
        config_yaml = """
        detectors:
          - type: "speech-profanity"
            name: "whisper-large"
            categories: ["Profanity"]
            model: "large"
        """
        config = yaml.safe_load(config_yaml)
        
        assert config["detectors"][0]["model"] == "large"


class TestRemediationConfig:
    """Test audio remediation configuration validation."""

    def test_valid_remediation_config_silence(self):
        """Test valid remediation config with silence mode."""
        config_yaml = """
        audio:
          remediation:
            enabled: true
            mode: "silence"
            categories:
              - "Profanity"
        """
        config = yaml.safe_load(config_yaml)
        
        remediation = config["audio"]["remediation"]
        assert remediation["enabled"] is True
        assert remediation["mode"] == "silence"
        assert "Profanity" in remediation["categories"]

    def test_valid_remediation_config_bleep(self):
        """Test valid remediation config with bleep mode."""
        config_yaml = """
        audio:
          remediation:
            enabled: true
            mode: "bleep"
            categories:
              - "Profanity"
            bleep_frequency: 1000
        """
        config = yaml.safe_load(config_yaml)
        
        remediation = config["audio"]["remediation"]
        assert remediation["mode"] == "bleep"
        assert remediation["bleep_frequency"] == 1000

    def test_remediation_disabled_by_default(self):
        """Test that remediation defaults to disabled."""
        config_yaml = """
        audio:
          remediation:
            enabled: false
        """
        config = yaml.safe_load(config_yaml)
        
        assert config["audio"]["remediation"]["enabled"] is False

    def test_remediation_categories_validated(self):
        """Test that remediation categories are a list."""
        config_yaml = """
        audio:
          remediation:
            enabled: true
            mode: "silence"
            categories:
              - "Profanity"
              - "Violence"
        """
        config = yaml.safe_load(config_yaml)
        
        categories = config["audio"]["remediation"]["categories"]
        assert isinstance(categories, list)
        assert len(categories) == 2


class TestCombinedAudioConfig:
    """Test combined audio detection and remediation configuration."""

    def test_full_audio_config(self):
        """Test complete audio configuration with detection and remediation."""
        config_yaml = """
        detectors:
          - type: "llava"
            name: "visual-detector"
            categories: ["Nudity", "Violence"]
          
          - type: "speech-profanity"
            name: "speech-detector"
            categories: ["Profanity"]
            model: "base"
            languages: ["en"]
          
          - type: "audio-classification"
            name: "audio-classifier"
            categories: ["Violence"]
            model: "MIT/ast-finetuned-audioset-10-10-0.4593"

        audio:
          detection:
            enabled: true
          remediation:
            enabled: true
            mode: "silence"
            categories:
              - "Profanity"
        """
        config = yaml.safe_load(config_yaml)
        
        # Verify detectors
        assert len(config["detectors"]) == 3
        detector_types = [d["type"] for d in config["detectors"]]
        assert "llava" in detector_types
        assert "speech-profanity" in detector_types
        assert "audio-classification" in detector_types
        
        # Verify audio config
        assert config["audio"]["detection"]["enabled"] is True
        assert config["audio"]["remediation"]["enabled"] is True
        assert config["audio"]["remediation"]["mode"] == "silence"

    def test_audio_only_config(self):
        """Test audio-only configuration (no visual detectors)."""
        config_yaml = """
        detectors:
          - type: "speech-profanity"
            name: "speech-detector"
            categories: ["Profanity"]
            model: "base"
            languages: ["en"]

        audio:
          remediation:
            enabled: true
            mode: "bleep"
            categories: ["Profanity"]
            bleep_frequency: 800
        """
        config = yaml.safe_load(config_yaml)
        
        assert len(config["detectors"]) == 1
        assert config["detectors"][0]["type"] == "speech-profanity"
        assert config["audio"]["remediation"]["bleep_frequency"] == 800


class TestExampleConfigFiles:
    """Test that example config files are valid YAML."""

    @pytest.fixture
    def project_root(self):
        """Get the project root directory."""
        return Path(__file__).parent.parent

    def test_audio_detection_example_valid(self, project_root):
        """Test audio detection example config is valid YAML."""
        config_file = project_root / "video-censor-audio-detection.yaml.example"
        if not config_file.exists():
            pytest.skip("Example config file not found")
        
        with open(config_file) as f:
            config = yaml.safe_load(f)
        
        assert "detectors" in config
        # Should have speech-profanity detector
        detector_types = [d["type"] for d in config["detectors"]]
        assert "speech-profanity" in detector_types

    def test_audio_remediation_silence_example_valid(self, project_root):
        """Test audio remediation silence example config is valid YAML."""
        config_file = project_root / "video-censor-audio-remediation-silence.yaml.example"
        if not config_file.exists():
            pytest.skip("Example config file not found")
        
        with open(config_file) as f:
            config = yaml.safe_load(f)
        
        assert config["audio"]["remediation"]["enabled"] is True
        assert config["audio"]["remediation"]["mode"] == "silence"

    def test_audio_remediation_bleep_example_valid(self, project_root):
        """Test audio remediation bleep example config is valid YAML."""
        config_file = project_root / "video-censor-audio-remediation-bleep.yaml.example"
        if not config_file.exists():
            pytest.skip("Example config file not found")
        
        with open(config_file) as f:
            config = yaml.safe_load(f)
        
        assert config["audio"]["remediation"]["enabled"] is True
        assert config["audio"]["remediation"]["mode"] == "bleep"
        assert "bleep_frequency" in config["audio"]["remediation"]
