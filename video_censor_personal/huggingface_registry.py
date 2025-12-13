"""Hugging Face model registry integration for auto-discovery and caching.

This module provides access to Hugging Face model metadata with local caching
to reduce API calls and improve performance.
"""

import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

logger = logging.getLogger(__name__)


class RegistryError(Exception):
    """Base error for registry operations."""

    pass


class ModelNotFoundError(RegistryError):
    """Raised when model not found on Hugging Face."""

    pass


@dataclass
class ModelMetadata:
    """Metadata for a Hugging Face model.

    Attributes:
        name: Model identifier on Hugging Face (e.g., "gpt2")
        versions: List of available versions
        checksums: Mapping of version -> SHA256 checksum
        sizes: Mapping of version -> size in bytes
        deprecated: Whether model is deprecated
        replacement: Suggested replacement if deprecated
        last_updated: When metadata was fetched
    """

    name: str
    versions: List[str]
    checksums: Dict[str, str]
    sizes: Dict[str, int]
    deprecated: bool = False
    replacement: Optional[str] = None
    last_updated: Optional[datetime] = None

    def to_dict(self) -> Dict:
        """Convert to dict for JSON serialization."""
        data = asdict(self)
        if data.get("last_updated"):
            data["last_updated"] = data["last_updated"].isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> "ModelMetadata":
        """Create from dict (deserialize from JSON)."""
        if data.get("last_updated"):
            data["last_updated"] = datetime.fromisoformat(data["last_updated"])
        return cls(**data)


