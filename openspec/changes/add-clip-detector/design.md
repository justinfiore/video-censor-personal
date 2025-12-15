# CLIP Detector Design

## Context

CLIP (OpenAI's Contrastive Language-Image Pre-training) is a lightweight, efficient vision model that classifies images by comparing them against text prompts. Unlike LLaVA (which generates text responses), CLIP returns similarity scores directly, making it faster and less memory-intensive. The user's example YAML shows the desired config pattern: specifying text prompts per category inline in the detector config.

## Goals / Non-Goals

### Goals
- Support CLIP as a pluggable detector in the framework
- Enable category detection via configurable text prompts
- Support multiple CLIP model sizes/variants
- Integrate seamlessly with existing DetectionPipeline
- Follow LLaVA detector patterns for consistency

### Non-Goals
- Auto-generate prompts from category names (users explicitly provide text prompts)
- Support video-level aggregation beyond per-frame analysis
- GPU quantization or advanced optimization (can be added later)

## Decisions

### 1. Configuration Format
**Decision**: Support inline prompts in detector config, following the example YAML structure.

```yaml
- type: "clip"
  name: "clip-detector"
  model_name: "openai/clip-vit-base-patch32"
  categories:
    - "Nudity"
    - "Violence"
    - "Sexual Theme"
  prompts:
    - category: "Nudity"
      text: ["nude person", "naked body", "exposed genitals"]
    - category: "Violence"
      text: ["fight", "blood", "injury", "weapon"]
    - category: "Sexual Theme"
      text: ["sexual activity", "erotic content"]
```

**Rationale**: Inline prompts are concise and intuitive. Each prompt is a list of candidate phrases, and CLIP will compute similarity scores for all of them and aggregate.

### 2. Prompt Aggregation Strategy
**Decision**: Compute similarity scores for all prompt candidates per category, and return the maximum similarity score as the category's confidence.

**Rationale**: Mirrors real-world CLIP usage; users can provide multiple ways to phrase a concept. If any phrase strongly matches, the category is likely present.

**Alternative Considered**: Average similarity across prompts—rejected because it dilutes strong signals.

### 3. Model Loading and Device Handling
**Decision**: Reuse patterns from LLaVA detector with download support:
- Auto-detect GPU (CUDA, MPS); fall back to CPU
- Allow device override via config
- Support optional model download via `--download-models` CLI flag
- If models not found and `--download-models` NOT specified, raise error with download instructions
- Log selected device at initialization

**Rationale**: Consistency with existing LLaVA detector; users already understand the device selection model. Download flag provides convenient one-time setup without requiring separate manual download steps.

### 4. Per-Frame Analysis
**Decision**: Run CLIP inference on every frame (no full-audio-analysis support).

**Rationale**: CLIP is fast enough for per-frame analysis; no benefit to batching across entire audio track. Audio detectors (speech profanity) are separate.

### 5. Confidence Score Source
**Decision**: CLIP logit scores converted to probabilities via softmax (or raw similarity scores clamped to [0, 1]).

**Rationale**: CLIP outputs logits; softmax or clipping produces interpretable confidence values.

**Alternative Considered**: Always use max similarity—rejected because it loses information about competing categories.

## Risks / Trade-offs

- **Risk**: User misconfigures prompts (too vague, too specific, contradictory).
  - **Mitigation**: Documentation with prompt engineering tips; example YAML provided.

- **Risk**: Multiple detectors (CLIP + LLaVA) consume GPU memory.
  - **Mitigation**: Users choose one or the other; both respect device selection; cleanup() releases models.

- **Risk**: Prompt-based detection may miss edge cases that vision-language models catch.
  - **Mitigation**: Document as architectural choice; users can chain CLIP + LLaVA if needed.

## Migration Plan

- New detector; no migration needed for existing LLaVA configs
- Users opt-in by adding CLIP detector to their YAML config
- Existing tests and pipelines continue unchanged

## Open Questions

- Should we support prompt file references (like LLaVA's prompt_file) for long/complex prompts?
  - **Decision for now**: Keep inline prompts only; add file support in future if needed.
- Should CLIP support custom device precision (float16, bfloat16)?
  - **Decision for now**: Stick with float32; add precision config in future if performance testing shows benefit.
