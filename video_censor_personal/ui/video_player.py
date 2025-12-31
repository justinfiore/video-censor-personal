from abc import ABC, abstractmethod
from typing import Callable, Optional
import logging

logger = logging.getLogger("video_censor_personal.ui")


class VideoPlayer(ABC):
    """Abstract base class for video playback."""
    
    @abstractmethod
    def load(self, video_path: str) -> None:
        """Load a video file for playback."""
        pass
    
    @abstractmethod
    def play(self) -> None:
        """Start or resume playback."""
        pass
    
    @abstractmethod
    def pause(self) -> None:
        """Pause playback."""
        pass
    
    @abstractmethod
    def seek(self, seconds: float) -> None:
        """Seek to a specific time position in seconds."""
        pass
    
    @abstractmethod
    def get_current_time(self) -> float:
        """Get current playback position in seconds."""
        pass
    
    @abstractmethod
    def on_time_changed(self, callback: Callable[[float], None]) -> None:
        """Register a callback for time change events."""
        pass
    
    @abstractmethod
    def set_playback_rate(self, rate: float) -> None:
        """Set playback speed (1.0 = normal, 0.5 = half speed, 2.0 = double speed)."""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Clean up resources and stop playback."""
        pass
    
    @abstractmethod
    def is_playing(self) -> bool:
        """Check if video is currently playing."""
        pass
    
    @abstractmethod
    def get_duration(self) -> float:
        """Get total duration of loaded video in seconds."""
        pass
