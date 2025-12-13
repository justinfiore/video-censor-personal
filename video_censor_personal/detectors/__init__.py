"""Detector implementations for content analysis."""

from video_censor_personal.audio_classification_detector import (
    AudioClassificationDetector,
)
from video_censor_personal.detectors.llava_detector import LLaVADetector
from video_censor_personal.detectors.mock_detector import MockDetector
from video_censor_personal.detection import register_detector
from video_censor_personal.speech_profanity_detector import SpeechProfanityDetector

# Register all detector types globally
register_detector("llava", LLaVADetector)
register_detector("mock", MockDetector)
register_detector("speech-profanity", SpeechProfanityDetector)
register_detector("audio-classification", AudioClassificationDetector)

__all__ = [
    "LLaVADetector",
    "MockDetector",
    "SpeechProfanityDetector",
    "AudioClassificationDetector",
]
