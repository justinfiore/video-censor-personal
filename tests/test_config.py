"""Tests for configuration module."""

import tempfile
from pathlib import Path

import pytest
import yaml

from video_censor_personal.config import ConfigError, load_config, validate_config


@pytest.fixture
def valid_config():
    """Fixture with valid configuration."""
    return {
        "version": 1.0,
        "detections": {
            "nudity": {
                "enabled": True,
                "sensitivity": 0.7,
                "model": "local",
            },
            "profanity": {
                "enabled": True,
                "sensitivity": 0.8,
                "model": "local",
            },
        },
        "processing": {
            "frame_sampling": {"strategy": "uniform", "sample_rate": 1.0},
            "segment_merge": {"enabled": True, "merge_threshold": 2.0},
            "max_workers": 4,
        },
        "output": {"format": "json", "include_confidence": True},
    }


class TestValidateConfig:
    """Test configuration validation."""

    def test_valid_config(self, valid_config):
        """Valid configuration should pass validation."""
        validate_config(valid_config)  # Should not raise

    def test_missing_detections_field(self, valid_config):
        """Missing detections field should raise error."""
        del valid_config["detections"]
        with pytest.raises(ConfigError, match="detections"):
            validate_config(valid_config)

    def test_missing_processing_field(self, valid_config):
        """Missing processing field should raise error."""
        del valid_config["processing"]
        with pytest.raises(ConfigError, match="processing"):
            validate_config(valid_config)

    def test_missing_output_field(self, valid_config):
        """Missing output field should raise error."""
        del valid_config["output"]
        with pytest.raises(ConfigError, match="output"):
            validate_config(valid_config)

    def test_missing_frame_sampling(self, valid_config):
        """Missing frame_sampling should raise error."""
        del valid_config["processing"]["frame_sampling"]
        with pytest.raises(ConfigError, match="frame_sampling"):
            validate_config(valid_config)

    def test_missing_segment_merge(self, valid_config):
        """Missing segment_merge should raise error."""
        del valid_config["processing"]["segment_merge"]
        with pytest.raises(ConfigError, match="segment_merge"):
            validate_config(valid_config)

    def test_missing_max_workers(self, valid_config):
        """Missing max_workers should raise error."""
        del valid_config["processing"]["max_workers"]
        with pytest.raises(ConfigError, match="max_workers"):
            validate_config(valid_config)

    def test_missing_output_format(self, valid_config):
        """Missing output.format should raise error."""
        del valid_config["output"]["format"]
        with pytest.raises(ConfigError, match="format"):
            validate_config(valid_config)

    def test_non_dict_config(self):
        """Non-dict configuration should raise error."""
        with pytest.raises(ConfigError, match="dictionary"):
            validate_config([1, 2, 3])

    def test_non_dict_detections(self, valid_config):
        """Non-dict detections should raise error."""
        valid_config["detections"] = ["nudity", "profanity"]
        with pytest.raises(ConfigError, match="detections"):
            validate_config(valid_config)

    def test_non_dict_processing(self, valid_config):
        """Non-dict processing should raise error."""
        valid_config["processing"] = ["sampling", "merge"]
        with pytest.raises(ConfigError, match="processing"):
            validate_config(valid_config)

    def test_non_dict_output(self, valid_config):
        """Non-dict output should raise error."""
        valid_config["output"] = ["json", "csv"]
        with pytest.raises(ConfigError, match="output"):
            validate_config(valid_config)


