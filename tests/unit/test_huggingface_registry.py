"""Unit tests for HuggingFace registry module."""

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

import pytest

from video_censor_personal.huggingface_registry import (
    HuggingFaceRegistry,
    ModelMetadata,
    ModelNotFoundError,
    RegistryError,
)


class TestModelMetadata:
    """Test ModelMetadata dataclass."""

    def test_creation(self):
        """Test creating ModelMetadata."""
        metadata = ModelMetadata(
            name="gpt2",
            versions=["main"],
            checksums={"main": "abc123"},
            sizes={"main": 1000000},
        )
        assert metadata.name == "gpt2"
        assert len(metadata.versions) == 1

    def test_to_dict(self):
        """Test converting to dict."""
        now = datetime.now()
        metadata = ModelMetadata(
            name="gpt2",
            versions=["main"],
            checksums={"main": "abc123"},
            sizes={"main": 1000000},
            last_updated=now,
        )
        data = metadata.to_dict()
        assert data["name"] == "gpt2"
        assert "last_updated" in data
        assert isinstance(data["last_updated"], str)

    def test_from_dict(self):
        """Test creating from dict."""
        data = {
            "name": "gpt2",
            "versions": ["main"],
            "checksums": {"main": "abc123"},
            "sizes": {"main": 1000000},
            "deprecated": False,
            "replacement": None,
            "last_updated": "2024-01-01T12:00:00",
        }
        metadata = ModelMetadata.from_dict(data)
        assert metadata.name == "gpt2"
        assert isinstance(metadata.last_updated, datetime)


