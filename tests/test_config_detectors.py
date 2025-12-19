"""Tests for detector section validation."""

import pytest

from video_censor_personal.config import ConfigError, validate_config


@pytest.fixture
def base_config():
    """Fixture with minimal valid configuration."""
    return {
        "detections": {
            "nudity": {
                "enabled": True,
                "sensitivity": 0.7,
                "model": "local",
            },
        },
        "processing": {
            "frame_sampling": {"strategy": "uniform"},
            "segment_merge": {"merge_threshold": 2.0},
            "max_workers": 4,
        },
        "output": {"format": "json"},
    }


class TestDetectorsSectionStructure:
    """Test detectors section structure validation."""

    def test_detectors_section_optional(self, base_config):
        """Detectors section is optional."""
        validate_config(base_config)  # Should not raise

    def test_detectors_section_not_list_raises_error(self, base_config):
        """Detectors field must be a list."""
        base_config["detectors"] = {"type": "llava"}
        with pytest.raises(ConfigError, match="'detectors' field must be a list"):
            validate_config(base_config)

    def test_detector_entry_not_dict_raises_error(self, base_config):
        """Each detector entry must be a dictionary."""
        base_config["detectors"] = ["invalid"]
        with pytest.raises(ConfigError, match="Detector 0 must be a dictionary"):
            validate_config(base_config)


class TestDetectorRequiredFields:
    """Test detector required field validation."""

    def test_detector_missing_type_field_raises_error(self, base_config):
        """Detector must have 'type' field."""
        base_config["detectors"] = [
            {
                "name": "detector1",
                "categories": ["Nudity"],
            }
        ]
        with pytest.raises(ConfigError, match="Detector 0 missing required 'type' field"):
            validate_config(base_config)

    def test_detector_missing_name_field_raises_error(self, base_config):
        """Detector must have 'name' field."""
        base_config["detectors"] = [
            {
                "type": "llava",
                "categories": ["Nudity"],
            }
        ]
        with pytest.raises(ConfigError, match="Detector 0 missing required 'name' field"):
            validate_config(base_config)

    def test_detector_missing_categories_field_raises_error(self, base_config):
        """Detector must have 'categories' field."""
        base_config["detectors"] = [
            {
                "type": "llava",
                "name": "detector1",
            }
        ]
        with pytest.raises(ConfigError, match="Detector 0 missing required 'categories' field"):
            validate_config(base_config)


class TestDetectorCategoriesValidation:
    """Test detector categories field validation."""

    def test_detector_categories_not_list_raises_error(self, base_config):
        """Detector categories must be a list."""
        base_config["detectors"] = [
            {
                "type": "llava",
                "name": "detector1",
                "categories": "Nudity",
            }
        ]
        with pytest.raises(ConfigError, match="'categories' must be a list"):
            validate_config(base_config)

    def test_detector_categories_empty_list_raises_error(self, base_config):
        """Detector must declare at least one category."""
        base_config["detectors"] = [
            {
                "type": "llava",
                "name": "detector1",
                "categories": [],
            }
        ]
        with pytest.raises(ConfigError, match="must declare at least one category"):
            validate_config(base_config)

    def test_detector_categories_single_item(self, base_config):
        """Detector with single category should be valid."""
        base_config["detectors"] = [
            {
                "type": "llava",
                "name": "detector1",
                "categories": ["Nudity"],
            }
        ]
        validate_config(base_config)  # Should not raise

    def test_detector_categories_multiple_items(self, base_config):
        """Detector with multiple categories should be valid."""
        base_config["detectors"] = [
            {
                "type": "llava",
                "name": "detector1",
                "categories": ["Nudity", "Violence"],
            }
        ]
        validate_config(base_config)  # Should not raise


class TestMultipleDetectors:
    """Test configuration with multiple detectors."""

    def test_multiple_detectors_valid(self, base_config):
        """Configuration with multiple detectors."""
        base_config["detectors"] = [
            {
                "type": "llava",
                "name": "visual-detector",
                "categories": ["Nudity", "Violence"],
            },
            {
                "type": "speech-profanity",
                "name": "audio-detector",
                "categories": ["Profanity"],
            }
        ]
        validate_config(base_config)  # Should not raise

    def test_detectors_different_types(self, base_config):
        """Detectors with different types should be valid."""
        base_config["detectors"] = [
            {
                "type": "llava",
                "name": "llava-detector",
                "categories": ["Nudity"],
            },
            {
                "type": "audio-classification",
                "name": "audio-classifier",
                "categories": ["Violence"],
            }
        ]
        validate_config(base_config)  # Should not raise
