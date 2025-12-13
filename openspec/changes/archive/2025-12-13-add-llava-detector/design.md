# Design: LLaVA Vision-Language Detector

## Context

LLaVA (Large Language and Vision Assistant) is an open-source vision-language model that combines a vision encoder and language model. It can analyze images and answer questions about them, making it well-suited for content detection tasks.

Users prefer local model execution for privacy and cost. LLaVA models are available pre-trained in two sizes:
- **7B**: ~4 GB download, ~7 GB loaded, runs on 16 GB RAM systems
- **13B**: ~26 GB download, ~26 GB loaded, requires 30+ GB RAM or GPU

The detector must verify models exist before use and provide actionable instructions if they're missing.

## Goals / Non-Goals

- **Goals**:
  - Load LLaVA model once at detector initialization
  - Reuse model across all frames (no per-frame reloading)
  - Detect 4 content categories (Nudity, Profanity, Violence, Sexual Themes) in single inference pass
  - Extract confidence scores from LLM responses
  - Support both 7B and 13B model sizes via configuration (default 7B)
  - Verify that the selected model exists pre-deployment; fail fast with helpful error messages
  - Allow prompt customization via external files (configurable in YAML)
  - Convert RGB frames to appropriate format for LLaVA (PIL Images)
  - Gracefully handle inference timeouts or OOM errors during frame analysis
    - Retry inference up to 3 times with exponential backoff
    - If still failing, return empty results and log error

- **Non-Goals**:
  - Auto-download models (assume pre-installed)
  - Optimize inference for GPU (deferred to future `add-gpu-optimization` feature)
  - Real-time streaming inference (batch processing only)
  - Fine-tuning or retraining LLaVA (use as-is)
  
  **Note on GPU Optimization**: PyTorch's `device_map="auto"` provides reasonable defaults.
  Users can optimize via environment variables (`CUDA_VISIBLE_DEVICES`, `TORCH_DTYPE`).
  Advanced GPU support (batch inference, quantization, per-GPU config) is planned as a
  separate feature after LLaVA detector is functional. See `openspec/project.md` for details.

## Decisions

### Model Loading Strategy

```python
class LLaVADetector(Detector):
    """Vision-language detector using LLaVA models."""
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize detector with model verification.
        
        Args:
            config: Dict with keys:
              - name: Detector instance name
              - categories: List of categories to detect
              - model_name: Model identifier ("llava-v1.5-7b" or "llava-v1.5-13b")
              - model_path: Optional custom path; defaults to HF cache
              - prompt_file: Path to prompt template file (e.g., "./prompts/default.txt")
        """
        super().__init__(config)
        
        self.model_name = config.get("model_name", "liuhaotian/llava-v1.5-7b")
        self.model_path = config.get("model_path")  # HF cache or custom
        self.prompt_file = config.get("prompt_file", "./prompts/llava-detector.txt")
        
        # Load prompt template
        self.prompt_template = self._load_prompt()
        
        # Load and validate model at init time
        self.model, self.processor = self._load_model()
        
    def _load_prompt(self) -> str:
        """Load prompt template from file."""
        try:
            with open(self.prompt_file, 'r') as f:
                return f.read().strip()
        except FileNotFoundError:
            raise ValueError(f"Prompt file not found: {self.prompt_file}")
    
    def _load_model(self) -> tuple:
        """Load LLaVA model and processor.
        
        Raises:
            ValueError: If model not found or loading fails.
        """
        try:
            from transformers import AutoProcessor, LlavaForConditionalGeneration
            
            # Attempt to load from cache or model_path
            # If model_path provided, validate it exists
            if self.model_path and not Path(self.model_path).exists():
                raise FileNotFoundError(f"Model path does not exist: {self.model_path}")
            
            processor = AutoProcessor.from_pretrained(self.model_name)
            model = LlavaForConditionalGeneration.from_pretrained(
                self.model_name,
                cache_dir=self.model_path
            )
            
            return model, processor
        
        except ImportError:
            raise ValueError(
                "LLaVA dependencies not installed. Install with:\n"
                "  pip install transformers torch torchvision pillow\n"
                "See QUICK_START.md for model download instructions."
            )
        
        except Exception as e:
            if "model not found" in str(e).lower() or "404" in str(e):
                raise ValueError(
                    f"Model '{self.model_name}' not found in cache or at {self.model_path}.\n"
                    f"Download the model first:\n"
                    f"  python -c \"from transformers import AutoTokenizer, AutoModelForCausalLM; "
                    f"AutoTokenizer.from_pretrained('{self.model_name}'); "
                    f"AutoModelForCausalLM.from_pretrained('{self.model_name}')\"\n"
                    f"Model location: ~/.cache/huggingface/hub/\n"
                    f"See QUICK_START.md for detailed instructions."
                )
            raise ValueError(f"Failed to load model '{self.model_name}': {e}")
```

