"""Mock detector for testing without model dependencies.

Returns deterministic results based on frame index for integration testing.
Allows full pipeline validation without downloading large models.
"""

import logging
from typing import Any, Dict, List, Optional

import numpy as np

from video_censor_personal.detection import Detector
from video_censor_personal.frame import DetectionResult

logger = logging.getLogger(__name__)


class MockDetector(Detector):
    """Mock detector for integration testing.

    Returns deterministic detection results based on frame index.
    Useful for validating pipeline logic without downloading models.

    Behavior:
    - Even frames (0, 2, 4, ...): Returns detections for configured categories
    - Odd frames: Returns no detections
    - Confidence varies by frame index (0.5 + 0.3 * (frame_index % 10) / 10)

    This allows testing:
    - Frame iteration and timecode assignment
    - Detection aggregation
    - Segment merging
    - JSON output generation
    - Error handling
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize mock detector.

        Args:
            config: Configuration dict with:
              - name: Detector instance name
              - categories: List of categories to return detections for
              - Optional: enable_nudity, enable_violence, etc. (all default True)

        Raises:
            ValueError: If required config fields are missing.
        """
        super().__init__(config)

        # Optional flags to control which categories return detections
        self.enable_nudity = config.get("enable_nudity", True)
        self.enable_violence = config.get("enable_violence", True)
        self.enable_profanity = config.get("enable_profanity", True)
        self.enable_sexual_theme = config.get("enable_sexual_theme", True)

        logger.debug(
            f"Initialized mock detector '{self.name}' with categories: "
            f"{', '.join(self.categories)}"
        )

    def detect(
        self,
        frame_data: Optional[np.ndarray] = None,
        audio_data: Optional[Any] = None,
    ) -> List[DetectionResult]:
        """Return mock detections based on frame index.

        Mock behavior:
        - If frame_data is None, return empty list (no detections)
        - Extract frame index from shape (deterministic based on call count)
        - On even frame indices: return detections for all enabled categories
        - On odd frame indices: return no detections

        Args:
            frame_data: Frame pixel data (can be None for testing).
            audio_data: Ignored (mock is visual only).

        Returns:
            List of mock DetectionResult objects.
        """
        # If no frame data, return empty
        if frame_data is None:
            return []

        # Use frame pixel sum as pseudo-frame-index for determinism
        # This allows tests to control behavior via frame content
        frame_index = int(np.sum(frame_data) % 100)

        results: List[DetectionResult] = []

        # Only return detections on even frames (0, 2, 4, ...)
        if frame_index % 2 == 0:
            # Calculate confidence based on frame index (varies 0.5-0.8)
            confidence = 0.5 + 0.3 * ((frame_index % 10) / 10.0)

            # Return detections for enabled categories
            category_flags = {
                "Nudity": self.enable_nudity,
                "Violence": self.enable_violence,
                "Profanity": self.enable_profanity,
                "Sexual Theme": self.enable_sexual_theme,
            }

            for category in self.categories:
                if category in category_flags and category_flags[category]:
                    results.append(
                        DetectionResult(
                            start_time=0.0,  # Set by pipeline
                            end_time=0.033,  # Set by pipeline
                            label=category,
                            confidence=confidence,
                            reasoning=f"Mock detection of {category} (deterministic)",
                            description=f"{category} detected by mock detector",
                        )
                    )

        logger.debug(
            f"Mock detector '{self.name}' frame index {frame_index}: "
            f"{len(results)} detection(s)"
        )
        return results
