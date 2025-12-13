"""LLaVA vision-language detector for multi-category content analysis."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import cv2
import numpy as np

from video_censor_personal.detection import Detector
from video_censor_personal.frame import DetectionResult

logger = logging.getLogger(__name__)


class LLaVADetector(Detector):
    """Vision-language detector using LLaVA model for content classification.

    Analyzes video frames with LLaVA to detect multiple content categories
    (Nudity, Profanity, Violence, Sexual Themes) in a single inference pass.
    Requires pre-downloaded LLaVA models; does not auto-download.
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize LLaVA detector with model and prompt validation.

        Args:
            config: Configuration dict with keys:
              - name: Detector instance name
              - categories: List of categories to analyze
              - model_name: HuggingFace model identifier (default: "liuhaotian/llava-v1.5-7b")
              - model_path: Optional custom model cache path (default: HF cache)
              - prompt_file: Path to prompt template file (default: "./prompts/llava-detector.txt")

        Raises:
            ValueError: If model not found, dependencies missing, or prompt file invalid.
        """
        super().__init__(config)

        self.model_name = config.get("model_name", "liuhaotian/llava-v1.5-7b")
        self.model_path = config.get("model_path")
        self.prompt_file = config.get("prompt_file", "./prompts/llava-detector.txt")

        # Load and validate prompt
        self.prompt_template = self._load_prompt()

        # Load and validate model
        self.model = None
        self.processor = None
        self.model, self.processor = self._load_model()

        logger.info(
            f"Initialized LLaVA detector '{self.name}' with model '{self.model_name}' "
            f"for categories: {', '.join(self.categories)}"
        )

    def _load_prompt(self) -> str:
        """Load detection prompt template from file.

        Returns:
            Prompt template as string.

        Raises:
            ValueError: If prompt file not found or not readable.
        """
        prompt_path = Path(self.prompt_file)
        if not prompt_path.exists():
            raise ValueError(
                f"Prompt file not found: {self.prompt_file}\n"
                f"Expected path: {prompt_path.resolve()}\n"
                f"Create the file or update 'prompt_file' in detector config."
            )

        try:
            with open(prompt_path, "r") as f:
                return f.read().strip()
        except Exception as e:
            raise ValueError(
                f"Failed to read prompt file '{self.prompt_file}': {e}"
            )

    def _load_model(self) -> tuple:
        """Load and validate LLaVA model and processor.

        Returns:
            Tuple of (model, processor) from transformers library.

        Raises:
            ValueError: If model not found, dependencies missing, or loading fails.
        """
        # Check if transformers is available
        try:
            from transformers import AutoProcessor, LlavaForConditionalGeneration
        except ImportError:
            raise ValueError(
                "LLaVA dependencies not installed. Install with:\n"
                "  pip install transformers torch torchvision pillow\n"
                "See QUICK_START.md for detailed model download instructions."
            )

        try:
            logger.debug(f"Loading LLaVA model: {self.model_name}")

            # Load processor
            processor = AutoProcessor.from_pretrained(self.model_name)

            # Load model with optional custom cache path
            load_kwargs = {}
            if self.model_path:
                load_kwargs["cache_dir"] = self.model_path

            model = LlavaForConditionalGeneration.from_pretrained(
                self.model_name, **load_kwargs
            )

            logger.debug(f"Successfully loaded model: {self.model_name}")
            return model, processor

        except FileNotFoundError as e:
            raise ValueError(
                f"Model '{self.model_name}' not found. Please download it first.\n\n"
                f"Download command:\n"
                f"  python -c \"from transformers import AutoTokenizer, "
                f"AutoModelForCausalLM; "
                f"AutoTokenizer.from_pretrained('{self.model_name}'); "
                f"AutoModelForCausalLM.from_pretrained('{self.model_name}')\"\n\n"
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
        """Analyze frame with LLaVA model for content detection.

        Args:
            frame_data: Frame pixel data as numpy array (BGR format) or None.
            audio_data: Ignored (LLaVA is visual only for this detector).

        Returns:
            List of DetectionResult for detected categories (may be empty).

        Raises:
            ValueError: If frame_data is None or invalid.
        """
        if frame_data is None:
            raise ValueError("LLaVA detector requires frame_data (numpy array)")

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
            rgb_frame = cv2.cvtColor(frame_data, cv2.COLOR_BGR2RGB)

            # Convert to PIL Image
            from PIL import Image

            pil_image = Image.fromarray(rgb_frame)

            # Prepare inputs for LLaVA
            inputs = self.processor(
                text=self.prompt_template,
                images=pil_image,
                return_tensors="pt",
            )

            # Run inference
            try:
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=512,
                    temperature=0.7,
                )
            except RuntimeError as e:
                if "out of memory" in str(e).lower():
                    logger.error(
                        f"LLaVA inference failed (out of memory): {e}. "
                        f"Detector '{self.name}' skipped for this frame."
                    )
                    return []
                raise

            # Decode response
            response = self.processor.decode(outputs[0], skip_special_tokens=True)

            # Parse JSON response
            try:
                result_dict = self._parse_response(response)
            except json.JSONDecodeError:
                logger.warning(
                    f"LLaVA response not valid JSON. Raw response:\n{response}\n"
                    f"Detector '{self.name}' returned no results for this frame."
                )
                return []

            # Convert to DetectionResult objects
            results = self._create_detection_results(result_dict)

            if results:
                logger.debug(
                    f"LLaVA detected {len(results)} categories: "
                    f"{[r.label for r in results]}"
                )

            return results

        except Exception as e:
            if isinstance(e, (ValueError, RuntimeError)):
                raise
            logger.error(f"Unexpected error during LLaVA inference: {e}")
            return []

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse LLaVA response and extract JSON.

        Args:
            response: Raw response string from LLaVA model.

        Returns:
            Parsed JSON dict.

        Raises:
            json.JSONDecodeError: If response is not valid JSON.
        """
        # Try to extract JSON if response contains extra text
        response = response.strip()

        # Look for JSON block
        if "{" in response and "}" in response:
            start = response.index("{")
            end = response.rindex("}") + 1
            response = response[start:end]

        return json.loads(response)

    def _create_detection_results(self, result_dict: Dict[str, Any]) -> List[DetectionResult]:
        """Convert parsed LLaVA response to DetectionResult objects.

        Args:
            result_dict: Parsed JSON dict from LLaVA response.

        Returns:
            List of DetectionResult for detected categories.
        """
        results = []

        # Map JSON keys to category labels
        category_map = {
            "nudity": "Nudity",
            "profanity": "Profanity",
            "violence": "Violence",
            "sexual_theme": "Sexual Theme",
        }

        for key, label in category_map.items():
            if key not in result_dict:
                continue

            category_result = result_dict[key]
            if not isinstance(category_result, dict):
                logger.warning(
                    f"Invalid format for category '{key}': expected dict, got {type(category_result)}"
                )
                continue

            # Check if detected
            detected = category_result.get("detected", False)
            if not detected:
                continue

            # Extract confidence
            try:
                confidence = float(category_result.get("confidence", 0.5))
                # Clamp to [0.0, 1.0]
                confidence = max(0.0, min(1.0, confidence))
            except (ValueError, TypeError):
                logger.warning(
                    f"Invalid confidence for {label}: {category_result.get('confidence')}. "
                    f"Using default 0.5."
                )
                confidence = 0.5

            # Extract reasoning
            reasoning = category_result.get(
                "reasoning", f"{label} detected by LLaVA"
            )

            results.append(
                DetectionResult(
                    start_time=0.0,  # Set by pipeline
                    end_time=0.033,  # Set by pipeline (~30fps frame duration)
                    label=label,
                    confidence=confidence,
                    reasoning=reasoning,
                )
            )

        return results

    def cleanup(self) -> None:
        """Clean up model and release GPU memory.

        Unloads the model from memory to allow garbage collection.
        """
        try:
            if self.model is not None:
                # Move model off GPU if applicable
                if hasattr(self.model, "cpu"):
                    self.model = self.model.cpu()
                self.model = None

            self.processor = None

            logger.debug(f"Cleaned up detector '{self.name}'")
        except Exception as e:
            logger.error(f"Error during cleanup of detector '{self.name}': {e}")
