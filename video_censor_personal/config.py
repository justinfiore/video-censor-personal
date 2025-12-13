"""Configuration file parsing and validation."""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import platformdirs
import yaml

logger = logging.getLogger(__name__)

# Required top-level fields in configuration
REQUIRED_FIELDS = {"detections", "processing", "output"}

# Required fields within each section
REQUIRED_DETECTION_FIELDS = {"enabled", "sensitivity", "model"}
REQUIRED_PROCESSING_FIELDS = {"frame_sampling", "segment_merge", "max_workers"}
REQUIRED_OUTPUT_FIELDS = {"format"}


@dataclass
class ModelSource:
    """Represents a downloadable model source.
    
    Attributes:
        name: Model identifier (e.g., "llava-7b")
        url: Full HTTP URL to download model from
        checksum: Hash value for integrity verification
        size_bytes: Expected file size in bytes
        algorithm: Checksum algorithm (default "sha256")
        optional: If True, analysis proceeds if download fails
    """

    name: str
    url: str
    checksum: str
    size_bytes: int
    algorithm: str = "sha256"
    optional: bool = False


@dataclass
class ModelsConfig:
    """Model management configuration.
    
    Attributes:
        cache_dir: Custom cache directory (None = platform default)
        sources: List of available models to download
        auto_download: Pre-configured auto-download (future feature)
    """

    cache_dir: Optional[str] = None
    sources: List[ModelSource] = field(default_factory=list)
    auto_download: bool = False

    def get_cache_dir(self) -> Path:
        """Resolve cache directory from config or platform defaults.
        
        Returns:
            Path to cache directory, using platform-appropriate defaults if not configured
        """
        if self.cache_dir:
            return Path(self.cache_dir).expanduser()
        
        # Use platformdirs for platform-appropriate defaults
        cache_dir = platformdirs.user_cache_dir("video-censor", "censor")
        return Path(cache_dir) / "models"


@dataclass
class Config:
    """Main configuration object.
    
    Attributes:
        models: Model management configuration (optional)
    """

    models: Optional[ModelsConfig] = None


class ConfigError(Exception):
    """Exception raised for configuration errors."""

    pass


def _validate_detection_structure(
    category_name: str, category_config: Dict[str, Any]
) -> None:
    """Validate structure of a single detection category.

    Args:
        category_name: Name of the detection category (e.g., "nudity").
        category_config: Configuration dictionary for the category.

    Raises:
        ConfigError: If required fields are missing or have wrong types.
    """
    if not isinstance(category_config, dict):
        raise ConfigError(
            f"Detection category '{category_name}' must be a dictionary"
        )

    required = {"enabled", "sensitivity", "model"}
    missing = required - set(category_config.keys())
    if missing:
        raise ConfigError(
            f"Detection category '{category_name}' missing required fields: "
            f"{', '.join(sorted(missing))}"
        )

    if not isinstance(category_config["enabled"], bool):
        raise ConfigError(
            f"Detection category '{category_name}' field 'enabled' must be boolean"
        )

    if not isinstance(category_config["sensitivity"], (int, float)):
        raise ConfigError(
            f"Detection category '{category_name}' field 'sensitivity' "
            "must be a number"
        )

    if not isinstance(category_config["model"], str):
        raise ConfigError(
            f"Detection category '{category_name}' field 'model' must be a string"
        )


def _validate_sensitivity_ranges(config: Dict[str, Any]) -> None:
    """Validate all sensitivity values are in range [0.0, 1.0].

    Args:
        config: Configuration dictionary.

    Raises:
        ConfigError: If any sensitivity value is outside [0.0, 1.0].
    """
    detections = config.get("detections", {})
    for category_name, category_config in detections.items():
        if isinstance(category_config, dict):
            sensitivity = category_config.get("sensitivity")
            if isinstance(sensitivity, (int, float)):
                if not (0.0 <= sensitivity <= 1.0):
                    raise ConfigError(
                        f"Detection category '{category_name}' sensitivity "
                        f"{sensitivity} is out of range [0.0, 1.0]"
                    )


