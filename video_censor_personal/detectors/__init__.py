"""Detector implementations for content analysis."""

from video_censor_personal.detectors.llava_detector import LLaVADetector
from video_censor_personal.detectors.mock_detector import MockDetector
from video_censor_personal.detection import register_detector

# Register all detector types globally
register_detector("llava", LLaVADetector)
register_detector("mock", MockDetector)

__all__ = ["LLaVADetector", "MockDetector"]