class TestHuggingFaceRegistryInit:
    """Test registry initialization."""

    def test_init_with_default_cache_dir(self):
        """Test initialization with default cache directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("platformdirs.user_cache_dir") as mock_cache:
                mock_cache.return_value = tmpdir
                registry = HuggingFaceRegistry()
                assert registry.cache_dir.parent == Path(tmpdir)

    def test_init_with_custom_cache_dir(self):
        """Test initialization with custom cache directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_dir = Path(tmpdir) / "custom_cache"
            registry = HuggingFaceRegistry(cache_dir=custom_dir)
            assert registry.cache_dir == custom_dir / "hf-metadata"

    def test_init_creates_cache_directory(self):
        """Test that cache directory is created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "new_cache"
            registry = HuggingFaceRegistry(cache_dir=cache_dir)
            assert registry.cache_dir.exists()

    def test_init_with_invalid_ttl(self):
        """Test that invalid TTL raises ValueError."""
        with pytest.raises(ValueError, match="ttl_hours must be > 0"):
            HuggingFaceRegistry(ttl_hours=0)

    def test_init_with_custom_ttl(self):
        """Test initialization with custom TTL."""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = HuggingFaceRegistry(cache_dir=Path(tmpdir), ttl_hours=48)
            assert registry.ttl_hours == 48


class TestRegistryCaching:
    """Test metadata caching functionality."""

    def test_cache_file_creation(self):
        """Test that metadata is cached to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = HuggingFaceRegistry(cache_dir=Path(tmpdir))
            metadata = ModelMetadata(
                name="gpt2",
                versions=["main"],
                checksums={"main": "abc123"},
                sizes={"main": 1000000},
            )
            registry._save_metadata("gpt2", metadata)

            cache_file = registry.cache_dir / "gpt2.json"
            assert cache_file.exists()

    def test_cache_file_with_slash_in_name(self):
        """Test caching model name with slash (org/model)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = HuggingFaceRegistry(cache_dir=Path(tmpdir))
            metadata = ModelMetadata(
                name="openai/gpt2",
                versions=["main"],
                checksums={"main": "abc123"},
                sizes={"main": 1000000},
            )
            registry._save_metadata("openai/gpt2", metadata)

            # Slash should be replaced with hyphen
            cache_file = registry.cache_dir / "openai-gpt2.json"
            assert cache_file.exists()

    def test_get_cached_metadata_valid(self):
        """Test retrieving valid cached metadata."""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = HuggingFaceRegistry(cache_dir=Path(tmpdir))
            original = ModelMetadata(
                name="gpt2",
                versions=["main"],
                checksums={"main": "abc123"},
                sizes={"main": 1000000},
                last_updated=datetime.now(),
            )
            registry._save_metadata("gpt2", original)

            retrieved = registry.get_cached_metadata("gpt2")
            assert retrieved is not None
            assert retrieved.name == original.name

    def test_get_cached_metadata_not_found(self):
        """Test retrieving metadata for non-existent cache."""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = HuggingFaceRegistry(cache_dir=Path(tmpdir))
            assert registry.get_cached_metadata("nonexistent") is None

    def test_is_metadata_valid_within_ttl(self):
        """Test TTL check for valid metadata."""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = HuggingFaceRegistry(cache_dir=Path(tmpdir), ttl_hours=24)
            metadata = ModelMetadata(
                name="gpt2",
                versions=["main"],
                checksums={"main": "abc123"},
                sizes={"main": 1000000},
            )
            registry._save_metadata("gpt2", metadata)

            assert registry.is_metadata_valid("gpt2") is True

    def test_is_metadata_valid_expired_ttl(self):
        """Test TTL check for expired metadata."""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = HuggingFaceRegistry(cache_dir=Path(tmpdir), ttl_hours=1)
            metadata = ModelMetadata(
                name="gpt2",
                versions=["main"],
                checksums={"main": "abc123"},
                sizes={"main": 1000000},
            )
            registry._save_metadata("gpt2", metadata)

            # Manually set file mtime to old time
            cache_file = registry.cache_dir / "gpt2.json"
            old_time = (datetime.now() - timedelta(hours=2)).timestamp()
            Path(cache_file).touch()
            import os

            os.utime(cache_file, (old_time, old_time))

            assert registry.is_metadata_valid("gpt2") is False


class TestRegistryAPIFetch:
    """Test API fetching functionality."""

    @patch("video_censor_personal.huggingface_registry.urlopen")
    def test_fetch_model_success(self, mock_urlopen):
        """Test successful model fetch from API."""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = HuggingFaceRegistry(cache_dir=Path(tmpdir))

            # Mock API response
            response_data = {
                "id": "gpt2",
                "tags": [],
                "revision": "main",
                "gated": False,
            }
            mock_response = MagicMock()
            mock_response.read.return_value = json.dumps(response_data).encode()
            mock_response.__enter__.return_value = mock_response
            mock_urlopen.return_value = mock_response

            metadata = registry._fetch_from_api("gpt2")
            assert metadata.name == "gpt2"

    @patch("video_censor_personal.huggingface_registry.urlopen")
    def test_fetch_model_not_found(self, mock_urlopen):
        """Test 404 error when model not found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = HuggingFaceRegistry(cache_dir=Path(tmpdir))

            # Mock 404 response
            mock_urlopen.side_effect = HTTPError(
                "url", 404, "Not Found", {}, None
            )

            with pytest.raises(ModelNotFoundError):
                registry._fetch_from_api("nonexistent-model")

    @patch("video_censor_personal.huggingface_registry.urlopen")
    def test_fetch_model_network_error(self, mock_urlopen):
        """Test network error during fetch."""
        from urllib.error import URLError

        with tempfile.TemporaryDirectory() as tmpdir:
            registry = HuggingFaceRegistry(cache_dir=Path(tmpdir))

            # Mock network error
            mock_urlopen.side_effect = URLError("Connection refused")

            with pytest.raises(RegistryError, match="Network error"):
                registry._fetch_from_api("gpt2")

    @patch("video_censor_personal.huggingface_registry.urlopen")
    def test_query_model_uses_cache(self, mock_urlopen):
        """Test that query_model uses cache when available."""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = HuggingFaceRegistry(cache_dir=Path(tmpdir))

            # Pre-populate cache
            cached_metadata = ModelMetadata(
                name="gpt2",
                versions=["main"],
                checksums={"main": "cached123"},
                sizes={"main": 999},
                last_updated=datetime.now(),
            )
            registry._save_metadata("gpt2", cached_metadata)

            # Query should return cached version
            result = registry.query_model("gpt2")
            assert result.checksums["main"] == "cached123"

            # API should not be called
            mock_urlopen.assert_not_called()

    @patch("video_censor_personal.huggingface_registry.urlopen")
    def test_query_model_force_refresh(self, mock_urlopen):
        """Test force_refresh bypasses cache."""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = HuggingFaceRegistry(cache_dir=Path(tmpdir))

            # Pre-populate cache
            cached_metadata = ModelMetadata(
                name="gpt2",
                versions=["main"],
                checksums={"main": "cached123"},
                sizes={"main": 999},
                last_updated=datetime.now(),
            )
            registry._save_metadata("gpt2", cached_metadata)

            # Mock API response with different data
            response_data = {
                "id": "gpt2",
                "tags": [],
                "revision": "v2",
                "gated": False,
            }
            mock_response = MagicMock()
            mock_response.read.return_value = json.dumps(response_data).encode()
            mock_response.__enter__.return_value = mock_response
            mock_urlopen.return_value = mock_response

            # Query with force_refresh should call API
            result = registry.query_model("gpt2", force_refresh=True)

            # Should fetch from API (new revision in response)
            assert mock_urlopen.called

    def test_refresh_metadata(self):
        """Test refresh_metadata forces update."""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = HuggingFaceRegistry(cache_dir=Path(tmpdir))

            with patch.object(registry, "query_model") as mock_query:
                mock_query.return_value = ModelMetadata(
                    name="gpt2",
                    versions=["main"],
                    checksums={"main": "abc123"},
                    sizes={"main": 1000000},
                )

                result = registry.refresh_metadata("gpt2")

                # Should call query_model with force_refresh=True
                mock_query.assert_called_once_with("gpt2", force_refresh=True)
                assert result.name == "gpt2"


class TestClearCache:
    """Test cache clearing functionality."""

    def test_clear_single_model(self):
        """Test clearing cache for single model."""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = HuggingFaceRegistry(cache_dir=Path(tmpdir))

            # Cache two models
            for name in ["gpt2", "bert"]:
                metadata = ModelMetadata(
                    name=name,
                    versions=["main"],
                    checksums={"main": "abc123"},
                    sizes={"main": 1000000},
                )
                registry._save_metadata(name, metadata)

            assert len(list(registry.cache_dir.glob("*.json"))) == 2

            # Clear one
            registry.clear_cache("gpt2")

            # Should have one left
            assert len(list(registry.cache_dir.glob("*.json"))) == 1
            assert (registry.cache_dir / "bert.json").exists()

    def test_clear_all_cache(self):
        """Test clearing all cached metadata."""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = HuggingFaceRegistry(cache_dir=Path(tmpdir))

            # Cache multiple models
            for name in ["gpt2", "bert", "roberta"]:
                metadata = ModelMetadata(
                    name=name,
                    versions=["main"],
                    checksums={"main": "abc123"},
                    sizes={"main": 1000000},
                )
                registry._save_metadata(name, metadata)

            assert len(list(registry.cache_dir.glob("*.json"))) == 3

            # Clear all
            registry.clear_cache()

            # Cache directory should be empty
            assert len(list(registry.cache_dir.glob("*.json"))) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
