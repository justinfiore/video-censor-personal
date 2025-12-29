"""Audio playback backend using pydub and simpleaudio."""

from abc import ABC, abstractmethod
import logging
import threading
import queue
import numpy as np
from typing import Optional, Callable

logger = logging.getLogger("video_censor_personal.ui")


class AudioPlayer(ABC):
    """Abstract base class for audio playback."""
    
    @abstractmethod
    def load_audio_data(self, audio_frames: np.ndarray, sample_rate: int, channels: int) -> None:
        """Load audio data for playback.
        
        Args:
            audio_frames: Numpy array of audio samples
            sample_rate: Sample rate in Hz (e.g., 48000)
            channels: Number of audio channels (1=mono, 2=stereo)
        """
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
    def stop(self) -> None:
        """Stop playback and reset position."""
        pass
    
    @abstractmethod
    def seek(self, time_seconds: float) -> None:
        """Seek to a specific time position."""
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
    def is_playing(self) -> bool:
        """Check if audio is currently playing."""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Clean up resources."""
        pass


class SimpleAudioPlayer(AudioPlayer):
    """Audio playback using pydub and simpleaudio."""
    
    def __init__(self):
        """Initialize the audio player."""
        try:
            import simpleaudio
            self.simpleaudio = simpleaudio
        except ImportError:
            raise RuntimeError("simpleaudio library not available")
        
        self._audio_frames: Optional[np.ndarray] = None
        self._sample_rate: int = 0
        self._channels: int = 0
        self._play_obj: Optional[object] = None
        self._is_playing: bool = False
        self._volume: float = 1.0
        self._current_frame: int = 0
        self._playback_thread: Optional[threading.Thread] = None
        self._stop_event: threading.Event = threading.Event()
        self._lock: threading.RLock = threading.RLock()
        
        logger.info("SimpleAudioPlayer initialized")
    
    def load_audio_data(self, audio_frames: np.ndarray, sample_rate: int, channels: int) -> None:
        """Load audio data for playback."""
        with self._lock:
            logger.info(f"Loading audio: {len(audio_frames)} frames, {sample_rate}Hz, {channels} channels")
            
            # Ensure audio is in the correct format (int16)
            if audio_frames.dtype != np.int16:
                # Normalize float audio to int16 range
                if audio_frames.dtype in [np.float32, np.float64]:
                    audio_frames = (audio_frames * 32767).astype(np.int16)
                else:
                    audio_frames = audio_frames.astype(np.int16)
            
            self._audio_frames = audio_frames
            self._sample_rate = sample_rate
            self._channels = channels
            self._current_frame = 0
            logger.info(f"Audio loaded: {self.get_duration():.2f}s duration")
    
    def play(self) -> None:
        """Start or resume playback."""
        with self._lock:
            if self._is_playing:
                logger.warning("Audio already playing")
                return
            
            if self._audio_frames is None:
                logger.warning("No audio data loaded")
                return
            
            logger.info(f"Starting playback from frame {self._current_frame}")
            self._is_playing = True
            self._stop_event.clear()
            
            if self._playback_thread is None or not self._playback_thread.is_alive():
                self._playback_thread = threading.Thread(target=self._playback_thread_main, daemon=True)
                self._playback_thread.start()
    
    def pause(self) -> None:
        """Pause playback."""
        with self._lock:
            if not self._is_playing:
                logger.warning("Audio not playing")
                return
            
            logger.info("Pausing audio playback")
            self._is_playing = False
            
            if self._play_obj is not None:
                try:
                    self._play_obj.stop()
                except Exception as e:
                    logger.warning(f"Error stopping playback: {e}")
                self._play_obj = None
    
    def stop(self) -> None:
        """Stop playback and reset position."""
        with self._lock:
            logger.info("Stopping audio playback")
            self._is_playing = False
            self._stop_event.set()
            
            if self._play_obj is not None:
                try:
                    self._play_obj.stop()
                except Exception as e:
                    logger.warning(f"Error stopping playback: {e}")
                self._play_obj = None
            
            self._current_frame = 0
    
    def seek(self, time_seconds: float) -> None:
        """Seek to a specific time position."""
        with self._lock:
            if self._audio_frames is None:
                logger.warning("No audio data loaded")
                return
            
            # Calculate frame position (account for 1D vs 2D arrays)
            total_samples = len(self._audio_frames) if self._audio_frames.ndim == 1 else self._audio_frames.shape[0]
            frame_position = int(time_seconds * self._sample_rate)
            frame_position = max(0, min(frame_position, total_samples - 1))
            
            logger.info(f"Seeking to {time_seconds:.2f}s (frame {frame_position})")
            self._current_frame = frame_position
            
            # Stop current playback if playing
            if self._is_playing:
                if self._play_obj is not None:
                    try:
                        self._play_obj.stop()
                    except Exception as e:
                        logger.warning(f"Error stopping playback: {e}")
                    self._play_obj = None
    
    def set_volume(self, level: float) -> None:
        """Set volume level (0.0 to 1.0)."""
        with self._lock:
            level = max(0.0, min(1.0, level))
            logger.info(f"Setting volume to {level * 100:.0f}%")
            self._volume = level
    
    def get_current_time(self) -> float:
        """Get current playback position in seconds."""
        with self._lock:
            if self._sample_rate == 0:
                return 0.0
            
            return self._current_frame / self._sample_rate
    
    def get_duration(self) -> float:
        """Get total audio duration in seconds."""
        with self._lock:
            if self._audio_frames is None or self._sample_rate == 0:
                return 0.0
            
            # Handle both 1D and 2D arrays
            total_samples = len(self._audio_frames) if self._audio_frames.ndim == 1 else self._audio_frames.shape[0]
            return total_samples / self._sample_rate
    
    def is_playing(self) -> bool:
        """Check if audio is currently playing."""
        with self._lock:
            return self._is_playing
    
    def cleanup(self) -> None:
        """Clean up resources."""
        logger.info("Cleaning up audio player")
        self.stop()
        
        if self._playback_thread is not None:
            self._playback_thread.join(timeout=1.0)
    
    def _playback_thread_main(self) -> None:
        """Main audio playback thread."""
        try:
            while not self._stop_event.is_set():
                with self._lock:
                    if not self._is_playing or self._audio_frames is None:
                        self._stop_event.wait(timeout=0.1)
                        continue
                    
                    # Get audio segment for playback
                    frames_to_play = self._audio_frames[self._current_frame:]
                    
                    if len(frames_to_play) == 0:
                        # Reached end of audio
                        logger.info("Audio playback finished")
                        self._is_playing = False
                        continue
                    
                    # Apply volume
                    if self._volume < 1.0:
                        frames_to_play = (frames_to_play * self._volume).astype(np.int16)
                    
                    # Play audio
                    try:
                        self._play_obj = self.simpleaudio.play_buffer(
                            frames_to_play.tobytes(),
                            self._channels,
                            2,  # 2 bytes per sample (int16)
                            self._sample_rate
                        )
                        
                        # Update current frame based on number of samples played
                        # (frames = samples per channel, not per sample rate)
                        if self._channels > 1:
                            samples_played = len(frames_to_play) // self._channels
                        else:
                            samples_played = len(frames_to_play)
                        self._current_frame += samples_played
                        
                        # Wait for playback to complete or pause signal
                        self._play_obj.wait_done()
                        
                    except Exception as e:
                        logger.error(f"Error during audio playback: {e}")
                        self._is_playing = False
        
        except Exception as e:
            logger.error(f"Playback thread error: {e}")
            self._is_playing = False
