"""Tests for video remediation configuration."""

import pytest

from video_censor_personal.config import (
    ConfigError,
    validate_config,
    is_video_remediation_enabled,
    get_video_remediation_mode,
    get_video_remediation_blank_color,
    get_video_remediation_category_modes,
)


@pytest.fixture
def base_config():
    """Fixture with minimal valid configuration."""
    return {
        "version": 1.0,
        "detections": {
            "nudity": {
                "enabled": True,
                "sensitivity": 0.7,
                "model": "local",
            },
        },
        "processing": {
            "frame_sampling": {"strategy": "uniform", "sample_rate": 1.0},
            "segment_merge": {"enabled": True, "merge_threshold": 2.0},
            "max_workers": 4,
        },
        "output": {"format": "json"},
    }


class TestVideoRemediationValidation:
    """Test video remediation configuration validation."""

    def test_video_remediation_enabled_valid(self, base_config):
        """Valid video remediation enabled configuration."""
        base_config["remediation"] = {
            "video": {
                "enabled": True,
                "mode": "blank",
            }
        }
        validate_config(base_config)  # Should not raise

    def test_video_remediation_disabled(self, base_config):
        """Valid video remediation disabled configuration."""
        base_config["remediation"] = {
            "video": {
                "enabled": False,
            }
        }
        validate_config(base_config)  # Should not raise

    def test_remediation_section_not_required(self, base_config):
        """Remediation section is optional."""
        validate_config(base_config)  # Should not raise

    def test_video_editing_section_not_required(self, base_config):
        """video section is optional within remediation."""
        base_config["remediation"] = {}
        validate_config(base_config)  # Should not raise

    def test_remediation_not_dict_raises_error(self, base_config):
        """remediation field must be a dictionary."""
        base_config["remediation"] = ["video"]
        with pytest.raises(ConfigError, match="'remediation' field must be a dictionary"):
            validate_config(base_config)

    def test_video_editing_not_dict_raises_error(self, base_config):
        """video_editing field must be a dictionary."""
        base_config["remediation"] = {
            "video": "enabled"
        }
        with pytest.raises(ConfigError, match="'remediation.video' field must be a dictionary"):
            validate_config(base_config)

    def test_enabled_not_boolean_raises_error(self, base_config):
        """enabled field must be a boolean."""
        base_config["remediation"] = {
            "video": {
                "enabled": "true",
            }
        }
        with pytest.raises(ConfigError, match="'remediation.video.enabled' must be a boolean"):
            validate_config(base_config)


class TestVideoRemediationModeValidation:
    """Test video remediation mode validation."""

    def test_valid_blank_mode(self, base_config):
        """Valid blank mode configuration."""
        base_config["remediation"] = {
            "video": {
                "enabled": True,
                "mode": "blank",
            }
        }
        validate_config(base_config)  # Should not raise

    def test_valid_cut_mode(self, base_config):
        """Valid cut mode configuration."""
        base_config["remediation"] = {
            "video": {
                "enabled": True,
                "mode": "cut",
            }
        }
        validate_config(base_config)  # Should not raise

    def test_invalid_mode_raises_error(self, base_config):
        """Invalid mode raises error."""
        base_config["remediation"] = {
            "video": {
                "enabled": True,
                "mode": "blur",
            }
        }
        with pytest.raises(ConfigError, match=r"must be one of \{.*blank.*\}.*got 'blur'"):
            validate_config(base_config)

    def test_mode_not_string_raises_error(self, base_config):
        """mode field must be a string."""
        base_config["remediation"] = {
            "video": {
                "enabled": True,
                "mode": True,
            }
        }
        with pytest.raises(ConfigError, match="'remediation.video.mode' must be a string"):
            validate_config(base_config)


