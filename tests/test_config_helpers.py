"""Tests for config helper functions."""

import pytest

from video_censor_personal.config import (
    get_audio_remediation_config,
    get_config_value,
    get_sample_rate_from_config,
    get_video_remediation_blank_color,
    get_video_remediation_category_modes,
    get_video_remediation_mode,
    is_audio_remediation_enabled,
    is_skip_chapters_enabled,
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


class TestGetConfigValue:
    """Test get_config_value helper function."""

    def test_get_config_value_simple_key(self, base_config):
        """Get simple configuration value."""
        value = get_config_value(base_config, "version")
        assert value == 1.0

    def test_get_config_value_nested_path(self, base_config):
        """Get nested configuration value using dot notation."""
        value = get_config_value(base_config, "processing.max_workers")
        assert value == 4

    def test_get_config_value_missing_path_returns_default(self, base_config):
        """Get missing path returns default value."""
        value = get_config_value(base_config, "nonexistent.path", default="default_value")
        assert value == "default_value"

    def test_get_config_value_partial_missing_path(self, base_config):
        """Partial missing path returns default."""
        value = get_config_value(base_config, "processing.missing.value", default=None)
        assert value is None

    def test_get_config_value_deeply_nested(self, base_config):
        """Get deeply nested value."""
        value = get_config_value(base_config, "processing.frame_sampling.strategy")
        assert value == "uniform"

    def test_get_config_value_none_default(self, base_config):
        """None is a valid default value."""
        value = get_config_value(base_config, "missing.key")
        assert value is None


class TestGetSampleRateFromConfig:
    """Test get_sample_rate_from_config helper function."""

    def test_get_sample_rate_from_config_custom(self, base_config):
        """Get custom sample rate from config."""
        base_config["processing"]["frame_sampling"]["sample_rate"] = 2.5
        value = get_sample_rate_from_config(base_config)
        assert value == 2.5

    def test_get_sample_rate_from_config_default(self, base_config):
        """Get default sample rate when not configured."""
        del base_config["processing"]["frame_sampling"]["sample_rate"]
        value = get_sample_rate_from_config(base_config)
        assert value == 1.0

    def test_get_sample_rate_from_config_integer(self, base_config):
        """Integer sample rate should work."""
        base_config["processing"]["frame_sampling"]["sample_rate"] = 2
        value = get_sample_rate_from_config(base_config)
        assert value == 2

    def test_get_sample_rate_from_config_zero(self, base_config):
        """Sample rate of zero should be returned as-is."""
        base_config["processing"]["frame_sampling"]["sample_rate"] = 0
        value = get_sample_rate_from_config(base_config)
        assert value == 0


class TestIsSkipChaptersEnabled:
    """Test is_skip_chapters_enabled helper function."""

    def test_is_skip_chapters_enabled_true(self, base_config):
        """Check skip chapters enabled when true."""
        base_config["video"] = {
            "metadata_output": {
                "skip_chapters": {
                    "enabled": True,
                }
            }
        }
        assert is_skip_chapters_enabled(base_config) is True

    def test_is_skip_chapters_enabled_false(self, base_config):
        """Check skip chapters disabled when false."""
        base_config["video"] = {
            "metadata_output": {
                "skip_chapters": {
                    "enabled": False,
                }
            }
        }
        assert is_skip_chapters_enabled(base_config) is False

    def test_is_skip_chapters_enabled_default(self, base_config):
        """Default is False when skip chapters not configured."""
        assert is_skip_chapters_enabled(base_config) is False

    def test_is_skip_chapters_enabled_no_video_section(self, base_config):
        """Default is False when video section missing."""
        assert is_skip_chapters_enabled(base_config) is False


class TestIsAudioRemediationEnabled:
    """Test is_audio_remediation_enabled helper function."""

    def test_is_audio_remediation_enabled_true(self, base_config):
        """Check audio remediation enabled when true."""
        base_config["remediation"] = {
            "audio": {
                "enabled": True,
            }
        }
        assert is_audio_remediation_enabled(base_config) is True

    def test_is_audio_remediation_enabled_false(self, base_config):
        """Check audio remediation disabled when false."""
        base_config["remediation"] = {
            "audio": {
                "enabled": False,
            }
        }
        assert is_audio_remediation_enabled(base_config) is False

    def test_is_audio_remediation_enabled_default(self, base_config):
        """Default is False when audio remediation not configured."""
        assert is_audio_remediation_enabled(base_config) is False


class TestGetAudioRemediationConfig:
    """Test get_audio_remediation_config helper function."""

    def test_get_audio_remediation_config_configured(self, base_config):
        """Get audio remediation config when configured."""
        expected_config = {
            "enabled": True,
            "mode": "silence",
            "categories": ["Profanity"],
        }
        base_config["remediation"] = {
            "audio": expected_config,
        }
        result = get_audio_remediation_config(base_config)
        assert result == expected_config

    def test_get_audio_remediation_config_not_configured(self, base_config):
        """Get empty dict when audio remediation not configured."""
        result = get_audio_remediation_config(base_config)
        assert result == {}

    def test_get_audio_remediation_config_with_bleep_frequency(self, base_config):
        """Get audio remediation config with bleep frequency."""
        expected_config = {
            "enabled": True,
            "mode": "bleep",
            "categories": ["Profanity"],
            "bleep_frequency": 1000,
        }
        base_config["remediation"] = {
            "audio": expected_config,
        }
        result = get_audio_remediation_config(base_config)
        assert result == expected_config


class TestGetVideoRemediationMode:
    """Test get_video_remediation_mode helper function."""

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


class TestGetVideoRemediationBlankColor:
    """Test get_video_remediation_blank_color helper function."""

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

    def test_get_video_remediation_blank_color_three_digit(self, base_config):
        """Get three-digit hex color."""
        base_config["remediation"] = {
            "video": {
                "blank_color": "#F00",
            }
        }
        assert get_video_remediation_blank_color(base_config) == "#F00"


class TestGetVideoRemediationCategoryModes:
    """Test get_video_remediation_category_modes helper function."""

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

    def test_get_video_remediation_category_modes_single(self, base_config):
        """Get single category mode."""
        base_config["remediation"] = {
            "video": {
                "category_modes": {
                    "Nudity": "cut",
                }
            }
        }
        modes = get_video_remediation_category_modes(base_config)
        assert modes == {"Nudity": "cut"}

    def test_get_video_remediation_category_modes_empty(self, base_config):
        """Get empty category modes."""
        base_config["remediation"] = {
            "video": {
                "category_modes": {}
            }
        }
        modes = get_video_remediation_category_modes(base_config)
        assert modes == {}
