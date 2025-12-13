# Design: Enhanced Configuration Validation

## Context

The current config system validates only structure (required fields, type correctness). Users can pass logically invalid configurations that fail at runtime. Semantic validation catches these early with clear error messages, improving developer experience and debugging.

## Goals / Non-Goals

- **Goals**:
  - Catch invalid configurations at load time before processing begins
  - Provide clear, specific error messages indicating which value is invalid and why
  - Support the 5 detection types specified in project.md (nudity, profanity, violence, sexual_themes, custom_concepts)
  - Enforce logical constraints (e.g., at least one detection enabled)
  - Minimize performance impact (validation happens once at startup)

- **Non-Goals**:
  - Real-time config reload (not in scope)
  - Support multiple output formats beyond JSON
  - Dynamic detection category registration

## Decisions

### Validation Strategy

1. **Layered approach**: Keep structural validation (current) separate from semantic validation (new)
   - Rationale: Easier to debug and maintain, clear separation of concerns

2. **Detection category validation**:
   - Each detection category under `detections.<category>` must have: `enabled` (bool), `sensitivity` (float 0.0-1.0), `model` (string)
   - Rationale: Ensures consistent structure across all detection types, allows flexible detection discovery

3. **At least one detection enabled**:
   - Iterate detection entries and check if any have `enabled=true`
   - Rationale: Processing a video with no detections enabled is a misconfiguration

4. **Enum constraints**:
   - `output.format`: must be "json" (only supported format currently)
   - `processing.frame_sampling.strategy`: must be one of ("uniform", "scene_based", "all")
   - Rationale: Fail fast on unsupported options; makes future format additions explicit

5. **Numeric constraints**:
   - `sensitivity`: 0.0 ≤ value ≤ 1.0
   - `max_workers`: > 0
   - `merge_threshold`: >= 0.0
   - Rationale: Prevent illogical parameter combinations

## Risks / Trade-offs

- **Risk**: Breaking change—existing configs with invalid values will fail validation
  - **Mitigation**: Document clearly in CHANGELOG and migration guide; provide error messages that guide users to fixes

- **Risk**: Detection category discovery is now implicit (any key under `detections` is treated as a category)
  - **Mitigation**: This matches the design in project.md which shows open-ended structure for custom_concepts

## Migration Plan

1. Before deployment, validate existing/example configs
2. Update `video-censor.yaml.example` to use only valid values
3. Add migration notes to QUICK_START.md if configs change
4. Provide clear error messages that explain what's wrong and expected ranges

## Open Questions

- Should we provide a "validate-only" CLI flag to test configs without processing?
- Should we log warnings for unused detection categories (e.g., enabled but may never be called)?
