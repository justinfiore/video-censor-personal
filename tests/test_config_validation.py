"""Comprehensive tests for config validation edge cases."""

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


class TestDetectionValidationEdgeCases:
    """Test edge cases in detection validation."""

    def test_detection_category_is_not_dict(self, base_config):
        """Detection category must be a dict."""
        base_config["detections"]["nudity"] = "invalid"
        with pytest.raises(ConfigError, match="must be a dictionary"):
            validate_config(base_config)

    def test_detection_sensitivity_is_string_number(self, base_config):
        """Detection sensitivity as string should fail."""
        base_config["detections"]["nudity"]["sensitivity"] = "0.5"
        with pytest.raises(ConfigError, match="must be a number"):
            validate_config(base_config)

    def test_detection_sensitivity_is_list(self, base_config):
        """Detection sensitivity as list should fail."""
        base_config["detections"]["nudity"]["sensitivity"] = [0.5]
        with pytest.raises(ConfigError, match="must be a number"):
            validate_config(base_config)

    def test_detection_enabled_is_string(self, base_config):
        """Detection enabled as string should fail."""
        base_config["detections"]["nudity"]["enabled"] = "true"
        with pytest.raises(ConfigError, match="must be boolean"):
            validate_config(base_config)

    def test_detection_model_is_number(self, base_config):
        """Detection model as number should fail."""
        base_config["detections"]["nudity"]["model"] = 123
        with pytest.raises(ConfigError, match="must be a string"):
            validate_config(base_config)


class TestVideoSectionValidationEdgeCases:
    """Test edge cases in video section validation."""

    def test_video_section_optional(self, base_config):
        """Video section is optional."""
        validate_config(base_config)  # Should not raise

    def test_video_section_not_dict_raises_error(self, base_config):
        """Video field must be a dictionary."""
        base_config["video"] = ["metadata"]
        with pytest.raises(ConfigError, match="'video' field must be a dictionary"):
            validate_config(base_config)

    def test_video_metadata_output_optional(self, base_config):
        """metadata_output in video section is optional."""
        base_config["video"] = {}
        validate_config(base_config)  # Should not raise

    def test_video_metadata_output_not_dict_raises_error(self, base_config):
        """metadata_output field must be a dictionary."""
        base_config["video"] = {
            "metadata_output": "invalid",
        }
        with pytest.raises(ConfigError, match="'video.metadata_output' field must be a dictionary"):
            validate_config(base_config)

    def test_video_skip_chapters_optional(self, base_config):
        """skip_chapters in metadata_output is optional."""
        base_config["video"] = {
            "metadata_output": {},
        }
        validate_config(base_config)  # Should not raise

    def test_video_skip_chapters_not_dict_raises_error(self, base_config):
        """skip_chapters field must be a dictionary."""
        base_config["video"] = {
            "metadata_output": {
                "skip_chapters": "invalid",
            }
        }
        with pytest.raises(ConfigError, match="'video.metadata_output.skip_chapters' field must be a dictionary"):
            validate_config(base_config)

    def test_video_skip_chapters_enabled_not_bool_raises_error(self, base_config):
        """skip_chapters.enabled must be a boolean."""
        base_config["video"] = {
            "metadata_output": {
                "skip_chapters": {
                    "enabled": "true",
                }
            }
        }
        with pytest.raises(ConfigError, match="'video.metadata_output.skip_chapters.enabled' must be a boolean"):
            validate_config(base_config)

    def test_video_skip_chapters_name_format_not_string_raises_error(self, base_config):
        """skip_chapters.name_format must be a string."""
        base_config["video"] = {
            "metadata_output": {
                "skip_chapters": {
                    "name_format": 123,
                }
            }
        }
        with pytest.raises(ConfigError, match="'video.metadata_output.skip_chapters.name_format' must be a string"):
            validate_config(base_config)

    def test_valid_video_skip_chapters_configuration(self, base_config):
        """Valid video skip_chapters configuration should pass."""
        base_config["video"] = {
            "metadata_output": {
                "skip_chapters": {
                    "enabled": True,
                    "name_format": "Chapter {number}",
                }
            }
        }
        validate_config(base_config)  # Should not raise


