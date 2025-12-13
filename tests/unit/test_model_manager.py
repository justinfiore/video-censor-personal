"""Unit tests for model manager module."""

import hashlib
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import time

from video_censor_personal.config import Config, ModelSource, ModelsConfig
from video_censor_personal.model_manager import (
    ModelManager,
    ModelDownloadError,
    ModelChecksumError,
    DiskSpaceError,
)


@pytest.fixture
def temp_cache_dir():
    """Create a temporary cache directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_model_source():
    """Create a sample ModelSource for testing."""
    return ModelSource(
        name="test-model",
        url="https://example.com/test-model.bin",
        checksum="abc123def456",
        size_bytes=1000000,
        algorithm="sha256",
        optional=False,
    )


@pytest.fixture
def config_with_cache(temp_cache_dir):
    """Create a config with temporary cache directory."""
    models_config = ModelsConfig(
        cache_dir=str(temp_cache_dir),
        sources=[],
    )
    config = Config()
    config.models = models_config
    return config


class TestModelManagerInit:
    """Tests for ModelManager initialization."""

    def test_init_with_custom_cache_dir(self, config_with_cache, temp_cache_dir):
        """Test initialization with custom cache directory."""
        manager = ModelManager(config_with_cache)
        assert manager.cache_dir == temp_cache_dir

    def test_init_creates_cache_dir(self, config_with_cache, temp_cache_dir):
        """Test that cache directory is created if needed."""
        cache_dir = temp_cache_dir / "nested" / "path"
        config_with_cache.models.cache_dir = str(cache_dir)
        
        manager = ModelManager(config_with_cache)
        # Cache dir created on first access (get_model_path)
        manager.get_model_path("test")
        assert cache_dir.exists()


class TestModelValidation:
    """Tests for model validation (checksum validation)."""

    def test_checksum_validation_pass(self, temp_cache_dir, sample_model_source):
        """Test checksum validation passes with correct hash."""
        config = Config()
        config.models = ModelsConfig(
            cache_dir=str(temp_cache_dir),
            sources=[sample_model_source],
        )
        manager = ModelManager(config)

        # Create test file with known content
        test_file = temp_cache_dir / "test-file.bin"
        test_content = b"test data"
        test_file.write_bytes(test_content)

        # Create source with correct checksum
        correct_hash = hashlib.sha256(test_content).hexdigest()
        source_with_correct_hash = ModelSource(
            name="test-model",
            url="https://example.com/model.bin",
            checksum=correct_hash,
            size_bytes=len(test_content),
        )

        # Should validate successfully
        assert manager._validate_checksum(test_file, source_with_correct_hash) is True

    def test_checksum_validation_fail(self, temp_cache_dir, sample_model_source):
        """Test checksum validation fails with incorrect hash."""
        config = Config()
        config.models = ModelsConfig(
            cache_dir=str(temp_cache_dir),
            sources=[sample_model_source],
        )
        manager = ModelManager(config)

        # Create test file
        test_file = temp_cache_dir / "test-file.bin"
        test_file.write_bytes(b"test data")

        # Source with incorrect checksum
        source_with_wrong_hash = ModelSource(
            name="test-model",
            url="https://example.com/model.bin",
            checksum="wrong_hash_value",
            size_bytes=9,
        )

        # Should fail validation
        assert manager._validate_checksum(test_file, source_with_wrong_hash) is False

    def test_checksum_validation_missing_file(self, temp_cache_dir):
        """Test checksum validation fails when file missing."""
        config = Config()
        config.models = ModelsConfig(cache_dir=str(temp_cache_dir))
        manager = ModelManager(config)

        missing_file = temp_cache_dir / "nonexistent.bin"
        source = ModelSource(
            name="test",
            url="https://example.com/model.bin",
            checksum="hash",
            size_bytes=100,
        )

        assert manager._validate_checksum(missing_file, source) is False

    def test_checksum_algorithm_support(self, temp_cache_dir):
        """Test multiple checksum algorithms."""
        config = Config()
        config.models = ModelsConfig(cache_dir=str(temp_cache_dir))
        manager = ModelManager(config)

        test_file = temp_cache_dir / "test.bin"
        test_content = b"test data for hashing"
        test_file.write_bytes(test_content)

        # Test sha256
        sha256_hash = hashlib.sha256(test_content).hexdigest()
        source_sha256 = ModelSource(
            name="test",
            url="https://example.com/model.bin",
            checksum=sha256_hash,
            size_bytes=len(test_content),
            algorithm="sha256",
        )
        assert manager._validate_checksum(test_file, source_sha256) is True

        # Test md5
        md5_hash = hashlib.md5(test_content).hexdigest()
        source_md5 = ModelSource(
            name="test",
            url="https://example.com/model.bin",
            checksum=md5_hash,
            size_bytes=len(test_content),
            algorithm="md5",
        )
        assert manager._validate_checksum(test_file, source_md5) is True


class TestAtomicDownload:
    """Tests for atomic download operations."""

    def test_atomic_download_success(self, temp_cache_dir, sample_model_source):
        """Test successful atomic download creates model file."""
        config = Config()
        config.models = ModelsConfig(
            cache_dir=str(temp_cache_dir),
            sources=[sample_model_source],
        )
        manager = ModelManager(config)

        # Mock the download_with_retry to create a file with correct checksum
        test_content = b"model data"
        correct_hash = hashlib.sha256(test_content).hexdigest()

        def mock_download(source, attempt, callback):
            temp_file = temp_cache_dir / f".{source.name}.tmp"
            temp_file.write_bytes(test_content)
            return temp_file

        source_with_hash = ModelSource(
            name="test-model",
            url="https://example.com/model.bin",
            checksum=correct_hash,
            size_bytes=len(test_content),
        )

        with patch.object(manager, "_download_with_retry", side_effect=mock_download):
            result = manager._download_model(source_with_hash)

        assert result.exists()
        assert result.read_bytes() == test_content
        # Temp file should be cleaned up
        assert not (temp_cache_dir / ".test-model.tmp").exists()

    def test_atomic_download_temp_cleanup_on_failure(
        self, temp_cache_dir, sample_model_source
    ):
        """Test temp file is cleaned up on download failure."""
        config = Config()
        config.models = ModelsConfig(
            cache_dir=str(temp_cache_dir),
            sources=[sample_model_source],
        )
        manager = ModelManager(config)

        # Mock download_with_retry to raise on all attempts
        def mock_download_fail(source, attempt, callback):
            from urllib.error import URLError
            raise URLError("Network error")

        with patch.object(
            manager, "_download_with_retry", side_effect=mock_download_fail
        ):
            with pytest.raises(ModelDownloadError):
                manager._download_model(sample_model_source)

        # Temp file should be cleaned up
        temp_files = list(temp_cache_dir.glob(".*.tmp"))
        assert len(temp_files) == 0

    def test_download_checksum_validation_failure(self, temp_cache_dir):
        """Test download fails if checksum doesn't match."""
        config = Config()
        config.models = ModelsConfig(cache_dir=str(temp_cache_dir))
        manager = ModelManager(config)

        # Mock download_with_retry to return file with bad checksum
        def mock_download(source, attempt, callback):
            temp_file = temp_cache_dir / f".{source.name}.tmp"
            temp_file.write_bytes(b"wrong data")
            return temp_file

        source = ModelSource(
            name="test-model",
            url="https://example.com/model.bin",
            checksum="wrong_hash",
            size_bytes=10,
        )

        with patch.object(manager, "_download_with_retry", side_effect=mock_download):
            # Should raise ModelDownloadError after retries exhaust
            with pytest.raises(ModelDownloadError, match="after 3 attempts"):
                manager._download_model(source)