class HuggingFaceRegistry:
    """Query and cache Hugging Face model metadata.

    Provides efficient access to model information with local caching
    to minimize API calls. Metadata is cached with a configurable TTL.
    """

    def __init__(self, cache_dir: Optional[Path] = None, ttl_hours: int = 24):
        """Initialize registry.

        Args:
            cache_dir: Directory for caching metadata. Defaults to
                ~/.cache/video-censor/hf-metadata if not specified.
            ttl_hours: Metadata cache TTL in hours. Defaults to 24.

        Raises:
            ValueError: If ttl_hours <= 0
        """
        if ttl_hours <= 0:
            raise ValueError("ttl_hours must be > 0")

        self.ttl_hours = ttl_hours

        if cache_dir is None:
            # Use platform-appropriate cache dir
            import platformdirs

            cache_dir = Path(
                platformdirs.user_cache_dir("video-censor", "video-censor")
            )

        self.cache_dir = cache_dir / "hf-metadata"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        logger.debug(f"HuggingFaceRegistry initialized: cache_dir={self.cache_dir}")

    def query_model(
        self, model_name: str, force_refresh: bool = False
    ) -> ModelMetadata:
        """Query Hugging Face for model metadata.

        Fetches model information from Hugging Face API, with local caching.
        Respects TTL to minimize API calls.

        Args:
            model_name: Name of model on Hugging Face (e.g., "gpt2")
            force_refresh: If True, bypass cache and fetch from API

        Returns:
            ModelMetadata with available versions and checksums

        Raises:
            ModelNotFoundError: If model not found on Hugging Face
            RegistryError: If API call fails
        """
        # Check cache first (unless force_refresh)
        if not force_refresh:
            cached = self.get_cached_metadata(model_name)
            if cached is not None:
                logger.debug(f"Using cached metadata for {model_name}")
                return cached

        # Fetch from API
        logger.info(f"Querying Hugging Face API for model: {model_name}")
        metadata = self._fetch_from_api(model_name)

        # Cache result
        self._save_metadata(model_name, metadata)

        return metadata

    def get_cached_metadata(self, model_name: str) -> Optional[ModelMetadata]:
        """Get cached metadata if valid (not expired).

        Args:
            model_name: Name of model

        Returns:
            ModelMetadata if cached and valid, None otherwise
        """
        cache_file = self._get_cache_file(model_name)

        if not cache_file.exists():
            return None

        try:
            # Check TTL
            if not self.is_metadata_valid(model_name):
                logger.debug(f"Cached metadata for {model_name} expired")
                return None

            with open(cache_file, "r") as f:
                data = json.load(f)
                return ModelMetadata.from_dict(data)

        except (OSError, json.JSONDecodeError) as e:
            logger.warning(f"Error reading cache for {model_name}: {e}")
            return None

    def is_metadata_valid(self, model_name: str) -> bool:
        """Check if cached metadata is within TTL.

        Args:
            model_name: Name of model

        Returns:
            True if metadata exists and is within TTL
        """
        cache_file = self._get_cache_file(model_name)

        if not cache_file.exists():
            return False

        mtime = cache_file.stat().st_mtime
        age_hours = (datetime.now().timestamp() - mtime) / 3600

        return age_hours < self.ttl_hours

    def refresh_metadata(self, model_name: str) -> ModelMetadata:
        """Force refresh of model metadata (bypass cache, update cache).

        Args:
            model_name: Name of model

        Returns:
            Updated ModelMetadata

        Raises:
            ModelNotFoundError: If model not found
            RegistryError: If API call fails
        """
        logger.info(f"Refreshing metadata for {model_name}")
        return self.query_model(model_name, force_refresh=True)

    def _fetch_from_api(self, model_name: str) -> ModelMetadata:
        """Fetch model metadata from Hugging Face API.

        Args:
            model_name: Name of model

        Returns:
            ModelMetadata

        Raises:
            ModelNotFoundError: If model not found
            RegistryError: If API fails
        """
        url = f"https://huggingface.co/api/models/{model_name}"

        try:
            logger.debug(f"Fetching from {url}")
            with urlopen(url) as response:
                data = json.loads(response.read().decode())

            # Parse response into ModelMetadata
            return self._parse_response(model_name, data)

        except HTTPError as e:
            if e.code == 404:
                raise ModelNotFoundError(
                    f"Model '{model_name}' not found on Hugging Face"
                )
            raise RegistryError(f"HTTP error querying Hugging Face: {e}")
        except URLError as e:
            raise RegistryError(f"Network error querying Hugging Face: {e}")
        except (json.JSONDecodeError, KeyError) as e:
            raise RegistryError(f"Error parsing Hugging Face response: {e}")

    def _parse_response(self, model_name: str, data: Dict) -> ModelMetadata:
        """Parse Hugging Face API response into ModelMetadata.

        Args:
            model_name: Name of model
            data: Raw API response dict

        Returns:
            ModelMetadata

        Raises:
            RegistryError: If response format invalid
        """
        try:
            # Check for deprecation tag
            tags = data.get("tags", [])
            deprecated = "not-for-all-use-cases" in tags or any(
                "deprecated" in tag.lower() for tag in tags
            )

            # Extract version info from siblings (file versions)
            # For simplicity, we'll use the model ID and assume single version for now
            versions = [data.get("revision", "main")]
            checksums = {versions[0]: ""}  # Empty checksum - would need file info
            sizes = {versions[0]: data.get("gated", False) and 0 or 1}

            # Future enhancement: Parse actual file info from model repo
            return ModelMetadata(
                name=model_name,
                versions=versions,
                checksums=checksums,
                sizes=sizes,
                deprecated=deprecated,
                replacement=None,  # Would extract from tags if available
                last_updated=datetime.now(),
            )

        except (KeyError, TypeError) as e:
            raise RegistryError(
                f"Unexpected Hugging Face response format: {e}"
            )

    def _save_metadata(self, model_name: str, metadata: ModelMetadata) -> None:
        """Save metadata to cache.

        Args:
            model_name: Name of model
            metadata: ModelMetadata to cache
        """
        cache_file = self._get_cache_file(model_name)

        try:
            with open(cache_file, "w") as f:
                json.dump(metadata.to_dict(), f, indent=2)
            logger.debug(f"Cached metadata for {model_name}")
        except OSError as e:
            logger.warning(f"Error caching metadata for {model_name}: {e}")

    def _get_cache_file(self, model_name: str) -> Path:
        """Get cache file path for a model.

        Args:
            model_name: Name of model

        Returns:
            Path to cache file
        """
        # Replace slashes with hyphens for file naming
        safe_name = model_name.replace("/", "-")
        return self.cache_dir / f"{safe_name}.json"

    def clear_cache(self, model_name: Optional[str] = None) -> None:
        """Clear metadata cache.

        Args:
            model_name: If specified, clear only this model. Otherwise clear all.
        """
        if model_name:
            cache_file = self._get_cache_file(model_name)
            if cache_file.exists():
                cache_file.unlink()
                logger.debug(f"Cleared cache for {model_name}")
        else:
            import shutil

            if self.cache_dir.exists():
                shutil.rmtree(self.cache_dir)
                self.cache_dir.mkdir(parents=True, exist_ok=True)
                logger.debug("Cleared all metadata cache")
