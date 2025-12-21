from abc import ABC, abstractmethod
from typing import Callable, Optional
import logging
import traceback

logger = logging.getLogger("video_censor_personal.ui")

try:
    import vlc
    VLC_AVAILABLE = True
except (ImportError, OSError):
    VLC_AVAILABLE = False
    vlc = None


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
    def set_volume(self, level: float) -> None:
        """Set volume level (0.0 to 1.0)."""
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


class VLCVideoPlayer(VideoPlayer):
    """VLC-based video player implementation."""
    
    def __init__(self, video_widget=None):
        """Initialize VLC player.
        
        Args:
            video_widget: Optional widget/canvas to embed video output
            
        Raises:
            RuntimeError: If VLC is not available
        """
        if not VLC_AVAILABLE or vlc is None:
            raise RuntimeError("VLC library not available. Install VLC and python-vlc.")
        
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()
        self._video_widget = video_widget
        self._time_callback: Optional[Callable[[float], None]] = None
        self._last_time = 0.0
        
        if video_widget:
            self._attach_to_widget(video_widget)
    
    @property
    def video_widget(self):
        """Get the current video widget."""
        return self._video_widget
    
    @video_widget.setter
    def video_widget(self, widget):
        """Set the video widget and attach VLC to it."""
        self._video_widget = widget
        if widget:
            self._attach_to_widget(widget)
    
    def _attach_to_widget(self, widget) -> None:
        """Attach VLC output to a widget window."""
        try:
            import sys
            widget_id = widget.winfo_id()
            logger.info(f"Attaching VLC to widget on platform {sys.platform}, widget_id={widget_id}")
            
            if sys.platform.startswith('linux'):
                logger.info("Using set_xwindow")
                self.player.set_xwindow(widget_id)
            elif sys.platform == 'darwin':
                logger.warning("Video output not supported on macOS with tkinter. Audio-only mode enabled.")
                # macOS has issues with VLC and tkinter OpenGL rendering
                # Just play audio without video output
            elif sys.platform == 'win32':
                logger.info("Using set_hwnd")
                self.player.set_hwnd(widget_id)
            else:
                logger.warning(f"Unknown platform: {sys.platform}")
            
            logger.info("VLC widget attachment complete")
        except Exception as e:
            logger.error(f"Failed to attach VLC to widget: {str(e)}")
            logger.error(traceback.format_exc())
            raise
    
    def load(self, video_path: str) -> None:
        """Load a video file for playback."""
        try:
            logger.info(f"Loading video: {video_path}")
            media = self.instance.media_new(video_path)
            logger.info("Media object created")
            self.player.set_media(media)
            logger.info("Media set to player")
            media.parse()
            logger.info("Media parsed successfully")
        except Exception as e:
            logger.error(f"Failed to load video: {str(e)}")
            logger.error(traceback.format_exc())
            raise
    
    def play(self) -> None:
        """Start or resume playback."""
        try:
            logger.info("Calling player.play()")
            self.player.play()
            logger.info("Play command sent")
        except Exception as e:
            logger.error(f"Failed to play: {str(e)}")
            logger.error(traceback.format_exc())
            raise
    
    def pause(self) -> None:
        """Pause playback."""
        try:
            logger.info("Calling player.pause()")
            self.player.pause()
            logger.info("Pause command sent")
        except Exception as e:
            logger.error(f"Failed to pause: {str(e)}")
            logger.error(traceback.format_exc())
            raise
    
    def seek(self, seconds: float) -> None:
        """Seek to a specific time position in seconds."""
        duration_ms = self.player.get_length()
        if duration_ms > 0:
            position = (seconds * 1000) / duration_ms
            position = max(0.0, min(1.0, position))
            self.player.set_position(position)
    
    def set_volume(self, level: float) -> None:
        """Set volume level (0.0 to 1.0)."""
        volume = int(level * 100)
        volume = max(0, min(100, volume))
        self.player.audio_set_volume(volume)
    
    def get_current_time(self) -> float:
        """Get current playback position in seconds."""
        try:
            time_ms = self.player.get_time()
            return time_ms / 1000.0 if time_ms >= 0 else 0.0
        except Exception as e:
            logger.error(f"Error getting current time: {str(e)}")
            logger.error(traceback.format_exc())
            return 0.0
    
    def on_time_changed(self, callback: Callable[[float], None]) -> None:
        """Register a callback for time change events."""
        self._time_callback = callback
    
    def _check_time_update(self) -> None:
        """Check if time has changed and trigger callback if needed."""
        if self._time_callback and self.is_playing():
            current_time = self.get_current_time()
            if abs(current_time - self._last_time) > 0.1:
                self._last_time = current_time
                self._time_callback(current_time)
    
    def set_playback_rate(self, rate: float) -> None:
        """Set playback speed (1.0 = normal, 0.5 = half speed, 2.0 = double speed)."""
        self.player.set_rate(rate)
    
    def cleanup(self) -> None:
        """Clean up resources and stop playback."""
        self.player.stop()
        self.player.release()
        self.instance.release()
    
    def is_playing(self) -> bool:
        """Check if video is currently playing."""
        try:
            return self.player.is_playing() == 1
        except Exception as e:
            logger.error(f"Error checking if playing: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    
    def get_duration(self) -> float:
        """Get total duration of loaded video in seconds."""
        try:
            duration_ms = self.player.get_length()
            return duration_ms / 1000.0 if duration_ms > 0 else 0.0
        except Exception as e:
            logger.error(f"Error getting duration: {str(e)}")
            logger.error(traceback.format_exc())
            return 0.0