def _validate_at_least_one_detection_enabled(
    config: Dict[str, Any],
) -> None:
    """Validate that at least one detection category is enabled.

    Args:
        config: Configuration dictionary.

    Raises:
        ConfigError: If no detection categories have enabled=true.
    """
    detections = config.get("detections", {})
    if not detections:
        raise ConfigError("At least one detection category must be defined")

    any_enabled = False
    for category_config in detections.values():
        if isinstance(category_config, dict) and category_config.get("enabled"):
            any_enabled = True
            break

    if not any_enabled:
        raise ConfigError(
            "At least one detection category must have 'enabled: true'"
        )


def _validate_output_format(config: Dict[str, Any]) -> None:
    """Validate output format is 'json'.

    Args:
        config: Configuration dictionary.

    Raises:
        ConfigError: If output format is not 'json'.
    """
    output = config.get("output", {})
    output_format = output.get("format")

    if output_format != "json":
        raise ConfigError(
            f"Output format '{output_format}' is not supported. "
            "Only 'json' is currently supported."
        )


def _validate_frame_sampling_strategy(config: Dict[str, Any]) -> None:
    """Validate frame sampling strategy is one of allowed values.

    Args:
        config: Configuration dictionary.

    Raises:
        ConfigError: If strategy is not in ('uniform', 'scene_based', 'all').
    """
    processing = config.get("processing", {})
    frame_sampling = processing.get("frame_sampling", {})
    strategy = frame_sampling.get("strategy")

    allowed_strategies = {"uniform", "scene_based", "all"}
    if strategy not in allowed_strategies:
        raise ConfigError(
            f"Frame sampling strategy '{strategy}' is invalid. "
            f"Allowed values: {', '.join(sorted(allowed_strategies))}"
        )


def _validate_max_workers(config: Dict[str, Any]) -> None:
    """Validate max_workers is a positive integer.

    Args:
        config: Configuration dictionary.

    Raises:
        ConfigError: If max_workers is not > 0.
    """
    processing = config.get("processing", {})
    max_workers = processing.get("max_workers")

    if not isinstance(max_workers, int) or max_workers <= 0:
        raise ConfigError(
            f"'processing.max_workers' must be a positive integer, "
            f"got {max_workers}"
        )


def _validate_merge_threshold(config: Dict[str, Any]) -> None:
    """Validate merge_threshold is non-negative.

    Args:
        config: Configuration dictionary.

    Raises:
        ConfigError: If merge_threshold is negative.
    """
    processing = config.get("processing", {})
    segment_merge = processing.get("segment_merge", {})
    merge_threshold = segment_merge.get("merge_threshold")

    if isinstance(merge_threshold, (int, float)) and merge_threshold < 0:
        raise ConfigError(
            f"'processing.segment_merge.merge_threshold' must be non-negative, "
            f"got {merge_threshold}"
        )


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


def _validate_model_source_structure(
    source_name: str, source_config: Dict[str, Any]
) -> None:
    """Validate structure of a single model source.

    Args:
        source_name: Name of the model source.
        source_config: Configuration dictionary for the model source.

    Raises:
        ConfigError: If required fields are missing or have wrong types.
    """
    if not isinstance(source_config, dict):
        raise ConfigError(
            f"Model source '{source_name}' must be a dictionary"
        )

    required = {"name", "url", "checksum", "size_bytes"}
    missing = required - set(source_config.keys())
    if missing:
        raise ConfigError(
            f"Model source '{source_name}' missing required fields: "
            f"{', '.join(sorted(missing))}"
        )

    if not isinstance(source_config["name"], str):
        raise ConfigError(
            f"Model source '{source_name}' field 'name' must be a string"
        )

    if not isinstance(source_config["url"], str):
        raise ConfigError(
            f"Model source '{source_name}' field 'url' must be a string"
        )

    if not isinstance(source_config["checksum"], str):
        raise ConfigError(
            f"Model source '{source_name}' field 'checksum' must be a string"
        )

    if not isinstance(source_config["size_bytes"], int):
        raise ConfigError(
            f"Model source '{source_name}' field 'size_bytes' must be an integer"
        )

    # Optional fields with defaults
    if "algorithm" in source_config and not isinstance(
        source_config["algorithm"], str
    ):
        raise ConfigError(
            f"Model source '{source_name}' field 'algorithm' must be a string"
        )

    if "optional" in source_config and not isinstance(
        source_config["optional"], bool
    ):
        raise ConfigError(
            f"Model source '{source_name}' field 'optional' must be a boolean"
        )