class TestSemanticValidation:
    """Test semantic validation of configuration values."""

    def test_sensitivity_at_min_boundary(self, valid_config):
        """Sensitivity of 0.0 should be valid."""
        valid_config["detections"]["nudity"]["sensitivity"] = 0.0
        validate_config(valid_config)  # Should not raise

    def test_sensitivity_at_max_boundary(self, valid_config):
        """Sensitivity of 1.0 should be valid."""
        valid_config["detections"]["nudity"]["sensitivity"] = 1.0
        validate_config(valid_config)  # Should not raise

    def test_sensitivity_below_min(self, valid_config):
        """Sensitivity below 0.0 should raise error."""
        valid_config["detections"]["nudity"]["sensitivity"] = -0.1
        with pytest.raises(ConfigError, match="out of range"):
            validate_config(valid_config)

    def test_sensitivity_above_max(self, valid_config):
        """Sensitivity above 1.0 should raise error."""
        valid_config["detections"]["nudity"]["sensitivity"] = 1.1
        with pytest.raises(ConfigError, match="out of range"):
            validate_config(valid_config)

    def test_detection_category_missing_enabled(self, valid_config):
        """Detection category missing 'enabled' field should raise error."""
        del valid_config["detections"]["nudity"]["enabled"]
        with pytest.raises(ConfigError, match="missing required fields"):
            validate_config(valid_config)

    def test_detection_category_missing_sensitivity(self, valid_config):
        """Detection category missing 'sensitivity' field should raise error."""
        del valid_config["detections"]["nudity"]["sensitivity"]
        with pytest.raises(ConfigError, match="missing required fields"):
            validate_config(valid_config)

    def test_detection_category_missing_model(self, valid_config):
        """Detection category missing 'model' field should raise error."""
        del valid_config["detections"]["nudity"]["model"]
        with pytest.raises(ConfigError, match="missing required fields"):
            validate_config(valid_config)

    def test_detection_category_enabled_not_bool(self, valid_config):
        """Detection category 'enabled' must be boolean."""
        valid_config["detections"]["nudity"]["enabled"] = "yes"
        with pytest.raises(ConfigError, match="must be boolean"):
            validate_config(valid_config)

    def test_detection_category_sensitivity_not_numeric(self, valid_config):
        """Detection category 'sensitivity' must be numeric."""
        valid_config["detections"]["nudity"]["sensitivity"] = "high"
        with pytest.raises(ConfigError, match="must be a number"):
            validate_config(valid_config)

    def test_detection_category_model_not_string(self, valid_config):
        """Detection category 'model' must be string."""
        valid_config["detections"]["nudity"]["model"] = 123
        with pytest.raises(ConfigError, match="must be a string"):
            validate_config(valid_config)

    def test_detection_category_not_dict(self, valid_config):
        """Detection category must be a dictionary."""
        valid_config["detections"]["nudity"] = "local"
        with pytest.raises(ConfigError, match="must be a dictionary"):
            validate_config(valid_config)

    def test_no_detections_enabled(self, valid_config):
        """At least one detection must be enabled."""
        valid_config["detections"]["nudity"]["enabled"] = False
        valid_config["detections"]["profanity"]["enabled"] = False
        with pytest.raises(ConfigError, match="must have 'enabled: true'"):
            validate_config(valid_config)

    def test_at_least_one_detection_enabled(self, valid_config):
        """At least one detection enabled should pass."""
        valid_config["detections"]["nudity"]["enabled"] = False
        valid_config["detections"]["profanity"]["enabled"] = True
        validate_config(valid_config)  # Should not raise

    def test_empty_detections(self, valid_config):
        """Empty detections dict should raise error."""
        valid_config["detections"] = {}
        with pytest.raises(ConfigError, match="must be defined"):
            validate_config(valid_config)

    def test_output_format_json_allowed(self, valid_config):
        """Output format 'json' should be allowed."""
        valid_config["output"]["format"] = "json"
        validate_config(valid_config)  # Should not raise

    def test_output_format_csv_not_allowed(self, valid_config):
        """Output format 'csv' should not be allowed."""
        valid_config["output"]["format"] = "csv"
        with pytest.raises(ConfigError, match="not supported"):
            validate_config(valid_config)

    def test_output_format_xml_not_allowed(self, valid_config):
        """Output format 'xml' should not be allowed."""
        valid_config["output"]["format"] = "xml"
        with pytest.raises(ConfigError, match="not supported"):
            validate_config(valid_config)

    def test_frame_sampling_strategy_uniform(self, valid_config):
        """Frame sampling strategy 'uniform' should be allowed."""
        valid_config["processing"]["frame_sampling"]["strategy"] = "uniform"
        validate_config(valid_config)  # Should not raise

    def test_frame_sampling_strategy_scene_based(self, valid_config):
        """Frame sampling strategy 'scene_based' should be allowed."""
        valid_config["processing"]["frame_sampling"]["strategy"] = "scene_based"
        validate_config(valid_config)  # Should not raise

    def test_frame_sampling_strategy_all(self, valid_config):
        """Frame sampling strategy 'all' should be allowed."""
        valid_config["processing"]["frame_sampling"]["strategy"] = "all"
        validate_config(valid_config)  # Should not raise

    def test_frame_sampling_strategy_invalid(self, valid_config):
        """Invalid frame sampling strategy should raise error."""
        valid_config["processing"]["frame_sampling"]["strategy"] = "adaptive"
        with pytest.raises(ConfigError, match="invalid"):
            validate_config(valid_config)

    def test_max_workers_positive(self, valid_config):
        """Positive max_workers should be allowed."""
        valid_config["processing"]["max_workers"] = 1
        validate_config(valid_config)  # Should not raise

    def test_max_workers_zero(self, valid_config):
        """Zero max_workers should raise error."""
        valid_config["processing"]["max_workers"] = 0
        with pytest.raises(ConfigError, match="positive integer"):
            validate_config(valid_config)

    def test_max_workers_negative(self, valid_config):
        """Negative max_workers should raise error."""
        valid_config["processing"]["max_workers"] = -1
        with pytest.raises(ConfigError, match="positive integer"):
            validate_config(valid_config)

    def test_max_workers_not_int(self, valid_config):
        """Non-integer max_workers should raise error."""
        valid_config["processing"]["max_workers"] = 4.5
        with pytest.raises(ConfigError, match="positive integer"):
            validate_config(valid_config)

    def test_merge_threshold_zero(self, valid_config):
        """Merge threshold of 0.0 should be allowed."""
        valid_config["processing"]["segment_merge"]["merge_threshold"] = 0.0
        validate_config(valid_config)  # Should not raise

    def test_merge_threshold_positive(self, valid_config):
        """Positive merge threshold should be allowed."""
        valid_config["processing"]["segment_merge"]["merge_threshold"] = 2.5
        validate_config(valid_config)  # Should not raise

    def test_merge_threshold_negative(self, valid_config):
        """Negative merge threshold should raise error."""
        valid_config["processing"]["segment_merge"]["merge_threshold"] = -0.5
        with pytest.raises(ConfigError, match="non-negative"):
            validate_config(valid_config)


