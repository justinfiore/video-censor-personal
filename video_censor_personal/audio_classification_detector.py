"""Audio classification detection for sound effects and music.

Uses pre-trained HuggingFace models to classify audio and map to
content categories (Violence, Sexual Theme, etc.).
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import torch

from video_censor_personal.detection import Detector
from video_censor_personal.device_utils import get_device
from video_censor_personal.frame import DetectionResult
from video_censor_personal.loading_spinner import loading_spinner, task_spinner
from video_censor_personal.model_size import get_audio_classification_model_size

logger = logging.getLogger(__name__)


class AudioClassificationDetector(Detector):
    """Detects sound effects and music using audio classification models.
    
    Uses HuggingFace pre-trained audio classification models (e.g., audioset)
    to classify audio clips and maps detected sound labels to content categories
    like Violence, Sexual Theme, etc.
    
    Attributes:
        model_name: HuggingFace model identifier.
        target_categories: List of content categories to detect.
        category_mapping: Dict mapping audio labels → content categories.
        processor: Feature extractor for audio preprocessing.
        model: Classification model.
    """
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize audio classification detector.
        
        Args:
            config: Configuration dict with:
                - name: Detector name
                - categories: Content categories to detect (e.g., ["Violence"])
                - model: HuggingFace model name (default: "MIT/ast-finetuned-audioset-10-10-0.4593")
                - confidence_threshold: Min confidence (default: 0.6)
                - chunk_duration: Audio chunk size in seconds (default: 2.0)
                - device: Optional device override ("cuda", "mps", "cpu")
        
        Raises:
            ValueError: If config is invalid.
            ImportError: If required dependencies not available.
        """
        super().__init__(config)
        
        self.model_name = config.get("model", "MIT/ast-finetuned-audioset-10-10-0.4593")
        self.target_categories = set(self.categories)
        self.confidence_threshold = config.get("confidence_threshold", 0.6)
        self.chunk_duration = config.get("chunk_duration", 2.0)  # seconds per chunk
        
        # Detect or override device
        device_override = config.get("device")
        self.device = get_device(device_override)
        
        # Load category mapping (audio labels → content categories)
        self.category_mapping = self._build_category_mapping()
        
        # Load HuggingFace model
        try:
            from transformers import (
                AutoFeatureExtractor,
                AutoModelForAudioClassification,
            )
            
            logger.info(f"Loading audio classification model '{self.model_name}' to {self.device}...")
            
            # Get actual model size from cache (or estimate if not cached)
            model_size_bytes = get_audio_classification_model_size(self.model_name)
            
            with loading_spinner(self.model_name, model_size_bytes, self.device):
                self.processor = AutoFeatureExtractor.from_pretrained(self.model_name)
                self.model = AutoModelForAudioClassification.from_pretrained(self.model_name)
                # Move model to device
                self.model = self.model.to(self.device)
            
            logger.info(f"Audio classification model loaded successfully on {self.device}")
        except ImportError as e:
            raise ImportError(
                "transformers and torch required for AudioClassificationDetector. "
                "Install with: pip install transformers torch"
            ) from e
        except Exception as e:
            raise ValueError(
                f"Failed to load model '{self.model_name}': {e}"
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
        """Classify full audio in chunks and return timestamped detections.
        
        Processes audio in overlapping windows, classifying each segment
        and returning detections with accurate timestamps.
        
        Args:
            audio_data: Complete audio as numpy array (mono, float32).
            sample_rate: Audio sample rate in Hz (default: 16000).
        
        Returns:
            List of DetectionResult with accurate start_time/end_time.
        """
        if audio_data is None or len(audio_data) == 0:
            logger.debug("No audio data provided; skipping audio classification")
            return []
        
        chunk_duration = self.chunk_duration
        hop_duration = chunk_duration / 2  # 50% overlap
        chunk_samples = int(chunk_duration * sample_rate)
        hop_samples = int(hop_duration * sample_rate)
        
        audio_duration = len(audio_data) / sample_rate
        logger.info(
            f"Classifying {audio_duration:.1f}s of audio in {chunk_duration}s chunks..."
        )
        
        results = []
        position = 0
        chunk_count = 0
        
        try:
            while position < len(audio_data):
                chunk_end = min(position + chunk_samples, len(audio_data))
                chunk = audio_data[position:chunk_end]
                
                if len(chunk) < chunk_samples // 2:
                    break
                
                start_time = position / sample_rate
                end_time = chunk_end / sample_rate
                
                detection = self._classify_chunk(chunk, start_time, end_time)
                if detection:
                    results.append(detection)
                
                position += hop_samples
                chunk_count += 1
            
            if results:
                logger.info(f"Audio classification found {len(results)} detections")
            else:
                logger.debug("No target sounds detected in audio")
            
            return results
        
        except Exception as e:
            logger.error(f"Audio classification failed: {e}", exc_info=True)
            return []

    def _classify_chunk(
        self,
        chunk: np.ndarray,
        start_time: float,
        end_time: float,
    ) -> Optional[DetectionResult]:
        """Classify a single audio chunk.
        
        Args:
            chunk: Audio chunk as numpy array.
            start_time: Start time in seconds.
            end_time: End time in seconds.
        
        Returns:
            DetectionResult if target category detected, None otherwise.
        """
        try:
            inputs = self.processor(
                chunk,
                sampling_rate=16000,
                return_tensors="pt"
            )
            
            inputs = {k: v.to(self.device) if hasattr(v, "to") else v for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self.model(**inputs)
            
            logits = outputs.logits
            predicted_class_idx = logits.argmax(-1).item()
            predicted_label = self.model.config.id2label[predicted_class_idx]
            confidence = logits.softmax(-1).max().item()
            
            if confidence < self.confidence_threshold:
                return None
            
            content_category = self.category_mapping.get(predicted_label)
            
            if not content_category or content_category not in self.target_categories:
                return None
            
            logger.debug(
                f"Detected '{predicted_label}' ({content_category}) at "
                f"{start_time:.2f}s-{end_time:.2f}s (confidence: {confidence:.3f})"
            )
            
            return DetectionResult(
                start_time=start_time,
                end_time=end_time,
                label=content_category,
                confidence=confidence,
                reasoning=f"Audio contains: {predicted_label}",
            )
        
        except Exception as e:
            logger.debug(f"Chunk classification failed: {e}")
            return None
    
    def _build_category_mapping(self) -> Dict[str, str]:
        """Build mapping from audio classification labels to content categories.
        
        Loads mapping from bundled data file, falls back to default mapping.
        
        Returns:
            Dict mapping audio labels → content categories.
        """
        # Try to load from data file
        data_dir = Path(__file__).parent / "data"
        mapping_file = data_dir / "audio_category_mapping.json"
        
        if mapping_file.exists():
            try:
                with open(mapping_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load category mapping file: {e}")
        
        # Fall back to default mapping
        return {
            # Violence sounds
            "gunshot": "Violence",
            "gun": "Violence",
            "shooting": "Violence",
            "explosion": "Violence",
            "explode": "Violence",
            "scream": "Violence",
            "screaming": "Violence",
            "yelling": "Violence",
            "shout": "Violence",
            "crash": "Violence",
            "bang": "Violence",
            "punch": "Violence",
            "hit": "Violence",
            # Sexual sounds
            "moan": "Sexual Theme",
            "moaning": "Sexual Theme",
            "pant": "Sexual Theme",
            "panting": "Sexual Theme",
            "breath": "Sexual Theme",
            "groaning": "Sexual Theme",
        }
    
    def cleanup(self) -> None:
        """Release model and free memory."""
        try:
            if hasattr(self, 'model') and self.model is not None:
                # Move model off GPU if applicable
                if hasattr(self.model, "cpu"):
                    self.model = self.model.cpu()
                del self.model
            if hasattr(self, 'processor'):
                del self.processor
            
            # Clear CUDA cache if available
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except ImportError:
                pass
            
            logger.debug("Cleaned up audio classification detector")
        except Exception as e:
            logger.warning(f"Error during audio classifier cleanup: {e}")
