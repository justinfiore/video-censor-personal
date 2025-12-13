"""Detection framework for content analysis."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import numpy as np

from video_censor_personal.frame import DetectionResult, Frame

logger = logging.getLogger(__name__)


class Detector(ABC):
    """Abstract base class for all detectors.
    
    Detectors analyze frames and/or audio to identify multiple content categories
    in a single inference pass.
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize detector with configuration.

        Args:
            config: Detector-specific config (name, categories, model, thresholds, etc.)

        Raises:
            ValueError: If required config fields are missing.
        """
        if not isinstance(config, dict):
            raise ValueError("Detector config must be a dictionary")

        self.config = config
        self.name = config.get("name", self.__class__.__name__)

        # Validate and store categories this detector covers
        categories = config.get("categories", [])
        if not isinstance(categories, list):
            raise ValueError(f"Detector '{self.name}' categories must be a list")
        if not categories:
            raise ValueError(f"Detector '{self.name}' must declare at least one category")

        self.categories = categories
        logger.debug(
            f"Initialized detector '{self.name}' for categories: {', '.join(categories)}"
        )

    @abstractmethod
    def detect(
        self,
        frame_data: Optional[np.ndarray] = None,
        audio_data: Optional[Any] = None,
    ) -> List[DetectionResult]:
        """Analyze frame and/or audio data, return detections for all identified categories.

        Args:
            frame_data: Frame pixel data as numpy array (BGR, uint8) or None.
            audio_data: Audio data (numpy array or bytes) or None.

        Returns:
            List of DetectionResult objects (one per category identified).
            Empty list if no detections found.

        Raises:
            ValueError: If both frame_data and audio_data are None.
        """
        pass

    def cleanup(self) -> None:
        """Clean up detector resources (models, temp files, etc.).

        Override in subclasses if cleanup is needed.
        """
        pass


class DetectorRegistry:
    """Registry for detector implementations.

    Allows registration and instantiation of detector types.
    """

    def __init__(self) -> None:
        """Initialize empty detector registry."""
        self._detectors: Dict[str, type] = {}

    def register(self, detector_type: str, detector_class: type) -> None:
        """Register a detector implementation.

        Args:
            detector_type: Name/type of detector (e.g., "llama-vision", "stub").
            detector_class: Detector class to register (must be subclass of Detector).

        Raises:
            TypeError: If detector_class is not a Detector subclass.
        """
        if not issubclass(detector_class, Detector):
            raise TypeError(
                f"Detector class {detector_class} must be subclass of Detector"
            )
        self._detectors[detector_type] = detector_class
        logger.debug(f"Registered detector type: {detector_type}")

    def get(self, detector_type: str) -> Optional[type]:
        """Get registered detector class by type.

        Args:
            detector_type: Name/type of detector.

        Returns:
            Detector class or None if not registered.
        """
        return self._detectors.get(detector_type)

    def create(self, detector_type: str, config: Dict[str, Any]) -> Detector:
        """Create detector instance with given configuration.

        Args:
            detector_type: Name/type of detector.
            config: Configuration dictionary for detector.

        Returns:
            Detector instance.

        Raises:
            ValueError: If detector_type is not registered.
        """
        detector_class = self.get(detector_type)
        if not detector_class:
            available = ", ".join(sorted(self._detectors.keys()))
            raise ValueError(
                f"Unknown detector type: {detector_type}. "
                f"Available types: {available}"
            )
        return detector_class(config)

    def registered_types(self) -> List[str]:
        """Get list of all registered detector types.

        Returns:
            Sorted list of detector type names.
        """
        return sorted(self._detectors.keys())


# Global registry instance
_registry = DetectorRegistry()


def register_detector(detector_type: str, detector_class: type) -> None:
    """Register a detector type globally.

    Args:
        detector_type: Name/type of detector.
        detector_class: Detector class to register.
    """
    _registry.register(detector_type, detector_class)


def get_detector_registry() -> DetectorRegistry:
    """Get global detector registry.

    Returns:
        DetectorRegistry instance.
    """
    return _registry


class DetectionPipeline:
    """Orchestrates detector execution across multiple detectors.

    Runs detectors sequentially on frames/audio and aggregates results.
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize detection pipeline with detector configurations.

        Args:
            config: Configuration dictionary with 'detectors' key containing list of detector configs.

        Raises:
            ValueError: If detector configuration is invalid.
        """
        self.config = config
        self.detectors: List[Detector] = []
        self._registry = get_detector_registry()
        self._initialize_detectors()

    def _initialize_detectors(self) -> None:
        """Create detector instances from configuration.

        Raises:
            ValueError: If detector config is invalid.
        """
        detector_configs = self.config.get("detectors", [])

        if not isinstance(detector_configs, list):
            raise ValueError("'detectors' config must be a list")

        if not detector_configs:
            logger.warning("No detectors configured in pipeline")
            return

        for detector_config in detector_configs:
            if not isinstance(detector_config, dict):
                raise ValueError("Each detector config must be a dictionary")

            detector_type = detector_config.get("type")
            if not detector_type:
                raise ValueError("Detector config missing required 'type' field")

            try:
                detector = self._registry.create(detector_type, detector_config)
                self.detectors.append(detector)
                logger.info(
                    f"Initialized detector '{detector.name}' of type '{detector_type}'"
                )
            except Exception as e:
                raise ValueError(
                    f"Failed to initialize detector '{detector_config.get('name', 'unknown')}' "
                    f"of type '{detector_type}': {e}"
                )

    def analyze_frame(
        self,
        frame: Frame,
        audio_data: Optional[Any] = None,
    ) -> List[DetectionResult]:
        """Run all detectors on frame and aggregate results.

        Args:
            frame: Frame object with pixel data and timecode.
            audio_data: Optional audio data for audio-based detectors.

        Returns:
            List of DetectionResult objects with assigned timecodes.
        """
        all_results: List[DetectionResult] = []

        for detector in self.detectors:
            try:
                results = detector.detect(frame_data=frame.data, audio_data=audio_data)

                # Assign frame timecode to all results
                for result in results:
                    result.start_time = frame.timecode
                    # Use a minimal duration (one frame at ~30fps ≈ 0.033 seconds)
                    result.end_time = frame.timecode + 0.033

                all_results.extend(results)
                logger.debug(
                    f"Detector '{detector.name}' found {len(results)} detections"
                )

            except Exception as e:
                logger.error(
                    f"Detector '{detector.name}' failed during analysis: {e}",
                    exc_info=True,
                )
                # Continue with other detectors
                continue

        return all_results

    def cleanup(self) -> None:
        """Clean up all detectors and release resources.

        Calls cleanup on each detector in reverse order.
        """
        for detector in reversed(self.detectors):
            try:
                detector.cleanup()
                logger.debug(f"Cleaned up detector '{detector.name}'")
            except Exception as e:
                logger.error(f"Error cleaning up detector '{detector.name}': {e}")