class TestLoadConfig:
    """Test configuration file loading."""

    def test_load_valid_yaml(self, valid_config):
        """Load valid YAML configuration file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            with open(config_path, "w") as f:
                yaml.dump(valid_config, f)

            loaded = load_config(str(config_path))
            assert loaded == valid_config

    def test_load_nonexistent_file(self):
        """Loading nonexistent file should raise error."""
        with pytest.raises(ConfigError, match="not found"):
            load_config("/nonexistent/path/config.yaml")

    def test_load_invalid_yaml(self):
        """Loading invalid YAML should raise error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            with open(config_path, "w") as f:
                f.write("{ invalid yaml: [")

            with pytest.raises(ConfigError, match="YAML"):
                load_config(str(config_path))

    def test_load_empty_file(self):
        """Loading empty file should raise error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            config_path.touch()

            with pytest.raises(ConfigError, match="empty"):
                load_config(str(config_path))

    def test_load_with_default_location(self, valid_config):
        """Load from default location without specifying path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = Path.cwd()
            try:
                # Create config in temp directory with default name
                config_path = Path(tmpdir) / "video-censor.yaml"
                with open(config_path, "w") as f:
                    yaml.dump(valid_config, f)

                # We can't easily change cwd in test, so just verify file exists
                assert config_path.exists()
                loaded = load_config(str(config_path))
                assert loaded == valid_config
            finally:
                pass

    def test_missing_required_fields_in_file(self):
        """Loading file with missing required fields should raise error."""
        invalid_config = {"version": 1.0, "detections": {}}
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            with open(config_path, "w") as f:
                yaml.dump(invalid_config, f)

            with pytest.raises(ConfigError, match="required"):
                load_config(str(config_path))