class TestBlankColorValidationEdgeCases:
    """Test blank color validation edge cases."""

    def test_blank_color_empty_string(self, base_config):
        """Blank color empty string should fail."""
        base_config["remediation"] = {
            "video": {
                "blank_color": "",
            }
        }
        with pytest.raises(ConfigError, match="must be a valid hex color"):
            validate_config(base_config)

    def test_blank_color_only_hash(self, base_config):
        """Blank color with only hash should fail."""
        base_config["remediation"] = {
            "video": {
                "blank_color": "#",
            }
        }
        with pytest.raises(ConfigError, match="must be a valid hex color"):
            validate_config(base_config)

    def test_blank_color_five_digit_hex(self, base_config):
        """Blank color with 5 digits should fail."""
        base_config["remediation"] = {
            "video": {
                "blank_color": "#00000",
            }
        }
        with pytest.raises(ConfigError, match="must be a valid hex color"):
            validate_config(base_config)

    def test_blank_color_eight_digit_hex(self, base_config):
        """Blank color with 8 digits should fail."""
        base_config["remediation"] = {
            "video": {
                "blank_color": "#00000000",
            }
        }
        with pytest.raises(ConfigError, match="must be a valid hex color"):
            validate_config(base_config)

    def test_blank_color_lowercase_hex_valid(self, base_config):
        """Blank color with lowercase hex digits should be valid."""
        base_config["remediation"] = {
            "video": {
                "blank_color": "#abcdef",
            }
        }
        validate_config(base_config)  # Should not raise

    def test_blank_color_uppercase_hex_valid(self, base_config):
        """Blank color with uppercase hex digits should be valid."""
        base_config["remediation"] = {
            "video": {
                "blank_color": "#AABBCC",
            }
        }
        validate_config(base_config)  # Should not raise

    def test_blank_color_mixed_case_hex_valid(self, base_config):
        """Blank color with mixed case hex digits should be valid."""
        base_config["remediation"] = {
            "video": {
                "blank_color": "#FfFfFf",
            }
        }
        validate_config(base_config)  # Should not raise

    def test_blank_color_three_digit_black(self, base_config):
        """Three-digit black color should be valid."""
        base_config["remediation"] = {
            "video": {
                "blank_color": "#000",
            }
        }
        validate_config(base_config)  # Should not raise

    def test_blank_color_three_digit_white(self, base_config):
        """Three-digit white color should be valid."""
        base_config["remediation"] = {
            "video": {
                "blank_color": "#FFF",
            }
        }
        validate_config(base_config)  # Should not raise

    def test_blank_color_with_numbers_only(self, base_config):
        """Blank color with only numbers should be valid."""
        base_config["remediation"] = {
            "video": {
                "blank_color": "#123456",
            }
        }
        validate_config(base_config)  # Should not raise

    def test_blank_color_invalid_hex_char_g(self, base_config):
        """Blank color with invalid hex char 'G' should fail."""
        base_config["remediation"] = {
            "video": {
                "blank_color": "#GGGGGG",
            }
        }
        with pytest.raises(ConfigError, match="must be a valid hex color"):
            validate_config(base_config)

    def test_blank_color_invalid_hex_char_z(self, base_config):
        """Blank color with invalid hex char 'Z' should fail."""
        base_config["remediation"] = {
            "video": {
                "blank_color": "#ZZZZZZ",
            }
        }
        with pytest.raises(ConfigError, match="must be a valid hex color"):
            validate_config(base_config)

    def test_blank_color_special_character(self, base_config):
        """Blank color with special character should fail."""
        base_config["remediation"] = {
            "video": {
                "blank_color": "#00!000",
            }
        }
        with pytest.raises(ConfigError, match="must be a valid hex color"):
            validate_config(base_config)

    def test_blank_color_with_space(self, base_config):
        """Blank color with space should fail."""
        base_config["remediation"] = {
            "video": {
                "blank_color": "#0 0000",
            }
        }
        with pytest.raises(ConfigError, match="must be a valid hex color"):
            validate_config(base_config)


class TestVideoRemediationModeValidation:
    """Test video remediation mode validation."""

    def test_video_mode_blank(self, base_config):
        """Video mode 'blank' should be valid."""
        base_config["remediation"] = {
            "video": {
                "mode": "blank",
            }
        }
        validate_config(base_config)  # Should not raise

    def test_video_mode_cut(self, base_config):
        """Video mode 'cut' should be valid."""
        base_config["remediation"] = {
            "video": {
                "mode": "cut",
            }
        }
        validate_config(base_config)  # Should not raise

    def test_video_mode_pixelate_invalid(self, base_config):
        """Video mode 'pixelate' should be invalid."""
        base_config["remediation"] = {
            "video": {
                "mode": "pixelate",
            }
        }
        with pytest.raises(ConfigError, match="must be one of"):
            validate_config(base_config)

    def test_video_mode_blur_invalid(self, base_config):
        """Video mode 'blur' should be invalid."""
        base_config["remediation"] = {
            "video": {
                "mode": "blur",
            }
        }
        with pytest.raises(ConfigError, match="must be one of"):
            validate_config(base_config)

    def test_video_mode_case_sensitive(self, base_config):
        """Video mode should be case-sensitive."""
        base_config["remediation"] = {
            "video": {
                "mode": "Blank",  # Wrong case
            }
        }
        with pytest.raises(ConfigError, match="must be one of"):
            validate_config(base_config)