class TestVideoRemediationBlankColorValidation:
    """Test video remediation blank_color validation."""

    def test_valid_hex_color_six_digits(self, base_config):
        """Valid 6-digit hex color."""
        base_config["remediation"] = {
            "video": {
                "enabled": True,
                "blank_color": "#000000",
            }
        }
        validate_config(base_config)  # Should not raise

    def test_valid_hex_color_three_digits(self, base_config):
        """Valid 3-digit hex color."""
        base_config["remediation"] = {
            "video": {
                "enabled": True,
                "blank_color": "#000",
            }
        }
        validate_config(base_config)  # Should not raise

    def test_valid_hex_color_uppercase(self, base_config):
        """Valid uppercase hex color."""
        base_config["remediation"] = {
            "video": {
                "enabled": True,
                "blank_color": "#FF0000",
            }
        }
        validate_config(base_config)  # Should not raise

    def test_invalid_color_no_hash_raises_error(self, base_config):
        """Color without # raises error."""
        base_config["remediation"] = {
            "video": {
                "enabled": True,
                "blank_color": "000000",
            }
        }
        with pytest.raises(ConfigError, match="must be a valid hex color"):
            validate_config(base_config)

    def test_invalid_color_wrong_length_raises_error(self, base_config):
        """Color with wrong length raises error."""
        base_config["remediation"] = {
            "video": {
                "enabled": True,
                "blank_color": "#00",
            }
        }
        with pytest.raises(ConfigError, match="must be a valid hex color"):
            validate_config(base_config)

    def test_invalid_color_non_hex_chars_raises_error(self, base_config):
        """Color with non-hex characters raises error."""
        base_config["remediation"] = {
            "video": {
                "enabled": True,
                "blank_color": "#GGGGGG",
            }
        }
        with pytest.raises(ConfigError, match="must be a valid hex color"):
            validate_config(base_config)

    def test_blank_color_not_string_raises_error(self, base_config):
        """blank_color field must be a string."""
        base_config["remediation"] = {
            "video": {
                "enabled": True,
                "blank_color": 0,
            }
        }
        with pytest.raises(ConfigError, match="'remediation.video.blank_color' must be a string"):
            validate_config(base_config)


class TestVideoRemediationCategoryModesValidation:
    """Test video remediation category_modes validation."""

    def test_valid_category_modes(self, base_config):
        """Valid category_modes configuration."""
        base_config["remediation"] = {
            "video": {
                "enabled": True,
                "category_modes": {
                    "Nudity": "cut",
                    "Violence": "blank",
                }
            }
        }
        validate_config(base_config)  # Should not raise

    def test_empty_category_modes(self, base_config):
        """Empty category_modes is valid."""
        base_config["remediation"] = {
            "video": {
                "enabled": True,
                "category_modes": {}
            }
        }
        validate_config(base_config)  # Should not raise

    def test_category_modes_not_dict_raises_error(self, base_config):
        """category_modes field must be a dictionary."""
        base_config["remediation"] = {
            "video": {
                "enabled": True,
                "category_modes": ["Nudity", "Violence"]
            }
        }
        with pytest.raises(ConfigError, match="'remediation.video.category_modes' must be a dictionary"):
            validate_config(base_config)

    def test_category_mode_invalid_value_raises_error(self, base_config):
        """Invalid mode value in category_modes raises error."""
        base_config["remediation"] = {
            "video": {
                "enabled": True,
                "category_modes": {
                    "Nudity": "blur",
                }
            }
        }
        with pytest.raises(ConfigError, match=r"must be one of \{.*blank.*\}.*got 'blur'"):
            validate_config(base_config)

    def test_category_mode_not_string_raises_error(self, base_config):
        """category_modes value must be a string."""
        base_config["remediation"] = {
            "video": {
                "enabled": True,
                "category_modes": {
                    "Nudity": True,
                }
            }
        }
        with pytest.raises(ConfigError, match="must be a string"):
            validate_config(base_config)


