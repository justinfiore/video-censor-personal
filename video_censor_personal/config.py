"""Configuration file parsing and validation."""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

logger = logging.getLogger(__name__)

# Required top-level fields in configuration
REQUIRED_FIELDS = {"detections", "processing", "output"}

# Required fields within each section
REQUIRED_DETECTION_FIELDS = {"enabled", "sensitivity", "model"}
REQUIRED_PROCESSING_FIELDS = {"frame_sampling", "segment_merge", "max_workers"}
REQUIRED_OUTPUT_FIELDS = {"format"}


class ConfigError(Exception):
    """Exception raised for configuration errors."""

    pass


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load and validate YAML configuration file.

    Args:
        config_path: Path to configuration file. If None, uses default locations.

    Returns:
        Dict containing parsed configuration.

    Raises:
        ConfigError: If configuration file is invalid or required fields missing.
    """
    # Determine config path
    if config_path:
        path = Path(config_path)
    else:
        # Check default locations
        defaults = [Path("./video-censor.yaml"), Path("./config.yaml")]
        path = None
        for default in defaults:
            if default.exists():
                path = default
                logger.info(f"Using default configuration: {path}")
                break

        if path is None:
            raise ConfigError(
                "No configuration file specified and no default found. "
                "Checked: ./video-censor.yaml, ./config.yaml"
            )

    # Load YAML file
    if not path.exists():
        raise ConfigError(f"Configuration file not found: {path}")

    try:
        with open(path, "r") as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigError(f"Invalid YAML syntax in {path}: {e}")
    except Exception as e:
        raise ConfigError(f"Error reading configuration file {path}: {e}")

    if config is None:
        raise ConfigError(f"Configuration file {path} is empty")

    # Validate required fields
    validate_config(config)

    logger.debug(f"Configuration loaded successfully from {path}")
    return config


def validate_config(config: Dict[str, Any]) -> None:
    """Validate configuration structure and required fields.

    Args:
        config: Configuration dictionary to validate.

    Raises:
        ConfigError: If required fields are missing or invalid.
    """
    if not isinstance(config, dict):
        raise ConfigError("Configuration must be a dictionary/mapping")

    # Check top-level required fields
    missing = REQUIRED_FIELDS - set(config.keys())
    if missing:
        raise ConfigError(
            f"Configuration missing required fields: {', '.join(sorted(missing))}"
        )

    # Validate detections section
    if not isinstance(config["detections"], dict):
        raise ConfigError("'detections' field must be a dictionary")

    # Validate processing section
    if not isinstance(config["processing"], dict):
        raise ConfigError("'processing' field must be a dictionary")

    processing = config["processing"]
    if "frame_sampling" not in processing:
        raise ConfigError(
            "'processing.frame_sampling' is required but missing"
        )
    if "segment_merge" not in processing:
        raise ConfigError(
            "'processing.segment_merge' is required but missing"
        )
    if "max_workers" not in processing:
        raise ConfigError("'processing.max_workers' is required but missing")

    # Validate output section
    if not isinstance(config["output"], dict):
        raise ConfigError("'output' field must be a dictionary")

    output = config["output"]
    if "format" not in output:
        raise ConfigError("'output.format' is required but missing")

    logger.debug("Configuration validation passed")


def get_config_value(config: Dict[str, Any], path: str, default: Any = None) -> Any:
    """Get a nested value from configuration using dot notation.

    Args:
        config: Configuration dictionary.
        path: Dot-separated path (e.g., "detections.nudity.enabled").
        default: Default value if path not found.

    Returns:
        Configuration value or default.
    """
    keys = path.split(".")
    value = config

    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return default

    return value
