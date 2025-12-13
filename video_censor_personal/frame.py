"""Data classes for video frames and audio segments."""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Union

import numpy as np


@dataclass
class Frame:
    """Represents a single video frame with metadata.

    Attributes:
        index: Zero-indexed frame number in sequence.
        timecode: Exact timestamp of frame in seconds.
        data: Frame pixel data as numpy array (BGR format, uint8 dtype).
    """

    index: int
    timecode: float
    data: np.ndarray

    def to_rgb(self) -> np.ndarray:
        """Convert BGR frame to RGB format.

        Returns:
            numpy array in RGB format (uint8 dtype).
        """
        return np.ascontiguousarray(self.data[..., ::-1])

    def timestamp_str(self) -> str:
        """Format timecode as HH:MM:SS.

        Returns:
            Formatted timecode string.
        """
        hours = int(self.timecode // 3600)
        minutes = int((self.timecode % 3600) // 60)
        seconds = int(self.timecode % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


@dataclass
class AudioSegment:
    """Represents an audio segment with metadata.

    Attributes:
        start_time: Start timecode in seconds.
        end_time: End timecode in seconds.
        data: Raw audio data (bytes or numpy array).
        sample_rate: Audio sample rate in Hz (default 16000).
    """

    start_time: float
    end_time: float
    data: Union[bytes, np.ndarray]
    sample_rate: int = 16000

    def duration(self) -> float:
        """Calculate duration of audio segment.

        Returns:
            Duration in seconds.
        """
        return self.end_time - self.start_time


@dataclass
class DetectionResult:
    """Represents a single detection result from a detection engine.

    Attributes:
        start_time: Start timecode in seconds.
        end_time: End timecode in seconds.
        label: Detection category (e.g., "Profanity", "Violence").
        confidence: Confidence score 0.0-1.0.
        reasoning: Human-readable explanation of detection.
        description: Optional segment-level description.
        frame_data: Optional frame metadata (frame_index, timecode, image).
    """

    start_time: float
    end_time: float
    label: str
    confidence: float
    reasoning: str
    description: Optional[str] = None
    frame_data: Optional[Dict[str, Any]] = None

    def __post_init__(self) -> None:
        """Validate DetectionResult fields."""
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(
                f"confidence must be in range [0.0, 1.0], got {self.confidence}"
            )
        if self.end_time < self.start_time:
            raise ValueError(
                f"end_time ({self.end_time}) must be >= start_time "
                f"({self.start_time})"
            )

    def duration(self) -> float:
        """Calculate duration of detection.

        Returns:
            Duration in seconds.
        """
        return self.end_time - self.start_time
