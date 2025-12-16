# Project Context

## Purpose

Video Censor is a personalized video censoring system that analyzes video content and identifies segments containing inappropriate or undesired material. It enables users to make informed decisions about which sections to skip or censor based on their preferences.

The system detects:
1. Nudity
2. Profanity
3. Violence
4. Sexual themes
5. Custom concepts specified in configuration

## Tech Stack

- **Language**: Python 3.13+
- **Configuration**: YAML format
- **Video Processing**: ffmpeg (or similar)
- **ML/AI**: Local LLMs and models preferred; third-party services as fallback
- **Output Format**: JSON

## Project Conventions

### Code Style

- Follow PEP 8 style guide
- Use type hints for all function signatures
- Line length: 100 characters maximum
- Use descriptive variable and function names (snake_case)
- Docstrings for all public functions/classes (Google-style format)

### Architecture Patterns

- Modular design with separation of concerns:
  - **Config Management**: YAML parsing and validation
  - **Video Processing**: Frame extraction and analysis
  - **Detection Engines**: Pluggable detection modules (nudity, profanity, violence, etc.)
  - **Output Generation**: Result serialization to JSON
- Support for local model inference as primary path
- Abstract interfaces for swapping between local and third-party services
- CLI-based entry point for flexibility

### Testing Strategy

- Unit tests for config parsing and output validation
- Integration tests for end-to-end analysis pipelines
- Test coverage minimum: 80%
- Use pytest as test framework

### Git Workflow

- Feature branches: `feature/[description]`
- Bug fixes: `fix/[description]`
- Main branch protection enabled
- Commit messages: descriptive, present tense

## Domain Context

### Video Analysis Scope

The system analyzes video content at two levels:
- **Temporal**: Precise timecode identification (start and end times)
- **Categorical**: Multi-label classification (e.g., a scene may contain both "Profanity" and "Sexual Theme")

### Detection Philosophy

- Users should have sufficient information to make their own decisions
- Multiple labels per segment enable nuanced filtering
- Descriptive text helps users understand what triggered detection

### Research Context

Extensive research on detection methodologies and model selection has been conducted. Reference: https://grok.com/share/bGVnYWN5LWNvcHk_90c99916-95b1-4e4f-8033-503598210af3

## Important Constraints

- **Processing**: Prefer local execution; minimize external API calls for privacy and cost
- **Performance**: Process videos in reasonable time (acceptable latency TBD)
- **Accuracy**: Balance detection sensitivity with false positive rates
- **Explainability**: Provide enough information for user decision-making

## Future Enhancements



## External Dependencies

- **ffmpeg**: Video frame extraction and metadata
- **Local LLMs**: Vision models (to be determined; candidates under research)
- **Third-party fallback**: APIs for specific detection tasks if local models insufficient

---

## Configuration Format (Proposed YAML)

```yaml
# video-censor.yaml - Analysis configuration

version: 1.0

# Detection enabled/disabled toggles
detections:
  nudity:
    enabled: true
    sensitivity: 0.7  # 0.0 (permissive) to 1.0 (strict)
    model: "local"    # "local" or specific model name
  
  profanity:
    enabled: true
    sensitivity: 0.8
    model: "local"
    # Optional language specification
    languages:
      - en
      - es
  
  violence:
    enabled: true
    sensitivity: 0.6
    model: "local"
  
  sexual_themes:
    enabled: true
    sensitivity: 0.75
    model: "local"
  
  # Custom detection categories
  custom_concepts:
    - name: "logos"
      enabled: false
      sensitivity: 0.5
      description: "Brand logos and product placement"
    
    - name: "spoilers"
      enabled: false
      sensitivity: 0.6
      description: "Movie/show spoiler content"

# Video processing settings
processing:
  # Frame sampling strategy
  frame_sampling:
    strategy: "uniform"  # "uniform", "scene_based", "all"
    sample_rate: 1.0    # seconds between frame analysis (1.0 = every second)
  
  # Temporal aggregation
  segment_merge:
    enabled: true
    merge_threshold: 2.0  # merge segments within N seconds
  
  # Performance tuning
  max_workers: 4        # parallel processing

# Output settings
output:
  format: "json"        # "json", "csv" (extensible)
  include_frames: false # include base64 encoded frame images
  include_confidence: true  # include confidence scores
  pretty_print: true    # human-readable JSON

# Model configuration
models:
  local:
    # TBD: specific model identifiers and paths
    vision_model: "llava-7b"  # example
    cache_dir: "./models"
  
  third_party:
    enabled_fallback: false
    # Credentials loaded from environment variables
    providers:
      - name: "example_api"
        enabled: false
```

---

## Output Format Specification

### JSON Output Structure

```json
{
  "metadata": {
    "file": "input_video.mp4",
    "duration": "1:23:45",
    "processed_at": "2025-12-13T14:30:00Z",
    "config": "video-censor.yaml"
  },
  "segments": [
    {
      "start_time": "00:48:25",
      "end_time": "00:48:26",
      "duration_seconds": 1,
      "labels": ["Profanity", "Sexual Theme"],
      "description": "A character uses explicit language in a sexual context",
      "confidence": 0.92,
      "detections": [
        {
          "label": "Profanity",
          "confidence": 0.95,
          "reasoning": "Detected strong profanity in audio"
        },
        {
          "label": "Sexual Theme",
          "confidence": 0.88,
          "reasoning": "Visual content combined with dialogue suggests sexual context"
        }
      ]
    },
    {
      "start_time": "01:12:30",
      "end_time": "01:12:45",
      "duration_seconds": 15,
      "labels": ["Violence"],
      "description": "Physical fight scene with impact sounds",
      "confidence": 0.87,
      "detections": [
        {
          "label": "Violence",
          "confidence": 0.87,
          "reasoning": "Rapid motion, impact sounds, and physical contact detected"
        }
      ]
    }
  ],
  "summary": {
    "total_segments_detected": 2,
    "total_flagged_duration": 16,
    "detection_counts": {
      "Profanity": 1,
      "Sexual Theme": 1,
      "Violence": 1
    }
  }
}
```

### Command-Line Interface

```bash
python -m video_censor \
  --input /path/to/video.mp4 \
  --output /path/to/results.json \
  --config /path/to/video-censor.yaml \
  [--verbose]
```