class TestAudioRemediationModeValidation:
    """Test audio remediation mode validation."""

    def test_audio_mode_silence(self, base_config):
        """Audio mode 'silence' should be valid."""
        base_config["remediation"] = {
            "audio": {
                "mode": "silence",
            }
        }
        validate_config(base_config)  # Should not raise

    def test_audio_mode_bleep(self, base_config):
        """Audio mode 'bleep' should be valid."""
        base_config["remediation"] = {
            "audio": {
                "mode": "bleep",
            }
        }
        validate_config(base_config)  # Should not raise

    def test_audio_mode_fade_invalid(self, base_config):
        """Audio mode 'fade' should be invalid."""
        base_config["remediation"] = {
            "audio": {
                "mode": "fade",
            }
        }
        with pytest.raises(ConfigError, match="must be one of"):
            validate_config(base_config)

    def test_audio_mode_case_sensitive(self, base_config):
        """Audio mode should be case-sensitive."""
        base_config["remediation"] = {
            "audio": {
                "mode": "Silence",  # Wrong case
            }
        }
        with pytest.raises(ConfigError, match="must be one of"):
            validate_config(base_config)


class TestCategoryModeValidation:
    """Test category mode validation in detail."""

    def test_category_mode_valid_blank(self, base_config):
        """Category mode 'blank' should be valid."""
        base_config["remediation"] = {
            "video": {
                "category_modes": {
                    "Nudity": "blank",
                }
            }
        }
        validate_config(base_config)  # Should not raise

    def test_category_mode_valid_cut(self, base_config):
        """Category mode 'cut' should be valid."""
        base_config["remediation"] = {
            "video": {
                "category_modes": {
                    "Violence": "cut",
                }
            }
        }
        validate_config(base_config)  # Should not raise

    def test_category_mode_invalid_pixelate(self, base_config):
        """Category mode 'pixelate' should be invalid."""
        base_config["remediation"] = {
            "video": {
                "category_modes": {
                    "Nudity": "pixelate",
                }
            }
        }
        with pytest.raises(ConfigError, match="must be one of"):
            validate_config(base_config)

    def test_category_mode_multiple_categories(self, base_config):
        """Multiple category modes should be valid."""
        base_config["remediation"] = {
            "video": {
                "category_modes": {
                    "Nudity": "blank",
                    "Violence": "cut",
                    "Profanity": "blank",
                }
            }
        }
        validate_config(base_config)  # Should not raise

    def test_category_mode_value_case_sensitive(self, base_config):
        """Category mode value should be case-sensitive."""
        base_config["remediation"] = {
            "video": {
                "category_modes": {
                    "Nudity": "Blank",  # Wrong case
                }
            }
        }
        with pytest.raises(ConfigError, match="must be one of"):
            validate_config(base_config)

    def test_category_mode_numeric_value(self, base_config):
        """Category mode value cannot be numeric."""
        base_config["remediation"] = {
            "video": {
                "category_modes": {
                    "Nudity": 1,
                }
            }
        }
        with pytest.raises(ConfigError, match="must be a string"):
            validate_config(base_config)

    def test_category_mode_boolean_value(self, base_config):
        """Category mode value cannot be boolean."""
        base_config["remediation"] = {
            "video": {
                "category_modes": {
                    "Nudity": True,
                }
            }
        }
        with pytest.raises(ConfigError, match="must be a string"):
            validate_config(base_config)


class TestProcessingValidationEdgeCases:
    """Test edge cases in processing validation."""

    def test_max_workers_float_raises_error(self, base_config):
        """max_workers as float should raise error."""
        base_config["processing"]["max_workers"] = 4.5
        with pytest.raises(ConfigError, match="positive integer"):
            validate_config(base_config)

    def test_max_workers_string_raises_error(self, base_config):
        """max_workers as string should raise error."""
        base_config["processing"]["max_workers"] = "4"
        with pytest.raises(ConfigError, match="positive integer"):
            validate_config(base_config)

    def test_merge_threshold_none_is_valid(self, base_config):
        """merge_threshold as None is valid (optional field)."""
        base_config["processing"]["segment_merge"]["merge_threshold"] = None
        validate_config(base_config)  # Should not raise

    def test_merge_threshold_string_is_ignored(self, base_config):
        """merge_threshold as non-numeric string is valid (not checked)."""
        base_config["processing"]["segment_merge"]["merge_threshold"] = "invalid"
        validate_config(base_config)  # Should not raise