class TestDiskSpaceCheck:
    """Tests for disk space verification."""

    def test_disk_space_sufficient(self, temp_cache_dir):
        """Test disk space check passes when sufficient space available."""
        config = Config()
        config.models = ModelsConfig(cache_dir=str(temp_cache_dir))
        manager = ModelManager(config)

        # Should not raise for 1MB (trivial amount)
        manager._check_disk_space(1024 * 1024)

    def test_disk_space_insufficient(self, temp_cache_dir):
        """Test disk space check fails with insufficient space."""
        config = Config()
        config.models = ModelsConfig(cache_dir=str(temp_cache_dir))
        manager = ModelManager(config)

        # Mock disk_usage to return very small free space
        mock_usage = MagicMock()
        mock_usage.free = 1024  # 1KB free
        
        with patch("shutil.disk_usage", return_value=mock_usage):
            # Requesting 1GB should fail
            with pytest.raises(DiskSpaceError, match="Insufficient disk space"):
                manager._check_disk_space(1024 * 1024 * 1024)


class TestRetryLogic:
    """Tests for retry logic with exponential backoff."""

    def test_retry_with_backoff(self, temp_cache_dir, sample_model_source):
        """Test retry logic with exponential backoff."""
        config = Config()
        config.models = ModelsConfig(
            cache_dir=str(temp_cache_dir),
            sources=[sample_model_source],
        )
        manager = ModelManager(config)

        call_count = [0]
        times = []

        def mock_download_fail_then_succeed(source, attempt, callback):
            call_count[0] += 1
            times.append(time.time())
            
            if call_count[0] < 3:
                from urllib.error import URLError
                raise URLError("Network error")
            
            # On 3rd attempt, succeed
            temp_file = temp_cache_dir / f".{source.name}.tmp"
            test_content = b"model"
            temp_file.write_bytes(test_content)
            return temp_file

        # Create source with correct hash
        test_content = b"model"
        correct_hash = hashlib.sha256(test_content).hexdigest()
        source_with_hash = ModelSource(
            name="test-model",
            url="https://example.com/model.bin",
            checksum=correct_hash,
            size_bytes=len(test_content),
        )

        with patch.object(
            manager, "_download_with_retry", side_effect=mock_download_fail_then_succeed
        ):
            result = manager._download_model(source_with_hash)

        assert result.exists()
        assert call_count[0] == 3  # 2 failures + 1 success


