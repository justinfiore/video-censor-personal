"""Tests for config loading functionality."""

import tempfile
from pathlib import Path

import pytest
import yaml

from video_censor_personal.config import ConfigError, load_config


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
        },
        "processing": {
            "frame_sampling": {"strategy": "uniform", "sample_rate": 1.0},
            "segment_merge": {"enabled": True, "merge_threshold": 2.0},
            "max_workers": 4,
        },
        "output": {"format": "json"},
    }


class TestLoadConfigBasic:
    """Test basic config file loading."""

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


class TestLoadConfigDefaultLocations:
    """Test load_config with default file locations."""

    def test_load_config_from_explicit_path(self, valid_config):
        """Load config from explicitly specified path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            with open(config_path, "w") as f:
                yaml.dump(valid_config, f)

            loaded = load_config(str(config_path))
            assert loaded == valid_config

    def test_load_config_finds_video_censor_yaml_first(self, valid_config):
        """load_config should find ./video-censor.yaml before ./config.yaml."""
        with tempfile.TemporaryDirectory() as tmpdir:
            video_censor_path = Path(tmpdir) / "video-censor.yaml"
            config_path = Path(tmpdir) / "config.yaml"
            
            # Create both files
            with open(video_censor_path, "w") as f:
                yaml.dump(valid_config, f)
            with open(config_path, "w") as f:
                yaml.dump(valid_config, f)
            
            # Modify one to verify which is loaded
            modified_config = valid_config.copy()
            modified_config["_test"] = "video-censor"
            with open(video_censor_path, "w") as f:
                yaml.dump(modified_config, f)
            
            loaded = load_config(str(video_censor_path))
            assert loaded.get("_test") == "video-censor"

    def test_load_config_prefers_explicit_path(self, valid_config):
        """load_config should use explicit path if provided."""
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_path = Path(tmpdir) / "custom.yaml"
            with open(custom_path, "w") as f:
                yaml.dump(valid_config, f)
            
            loaded = load_config(str(custom_path))
            assert loaded == valid_config


class TestLoadConfigErrorHandling:
    """Test error handling in load_config."""

    def test_load_config_with_read_permission_error(self):
        """Raise ConfigError when file cannot be read."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            # Create file then remove read permissions
            with open(config_path, "w") as f:
                f.write("test: true\n")
            
            # Make it unreadable
            config_path.chmod(0o000)
            
            try:
                with pytest.raises(ConfigError, match="Error reading configuration file"):
                    load_config(str(config_path))
            finally:
                # Restore permissions for cleanup
                config_path.chmod(0o644)

    def test_load_config_empty_yaml_is_none(self):
        """Raise ConfigError when YAML file is empty (parses to None)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            # Create empty YAML file
            with open(config_path, "w") as f:
                f.write("")
            
            with pytest.raises(ConfigError, match="empty"):
                load_config(str(config_path))

    def test_load_config_whitespace_only_yaml_is_none(self):
        """Raise ConfigError when YAML file contains only whitespace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            with open(config_path, "w") as f:
                f.write("   \n  \n  ")
            
            with pytest.raises(ConfigError, match="empty"):
                load_config(str(config_path))

    def test_load_config_comment_only_yaml_is_none(self):
        """Raise ConfigError when YAML file contains only comments."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            with open(config_path, "w") as f:
                f.write("# Just a comment\n# Another comment\n")
            
            with pytest.raises(ConfigError, match="empty"):
                load_config(str(config_path))

    def test_load_config_directory_not_file(self):
        """Raise ConfigError when trying to load a directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(ConfigError, match="Error reading configuration file"):
                load_config(tmpdir)