class TestAudioRemediationValidationEdgeCases:
    """Test edge cases in audio remediation validation."""

    def test_audio_remediation_not_dict_raises_error(self, base_config):
        """Audio field in remediation must be a dictionary."""
        base_config["remediation"] = {
            "audio": "invalid",
        }
        with pytest.raises(ConfigError, match="'remediation.audio' field must be a dictionary"):
            validate_config(base_config)

    def test_audio_remediation_enabled_not_bool_raises_error(self, base_config):
        """Audio.enabled must be a boolean."""
        base_config["remediation"] = {
            "audio": {
                "enabled": "true",
            }
        }
        with pytest.raises(ConfigError, match="'remediation.audio.enabled' must be a boolean"):
            validate_config(base_config)

    def test_audio_remediation_mode_not_string_raises_error(self, base_config):
        """Audio.mode must be a string."""
        base_config["remediation"] = {
            "audio": {
                "mode": True,
            }
        }
        with pytest.raises(ConfigError, match="'remediation.audio.mode' must be a string"):
            validate_config(base_config)

    def test_audio_remediation_categories_not_list_raises_error(self, base_config):
        """Audio.categories must be a list."""
        base_config["remediation"] = {
            "audio": {
                "categories": "Profanity",
            }
        }
        with pytest.raises(ConfigError, match="'remediation.audio.categories' must be a list"):
            validate_config(base_config)

    def test_audio_remediation_categories_non_string_item_raises_error(self, base_config):
        """Audio.categories must contain strings."""
        base_config["remediation"] = {
            "audio": {
                "categories": ["Profanity", 123],
            }
        }
        with pytest.raises(ConfigError, match="'remediation.audio.categories' must contain strings"):
            validate_config(base_config)

    def test_audio_remediation_bleep_frequency_not_number_raises_error(self, base_config):
        """Audio.bleep_frequency must be a positive number."""
        base_config["remediation"] = {
            "audio": {
                "bleep_frequency": "1000",
            }
        }
        with pytest.raises(ConfigError, match="'remediation.audio.bleep_frequency' must be a positive number"):
            validate_config(base_config)

    def test_audio_remediation_bleep_frequency_zero_raises_error(self, base_config):
        """Audio.bleep_frequency must be positive."""
        base_config["remediation"] = {
            "audio": {
                "bleep_frequency": 0,
            }
        }
        with pytest.raises(ConfigError, match="'remediation.audio.bleep_frequency' must be a positive number"):
            validate_config(base_config)

    def test_audio_remediation_bleep_frequency_negative_raises_error(self, base_config):
        """Audio.bleep_frequency must not be negative."""
        base_config["remediation"] = {
            "audio": {
                "bleep_frequency": -1000,
            }
        }
        with pytest.raises(ConfigError, match="'remediation.audio.bleep_frequency' must be a positive number"):
            validate_config(base_config)


class TestComplexConfigScenarios:
    """Test complex configuration scenarios."""

    def test_full_config_with_all_sections(self, base_config):
        """Valid configuration with all optional sections."""
        base_config["detectors"] = [
            {
                "type": "llava",
                "name": "visual-detector",
                "categories": ["Nudity", "Violence"],
            }
        ]
        base_config["video"] = {
            "metadata_output": {
                "skip_chapters": {
                    "enabled": True,
                    "name_format": "Chapter {number}",
                }
            }
        }
        base_config["remediation"] = {
            "audio": {
                "enabled": True,
                "mode": "silence",
                "categories": ["Profanity"],
            },
            "video": {
                "enabled": True,
                "mode": "blank",
                "blank_color": "#000000",
                "category_modes": {
                    "Nudity": "cut",
                }
            }
        }
        base_config["models"] = {
            "cache_dir": "/custom/path",
            "sources": [
                {
                    "name": "llava-7b",
                    "url": "https://example.com/model.bin",
                    "checksum": "abc123",
                    "size_bytes": 1000000,
                    "algorithm": "sha256",
                    "optional": False,
                }
            ],
            "auto_download": True,
        }
        validate_config(base_config)  # Should not raise

    def test_config_with_multiple_detection_categories(self, base_config):
        """Configuration with multiple detection categories."""
        base_config["detections"]["violence"] = {
            "enabled": True,
            "sensitivity": 0.5,
            "model": "local",
        }
        base_config["detections"]["profanity"] = {
            "enabled": False,
            "sensitivity": 0.6,
            "model": "local",
        }
        validate_config(base_config)  # Should not raise
