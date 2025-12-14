"""Utilities for detecting actual model sizes from HuggingFace cache."""

import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def get_hf_cache_dir() -> Path:
    """Get the HuggingFace cache directory.

    Checks environment variables in order of priority:
    1. HF_HUB_CACHE
    2. TRANSFORMERS_CACHE
    3. HF_HOME/hub
    4. ~/.cache/huggingface/hub (default)

    Returns:
        Path to HuggingFace cache directory.
    """
    if os.environ.get("HF_HUB_CACHE"):
        return Path(os.environ["HF_HUB_CACHE"])
    if os.environ.get("TRANSFORMERS_CACHE"):
        return Path(os.environ["TRANSFORMERS_CACHE"])
    if os.environ.get("HF_HOME"):
        return Path(os.environ["HF_HOME"]) / "hub"
    return Path.home() / ".cache" / "huggingface" / "hub"


def get_model_cache_path(model_name: str) -> Optional[Path]:
    """Get the cache path for a specific model.

    Args:
        model_name: HuggingFace model identifier (e.g., "openai/whisper-base").

    Returns:
        Path to model cache directory, or None if not found.
    """
    cache_dir = get_hf_cache_dir()
    
    # Model names are stored with -- separator instead of /
    # e.g., "openai/whisper-base" -> "models--openai--whisper-base"
    safe_name = model_name.replace("/", "--")
    model_path = cache_dir / f"models--{safe_name}"
    
    if model_path.exists():
        return model_path
    
    return None


def get_model_size_bytes(model_name: str) -> Optional[int]:
    """Get the actual size of a cached model in bytes.

    Calculates the total size of all files in the model's cache directory,
    including all snapshots and blobs.

    Args:
        model_name: HuggingFace model identifier (e.g., "openai/whisper-base").

    Returns:
        Size in bytes, or None if model not found in cache.
    """
    model_path = get_model_cache_path(model_name)
    
    if model_path is None:
        logger.debug(f"Model '{model_name}' not found in cache")
        return None
    
    try:
        total_size = 0
        blobs_dir = model_path / "blobs"
        
        if blobs_dir.exists():
            # Count actual blob files (the real data)
            for blob_file in blobs_dir.iterdir():
                if blob_file.is_file():
                    total_size += blob_file.stat().st_size
        else:
            # Fallback: count all files in snapshots
            snapshots_dir = model_path / "snapshots"
            if snapshots_dir.exists():
                for snapshot in snapshots_dir.iterdir():
                    if snapshot.is_dir():
                        for file in snapshot.rglob("*"):
                            if file.is_file() and not file.is_symlink():
                                total_size += file.stat().st_size
        
        if total_size > 0:
            logger.debug(
                f"Model '{model_name}' cache size: {total_size / 1024**2:.1f}MB"
            )
            return total_size
        
        return None
        
    except Exception as e:
        logger.debug(f"Error calculating size for '{model_name}': {e}")
        return None


def get_model_size_with_fallback(
    model_name: str,
    fallback_bytes: int,
) -> int:
    """Get model size from cache, falling back to estimate if not cached.

    Args:
        model_name: HuggingFace model identifier.
        fallback_bytes: Estimated size to use if model not in cache.

    Returns:
        Actual size if cached, otherwise fallback value.
    """
    actual_size = get_model_size_bytes(model_name)
    
    if actual_size is not None:
        return actual_size
    
    logger.debug(
        f"Model '{model_name}' not cached, using estimate: "
        f"{fallback_bytes / 1024**2:.1f}MB"
    )
    return fallback_bytes


# Fallback estimates for common models (used when model not yet cached)
WHISPER_MODEL_ESTIMATES = {
    "tiny": 75 * 1024**2,
    "tiny.en": 75 * 1024**2,
    "base": 150 * 1024**2,
    "base.en": 150 * 1024**2,
    "small": 500 * 1024**2,
    "small.en": 500 * 1024**2,
    "medium": 1500 * 1024**2,
    "medium.en": 1500 * 1024**2,
    "large": 3000 * 1024**2,
    "large-v2": 3000 * 1024**2,
    "large-v3": 3000 * 1024**2,
}

LLAVA_MODEL_ESTIMATES = {
    "7b": 14 * 1024**3,
    "13b": 26 * 1024**3,
}

AST_MODEL_ESTIMATE = 85 * 1024**2  # Audio Spectrogram Transformer


def get_whisper_model_size(model_size: str) -> int:
    """Get Whisper model size (actual or estimated).

    Args:
        model_size: Whisper model size (tiny, base, small, medium, large).

    Returns:
        Size in bytes.
    """
    model_name = f"openai/whisper-{model_size}"
    fallback = WHISPER_MODEL_ESTIMATES.get(
        model_size.lower(),
        150 * 1024**2  # Default to base size
    )
    return get_model_size_with_fallback(model_name, fallback)


def get_llava_model_size(model_name: str) -> int:
    """Get LLaVA model size (actual or estimated).

    Args:
        model_name: Full HuggingFace model name.

    Returns:
        Size in bytes.
    """
    # Determine fallback based on model name
    fallback = 14 * 1024**3  # Default to 7B
    model_lower = model_name.lower()
    for key, size in LLAVA_MODEL_ESTIMATES.items():
        if key in model_lower:
            fallback = size
            break
    
    return get_model_size_with_fallback(model_name, fallback)


def get_audio_classification_model_size(model_name: str) -> int:
    """Get audio classification model size (actual or estimated).

    Args:
        model_name: Full HuggingFace model name.

    Returns:
        Size in bytes.
    """
    return get_model_size_with_fallback(model_name, AST_MODEL_ESTIMATE)
