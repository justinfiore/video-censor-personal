"""CLIP-based detector for efficient, configurable content classification."""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import cv2
import numpy as np

from video_censor_personal.detection import Detector
from video_censor_personal.device_utils import get_device
from video_censor_personal.frame import DetectionResult

logger = logging.getLogger(__name__)

TRACE_LEVEL = 5


class CLIPDetector(Detector):
    """CLIP-based detector using OpenAI's Contrastive Language-Image Pre-training.

    Analyzes video frames with CLIP to detect multiple content categories via
    configurable text prompts. Lightweight and efficient alternative to vision-
    language models like LLaVA.
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize CLIP detector with model and prompt validation.

        Args:
            config: Configuration dict with keys:
              - name: Detector instance name
              - categories: List of categories to analyze
              - model_name: HuggingFace model identifier
                (default: "openai/clip-vit-base-patch32")
              - model_path: Optional custom model cache path (default: HF cache)
              - prompts: List of dicts with 'category' and 'text' (list of strings)
              - device: Optional device override ("cuda", "mps", "cpu")

        Raises:
            ValueError: If model not found, dependencies missing, or config invalid.
        """
        super().__init__(config)

        self.model_name = config.get("model_name", "openai/clip-vit-base-patch32")
        self.model_path = config.get("model_path")

        # Detect or override device
        device_override = config.get("device")
        self.device = get_device(device_override)

        # Parse and validate prompts
        self.prompts_config = config.get("prompts", [])
        self._validate_prompts()
        self.prompts_dict = self._build_prompts_dict()

        # Load and validate model
        self.model = None
        self.processor = None
        self.model, self.processor = self._load_model()

        logger.info(
            f"Initialized CLIP detector '{self.name}' with model '{self.model_name}' "
            f"on device '{self.device}' for categories: {', '.join(self.categories)}"
        )

    def _validate_prompts(self) -> None:
        """Validate prompt configuration from config.

        Raises:
            ValueError: If prompts invalid or missing required categories.
        """
        if not isinstance(self.prompts_config, list):
            raise ValueError("'prompts' must be a list of dicts")

        if not self.prompts_config:
            raise ValueError("'prompts' list cannot be empty")

        # Check each prompt has required fields
        for i, prompt in enumerate(self.prompts_config):
            if not isinstance(prompt, dict):
                raise ValueError(f"Prompt {i} must be a dict, got {type(prompt)}")

            if "category" not in prompt:
                raise ValueError(f"Prompt {i} missing 'category' field")

            if "text" not in prompt:
                raise ValueError(f"Prompt {i} missing 'text' field")

            category = prompt["category"]
            text = prompt["text"]

            if not isinstance(text, list):
                raise ValueError(
                    f"Prompt for category '{category}': 'text' must be a list of strings, "
                    f"got {type(text)}"
                )

            for j, t in enumerate(text):
                if not isinstance(t, str):
                    raise ValueError(
                        f"Prompt for category '{category}': text[{j}] must be string, "
                        f"got {type(t)}"
                    )

        # Verify all categories have prompts
        prompt_categories = {p["category"] for p in self.prompts_config}
        missing = set(self.categories) - prompt_categories
        if missing:
            raise ValueError(
                f"Categories missing prompts: {', '.join(missing)}. "
                f"All categories must have corresponding text prompts."
            )

    def _build_prompts_dict(self) -> Dict[str, List[str]]:
        """Build mapping of category -> list of candidate prompt texts.

        Returns:
            Dict mapping category name to list of prompt strings.
        """
        result = {}
        for prompt_entry in self.prompts_config:
            category = prompt_entry["category"]
            text_list = prompt_entry["text"]
            result[category] = text_list
        return result

    def _load_model(self) -> tuple:
        """Load and validate CLIP model and processor.

        Returns:
            Tuple of (model, processor) from transformers library.

        Raises:
            ValueError: If model not found, dependencies missing, or loading fails.
        """
        # Check if required libraries are available
        try:
            from transformers import CLIPModel, CLIPProcessor
            import torch
        except ImportError as e:
            raise ValueError(
                f"CLIP dependencies not installed: {e}\n"
                f"Install with:\n"
                f"  pip install transformers torch torchvision pillow\n"
                f"See QUICK_START.md for detailed setup instructions."
            )

        try:
            logger.info(f"Loading CLIP model '{self.model_name}' to {self.device}...")

            # Build load kwargs
            load_kwargs = {}
            if self.model_path:
                load_kwargs["cache_dir"] = self.model_path

            # Load processor
            processor = CLIPProcessor.from_pretrained(self.model_name)

            # Load model
            model = CLIPModel.from_pretrained(self.model_name, **load_kwargs)
            model = model.to(self.device)

            logger.info(f"CLIP model loaded successfully on {self.device}")
            return model, processor

        except FileNotFoundError as e:
            raise ValueError(
                f"Model '{self.model_name}' not found locally.\n\n"
                f"To auto-download the model, run:\n"
                f"  python -m video_censor --download-models --config <your-config.yaml>\n\n"
                f"Or download manually:\n"
                f"  python -c \"from transformers import CLIPModel; "
                f"CLIPModel.from_pretrained('{self.model_name}')\"\n\n"
                f"Model cache location: ~/.cache/huggingface/hub/\n"
                f"See QUICK_START.md for detailed setup instructions."
            )

        except ImportError as e:
            raise ValueError(
                f"Failed to load model due to missing dependencies: {e}\n"
                f"Install with: pip install transformers torch torchvision pillow\n"
                f"See QUICK_START.md for detailed instructions."
            )

        except Exception as e:
            raise ValueError(
                f"Failed to load model '{self.model_name}': {e}\n"
                f"Ensure the model is downloaded to: ~/.cache/huggingface/hub/\n"
                f"See QUICK_START.md for model download instructions."
            )

    def detect(
        self,
        frame_data: Optional[np.ndarray] = None,
        audio_data: Optional[Any] = None,
    ) -> List[DetectionResult]:
        """Analyze frame with CLIP model for content detection.

        Args:
            frame_data: Frame pixel data as numpy array (BGR format) or None.
            audio_data: Ignored (CLIP is visual only).

        Returns:
            List of DetectionResult for detected categories (may be empty).

        Raises:
            ValueError: If frame_data is None or invalid.
        """
        if frame_data is None:
            raise ValueError("CLIP detector requires frame_data (numpy array)")

        if not isinstance(frame_data, np.ndarray):
            raise ValueError(
                f"frame_data must be numpy array, got {type(frame_data)}"
            )

        if len(frame_data.shape) != 3 or frame_data.shape[2] != 3:
            raise ValueError(
                f"frame_data must have shape (height, width, 3), got {frame_data.shape}"
            )

        try:
            # Convert BGR to RGB
            height, width = frame_data.shape[:2]
            logger.log(
                TRACE_LEVEL,
                f"[{self.name}] Converting frame BGR→RGB ({width}x{height}, "
                f"{frame_data.nbytes / 1024:.1f}KB)"
            )
            rgb_frame = cv2.cvtColor(frame_data, cv2.COLOR_BGR2RGB)

            # Convert to PIL Image
            from PIL import Image

            pil_image = Image.fromarray(rgb_frame)
            logger.log(
                TRACE_LEVEL,
                f"[{self.name}] Converted to PIL Image mode={pil_image.mode} "
                f"size={pil_image.size}"
            )

            # Prepare all candidate prompts
            all_prompts = []
            prompt_to_category = {}  # Map prompt text to category
            for category, candidate_texts in self.prompts_dict.items():
                for text in candidate_texts:
                    all_prompts.append(text)
                    prompt_to_category[text] = category

            logger.log(
                TRACE_LEVEL,
                f"[{self.name}] Prepared {len(all_prompts)} prompt candidates "
                f"across {len(self.prompts_dict)} categories"
            )

            # Process image and text with CLIP
            logger.log(TRACE_LEVEL, f"[{self.name}] Processing with CLIP processor...")
            inputs = self.processor(
                text=all_prompts,
                images=pil_image,
                return_tensors="pt",
                padding=True,
            )

            # Move inputs to device
            logger.log(TRACE_LEVEL, f"[{self.name}] Moving inputs to {self.device}...")
            inputs = {k: v.to(self.device) if hasattr(v, "to") else v for k, v in inputs.items()}

            # Run inference
            logger.log(
                TRACE_LEVEL,
                f"[{self.name}] Running inference on {self.model_name} ({self.device})..."
            )
            try:
                with __import__("torch").no_grad():
                    outputs = self.model(**inputs)
            except RuntimeError as e:
                if "out of memory" in str(e).lower():
                    logger.error(
                        f"CLIP inference failed (out of memory): {e}. "
                        f"Detector '{self.name}' skipped for this frame."
                    )
                    return []
                raise

            # Extract logits and compute similarities
            logits_per_image = outputs.logits_per_image
            logger.log(
                TRACE_LEVEL,
                f"[{self.name}] Got logits shape: {logits_per_image.shape}"
            )

            # Convert logits to probabilities via softmax
            import torch
            probs = torch.nn.functional.softmax(logits_per_image, dim=-1)

            # Aggregate by category (max similarity per category)
            category_scores = {}
            for i, prompt_text in enumerate(all_prompts):
                category = prompt_to_category[prompt_text]
                score = float(probs[0, i].cpu().item())

                # Keep max score per category
                if category not in category_scores:
                    category_scores[category] = score
                else:
                    category_scores[category] = max(category_scores[category], score)

            logger.log(
                TRACE_LEVEL,
                f"[{self.name}] Category scores: {category_scores}"
            )

            # Create DetectionResult for each category with non-zero confidence
            results = self._create_detection_results(category_scores)

            if results:
                logger.debug(
                    f"CLIP detected {len(results)} categories: "
                    f"{[r.label for r in results]}"
                )

            return results

        except Exception as e:
            if isinstance(e, ValueError):
                raise
            logger.error(f"Unexpected error during CLIP inference: {e}")
            return []

    def _create_detection_results(self, category_scores: Dict[str, float]) -> List[DetectionResult]:
        """Convert category scores to DetectionResult objects.

        Args:
            category_scores: Dict mapping category name to confidence score [0, 1].

        Returns:
            List of DetectionResult for categories with non-zero confidence.
        """
        results = []

        for category in self.categories:
            confidence = category_scores.get(category, 0.0)

            # Only include if confidence is above zero (avoid noise)
            if confidence > 0.0:
                results.append(
                    DetectionResult(
                        start_time=0.0,  # Set by pipeline
                        end_time=0.033,  # Set by pipeline (~30fps frame duration)
                        label=category,
                        confidence=confidence,
                        reasoning=f"CLIP detected '{category}' with confidence {confidence:.3f}",
                    )
                )

        return results

    def cleanup(self) -> None:
        """Clean up model and release GPU memory.

        Unloads the model from memory to allow garbage collection.
        Moves model to CPU before dereferencing to release GPU memory.
        """
        try:
            if self.model is not None:
                # Move model off GPU if applicable
                if hasattr(self.model, "cpu"):
                    self.model = self.model.cpu()
                self.model = None

            self.processor = None

            # Clear CUDA cache if available
            try:
                import torch

                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except ImportError:
                pass

            logger.debug(f"Cleaned up detector '{self.name}'")
        except Exception as e:
            logger.error(f"Error during cleanup of detector '{self.name}': {e}")

    @staticmethod
    def download_model(
        model_name: str,
        model_path: Optional[str] = None,
    ) -> None:
        """Download CLIP model from HuggingFace and cache locally.

        Args:
            model_name: HuggingFace model identifier (e.g., "openai/clip-vit-base-patch32").
            model_path: Optional custom cache path. If None, uses HF default cache.

        Raises:
            ValueError: If download fails or dependencies missing.
        """
        try:
            from transformers import CLIPModel, CLIPProcessor
        except ImportError as e:
            raise ValueError(
                f"CLIP dependencies not installed: {e}\n"
                f"Install with:\n"
                f"  pip install transformers torch torchvision pillow"
            )

        try:
            logger.info(f"Downloading CLIP model '{model_name}'...")

            load_kwargs = {}
            if model_path:
                load_kwargs["cache_dir"] = model_path

            # Download processor
            logger.info(f"  → Downloading processor...")
            CLIPProcessor.from_pretrained(model_name, **load_kwargs)
            logger.info(f"  ✓ Processor downloaded")

            # Download model
            logger.info(f"  → Downloading model (this may take a minute)...")
            CLIPModel.from_pretrained(model_name, **load_kwargs)
            logger.info(f"  ✓ Model downloaded successfully")

            if model_path:
                logger.info(f"Cached to: {model_path}")
            else:
                logger.info(f"Cached to: ~/.cache/huggingface/hub/")

        except Exception as e:
            logger.error(f"Failed to download model '{model_name}': {e}")
            raise ValueError(
                f"Download failed for '{model_name}': {e}\n"
                f"Check your internet connection and disk space."
            )