class TestVideoRemediationConfigHelpers:
    """Test helper functions for video remediation configuration."""

    def test_is_video_remediation_enabled_true(self, base_config):
        """Check if video remediation is enabled."""
        base_config["remediation"] = {
            "video": {
                "enabled": True,
            }
        }
        assert is_video_remediation_enabled(base_config) is True

    def test_is_video_remediation_enabled_false(self, base_config):
        """Check if video remediation is disabled."""
        base_config["remediation"] = {
            "video": {
                "enabled": False,
            }
        }
        assert is_video_remediation_enabled(base_config) is False

    def test_is_video_remediation_enabled_default(self, base_config):
        """Default is False when not configured."""
        assert is_video_remediation_enabled(base_config) is False

    def test_get_video_remediation_mode_blank(self, base_config):
        """Get blank mode from configuration."""
        base_config["remediation"] = {
            "video": {
                "mode": "blank",
            }
        }
        assert get_video_remediation_mode(base_config) == "blank"

    def test_get_video_remediation_mode_cut(self, base_config):
        """Get cut mode from configuration."""
        base_config["remediation"] = {
            "video": {
                "mode": "cut",
            }
        }
        assert get_video_remediation_mode(base_config) == "cut"

    def test_get_video_remediation_mode_default(self, base_config):
        """Default mode is blank when not configured."""
        assert get_video_remediation_mode(base_config) == "blank"

    def test_get_video_remediation_blank_color_custom(self, base_config):
        """Get custom blank color from configuration."""
        base_config["remediation"] = {
            "video": {
                "blank_color": "#FF0000",
            }
        }
        assert get_video_remediation_blank_color(base_config) == "#FF0000"

    def test_get_video_remediation_blank_color_default(self, base_config):
        """Default blank color is black when not configured."""
        assert get_video_remediation_blank_color(base_config) == "#000000"

    def test_get_video_remediation_category_modes_configured(self, base_config):
        """Get category modes from configuration."""
        base_config["remediation"] = {
            "video": {
                "category_modes": {
                    "Nudity": "cut",
                    "Violence": "blank",
                }
            }
        }
        category_modes = get_video_remediation_category_modes(base_config)
        assert category_modes == {"Nudity": "cut", "Violence": "blank"}

    def test_get_video_remediation_category_modes_default(self, base_config):
        """Default category modes is empty dict when not configured."""
        assert get_video_remediation_category_modes(base_config) == {}


class TestVideoRemediationCompleteConfig:
    """Test complete video remediation configuration scenarios."""

    def test_complete_video_remediation_config_blank_mode(self, base_config):
        """Complete configuration with blank mode and all options."""
        base_config["remediation"] = {
            "video": {
                "enabled": True,
                "mode": "blank",
                "blank_color": "#FF0000",
                "category_modes": {
                    "Nudity": "cut",
                    "Violence": "blank",
                    "Profanity": "cut",
                }
            }
        }
        validate_config(base_config)  # Should not raise
        
        assert is_video_remediation_enabled(base_config) is True
        assert get_video_remediation_mode(base_config) == "blank"
        assert get_video_remediation_blank_color(base_config) == "#FF0000"
        assert get_video_remediation_category_modes(base_config) == {
            "Nudity": "cut",
            "Violence": "blank",
            "Profanity": "cut",
        }

    def test_complete_video_remediation_config_cut_mode(self, base_config):
        """Complete configuration with cut mode."""
        base_config["remediation"] = {
            "video": {
                "enabled": True,
                "mode": "cut",
                "category_modes": {
                    "Nudity": "blank",
                }
            }
        }
        validate_config(base_config)  # Should not raise
        
        assert is_video_remediation_enabled(base_config) is True
        assert get_video_remediation_mode(base_config) == "cut"
        assert get_video_remediation_category_modes(base_config) == {
            "Nudity": "blank",
        }

    def test_minimal_video_remediation_config(self, base_config):
        """Minimal valid video remediation configuration."""
        base_config["remediation"] = {
            "video": {
                "enabled": True,
            }
        }
        validate_config(base_config)  # Should not raise
        
        # Check defaults
        assert is_video_remediation_enabled(base_config) is True
        assert get_video_remediation_mode(base_config) == "blank"
        assert get_video_remediation_blank_color(base_config) == "#000000"
        assert get_video_remediation_category_modes(base_config) == {}
