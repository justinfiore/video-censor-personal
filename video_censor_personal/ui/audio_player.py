"""Audio playback backend using sounddevice."""

from abc import ABC, abstractmethod
import logging
import threading
import time
import numpy as np
from typing import Optional

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


class SoundDeviceAudioPlayer(AudioPlayer):
    """Audio playback using sounddevice with callback-based streaming.
    
    This implementation uses sounddevice's OutputStream with a callback function
    to stream audio data. This is more reliable than simpleaudio because:
    1. No use-after-free issues - we control when data is accessed
    2. Better integration with Python's threading model
    3. Low-latency audio output
    """
    
    def __init__(self):
        """Initialize the audio player."""
        try:
            import sounddevice as sd
            self.sd = sd
        except ImportError:
            raise RuntimeError("sounddevice library not available. Install with: pip install sounddevice")
        
        self._audio_frames: Optional[np.ndarray] = None
        self._sample_rate: int = 0
        self._channels: int = 0
        self._stream: Optional[object] = None
        self._is_playing: bool = False
        self._current_frame: int = 0
        self._lock: threading.RLock = threading.RLock()
        
        logger.info("SoundDeviceAudioPlayer initialized")
    
    def load_audio_data(self, audio_frames: np.ndarray, sample_rate: int, channels: int) -> None:
        """Load audio data for playback.
        
        Args:
            audio_frames: Numpy array - either (samples,) for mono or (samples, channels) for stereo
            sample_rate: Sample rate in Hz
            channels: Number of channels
        """
        with self._lock:
            logger.info(f"Loading audio: shape={audio_frames.shape}, {sample_rate}Hz, {channels} channels")
            
            # Ensure audio is in float32 format for sounddevice
            if audio_frames.dtype == np.int16:
                audio_frames = audio_frames.astype(np.float32) / 32767.0
            elif audio_frames.dtype not in [np.float32, np.float64]:
                audio_frames = audio_frames.astype(np.float32)
            
            # Ensure float32 for output
            if audio_frames.dtype != np.float32:
                audio_frames = audio_frames.astype(np.float32)
            
            # Handle mono audio - convert to 2D array for consistent handling
            if audio_frames.ndim == 1:
                audio_frames = audio_frames.reshape(-1, 1)
            
            # Ensure shape is (samples, channels)
            if audio_frames.ndim == 2 and audio_frames.shape[0] < audio_frames.shape[1]:
                # Likely (channels, samples) - transpose
                audio_frames = audio_frames.T
            
            self._audio_frames = audio_frames
            self._sample_rate = sample_rate
            self._channels = channels
            self._current_frame = 0
            logger.info(f"Audio loaded: {self.get_duration():.2f}s duration, shape={audio_frames.shape}")
    
    def _audio_callback(self, outdata: np.ndarray, frames: int, time_info, status) -> None:
        """Callback function called by sounddevice to fill the output buffer.
        
        This runs in a separate audio thread managed by sounddevice.
        We need to be careful about thread safety here.
        """
        if status:
            logger.warning(f"Audio callback status: {status}")
        
        # Get current state with lock
        with self._lock:
            if not self._is_playing or self._audio_frames is None:
                # Output silence
                outdata.fill(0)
                return
            
            total_samples = self._audio_frames.shape[0]
            start_frame = self._current_frame
            end_frame = min(start_frame + frames, total_samples)
            frames_available = end_frame - start_frame
            
            if frames_available <= 0:
                # End of audio - output silence
                outdata.fill(0)
                self._is_playing = False
                return
            
            # Copy audio data to output buffer
            audio_chunk = self._audio_frames[start_frame:end_frame]
            
            # Handle channel mismatch
            if audio_chunk.shape[1] != outdata.shape[1]:
                # Convert mono to stereo or vice versa
                if audio_chunk.shape[1] == 1 and outdata.shape[1] == 2:
                    audio_chunk = np.column_stack([audio_chunk, audio_chunk])
                elif audio_chunk.shape[1] == 2 and outdata.shape[1] == 1:
                    audio_chunk = audio_chunk.mean(axis=1, keepdims=True)
            
            # Fill the output buffer
            if frames_available < frames:
                # Partial buffer at end of audio
                outdata[:frames_available] = audio_chunk
                outdata[frames_available:] = 0
                self._is_playing = False
            else:
                outdata[:] = audio_chunk
            
            # Update position
            self._current_frame = end_frame
    
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
            
            # Create and start the output stream
            if self._stream is None:
                try:
                    self._stream = self.sd.OutputStream(
                        samplerate=self._sample_rate,
                        channels=self._channels,
                        dtype=np.float32,
                        callback=self._audio_callback,
                        blocksize=1024,  # ~23ms at 44100Hz - good balance of latency and efficiency
                    )
                    self._stream.start()
                    logger.info("Audio stream started")
                except Exception as e:
                    logger.error(f"Failed to create audio stream: {e}")
                    self._is_playing = False
                    raise
            elif not self._stream.active:
                try:
                    self._stream.start()
                    logger.info("Audio stream resumed")
                except Exception as e:
                    logger.error(f"Failed to resume audio stream: {e}")
                    self._is_playing = False
    
    def pause(self) -> None:
        """Pause playback."""
        with self._lock:
            if not self._is_playing:
                logger.warning("Audio not playing")
                return
            
            logger.info("Pausing audio playback")
            self._is_playing = False
            
            # Stop the stream (will output silence due to _is_playing = False)
            if self._stream is not None and self._stream.active:
                try:
                    self._stream.stop()
                except Exception as e:
                    logger.warning(f"Error stopping stream: {e}")
    
    def stop(self) -> None:
        """Stop playback and reset position."""
        with self._lock:
            logger.info("Stopping audio playback")
            self._is_playing = False
            self._current_frame = 0
            
            if self._stream is not None:
                try:
                    self._stream.stop()
                    self._stream.close()
                except Exception as e:
                    logger.warning(f"Error closing stream: {e}")
                self._stream = None
    
    def seek(self, time_seconds: float) -> None:
        """Seek to a specific time position."""
        with self._lock:
            if self._audio_frames is None:
                logger.warning("No audio data loaded")
                return
            
            total_samples = self._audio_frames.shape[0]
            frame_position = int(time_seconds * self._sample_rate)
            frame_position = max(0, min(frame_position, total_samples - 1))
            
            logger.info(f"Seeking to {time_seconds:.2f}s (frame {frame_position})")
            self._current_frame = frame_position
    
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
            return self._audio_frames.shape[0] / self._sample_rate
    
    def is_playing(self) -> bool:
        """Check if audio is currently playing."""
        with self._lock:
            return self._is_playing
    
    def cleanup(self) -> None:
        """Clean up resources."""
        logger.info("Cleaning up audio player")
        self.stop()


# For backwards compatibility, alias the new player
SimpleAudioPlayer = SoundDeviceAudioPlayer
