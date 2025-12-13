"""Model download and verification management."""

import hashlib
import logging
import shutil
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional
from urllib.request import urlopen
from urllib.error import URLError, HTTPError

import platformdirs
from tqdm import tqdm

from video_censor_personal.config import Config, ModelSource

logger = logging.getLogger(__name__)


class ModelDownloadError(Exception):
    """Base exception for model download failures."""

    pass


class ModelChecksumError(ModelDownloadError):
    """Raised when checksum validation fails."""

    pass


class DiskSpaceError(ModelDownloadError):
    """Raised when insufficient disk space."""

    pass


class ModelNotFoundError(ModelDownloadError):
    """Raised when model cannot be found."""

    pass


class ModelManager:
    """Manages model verification and automatic download.
    
    Handles atomic downloads, checksum validation, retry logic,
    disk space checks, and progress reporting for model files.
    """

    DEFAULT_TIMEOUT = 300  # 5 minutes
    MAX_RETRIES = 3
    RETRY_BACKOFF = [2, 4, 8]  # exponential backoff in seconds

    def __init__(self, config: Config):
        """Initialize ModelManager with configuration.
        
        Args:
            config: Config object with models section
            
        Raises:
            ConfigError: If models config is invalid
        """
        self.config = config
        # Resolve cache directory from config or platform defaults
        if config.models and config.models.cache_dir:
            self.cache_dir = Path(config.models.cache_dir).expanduser()
        else:
            self.cache_dir = self._get_platform_cache_dir()
        
        logger.debug(f"Model cache directory: {self.cache_dir}")

    @staticmethod
    def _get_platform_cache_dir() -> Path:
        """Get platform-appropriate cache directory.
        
        Returns:
            Path to cache directory using platformdirs
        """
        cache_dir = platformdirs.user_cache_dir("video-censor", "censor")
        return Path(cache_dir) / "models"

    def verify_models(
        self,
        sources: Optional[List[ModelSource]] = None,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> Dict[str, bool]:
        """Verify and download missing models.
        
        Checks if models exist in cache with valid checksums.
        Downloads missing models with automatic retries and checksum validation.
        
        Args:
            sources: List of ModelSource to verify. If None, use config.models.sources
            progress_callback: Optional callback(model_name, bytes_done, total_bytes)
            
        Returns:
            Dict mapping model name → True if verified/downloaded, 
            False if optional and failed
            
        Raises:
            ModelDownloadError: If required model download fails
            DiskSpaceError: If insufficient disk space
        """
        if sources is None:
            if not self.config.models or not self.config.models.sources:
                logger.info("No models to verify")
                return {}
            sources = self.config.models.sources

        results = {}

        # Calculate total download size for disk space check
        total_size = sum(
            source.size_bytes
            for source in sources
            if not self.is_model_valid(source.name)
        )

        if total_size > 0:
            self._check_disk_space(total_size)

        for source in sources:
            try:
                if self.is_model_valid(source.name):
                    logger.info(f"Model {source.name} already valid, skipping")
                    results[source.name] = True
                    continue

                logger.info(f"Downloading model: {source.name}")
                self._download_model(source, progress_callback)
                results[source.name] = True
                logger.info(f"Successfully verified {source.name}")

            except ModelDownloadError as e:
                if source.optional:
                    logger.warning(
                        f"Optional model {source.name} download failed: {e}"
                    )
                    results[source.name] = False
                else:
                    logger.error(f"Required model {source.name} download failed: {e}")
                    raise

        return results

    def is_model_valid(self, model_name: str) -> bool:
        """Check if model exists in cache with valid checksum.
        
        Args:
            model_name: Name of model (matches ModelSource.name)
            
        Returns:
            True if model exists and checksum matches, False otherwise
        """
        model_path = self.get_model_path(model_name)

        if not model_path.exists():
            logger.debug(f"Model {model_name} not found at {model_path}")
            return False

        # Get the source config for checksum
        if not self.config.models or not self.config.models.sources:
            return False

        source = next(
            (s for s in self.config.models.sources if s.name == model_name), None
        )
        if not source:
            logger.warning(f"Model {model_name} not in configuration sources")
            return False

        # Verify checksum
        try:
            is_valid = self._validate_checksum(model_path, source)
            if is_valid:
                logger.debug(f"Model {model_name} checksum valid")
            else:
                logger.warning(f"Model {model_name} checksum mismatch, will re-download")
                model_path.unlink()
            return is_valid
        except Exception as e:
            logger.error(f"Error validating {model_name}: {e}")
            return False

    def get_model_path(self, model_name: str) -> Path:
        """Get cached path for a model.
        
        Args:
            model_name: Name of model
            
        Returns:
            Path to model file (may not exist)
        """
        # Create cache directory if needed
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        return self.cache_dir / model_name

    def _check_disk_space(self, required_bytes: int) -> None:
        """Check if sufficient disk space is available.
        
        Requires 2x the model size free space (for temp file + cache).
        
        Args:
            required_bytes: Number of bytes required
            
        Raises:
            DiskSpaceError: If insufficient space available
        """
        # Ensure cache directory exists for stat
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        stat = shutil.disk_usage(self.cache_dir)
        available = stat.free
        required_with_buffer = required_bytes * 2

        if available < required_with_buffer:
            required_gb = required_with_buffer / (1024**3)
            available_gb = available / (1024**3)
            raise DiskSpaceError(
                f"Insufficient disk space. Required: {required_gb:.2f}GB, "
                f"Available: {available_gb:.2f}GB. "
                f"Free up space or set models.cache_dir to a different location."
            )

        logger.debug(
            f"Disk space check passed: {available / (1024**3):.2f}GB available"
        )

    def _download_model(
        self,
        source: ModelSource,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> Path:
        """Download a single model with retries and progress reporting.
        
        Uses atomic downloads (temp file) to prevent cache corruption.
        Validates checksum after download completes.
        
        Args:
            source: ModelSource configuration
            progress_callback: Optional callback for progress updates
            
        Returns:
            Path to downloaded model
            
        Raises:
            ModelDownloadError: If download fails after retries
            ModelChecksumError: If checksum validation fails
        """
        temp_file = None

        for attempt in range(self.MAX_RETRIES):
            try:
                temp_file = self._download_with_retry(
                    source, attempt, progress_callback
                )
                
                # Validate checksum
                if not self._validate_checksum(temp_file, source):
                    raise ModelChecksumError(
                        f"Checksum validation failed for {source.name}"
                    )

                # Atomic move to cache
                model_path = self.get_model_path(source.name)
                temp_file.replace(model_path)
                logger.info(f"Model {source.name} downloaded successfully")
                return model_path

            except (URLError, HTTPError, ModelChecksumError) as e:
                if temp_file and temp_file.exists():
                    temp_file.unlink()

                if attempt < self.MAX_RETRIES - 1:
                    wait_time = self.RETRY_BACKOFF[attempt]
                    logger.warning(
                        f"Attempt {attempt + 1}/{self.MAX_RETRIES} failed for "
                        f"{source.name}: {e}. Retrying in {wait_time}s..."
                    )
                    time.sleep(wait_time)
                else:
                    raise ModelDownloadError(
                        f"Failed to download {source.name} after {self.MAX_RETRIES} "
                        f"attempts. URL: {source.url}. Error: {e}"
                    )

        raise ModelDownloadError(f"Unexpected error downloading {source.name}")

    def _download_with_retry(
        self,
        source: ModelSource,
        attempt: int,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> Path:
        """Download model to temporary file with progress reporting.
        
        Args:
            source: ModelSource configuration
            attempt: Current attempt number (for logging)
            progress_callback: Optional callback(model_name, bytes_done, total_bytes)
            
        Returns:
            Path to temporary file
            
        Raises:
            URLError: If download fails
            HTTPError: If HTTP error occurs
        """
        # Create temp file in cache directory for atomicity
        temp_file = self.cache_dir / f".{source.name}.tmp"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        logger.debug(
            f"Downloading {source.name} from {source.url} "
            f"(attempt {attempt + 1}/{self.MAX_RETRIES})"
        )

        try:
            response = urlopen(source.url, timeout=self.DEFAULT_TIMEOUT)
            total_size = int(response.headers.get("content-length", 0))

            with open(temp_file, "wb") as f:
                downloaded = 0
                chunk_size = 8192

                with tqdm(
                    total=total_size,
                    unit="B",
                    unit_scale=True,
                    desc=source.name,
                    disable=progress_callback is not None,
                ) as pbar:
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break

                        f.write(chunk)
                        downloaded += len(chunk)
                        pbar.update(len(chunk))

                        if progress_callback:
                            progress_callback(source.name, downloaded, total_size)

            return temp_file

        except Exception as e:
            if temp_file.exists():
                temp_file.unlink()
            raise

    def _validate_checksum(self, file_path: Path, source: ModelSource) -> bool:
        """Validate file checksum against source configuration.
        
        Supports multiple hash algorithms (sha256, md5, etc.).
        
        Args:
            file_path: Path to file to validate
            source: ModelSource with checksum and algorithm
            
        Returns:
            True if checksum matches, False otherwise
            
        Raises:
            ValueError: If algorithm not supported
        """
        if not file_path.exists():
            return False

        algorithm = source.algorithm.lower()
        
        try:
            hasher = hashlib.new(algorithm)
        except ValueError:
            raise ValueError(
                f"Unsupported checksum algorithm: {algorithm}. "
                f"Supported: {', '.join(hashlib.algorithms_available)}"
            )

        logger.debug(f"Computing {algorithm} checksum for {file_path.name}")

        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                hasher.update(chunk)

        computed = hasher.hexdigest()
        expected = source.checksum.lower()

        if computed == expected:
            logger.debug(f"Checksum valid for {file_path.name}")
            return True
        else:
            logger.warning(
                f"Checksum mismatch for {file_path.name}. "
                f"Expected {expected}, got {computed}"
            )
            return False