Rationale:
- Model loaded once at `__init__`, stored as instance variable
- Reused across all `detect()` calls (same detector instance processes multiple frames)
- Pre-flight validation prevents runtime surprises
- Clear error messages guide users to resolution

### Prompt Template Pattern

Prompts live in separate files to enable experimentation without code changes:

```
# prompts/llava-detector.txt
Analyze this image for content. 

For each category below, determine if it's present (Yes/No) and provide a confidence score (0.0-1.0).
Return ONLY valid JSON with no additional text.

Categories to detect:
1. Nudity - Nude or partially nude bodies
2. Profanity - Text, signs, or logos with explicit language
3. Violence - Physical violence, weapons, injuries, aggressive acts
4. Sexual Theme - Sexual or suggestive content

Return JSON format:
{
  "nudity": {"detected": true/false, "confidence": 0.0-1.0, "reasoning": "..."},
  "profanity": {"detected": true/false, "confidence": 0.0-1.0, "reasoning": "..."},
  "violence": {"detected": true/false, "confidence": 0.0-1.0, "reasoning": "..."},
  "sexual_theme": {"detected": true/false, "confidence": 0.0-1.0, "reasoning": "..."}
}
```

Rationale:
- Structured JSON response enables reliable parsing
- Explicit format requirements reduce ambiguity
- Prompt file allows A/B testing without redeploying
- Confidence scores included in response (not computed separately)

### Detection Flow

```python
def detect(
    self,
    frame_data: Optional[np.ndarray] = None,
    audio_data: Optional[Any] = None,
) -> List[DetectionResult]:
    """Analyze frame with LLaVA model.
    
    Args:
        frame_data: numpy array in BGR format (from OpenCV)
        audio_data: Ignored (LLaVA is visual + text only)
    
    Returns:
        List of DetectionResult for detected categories
    """
    if frame_data is None:
        raise ValueError("LLaVA requires frame_data")
    
    # Convert BGR to RGB and create PIL Image
    rgb_frame = cv2.cvtColor(frame_data, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(rgb_frame)
    
    # Prepare inputs
    inputs = self.processor(
        text=self.prompt_template,
        images=pil_image,
        return_tensors="pt"
    )
    
    # Inference
    try:
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=512,
            temperature=0.7,
        )
    except RuntimeError as e:
        if "out of memory" in str(e).lower():
            logger.error(f"OOM during inference: {e}")
            # Return empty results; pipeline will continue with other detectors
            return []
        raise
    
    # Decode response
    response = self.processor.decode(outputs[0], skip_special_tokens=True)
    
    # Parse JSON response
    try:
        result_dict = json.loads(response)
    except json.JSONDecodeError:
        logger.error(f"Failed to parse LLaVA response as JSON: {response}")
        return []
    
    # Convert to DetectionResult objects
    results = []
    category_map = {
        "nudity": "Nudity",
        "profanity": "Profanity",
        "violence": "Violence",
        "sexual_theme": "Sexual Theme",
    }
    
    for key, label in category_map.items():
        if key in result_dict and result_dict[key].get("detected"):
            confidence = float(result_dict[key].get("confidence", 0.5))
            confidence = max(0.0, min(1.0, confidence))  # Clamp to [0, 1]
            reasoning = result_dict[key].get("reasoning", f"{label} detected")
            
            results.append(
                DetectionResult(
                    start_time=0.0,  # Will be set by pipeline
                    end_time=0.033,  # Will be set by pipeline
                    label=label,
                    confidence=confidence,
                    reasoning=reasoning,
                )
            )
    
    return results
```

