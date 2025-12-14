"""GPU device detection and configuration utilities."""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def get_device(config_override: Optional[str] = None) -> str:
    """Detect and return the best available compute device.

    Checks for GPU availability in order: CUDA → MPS → CPU.
    Allows manual override via config_override parameter.

    Args:
        config_override: Optional device name to use instead of auto-detection.
            Valid values: "cuda", "mps", "cpu", or None for auto-detection.

    Returns:
        Device string suitable for PyTorch: "cuda", "mps", or "cpu".

    Raises:
        ValueError: If config_override specifies an unavailable device.
    """
    import torch

    if config_override is not None:
        device = config_override.lower().strip()
        
        if device == "cuda":
            if not torch.cuda.is_available():
                raise ValueError(
                    f"Device 'cuda' requested but CUDA is not available. "
                    f"Available options: {_get_available_devices()}"
                )
            logger.info("Using device: cuda (manual override)")
            return "cuda"
        
        elif device == "mps":
            if not (hasattr(torch.backends, "mps") and torch.backends.mps.is_available()):
                raise ValueError(
                    f"Device 'mps' requested but MPS is not available. "
                    f"Available options: {_get_available_devices()}"
                )
            logger.info("Using device: mps (manual override)")
            return "mps"
        
        elif device == "cpu":
            logger.info("Using device: cpu (manual override)")
            return "cpu"
        
        else:
            raise ValueError(
                f"Unknown device '{device}'. "
                f"Available options: {_get_available_devices()}"
            )

    if torch.cuda.is_available():
        logger.info("Using device: cuda")
        return "cuda"

    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        logger.info("Using device: mps")
        return "mps"

    logger.info("Using device: cpu (no GPU available)")
    return "cpu"


def _get_available_devices() -> list:
    """Return list of available device options."""
    import torch

    devices = ["cpu"]
    if torch.cuda.is_available():
        devices.insert(0, "cuda")
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        devices.insert(0, "mps")
    return devices
