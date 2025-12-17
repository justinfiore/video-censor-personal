"""Tests for models section configuration and validation."""

import pytest

from video_censor_personal.config import (
    ConfigError,
    ModelsConfig,
    ModelSource,
    validate_config,
)


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


class TestModelSourceDataclass:
    """Tests for ModelSource dataclass."""

    def test_model_source_creation_required_fields(self):
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


class TestModelsConfigDataclass:
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


class TestModelsConfigCacheDir:
    """Test ModelsConfig.get_cache_dir method."""

    def test_get_cache_dir_returns_path_object(self):
        """get_cache_dir should return a Path object."""
        from pathlib import Path
        config = ModelsConfig(cache_dir="/tmp/cache")
        result = config.get_cache_dir()
        assert isinstance(result, Path)

    def test_get_cache_dir_custom_directory(self):
        """get_cache_dir should return custom cache directory."""
        from pathlib import Path
        config = ModelsConfig(cache_dir="/custom/cache/path")
        result = config.get_cache_dir()
        assert result == Path("/custom/cache/path")

    def test_get_cache_dir_expanduser(self):
        """Test get_cache_dir expands home directory."""
        from pathlib import Path
        config = ModelsConfig(cache_dir="~/my_models")
        result = config.get_cache_dir()
        assert result == Path.home() / "my_models"

    def test_get_cache_dir_default(self):
        """Test get_cache_dir uses platform defaults when None."""
        from pathlib import Path
        config = ModelsConfig(cache_dir=None)
        result = config.get_cache_dir()
        # Should contain video-censor and models
        assert "video-censor" in str(result)
        assert "models" in str(result)


class TestModelsConfigValidation:
    """Tests for YAML configuration validation with models section."""

    def test_valid_config_with_models_section(self, base_config):
        """Test validation passes with valid models section."""
        base_config["models"] = {
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
        }
        validate_config(base_config)  # Should not raise

    def test_config_without_models_section(self, base_config):
        """Test validation passes when models section is omitted."""
        validate_config(base_config)  # Should not raise

    def test_invalid_models_not_dict(self, base_config):
        """Test validation fails when models is not a dict."""
        base_config["models"] = "invalid"
        with pytest.raises(ConfigError, match="'models' field must be a dictionary"):
            validate_config(base_config)

    def test_models_cache_dir_not_dict(self, base_config):
        """Test validation when models is not a dict."""
        base_config["models"] = ["models"]
        with pytest.raises(ConfigError, match="'models' field must be a dictionary"):
            validate_config(base_config)


class TestModelsCacheDirValidation:
    """Test models cache_dir field validation."""

    def test_invalid_cache_dir_type(self, base_config):
        """Test validation fails when cache_dir is not a string."""
        base_config["models"] = {
            "cache_dir": 123,
        }
        with pytest.raises(ConfigError, match="'models.cache_dir' must be a string or null"):
            validate_config(base_config)

    def test_cache_dir_null_is_valid(self, base_config):
        """Model cache_dir can be null/None."""
        base_config["models"] = {
            "cache_dir": None,
        }
        validate_config(base_config)  # Should not raise

    def test_cache_dir_string_is_valid(self, base_config):
        """Model cache_dir can be a string."""
        base_config["models"] = {
            "cache_dir": "/custom/cache",
        }
        validate_config(base_config)  # Should not raise


class TestModelsSourcesListValidation:
    """Test models sources list validation."""

    def test_invalid_sources_not_list(self, base_config):
        """Test validation fails when sources is not a list."""
        base_config["models"] = {
            "sources": "not a list",
        }
        with pytest.raises(ConfigError, match="'models.sources' must be a list"):
            validate_config(base_config)

    def test_sources_null_is_valid(self, base_config):
        """Model sources can be null/None."""
        base_config["models"] = {
            "sources": None,
        }
        validate_config(base_config)  # Should not raise

    def test_sources_empty_list_is_valid(self, base_config):
        """Model sources can be empty list."""
        base_config["models"] = {
            "sources": [],
        }
        validate_config(base_config)  # Should not raise