Rationale:
- Structured prompts produce JSON; easier to parse reliably
- Confidence scores come from LLM, ensuring consistency
- Graceful error handling (OOM, JSON parse failures) logs and returns empty results
- Pipeline will continue with other detectors even if this one fails

### Configuration Schema

```yaml
detectors:
  - type: "llava"
    name: "llava-vision"
    categories:
      - "Nudity"
      - "Profanity"
      - "Violence"
      - "Sexual Theme"
    model_name: "liuhaotian/llava-v1.5-7b"      # or "...13b"
    model_path: null                             # Use HF default cache, or specify custom
    prompt_file: "./prompts/llava-detector.txt" # External prompt file
```

Rationale:
- `model_name`: Allows swapping between 7B and 13B or other variants
- `model_path`: Enables custom cache location (e.g., NVMe for speed)
- `prompt_file`: External configuration enables experimentation

### Error Messages & Recovery

**Model Not Found**:
```
ValueError: Model 'liuhaotian/llava-v1.5-7b' not found in cache or at /custom/path.
Download the model first:
  python -c "from transformers import AutoTokenizer, AutoModelForCausalLM; 
  AutoTokenizer.from_pretrained('liuhaotian/llava-v1.5-7b'); 
  AutoModelForCausalLM.from_pretrained('liuhaotian/llava-v1.5-7b')"
Model location: ~/.cache/huggingface/hub/
See QUICK_START.md for detailed instructions.
```

**Dependencies Missing**:
```
ValueError: LLaVA dependencies not installed. Install with:
  pip install transformers torch torchvision pillow
See QUICK_START.md for model download instructions.
```

**Prompt File Missing**:
```
ValueError: Prompt file not found: ./prompts/llava-detector.txt
Create prompt file or update 'prompt_file' in detector config.
```

## Risks / Trade-offs

- **Risk**: Model inference is slow (~1-5s per frame depending on GPU/CPU)
  - **Mitigation**: Document in README, recommend GPU setups, allow configurable sample rates
  
- **Risk**: OOM errors if system lacks sufficient RAM
  - **Mitigation**: Gracefully handle RuntimeError, return empty results, allow fallback detectors
  
- **Risk**: Prompt brittleness - LLM may not always return valid JSON
  - **Mitigation**: Try-catch JSON parsing, log failures, return empty results (pipeline continues)
  
- **Risk**: Confidence scores from LLM may not be well-calibrated
  - **Mitigation**: Document as experimental, allow threshold tuning in config, A/B test prompts

## Migration Plan

1. Create `LLaVADetector` class in `video_censor_personal/detectors/llava_detector.py`
2. Register detector globally in `video_censor_personal/detectors/__init__.py`
3. Create prompt template file `prompts/llava-detector.txt`
4. Add example config to `video-censor.yaml.example`
5. Write unit tests with mocked model
6. Write integration tests with stub LLaVA response
7. Update `requirements.txt` (uncomment transformers/torch/pillow)
8. Update documentation (QUICK_START.md) with detector usage example

## Open Questions

- Should we support batch inference (multiple frames at once) for efficiency? Deferred to future optimization.
- Should we cache frame encodings to avoid re-processing identical frames? Deferred to future caching layer.
- Should timeout be configurable? For now, use default transformers timeout; make configurable in future.