class TestModelValidationFlow:
    """Tests for is_model_valid method."""

    def test_is_model_valid_missing(self, temp_cache_dir):
        """Test is_model_valid returns False for missing model."""
        config = Config()
        config.models = ModelsConfig(cache_dir=str(temp_cache_dir))
        manager = ModelManager(config)

        assert manager.is_model_valid("nonexistent-model") is False

    def test_is_model_valid_with_correct_checksum(self, temp_cache_dir):
        """Test is_model_valid returns True with correct checksum."""
        test_content = b"model data"
        correct_hash = hashlib.sha256(test_content).hexdigest()

        source = ModelSource(
            name="test-model",
            url="https://example.com/model.bin",
            checksum=correct_hash,
            size_bytes=len(test_content),
        )

        config = Config()
        config.models = ModelsConfig(
            cache_dir=str(temp_cache_dir),
            sources=[source],
        )
        manager = ModelManager(config)

        # Create the model file
        model_path = manager.get_model_path("test-model")
        model_path.parent.mkdir(parents=True, exist_ok=True)
        model_path.write_bytes(test_content)

        assert manager.is_model_valid("test-model") is True

    def test_is_model_valid_wrong_checksum_removes_file(self, temp_cache_dir):
        """Test is_model_valid removes file with wrong checksum."""
        test_content = b"model data"
        wrong_hash = "wrong_hash_value"

        source = ModelSource(
            name="test-model",
            url="https://example.com/model.bin",
            checksum=wrong_hash,
            size_bytes=len(test_content),
        )

        config = Config()
        config.models = ModelsConfig(
            cache_dir=str(temp_cache_dir),
            sources=[source],
        )
        manager = ModelManager(config)

        # Create the model file
        model_path = manager.get_model_path("test-model")
        model_path.parent.mkdir(parents=True, exist_ok=True)
        model_path.write_bytes(test_content)

        assert model_path.exists()
        assert manager.is_model_valid("test-model") is False
        # File should be removed for re-download
        assert not model_path.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
