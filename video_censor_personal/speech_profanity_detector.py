"""Speech profanity detection using Whisper ASR and keyword matching."""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from video_censor_personal.detection import Detector
from video_censor_personal.device_utils import get_device
from video_censor_personal.frame import DetectionResult

logger = logging.getLogger(__name__)


class SpeechProfanityDetector(Detector):
    """Detects profanity in speech using Whisper ASR and keyword matching.
    
    Transcribes audio to text using OpenAI Whisper, then matches against
    configurable profanity keyword lists for specified languages.
    
    Attributes:
        whisper_model: Whisper model size (tiny, base, small, medium, large).
        languages: List of language codes (en, es, etc.).
        keywords: Dict mapping language → set of profanity keywords.
        pipeline: Hugging Face transformers pipeline for speech recognition.
    """
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize speech profanity detector.
        
        Args:
            config: Configuration dict with:
                - name: Detector name
                - categories: List containing "Profanity"
                - model: Whisper model size (default: "base")
                - languages: List of language codes (default: ["en"])
                - confidence_threshold: Min confidence for detection (default: 0.8)
                - device: Optional device override ("cuda", "mps", "cpu")
        
        Raises:
            ValueError: If config is invalid.
            ImportError: If required dependencies not available.
        """
        super().__init__(config)
        
        self.model_size = config.get("model", "base")
        self.languages = config.get("languages", ["en"])
        self.confidence_threshold = config.get("confidence_threshold", 0.8)
        
        # Detect or override device
        device_override = config.get("device")
        self.device = get_device(device_override)
        
        # Validate
        if "Profanity" not in self.categories:
            raise ValueError("SpeechProfanityDetector must include 'Profanity' in categories")
        if not self.languages:
            raise ValueError("At least one language must be specified")
        
        # Load profanity keywords
        self.keywords = self._load_profanity_keywords()
        
        # Load Whisper pipeline with device parameter
        try:
            from transformers import pipeline
            
            logger.info(f"Loading Whisper model '{self.model_size}' to {self.device}...")
            
            # Convert device string to pipeline device parameter
            # pipeline() accepts device index for CUDA, or -1 for CPU, or "mps" for Apple Silicon
            device_param = self._get_pipeline_device_param()
            
            self.pipeline = pipeline(
                "automatic-speech-recognition",
                model=f"openai/whisper-{self.model_size}",
                device=device_param,
            )
            logger.info(f"Whisper model loaded successfully on {self.device}")
        except ImportError as e:
            raise ImportError(
                "transformers and torch required for SpeechProfanityDetector. "
                "Install with: pip install transformers torch"
            ) from e
    
    def detect(
        self,
        frame_data: Optional[np.ndarray] = None,
        audio_data: Optional[np.ndarray] = None,
    ) -> List[DetectionResult]:
        """Detect profanity in audio using speech recognition.
        
        Transcribes audio and matches keywords case-insensitively.
        Returns one DetectionResult per profanity keyword found.
        
        Args:
            frame_data: Ignored (audio-only detector).
            audio_data: Audio as numpy array (mono, float32, 16kHz).
        
        Returns:
            List of DetectionResult with label="Profanity".
        """
        if audio_data is None:
            logger.debug("No audio data provided; skipping speech detection")
            return []
        
        try:
            # Transcribe audio
            logger.debug("Transcribing audio with Whisper")
            result = self.pipeline(
                audio_data,
                chunk_length_s=30,  # Process in 30s chunks
                stride_length_s=(4, 2),  # Overlapping windows
            )
            transcription = result.get("text", "").lower()
            
            if not transcription:
                logger.debug("Empty transcription; no profanity detected")
                return []
            
            logger.debug(f"Transcription: {transcription[:100]}...")
            
            # Find profanity keywords
            matches = self._find_profanity(transcription)
            
            if not matches:
                logger.debug("No profanity keywords found in transcription")
                return []
            
            logger.debug(f"Found {len(matches)} profanity keyword(s): {matches}")
            
            # Return one DetectionResult per keyword found
            results = []
            for keyword in matches:
                results.append(
                    DetectionResult(
                        start_time=0.0,  # Will be set by pipeline
                        end_time=0.033,  # Will be set by pipeline
                        label="Profanity",
                        confidence=0.95,
                        reasoning=f"Speech contains profanity: '{keyword}'",
                    )
                )
            
            return results
        
        except Exception as e:
            logger.error(f"Speech profanity detection failed: {e}", exc_info=True)
            return []
    
    def _load_profanity_keywords(self) -> Dict[str, set]:
        """Load language-specific profanity keyword lists.
        
        Returns:
            Dict mapping language code → set of lowercase keywords.
        """
        keywords = {}
        data_dir = Path(__file__).parent / "data"
        
        for lang in self.languages:
            keyword_file = data_dir / f"profanity_{lang}.txt"
            
            if not keyword_file.exists():
                logger.warning(f"Profanity list not found for language '{lang}'")
                keywords[lang] = set()
                continue
            
            try:
                with open(keyword_file, "r", encoding="utf-8") as f:
                    # Read keywords, skip empty lines, convert to lowercase
                    kw_set = {
                        line.strip().lower()
                        for line in f
                        if line.strip()
                    }
                    keywords[lang] = kw_set
                    logger.debug(f"Loaded {len(kw_set)} keywords for language '{lang}'")
            except Exception as e:
                logger.error(f"Failed to load keywords for '{lang}': {e}")
                keywords[lang] = set()
        
        return keywords
    
    def _find_profanity(self, text: str) -> List[str]:
        """Match profanity keywords in text.
        
        Performs case-insensitive word boundary matching.
        
        Args:
            text: Transcribed text (already lowercase).
        
        Returns:
            List of unique matched keywords (in lowercase).
        """
        import re
        
        matches = []
        matched_set = set()
        
        # Combine all keywords from enabled languages
        all_keywords = set()
        for lang in self.languages:
            all_keywords.update(self.keywords.get(lang, set()))
        
        # Search for each keyword with word boundaries
        for keyword in all_keywords:
            # Escape special regex characters in keyword
            escaped = re.escape(keyword)
            # Use word boundaries for matching
            pattern = rf"\b{escaped}\b"
            
            if re.search(pattern, text):
                if keyword not in matched_set:
                    matches.append(keyword)
                    matched_set.add(keyword)
        
        return matches
    
    def _get_pipeline_device_param(self):
        """Convert device string to transformers pipeline device parameter.
        
        Returns:
            Device parameter for pipeline(): 0 for CUDA, -1 for CPU, "mps" for Apple Silicon.
        """
        if self.device == "cuda":
            return 0
        elif self.device == "mps":
            return "mps"
        else:
            return -1
    
    def cleanup(self) -> None:
        """Release Whisper model and free memory."""
        try:
            if hasattr(self, 'pipeline'):
                del self.pipeline
            
            # Clear CUDA cache if available
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except ImportError:
                pass
            
            logger.debug("Cleaned up speech profanity detector")
        except Exception as e:
            logger.warning(f"Error during speech detector cleanup: {e}")