def _validate_models_section(config: Dict[str, Any]) -> None:
    """Validate optional models section if present.

    Args:
        config: Configuration dictionary.

    Raises:
        ConfigError: If models section is invalid.
    """
    models = config.get("models")
    if models is None:
        return  # Optional section

    if not isinstance(models, dict):
        raise ConfigError("'models' field must be a dictionary")

    # Validate cache_dir if present
    if "cache_dir" in models and models["cache_dir"] is not None:
        if not isinstance(models["cache_dir"], str):
            raise ConfigError("'models.cache_dir' must be a string or null")

    # Validate sources list if present
    if "sources" in models:
        sources = models["sources"]
        if sources is not None:
            if not isinstance(sources, list):
                raise ConfigError("'models.sources' must be a list")

            for idx, source_config in enumerate(sources):
                if not isinstance(source_config, dict):
                    raise ConfigError(f"Model source {idx} must be a dictionary")

                source_name = source_config.get("name", f"[index {idx}]")
                _validate_model_source_structure(source_name, source_config)

    # Validate auto_download if present
    if "auto_download" in models:
        if not isinstance(models["auto_download"], bool):
            raise ConfigError("'models.auto_download' must be a boolean")


def _validate_detectors_section(config: Dict[str, Any]) -> None:
    """Validate optional detectors section if present.

    Args:
        config: Configuration dictionary.

    Raises:
        ConfigError: If detectors section is invalid.
    """
    detectors = config.get("detectors")
    if detectors is None:
        return  # Optional section

    if not isinstance(detectors, list):
        raise ConfigError("'detectors' field must be a list")

    for idx, detector_config in enumerate(detectors):
        if not isinstance(detector_config, dict):
            raise ConfigError(f"Detector {idx} must be a dictionary")

        if "type" not in detector_config:
            raise ConfigError(f"Detector {idx} missing required 'type' field")

        if "name" not in detector_config:
            raise ConfigError(f"Detector {idx} missing required 'name' field")

        if "categories" not in detector_config:
            raise ConfigError(f"Detector {idx} missing required 'categories' field")

        categories = detector_config["categories"]
        if not isinstance(categories, list):
            raise ConfigError(
                f"Detector {idx} 'categories' must be a list, got {type(categories)}"
            )

        if not categories:
            raise ConfigError(f"Detector {idx} must declare at least one category")


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

    # Validate each detection category structure
    for category_name, category_config in config["detections"].items():
        _validate_detection_structure(category_name, category_config)

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

    # Validate optional models section if present
    _validate_models_section(config)

    # Validate optional detectors section if present
    _validate_detectors_section(config)

    # Semantic validation
    _validate_sensitivity_ranges(config)
    _validate_at_least_one_detection_enabled(config)
    _validate_output_format(config)
    _validate_frame_sampling_strategy(config)
    _validate_max_workers(config)
    _validate_merge_threshold(config)

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


def get_sample_rate_from_config(config: Dict[str, Any]) -> float:
    """Get frame sample rate from configuration.

    Reads the processing.frame_sampling.sample_rate value from config,
    defaulting to 1.0 if not specified.

    Args:
        config: Configuration dictionary.

    Returns:
        Sample rate in seconds (float). Default is 1.0.
    """
    return get_config_value(config, "processing.frame_sampling.sample_rate", 1.0)
