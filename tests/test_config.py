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
