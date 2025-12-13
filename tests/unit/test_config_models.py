"""Unit tests for model configuration schema."""

import pytest
from pathlib import Path
import tempfile
import yaml

from video_censor_personal.config import (
    ConfigError,
    ModelSource,
    ModelsConfig,
    load_config,
    validate_config,
)


class TestModelSource:
    """Tests for ModelSource dataclass."""

    def test_model_source_creation(self):
        """Test creating a ModelSource with required fields."""
        source = ModelSource(
            name="llava-7b",
            url="https://example.com/model.bin",
            checksum="abc123",
            size_bytes=1000000,
        )
        assert source.name == "llava-7b"
        assert source.url == "https://example.com/model.bin"
        assert source.checksum == "abc123"
        assert source.size_bytes == 1000000
        assert source.algorithm == "sha256"  # default
        assert source.optional is False  # default

    def test_model_source_with_optional_fields(self):
        """Test creating a ModelSource with optional fields."""
        source = ModelSource(
            name="custom-model",
            url="https://example.com/model.safetensors",
            checksum="def456",
            size_bytes=2000000,
            algorithm="md5",
            optional=True,
        )
        assert source.algorithm == "md5"
        assert source.optional is True


class TestModelsConfig:
    """Tests for ModelsConfig dataclass."""

    def test_models_config_defaults(self):
        """Test ModelsConfig with default values."""
        config = ModelsConfig()
        assert config.cache_dir is None
        assert config.sources == []
        assert config.auto_download is False

    def test_models_config_with_sources(self):
        """Test ModelsConfig with model sources."""
        sources = [
            ModelSource(
                name="model1",
                url="https://example.com/model1.bin",
                checksum="hash1",
                size_bytes=1000000,
            ),
            ModelSource(
                name="model2",
                url="https://example.com/model2.bin",
                checksum="hash2",
                size_bytes=2000000,
            ),
        ]
        config = ModelsConfig(sources=sources)
        assert len(config.sources) == 2
        assert config.sources[0].name == "model1"
        assert config.sources[1].name == "model2"

    def test_get_cache_dir_custom(self):
        """Test get_cache_dir with custom cache directory."""
        config = ModelsConfig(cache_dir="/custom/cache")
        cache_dir = config.get_cache_dir()
        assert cache_dir == Path("/custom/cache")

    def test_get_cache_dir_expanduser(self):
        """Test get_cache_dir expands home directory."""
        config = ModelsConfig(cache_dir="~/my_models")
        cache_dir = config.get_cache_dir()
        assert cache_dir == Path.home() / "my_models"

    def test_get_cache_dir_default(self):
        """Test get_cache_dir uses platform defaults when not set."""
        config = ModelsConfig(cache_dir=None)
        cache_dir = config.get_cache_dir()
        # Should be a Path object
        assert isinstance(cache_dir, Path)
        # Should contain "video-censor" and "models"
        assert "video-censor" in str(cache_dir)
        assert "models" in str(cache_dir)


