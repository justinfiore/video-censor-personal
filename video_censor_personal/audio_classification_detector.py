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
                - device: Optional device override ("cuda", "mps", "cpu")
        
        Raises:
            ValueError: If config is invalid.
            ImportError: If required dependencies not available.
        """
        super().__init__(config)
        
        self.model_name = config.get("model", "MIT/ast-finetuned-audioset-10-10-0.4593")
        self.target_categories = set(self.categories)
        self.confidence_threshold = config.get("confidence_threshold", 0.6)
        
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
            
            self.processor = AutoFeatureExtractor.from_pretrained(self.model_name)
            self.model = AutoModelForAudioClassification.from_pretrained(self.model_name)
            
            # Move model to device
            self.model = self.model.to(self.device)
            logger.info(f"Loaded audio classification model: {self.model_name} on device: {self.device}")
        except ImportError as e:
            raise ImportError(
                "transformers and torch required for AudioClassificationDetector. "
                "Install with: pip install transformers torch"
            ) from e
        except Exception as e:
            raise ValueError(
                f"Failed to load model '{self.model_name}': {e}"
            ) from e
    
    def detect(
        self,
        frame_data: Optional[np.ndarray] = None,
        audio_data: Optional[np.ndarray] = None,
    ) -> List[DetectionResult]:
        """Classify audio and detect mapped content categories.
        
        Args:
            frame_data: Ignored (audio-only detector).
            audio_data: Audio as numpy array (mono, float32, 16kHz).
        
        Returns:
            List of DetectionResult for detected categories.
        """
        if audio_data is None:
            logger.debug("No audio data provided; skipping audio classification")
            return []
        
        try:
            # Preprocess audio
            inputs = self.processor(
                audio_data,
                sampling_rate=16000,
                return_tensors="pt"
            )
            
            # Move inputs to device
            inputs = {k: v.to(self.device) if hasattr(v, "to") else v for k, v in inputs.items()}
            
            # Classify
            with torch.no_grad():
                outputs = self.model(**inputs)
            
            logits = outputs.logits
            predicted_class_idx = logits.argmax(-1).item()
            predicted_label = self.model.config.id2label[predicted_class_idx]
            confidence = logits.softmax(-1).max().item()
            
            logger.debug(
                f"Audio classification: {predicted_label} (confidence: {confidence:.3f})"
            )
            
            # Skip if below confidence threshold
            if confidence < self.confidence_threshold:
                logger.debug(
                    f"Confidence {confidence:.3f} below threshold {self.confidence_threshold}"
                )
                return []
            
            # Map audio label to content category
            content_category = self.category_mapping.get(predicted_label)
            
            if not content_category or content_category not in self.target_categories:
                logger.debug(
                    f"Audio label '{predicted_label}' maps to '{content_category}' "
                    f"which is not in target categories {self.target_categories}"
                )
                return []
            
            # Return detection result
            return [
                DetectionResult(
                    start_time=0.0,  # Will be set by pipeline
                    end_time=0.033,  # Will be set by pipeline
                    label=content_category,
                    confidence=confidence,
                    reasoning=f"Audio contains: {predicted_label}",
                )
            ]
        
        except Exception as e:
            logger.error(f"Audio classification failed: {e}", exc_info=True)
            return []
    
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
