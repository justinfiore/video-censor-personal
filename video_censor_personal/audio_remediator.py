"""Audio remediation engine for silencing or bleeping detected content."""

import logging
from typing import Any, Dict, List, Optional

import numpy as np

from video_censor_personal.frame import DetectionResult

logger = logging.getLogger(__name__)


class AudioRemediator:
    """Applies remediation (silence or bleep) to detected audio segments.
    
    Takes raw audio and detection results, then modifies audio by either:
    - Silencing (zeroing out samples)
    - Bleeping (replacing with sine wave tone)
    
    Per-category control allows selective remediation (e.g., silence profanity
    but keep violence sounds).
    
    Attributes:
        enabled: Whether remediation is active.
        mode: "silence" or "bleep".
        categories: Set of detection categories to remediate.
        bleep_frequency: Frequency for bleep tone in Hz.
    """
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize audio remediator.
        
        Args:
            config: Configuration dict with:
                - enabled: bool, whether remediation is active (default: False)
                - mode: "silence" or "bleep" (default: "silence")
                - categories: List of category names to remediate
                - bleep_frequency: Frequency in Hz for bleep mode (default: 1000)
        
        Raises:
            ValueError: If config is invalid.
        """
        self.enabled = config.get("enabled", False)
        self.mode = config.get("mode", "silence")
        self.categories = set(config.get("categories", []))
        self.bleep_frequency = config.get("bleep_frequency", 1000)
        
        # Validate mode
        if self.mode not in ("silence", "bleep"):
            raise ValueError(f"Invalid remediation mode: {self.mode}. Must be 'silence' or 'bleep'")
        
        # Validate frequency
        if self.bleep_frequency <= 0:
            raise ValueError(f"Bleep frequency must be positive, got {self.bleep_frequency}")
        
        logger.debug(
            f"Initialized AudioRemediator: enabled={self.enabled}, "
            f"mode={self.mode}, categories={self.categories}"
        )
    
    def remediate(
        self,
        audio_data: np.ndarray,
        sample_rate: int,
        detections: List[DetectionResult],
    ) -> np.ndarray:
        """Apply remediation to audio based on detections.
        
        Modifies audio in-place for specified detection categories.
        Handles overlapping detections and respects sample rate.
        
        Args:
            audio_data: Audio array (mono, float32).
            sample_rate: Sample rate in Hz (typically 16000).
            detections: List of DetectionResult with timecodes.
        
        Returns:
            Remediated audio array (same shape as input).
        """
        if not self.enabled:
            logger.debug("Remediation disabled; returning original audio")
            return audio_data
        
        if not detections:
            logger.debug("No detections provided; returning original audio")
            return audio_data
        
        remediated = audio_data.copy()
        
        # Determine number of channels (mono = 1D, stereo/multi = 2D)
        if remediated.ndim == 1:
            num_channels = 1
            num_samples = len(remediated)
        else:
            num_samples, num_channels = remediated.shape
        
        # Filter and apply remediation per detection
        remediated_count = 0
        for detection in detections:
            if detection.label not in self.categories:
                logger.debug(
                    f"Skipping '{detection.label}' (not in remediation categories)"
                )
                continue
            
            # Convert timecode to sample indices
            start_sample = int(detection.start_time * sample_rate)
            end_sample = int(detection.end_time * sample_rate)
            
            # Clamp to valid range
            start_sample = max(0, start_sample)
            end_sample = min(num_samples, end_sample)
            
            if start_sample >= end_sample:
                logger.debug(
                    f"Invalid range for detection at {detection.start_time:.2f}s: "
                    f"samples [{start_sample}, {end_sample}]"
                )
                continue
            
            # Apply remediation mode
            if self.mode == "silence":
                remediated[start_sample:end_sample] = 0.0
                logger.debug(
                    f"Silenced {detection.label} at {detection.start_time:.2f}s "
                    f"({end_sample - start_sample} samples)"
                )
            elif self.mode == "bleep":
                # Generate sine wave tone
                duration_samples = end_sample - start_sample
                t = np.arange(duration_samples, dtype=np.float32) / sample_rate
                tone = 0.2 * np.sin(2 * np.pi * self.bleep_frequency * t)
                
                # Expand tone to match number of channels
                if num_channels > 1:
                    tone = np.tile(tone[:, np.newaxis], (1, num_channels))
                
                remediated[start_sample:end_sample] = tone
                logger.debug(
                    f"Beeped {detection.label} at {detection.start_time:.2f}s "
                    f"({duration_samples} samples, {self.bleep_frequency}Hz)"
                )
            
            remediated_count += 1
        
        logger.info(f"Remediated {remediated_count} detection(s)")
        return remediated
    
    def write_audio(
        self,
        audio_data: np.ndarray,
        sample_rate: int,
        output_path: str,
    ) -> None:
        """Write audio to WAV file.
        
        Args:
            audio_data: Audio array (mono, float32).
            sample_rate: Sample rate in Hz.
            output_path: Path where WAV file will be saved.
        
        Raises:
            RuntimeError: If write fails.
        """
        try:
            import soundfile as sf
            
            sf.write(output_path, audio_data, sample_rate)
            logger.info(f"Wrote remediated audio to {output_path}")
        except ImportError:
            raise RuntimeError(
                "soundfile required for audio output. "
                "Install with: pip install soundfile"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to write audio to {output_path}: {e}") from e
