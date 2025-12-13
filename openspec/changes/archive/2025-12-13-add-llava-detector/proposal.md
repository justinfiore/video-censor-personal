# Change: Add LLaVA Vision-Language Detector Implementation

## Why

The detection framework provides the abstract infrastructure for pluggable detectors, but lacks a concrete, functional implementation. LLaVA (Large Language and Vision Assistant) is a capable open-source vision-language model that can analyze video frames and identify multiple content categories (Nudity, Profanity, Violence, Sexual Themes) in a single inference pass. Implementing a LLaVA detector makes the framework end-to-end functional and enables users to perform real video analysis.

## What Changes

- **LLaVA Detector Implementation**: Concrete Detector subclass that loads LLaVA models (7B or 13B) and performs multi-category content detection on video frames
- **Prompt Management**: Configurable detection prompts loaded from external files (not hardcoded), allowing customization without code changes
- **Model Verification**: Pre-flight checks ensure models exist at expected locations before initialization; fail fast with actionable error messages
- **Single-Pass Multi-Category Detection**: Detects Nudity, Profanity, Violence, and Sexual Themes in one inference pass
- **Confidence Scoring**: LLM provides confidence scores directly in responses; parser extracts and validates scores
- **No Auto-Download**: Assumes models are pre-installed; validates and provides clear download instructions if missing
- **Configuration Integration**: LLaVA detector config references prompt file path and model selection (7B vs 13B)

## Impact

- **New capability**: llava-detector (concrete vision-language model detector)
- **Affected specs**: llava-detector (new), detection-framework (MODIFIED - no API changes, added example config)
- **Code changes**: 
  - `video_censor_personal/detectors/llava_detector.py` (new, ~150-200 lines)
  - `video_censor_personal/detectors/__init__.py` (new, registration)
  - `prompts/` directory (new, template prompt files)
  - `requirements.txt` (uncomment transformers/torch/pillow dependencies)
- **Tests**: `tests/test_llava_detector.py` (unit tests with mocks, ~250+ lines)
- **Config**: Example detector config added to `video-censor.yaml.example`

## Key Architectural Decisions

1. **No Model Downloads**: Detector assumes models pre-exist; validates before use and instructs user where to place them
2. **Prompt as Separate File**: Prompts live in dedicated files (`prompts/*.txt`) and are referenced from YAML config, enabling experimentation without code changes
3. **Single Model Instance**: Model loaded once at detector initialization and reused across all frames for efficiency
4. **LLM-Provided Confidence**: Confidence scores come directly from LLM responses (not computed separately), ensuring consistency between reasoning and confidence
5. **Fail-Fast Model Validation**: During detector `__init__`, verify model exists and can be loaded; provide helpful error messages with download instructions