class TestModelSourceStructureValidation:
    """Test individual model source validation."""

    def test_model_source_not_dict_raises_error(self, base_config):
        """Model source entry must be a dictionary."""
        base_config["models"] = {
            "sources": ["invalid"]
        }
        with pytest.raises(ConfigError, match="Model source 0 must be a dictionary"):
            validate_config(base_config)

    def test_model_source_missing_name_raises_error(self, base_config):
        """Model source missing 'name' field raises error."""
        base_config["models"] = {
            "sources": [
                {
                    "url": "https://example.com/model.bin",
                    "checksum": "abc123",
                    "size_bytes": 1000000,
                }
            ]
        }
        with pytest.raises(ConfigError, match="missing required fields"):
            validate_config(base_config)

    def test_model_source_missing_url_raises_error(self, base_config):
        """Model source missing 'url' field raises error."""
        base_config["models"] = {
            "sources": [
                {
                    "name": "model1",
                    "checksum": "abc123",
                    "size_bytes": 1000000,
                }
            ]
        }
        with pytest.raises(ConfigError, match="missing required fields"):
            validate_config(base_config)

    def test_model_source_missing_checksum_raises_error(self, base_config):
        """Model source missing 'checksum' field raises error."""
        base_config["models"] = {
            "sources": [
                {
                    "name": "model1",
                    "url": "https://example.com/model.bin",
                    "size_bytes": 1000000,
                }
            ]
        }
        with pytest.raises(ConfigError, match="missing required fields"):
            validate_config(base_config)

    def test_model_source_missing_size_bytes_raises_error(self, base_config):
        """Model source missing 'size_bytes' field raises error."""
        base_config["models"] = {
            "sources": [
                {
                    "name": "model1",
                    "url": "https://example.com/model.bin",
                    "checksum": "abc123",
                }
            ]
        }
        with pytest.raises(ConfigError, match="missing required fields"):
            validate_config(base_config)

    def test_model_source_name_not_string_raises_error(self, base_config):
        """Model source 'name' must be a string."""
        base_config["models"] = {
            "sources": [
                {
                    "name": 123,
                    "url": "https://example.com/model.bin",
                    "checksum": "abc123",
                    "size_bytes": 1000000,
                }
            ]
        }
        with pytest.raises(ConfigError, match="'name' must be a string"):
            validate_config(base_config)

    def test_model_source_url_not_string_raises_error(self, base_config):
        """Model source 'url' must be a string."""
        base_config["models"] = {
            "sources": [
                {
                    "name": "model1",
                    "url": 123,
                    "checksum": "abc123",
                    "size_bytes": 1000000,
                }
            ]
        }
        with pytest.raises(ConfigError, match="'url' must be a string"):
            validate_config(base_config)

    def test_model_source_checksum_not_string_raises_error(self, base_config):
        """Model source 'checksum' must be a string."""
        base_config["models"] = {
            "sources": [
                {
                    "name": "model1",
                    "url": "https://example.com/model.bin",
                    "checksum": 123,
                    "size_bytes": 1000000,
                }
            ]
        }
        with pytest.raises(ConfigError, match="'checksum' must be a string"):
            validate_config(base_config)

    def test_model_source_size_bytes_not_integer_raises_error(self, base_config):
        """Model source 'size_bytes' must be an integer."""
        base_config["models"] = {
            "sources": [
                {
                    "name": "model1",
                    "url": "https://example.com/model.bin",
                    "checksum": "abc123",
                    "size_bytes": "1000000",
                }
            ]
        }
        with pytest.raises(ConfigError, match="'size_bytes' must be an integer"):
            validate_config(base_config)


class TestModelSourceOptionalFields:
    """Test model source optional field validation."""

    def test_model_source_algorithm_not_string_raises_error(self, base_config):
        """Model source 'algorithm' must be a string if provided."""
        base_config["models"] = {
            "sources": [
                {
                    "name": "model1",
                    "url": "https://example.com/model.bin",
                    "checksum": "abc123",
                    "size_bytes": 1000000,
                    "algorithm": 123,
                }
            ]
        }
        with pytest.raises(ConfigError, match="'algorithm' must be a string"):
            validate_config(base_config)

    def test_model_source_algorithm_valid(self, base_config):
        """Model source with custom algorithm."""
        base_config["models"] = {
            "sources": [
                {
                    "name": "model1",
                    "url": "https://example.com/model.bin",
                    "checksum": "abc123",
                    "size_bytes": 1000000,
                    "algorithm": "md5",
                }
            ]
        }
        validate_config(base_config)  # Should not raise

    def test_model_source_optional_not_bool_raises_error(self, base_config):
        """Model source 'optional' must be a boolean if provided."""
        base_config["models"] = {
            "sources": [
                {
                    "name": "model1",
                    "url": "https://example.com/model.bin",
                    "checksum": "abc123",
                    "size_bytes": 1000000,
                    "optional": "yes",
                }
            ]
        }
        with pytest.raises(ConfigError, match="'optional' must be a boolean"):
            validate_config(base_config)

    def test_model_source_optional_true(self, base_config):
        """Model source marked as optional."""
        base_config["models"] = {
            "sources": [
                {
                    "name": "model1",
                    "url": "https://example.com/model.bin",
                    "checksum": "abc123",
                    "size_bytes": 1000000,
                    "optional": True,
                }
            ]
        }
        validate_config(base_config)  # Should not raise

    def test_model_source_optional_false(self, base_config):
        """Model source marked as required."""
        base_config["models"] = {
            "sources": [
                {
                    "name": "model1",
                    "url": "https://example.com/model.bin",
                    "checksum": "abc123",
                    "size_bytes": 1000000,
                    "optional": False,
                }
            ]
        }
        validate_config(base_config)  # Should not raise


class TestModelsAutoDownloadValidation:
    """Test models auto_download field validation."""

    def test_invalid_auto_download_type(self, base_config):
        """Test validation fails when auto_download is not boolean."""
        base_config["models"] = {
            "auto_download": "yes",
        }
        with pytest.raises(ConfigError, match="'models.auto_download' must be a boolean"):
            validate_config(base_config)

    def test_auto_download_true_is_valid(self, base_config):
        """auto_download can be true."""
        base_config["models"] = {
            "auto_download": True,
        }
        validate_config(base_config)  # Should not raise

    def test_auto_download_false_is_valid(self, base_config):
        """auto_download can be false."""
        base_config["models"] = {
            "auto_download": False,
        }
        validate_config(base_config)  # Should not raise


class TestMultipleModelSources:
    """Test configuration with multiple model sources."""

    def test_multiple_model_sources_valid(self, base_config):
        """Valid configuration with multiple model sources."""
        base_config["models"] = {
            "sources": [
                {
                    "name": "model1",
                    "url": "https://example.com/model1.bin",
                    "checksum": "abc123",
                    "size_bytes": 1000000,
                },
                {
                    "name": "model2",
                    "url": "https://example.com/model2.bin",
                    "checksum": "def456",
                    "size_bytes": 2000000,
                    "optional": True,
                }
            ]
        }
        validate_config(base_config)  # Should not raise

    def test_models_with_all_options(self, base_config):
        """Valid models section with all options specified."""
        base_config["models"] = {
            "cache_dir": "/custom/cache",
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
