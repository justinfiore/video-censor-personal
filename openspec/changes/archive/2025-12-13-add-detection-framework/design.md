# Design: Detection Framework

## Context

Detection is the core product. The system must:
1. Support multiple detector implementations (LLMs, vision models, APIs)
2. Enable each detector to identify multiple categories efficiently (not one detector per category)
3. Allow flexible orchestration of multiple detectors on same content
4. Handle detector initialization, model loading, and cleanup
5. Provide consistent error handling and fallbacks

## Goals / Non-Goals

- **Goals**:
  - Define abstract detector interface (initialize, detect, cleanup)
  - Support multi-category detection per detector (single LLM inference → multiple category results)
  - Allow multiple detector instances running in sequence/parallel
  - Abstract detector configuration and model selection
  - Handle detector-specific errors gracefully
  - Enable future detector implementations without framework changes
  - Support both frame-based (visual) and audio-based detection

- **Non-Goals**:
  - Real-time streaming detection (batch processing only, per-frame analysis)
  - Automatic model downloading (assume models pre-installed or configured)
  - GPU memory optimization (defer to detector implementation)

## Decisions

### Detector Interface (Abstract Base Class)

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from video_censor_personal.frame import DetectionResult

class Detector(ABC):
    """Abstract base class for all detectors."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize detector with configuration.
        
        Args:
            config: Detector-specific config (model name, threshold, etc.)
        """
        self.config = config
        self.name = config.get("name", self.__class__.__name__)
        self.categories = config.get("categories", [])  # What this detector analyzes
        
    @abstractmethod
    def detect(self, frame_data: Any, audio_data: Optional[Any] = None) -> List[DetectionResult]:
        """Analyze frame and/or audio, return detections for all categories.
        
        Args:
            frame_data: numpy array or None
            audio_data: numpy array/bytes or None
            
        Returns:
            List of DetectionResult objects (multiple categories possible)
        """
        pass
        
    def cleanup(self) -> None:
        """Clean up resources (models, temp files, etc.)."""
        pass
```

Rationale:
- Abstract interface allows multiple implementations
- `categories` field describes what this detector covers (e.g., ["Profanity", "Nudity", "Violence"])
- `detect()` returns multiple DetectionResult objects (one per category found)
- Optional audio_data enables audio-based detectors (profanity detection from speech)

### Multi-Category Detection Pattern

When a detector runs on a frame, it can return results for multiple categories:

```python
# Single detector identifies multiple issues in one pass
results = detector.detect(frame_data=frame_pixels)
# Returns:
[
    DetectionResult(start_time=10.0, end_time=10.033, label="Profanity", confidence=0.92, reasoning="..."),
    DetectionResult(start_time=10.0, end_time=10.033, label="Violence", confidence=0.85, reasoning="..."),
    # Both from same detector, same frame analysis
]
```

Rationale: Efficient inference (single LLM forward pass) vs. multiple category-specific models

### Detector Registry

```python
class DetectorRegistry:
    """Registry for detector implementations."""
    
    def __init__(self):
        self.detectors = {}  # name -> detector_class
        
    def register(self, name: str, detector_class: type) -> None:
        """Register detector implementation."""
        self.detectors[name] = detector_class
        
    def get(self, name: str) -> type:
        """Get registered detector class."""
        return self.detectors.get(name)
        
    def create(self, name: str, config: Dict) -> Detector:
        """Instantiate detector with config."""
        detector_class = self.get(name)
        if not detector_class:
            raise ValueError(f"Unknown detector: {name}")
        return detector_class(config)
```

Rationale: Enables plugin architecture; new detector types registered at runtime

### Detection Pipeline

```python
class DetectionPipeline:
    """Orchestrates multi-detector analysis."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize pipeline with detector configs."""
        self.detectors: List[Detector] = []
        self.config = config
        self._initialize_detectors()
        
    def _initialize_detectors(self) -> None:
        """Create detector instances from config."""
        for detector_config in self.config.get("detectors", []):
            detector_type = detector_config.get("type")
            detector = registry.create(detector_type, detector_config)
            self.detectors.append(detector)
            
    def analyze_frame(self, frame: Frame, timecode: float) -> List[DetectionResult]:
        """Run all detectors on frame, aggregate results."""
        all_results = []
        for detector in self.detectors:
            try:
                results = detector.detect(frame_data=frame.data)
                for result in results:
                    # Set timecode from frame
                    result.start_time = timecode
                    result.end_time = timecode + frame_duration
                all_results.extend(results)
            except Exception as e:
                logger.error(f"Detector {detector.name} failed: {e}")
                # Continue with other detectors
                continue
        return all_results
        
    def cleanup(self) -> None:
        """Clean up all detectors."""
        for detector in self.detectors:
            detector.cleanup()
```

Rationale:
- Sequential detector execution allows graceful error handling
- Results aggregated with frame-level timecode
- Detector failure doesn't stop pipeline

### Configuration Structure

Config file specifies which detectors to use:

```yaml
detectors:
  - type: "llama-vision"           # Detector implementation type
    name: "primary-llm"             # Instance name
    model: "llava-v1.5-7b"          # Model identifier
    categories:                      # What to analyze
      - "Profanity"
      - "Nudity"
      - "Violence"
      - "Sexual Theme"
    confidence_threshold: 0.7       # Detector-specific param
    
  - type: "audio-profanity"        # Different detector for audio
    name: "audio-detector"
    model: "openai-whisper"
    categories:
      - "Profanity"
    languages:
      - "en"
      - "es"
```

Rationale:
- Declarative detector setup
- Each detector declares categories it can identify
- Detector-specific parameters (thresholds, model paths, etc.) isolated

## Risks / Trade-offs

- **Risk**: Single detector failure stops frame analysis (if not handled)
  - **Mitigation**: Try-catch around detector.detect(); continue with other detectors; log errors

- **Risk**: Multi-category detectors may have different confidence per category
  - **Mitigation**: Each result includes own confidence; framework treats each independently

- **Risk**: Detector initialization can be slow (model loading)
  - **Mitigation**: Initialize once at startup; cleanup at end; reuse for all frames

## Migration Plan

1. Implement framework abstractions (Detector, DetectorRegistry, DetectionPipeline)
2. Add framework tests (mocks, stubs)
3. Implement stub/dummy detector for testing
4. Integration tests with real frame data
5. Later: implement actual LLM-based detectors

## Decisions Finalized

- **Detector execution**: Sequential (not parallel threading). Each detector runs on frame in order; results aggregated. Parallelization deferred to future optimization.
- **Result caching**: No caching initially. Detectors run fresh on each frame; detectors handle their own optimization (e.g., batching, model caching) internally.
