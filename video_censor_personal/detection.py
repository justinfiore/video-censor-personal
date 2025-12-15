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

    def supports_full_audio_analysis(self) -> bool:
        """Check if detector supports full audio analysis mode.

        Override to return True if detector implements analyze_full_audio().

        Returns:
            True if analyze_full_audio() is implemented, False otherwise.
        """
        return False

    def analyze_full_audio(
        self,
        audio_data: np.ndarray,
        sample_rate: int = 16000,
    ) -> List[DetectionResult]:
        """Analyze complete audio track and return timestamped detections.

        This method processes the entire audio once and returns results with
        accurate start_time/end_time values. More efficient than per-frame
        processing for audio-only detectors.

        Args:
            audio_data: Complete audio as numpy array (mono, float32).
            sample_rate: Audio sample rate in Hz (default: 16000).

        Returns:
            List of DetectionResult objects with accurate timestamps.

        Raises:
            NotImplementedError: If detector doesn't support full audio analysis.
        """
        raise NotImplementedError(
            f"Detector '{self.name}' does not support full audio analysis"
        )

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
    Supports lazy initialization to avoid loading all models at once.
    """

    def __init__(self, config: Dict[str, Any], lazy_init: bool = False) -> None:
        """Initialize detection pipeline with detector configurations.

        Args:
            config: Configuration dictionary with 'detectors' key containing list of detector configs.
            lazy_init: If True, defer detector initialization until needed.

        Raises:
            ValueError: If detector configuration is invalid.
        """
        self.config = config
        self.detectors: List[Detector] = []
        self._registry = get_detector_registry()
        self._detector_configs: List[Dict[str, Any]] = []
        self._audio_detectors_initialized = False
        self._frame_detectors_initialized = False

        # Parse and validate configs
        self._parse_detector_configs()

        if not lazy_init:
            self._initialize_all_detectors()

    def _parse_detector_configs(self) -> None:
        """Parse and validate detector configurations without initializing."""
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

            # Validate detector type exists
            if not self._registry.get(detector_type):
                available = ", ".join(sorted(self._registry.registered_types()))
                raise ValueError(
                    f"Unknown detector type: {detector_type}. "
                    f"Available types: {available}"
                )

            self._detector_configs.append(detector_config)

    def download_models(self) -> None:
        """Download all required detector models before initialization.

        Calls static download_model() method on each detector class that supports it.
        Logs progress and handles errors gracefully (skips failed models, continues).
        """
        logger.info("Downloading detector models...")

        for detector_config in self._detector_configs:
            detector_type = detector_config.get("type")
            detector_class = self._registry.get(detector_type)

            if not detector_class:
                logger.warning(f"Unknown detector type: {detector_type}")
                continue

            # Check if detector has static download_model method
            if not hasattr(detector_class, "download_model"):
                logger.debug(f"Detector type '{detector_type}' does not support model download")
                continue

            try:
                # Call static download_model with detector-specific config
                model_name = detector_config.get("model_name")
                model_path = detector_config.get("model_path")

                if model_name:
                    logger.info(f"  Downloading {detector_type} model '{model_name}'...")
                    detector_class.download_model(model_name, model_path)
                    logger.info(f"  ✓ {model_name} ready")
                else:
                    logger.debug(
                        f"Detector '{detector_config.get('name', detector_type)}' "
                        f"has no model_name, skipping download"
                    )

            except Exception as e:
                logger.error(
                    f"Failed to download model for detector '{detector_type}': {e}\n"
                    f"Continuing with remaining models..."
                )

        logger.info("Model download complete")

    def _initialize_all_detectors(self) -> None:
        """Initialize all detectors at once."""
        for detector_config in self._detector_configs:
            self._create_detector(detector_config)

    def _create_detector(self, detector_config: Dict[str, Any]) -> Detector:
        """Create a single detector instance."""
        detector_type = detector_config.get("type")
        try:
            detector = self._registry.create(detector_type, detector_config)
            self.detectors.append(detector)
            logger.info(
                f"Initialized detector '{detector.name}' of type '{detector_type}'"
            )
            return detector
        except Exception as e:
            raise ValueError(
                f"Failed to initialize detector '{detector_config.get('name', 'unknown')}' "
                f"of type '{detector_type}': {e}"
            )

    def initialize_audio_detectors(self) -> None:
        """Initialize only audio-based detectors (those supporting full audio analysis).

        Call this before analyze_full_audio() when using lazy initialization.
        """
        if self._audio_detectors_initialized:
            return

        # Audio detector types
        audio_types = {"speech-profanity", "audio-classification"}

        for detector_config in self._detector_configs:
            detector_type = detector_config.get("type")
            if detector_type in audio_types:
                self._create_detector(detector_config)

        self._audio_detectors_initialized = True

    def initialize_frame_detectors(self) -> None:
        """Initialize only frame-based detectors (visual/video).

        Call this before frame analysis when using lazy initialization.
        """
        if self._frame_detectors_initialized:
            return

        # Audio detector types to exclude
        audio_types = {"speech-profanity", "audio-classification"}

        for detector_config in self._detector_configs:
            detector_type = detector_config.get("type")
            if detector_type not in audio_types:
                self._create_detector(detector_config)

        self._frame_detectors_initialized = True

    def cleanup_audio_detectors(self) -> None:
        """Clean up and release audio detectors to free GPU memory."""
        audio_detectors = [d for d in self.detectors if d.supports_full_audio_analysis()]
        for detector in audio_detectors:
            try:
                detector.cleanup()
                logger.debug(f"Cleaned up audio detector '{detector.name}'")
            except Exception as e:
                logger.error(f"Error cleaning up detector '{detector.name}': {e}")

        # Remove from list
        self.detectors = [d for d in self.detectors if not d.supports_full_audio_analysis()]

    def analyze_full_audio(
        self,
        audio_data: np.ndarray,
        sample_rate: int = 16000,
    ) -> List[DetectionResult]:
        """Run full-audio analysis on detectors that support it.

        This should be called once before frame processing to efficiently
        analyze audio-only detectors like speech-profanity.

        Args:
            audio_data: Complete audio as numpy array (mono, float32).
            sample_rate: Audio sample rate in Hz (default: 16000).

        Returns:
            List of DetectionResult objects with accurate timestamps.
        """
        all_results: List[DetectionResult] = []

        for detector in self.detectors:
            if not detector.supports_full_audio_analysis():
                continue

            try:
                logger.info(f"Running full audio analysis with '{detector.name}'...")
                results = detector.analyze_full_audio(audio_data, sample_rate)
                all_results.extend(results)
                logger.info(
                    f"Detector '{detector.name}' found {len(results)} audio detections"
                )
            except Exception as e:
                logger.error(
                    f"Detector '{detector.name}' failed during full audio analysis: {e}",
                    exc_info=True,
                )
                continue

        return all_results

    def get_frame_detectors(self) -> List[Detector]:
        """Get detectors that process frames (not full-audio-only).

        Returns:
            List of detectors that should run per-frame.
        """
        return [d for d in self.detectors if not d.supports_full_audio_analysis()]

    def analyze_frame(
        self,
        frame: Frame,
        audio_data: Optional[Any] = None,
    ) -> List[DetectionResult]:
        """Run frame-based detectors on frame and aggregate results.

        Only runs detectors that don't support full_audio_analysis.
        Audio-only detectors should be run via analyze_full_audio() instead.

        Args:
            frame: Frame object with pixel data and timecode.
            audio_data: Optional audio data for audio-based detectors.

        Returns:
            List of DetectionResult objects with assigned timecodes.
        """
        all_results: List[DetectionResult] = []

        for detector in self.detectors:
            if detector.supports_full_audio_analysis():
                continue

            try:
                results = detector.detect(frame_data=frame.data, audio_data=audio_data)

                for result in results:
                    result.start_time = frame.timecode
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
