"""Audio extraction and caching for detector reuse.

Provides cached audio extraction from video files with resampling to 16kHz,
enabling efficient audio-based detection across multiple detectors.
"""

import logging
from typing import Optional, Tuple

import librosa
import numpy as np

from video_censor_personal.video_extraction import VideoExtractor

logger = logging.getLogger(__name__)

# Target sample rate for audio processing (16kHz for Whisper compatibility)
TARGET_SAMPLE_RATE = 16000


class AudioExtractor:
    """Extracts and caches audio from video for detector reuse.
    
    Handles:
    - Single extraction from video (cached in memory as numpy array)
    - Automatic resampling to 16kHz
    - Per-frame audio segment slicing by timecode
    - Memory cleanup when done
    
    Attributes:
        video_path: Path to video file.
        _audio_data: Cached audio as numpy array (mono, float32, 16kHz).
        _sample_rate: Cached sample rate (always 16000 Hz).
        _duration: Duration of audio in seconds.
        _extractor: VideoExtractor instance for audio extraction.
    """
    
    def __init__(self, video_path: str) -> None:
        """Initialize audio extractor.
        
        Args:
            video_path: Path to video file.
        """
        self.video_path = video_path
        self._audio_data: Optional[np.ndarray] = None
        self._sample_rate = TARGET_SAMPLE_RATE
        self._duration: Optional[float] = None
        self._extractor = VideoExtractor(video_path)
    
    def extract(self) -> Tuple[np.ndarray, int]:
        """Extract audio once and cache result.
        
        Extracts audio from video using ffmpeg (via VideoExtractor),
        loads as numpy array, and resamples to 16kHz. Subsequent calls
        return cached result without re-extraction.
        
        Returns:
            Tuple of (audio_data, sample_rate) where:
            - audio_data: numpy array (mono, float32)
            - sample_rate: 16000 Hz
            
        Raises:
            RuntimeError: If audio extraction fails.
        """
        if self._audio_data is not None:
            logger.debug("Using cached audio")
            return self._audio_data, self._sample_rate
        
        logger.debug(f"Extracting audio from {self.video_path}")
        
        try:
            # Extract audio segment (full duration)
            audio_segment = self._extractor.extract_audio()
            self._duration = audio_segment.duration()
            
            # Load bytes as audio using librosa
            # Audio is in WAV format from ffmpeg extraction
            audio_bytes = audio_segment.data
            
            # Load audio from bytes
            audio_data, sr = librosa.load(
                audio_segment.data if isinstance(audio_segment.data, np.ndarray)
                else librosa.load(audio_bytes, sr=None)[0],  # Load from bytes
                sr=None,
                mono=True
            )
            
            # If we got bytes, we need a different approach
            # Actually, let me check what audio_segment.data contains
            # From video_extraction.py, it's bytes from reading the WAV file
            # So we need to use soundfile or another method
            
            # Better approach: use librosa to load the WAV file directly
            # But we have bytes. Use io.BytesIO
            import io
            import soundfile as sf
            
            audio_data, sr = sf.read(
                io.BytesIO(audio_segment.data),
                dtype='float32'
            )
            
            # Ensure mono
            if len(audio_data.shape) > 1:
                audio_data = audio_data.mean(axis=1)
            
            # Resample to 16kHz if needed
            if sr != TARGET_SAMPLE_RATE:
                logger.debug(f"Resampling audio from {sr} Hz to {TARGET_SAMPLE_RATE} Hz")
                audio_data = librosa.resample(
                    audio_data,
                    orig_sr=sr,
                    target_sr=TARGET_SAMPLE_RATE
                )
            
            self._audio_data = audio_data
            logger.debug(
                f"Extracted audio: {len(audio_data)} samples, "
                f"{self._duration:.2f}s duration"
            )
            
            return self._audio_data, self._sample_rate
        
        except Exception as e:
            raise RuntimeError(f"Failed to extract audio: {e}") from e
    
    def get_audio_segment(
        self,
        start_time: float,
        duration: float
    ) -> Optional[np.ndarray]:
        """Get audio chunk for frame at given timecode.
        
        Returns a slice of the cached full audio corresponding to the
        specified time range. Handles edge cases where time range extends
        beyond available audio.
        
        Args:
            start_time: Start time in seconds.
            duration: Duration in seconds.
        
        Returns:
            numpy array (float32, mono, 16kHz) or None if no audio available.
        """
        if self._audio_data is None:
            return None
        
        # Convert time to sample indices
        start_sample = int(start_time * self._sample_rate)
        num_samples = int(duration * self._sample_rate)
        end_sample = start_sample + num_samples
        
        # Clamp to available audio range
        start_sample = max(0, start_sample)
        end_sample = min(len(self._audio_data), end_sample)
        
        if start_sample >= len(self._audio_data):
            return None  # Beyond available audio
        
        segment = self._audio_data[start_sample:end_sample]
        if len(segment) == 0:
            return None
        
        return segment
    
    def cleanup(self) -> None:
        """Release cached audio and close extractor.
        
        Frees memory and closes underlying VideoExtractor.
        """
        self._audio_data = None
        if self._extractor:
            try:
                self._extractor.close()
            except Exception as e:
                logger.warning(f"Error closing VideoExtractor: {e}")
    
    def __enter__(self) -> "AudioExtractor":
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.cleanup()