class TestConfigValidation:
    """Tests for YAML configuration validation with models section."""

    def test_valid_config_with_models_section(self):
        """Test validation passes with valid models section."""
        config = {
            "detections": {
                "nudity": {
                    "enabled": True,
                    "sensitivity": 0.7,
                    "model": "local",
                }
            },
            "processing": {
                "frame_sampling": {"strategy": "uniform"},
                "segment_merge": {"merge_threshold": 2.0},
                "max_workers": 4,
            },
            "output": {"format": "json"},
            "models": {
                "cache_dir": None,
                "sources": [
                    {
                        "name": "llava-7b",
                        "url": "https://example.com/model.bin",
                        "checksum": "abc123",
                        "size_bytes": 1000000,
                    }
                ],
                "auto_download": False,
            },
        }
        # Should not raise
        validate_config(config)

    def test_config_without_models_section(self):
        """Test validation passes when models section is omitted."""
        config = {
            "detections": {
                "nudity": {
                    "enabled": True,
                    "sensitivity": 0.7,
                    "model": "local",
                }
            },
            "processing": {
                "frame_sampling": {"strategy": "uniform"},
                "segment_merge": {"merge_threshold": 2.0},
                "max_workers": 4,
            },
            "output": {"format": "json"},
        }
        # Should not raise
        validate_config(config)

    def test_invalid_models_not_dict(self):
        """Test validation fails when models is not a dict."""
        config = {
            "detections": {
                "nudity": {
                    "enabled": True,
                    "sensitivity": 0.7,
                    "model": "local",
                }
            },
            "processing": {
                "frame_sampling": {"strategy": "uniform"},
                "segment_merge": {"merge_threshold": 2.0},
                "max_workers": 4,
            },
            "output": {"format": "json"},
            "models": "invalid",  # Should be dict
        }
        with pytest.raises(ConfigError, match="'models' field must be a dictionary"):
            validate_config(config)

    def test_invalid_cache_dir_type(self):
        """Test validation fails when cache_dir is not a string."""
        config = {
            "detections": {
                "nudity": {
                    "enabled": True,
                    "sensitivity": 0.7,
                    "model": "local",
                }
            },
            "processing": {
                "frame_sampling": {"strategy": "uniform"},
                "segment_merge": {"merge_threshold": 2.0},
                "max_workers": 4,
            },
            "output": {"format": "json"},
            "models": {
                "cache_dir": 123,  # Should be string or null
            },
        }
        with pytest.raises(ConfigError, match="'models.cache_dir' must be a string or null"):
            validate_config(config)

    def test_invalid_sources_not_list(self):
        """Test validation fails when sources is not a list."""
        config = {
            "detections": {
                "nudity": {
                    "enabled": True,
                    "sensitivity": 0.7,
                    "model": "local",
                }
            },
            "processing": {
                "frame_sampling": {"strategy": "uniform"},
                "segment_merge": {"merge_threshold": 2.0},
                "max_workers": 4,
            },
            "output": {"format": "json"},
            "models": {
                "sources": "not a list",  # Should be list
            },
        }
        with pytest.raises(ConfigError, match="'models.sources' must be a list"):
            validate_config(config)

    def test_missing_required_model_field(self):
        """Test validation fails when model source missing required field."""
        config = {
            "detections": {
                "nudity": {
                    "enabled": True,
                    "sensitivity": 0.7,
                    "model": "local",
                }
            },
            "processing": {
                "frame_sampling": {"strategy": "uniform"},
                "segment_merge": {"merge_threshold": 2.0},
                "max_workers": 4,
            },
            "output": {"format": "json"},
            "models": {
                "sources": [
                    {
                        "name": "llava-7b",
                        "url": "https://example.com/model.bin",
                        # Missing "checksum" and "size_bytes"
                    }
                ],
            },
        }
        with pytest.raises(ConfigError, match="missing required fields"):
            validate_config(config)

    def test_invalid_model_source_field_type(self):
        """Test validation fails when model source field has wrong type."""
        config = {
            "detections": {
                "nudity": {
                    "enabled": True,
                    "sensitivity": 0.7,
                    "model": "local",
                }
            },
            "processing": {
                "frame_sampling": {"strategy": "uniform"},
                "segment_merge": {"merge_threshold": 2.0},
                "max_workers": 4,
            },
            "output": {"format": "json"},
            "models": {
                "sources": [
                    {
                        "name": "llava-7b",
                        "url": "https://example.com/model.bin",
                        "checksum": "abc123",
                        "size_bytes": "not an integer",  # Should be int
                    }
                ],
            },
        }
        with pytest.raises(ConfigError, match="'size_bytes' must be an integer"):
            validate_config(config)

    def test_invalid_auto_download_type(self):
        """Test validation fails when auto_download is not boolean."""
        config = {
            "detections": {
                "nudity": {
                    "enabled": True,
                    "sensitivity": 0.7,
                    "model": "local",
                }
            },
            "processing": {
                "frame_sampling": {"strategy": "uniform"},
                "segment_merge": {"merge_threshold": 2.0},
                "max_workers": 4,
            },
            "output": {"format": "json"},
            "models": {
                "auto_download": "yes",  # Should be bool
            },
        }
        with pytest.raises(ConfigError, match="'models.auto_download' must be a boolean"):
            validate_config(config)


class TestLoadConfigWithModels:
    """Integration tests for load_config with models section."""

    def test_load_config_with_models_yaml(self):
        """Test loading YAML config with models section."""
        yaml_content = """
detections:
  nudity:
    enabled: true
    sensitivity: 0.7
    model: "local"

processing:
  frame_sampling:
    strategy: "uniform"
  segment_merge:
    merge_threshold: 2.0
  max_workers: 4

output:
  format: "json"

models:
  cache_dir: null
  sources:
    - name: "llava-7b"
      url: "https://example.com/model.bin"
      checksum: "abc123"
      size_bytes: 1000000
      algorithm: "sha256"
      optional: false
  auto_download: false
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write(yaml_content)
            f.flush()
            config = load_config(f.name)

        assert "models" in config
        assert config["models"]["cache_dir"] is None
        assert len(config["models"]["sources"]) == 1
        assert config["models"]["sources"][0]["name"] == "llava-7b"
        assert config["models"]["auto_download"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
