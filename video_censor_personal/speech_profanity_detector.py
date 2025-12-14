"""Speech profanity detection using Whisper ASR and keyword matching."""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from video_censor_personal.detection import Detector
from video_censor_personal.device_utils import get_device
from video_censor_personal.frame import DetectionResult
from video_censor_personal.loading_spinner import loading_spinner, task_spinner
from video_censor_personal.model_size import get_whisper_model_size

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
            
            # Get actual model size from cache (or estimate if not cached)
            model_size_bytes = get_whisper_model_size(self.model_size)
            
            with loading_spinner(
                f"openai/whisper-{self.model_size}",
                model_size_bytes,
                self.device,
            ):
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
    
    def supports_full_audio_analysis(self) -> bool:
        """Return True - this detector supports efficient full-audio analysis."""
        return True

    def detect(
        self,
        frame_data: Optional[np.ndarray] = None,
        audio_data: Optional[np.ndarray] = None,
    ) -> List[DetectionResult]:
        """Per-frame detection - returns empty since full audio analysis is preferred.
        
        This detector uses analyze_full_audio() for efficient processing.
        Per-frame calls are skipped to avoid redundant transcription.
        
        Args:
            frame_data: Ignored (audio-only detector).
            audio_data: Ignored (use analyze_full_audio instead).
        
        Returns:
            Empty list - use analyze_full_audio() for results.
        """
        return []

    def analyze_full_audio(
        self,
        audio_data: np.ndarray,
        sample_rate: int = 16000,
    ) -> List[DetectionResult]:
        """Transcribe full audio with word timestamps and detect profanity.
        
        Processes the entire audio track once, extracting word-level timestamps
        from Whisper, then matches profanity keywords to return accurately
        timestamped detection results.
        
        Args:
            audio_data: Complete audio as numpy array (mono, float32).
            sample_rate: Audio sample rate in Hz (default: 16000).
        
        Returns:
            List of DetectionResult with accurate start_time/end_time.
        """
        if audio_data is None or len(audio_data) == 0:
            logger.debug("No audio data provided; skipping speech detection")
            return []
        
        try:
            audio_duration = len(audio_data) / sample_rate
            logger.info(
                f"Transcribing {audio_duration:.1f}s of audio with Whisper "
                f"(word-level timestamps)..."
            )
            
            with task_spinner(
                "Transcribing audio with Whisper",
                f"{audio_duration:.1f}s"
            ):
                result = self.pipeline(
                    audio_data,
                    chunk_length_s=30,
                    stride_length_s=(4, 2),
                    return_timestamps="word",
                )
            
            chunks = result.get("chunks", [])
            full_text = result.get("text", "").lower()
            
            if not chunks:
                logger.debug("No word chunks returned from Whisper")
                if full_text:
                    logger.debug(f"Full transcription: {full_text[:200]}...")
                return []
            
            logger.info(f"Transcribed {len(chunks)} words")
            logger.debug(f"Full transcription: {full_text[:200]}...")
            
            all_keywords = set()
            for lang in self.languages:
                all_keywords.update(self.keywords.get(lang, set()))
            
            results = []
            for chunk in chunks:
                word = chunk.get("text", "").strip().lower()
                word_clean = self._clean_word(word)
                
                if word_clean in all_keywords:
                    timestamp = chunk.get("timestamp", (0.0, 0.0))
                    if isinstance(timestamp, tuple) and len(timestamp) == 2:
                        start_time, end_time = timestamp
                    else:
                        start_time = 0.0
                        end_time = 0.0
                    
                    if start_time is None:
                        start_time = 0.0
                    if end_time is None:
                        end_time = start_time + 0.5
                    
                    results.append(
                        DetectionResult(
                            start_time=float(start_time),
                            end_time=float(end_time),
                            label="Profanity",
                            confidence=0.95,
                            reasoning=f"Speech contains profanity: '{word_clean}'",
                        )
                    )
                    logger.debug(
                        f"Found profanity '{word_clean}' at {start_time:.2f}s - {end_time:.2f}s"
                    )
            
            if results:
                logger.info(f"Detected {len(results)} profanity instance(s)")
            else:
                logger.debug("No profanity keywords found in transcription")
            
            return results
        
        except Exception as e:
            logger.error(f"Speech profanity detection failed: {e}", exc_info=True)
            return []

    def _clean_word(self, word: str) -> str:
        """Remove punctuation from word for keyword matching.
        
        Args:
            word: Raw word from transcription.
        
        Returns:
            Cleaned lowercase word.
        """
        import re
        return re.sub(r'[^\w\s]', '', word).strip().lower()
    
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
