# Design: Model Auto-Download

## Context
Video Censor currently relies on pre-downloaded models, creating setup friction. Users must manually locate, download, and organize models before running analysis. This blocks MVP rollout and complicates first-time user experience.

The feature must handle:
- Multiple model sources (local cache, HTTP, conditional fallbacks)
- Cross-platform file paths (Windows, macOS, Linux)
- Concurrent downloads (performance for multi-model setups)
- Network failures and partial downloads (resilience)
- Checksum verification (integrity assurance)
- User visibility into progress (particularly for large models >1GB)

## Goals / Non-Goals

### Goals
- Enable `--download-models` flag to trigger pre-execution model verification and download
- Support configurable cache directory via YAML (`models.cache_dir`)
- Provide human-friendly download progress reporting (speed, ETA, completion %)
- Validate downloads via checksums to detect corruption
- Handle network failures gracefully with clear error messages
- Support atomic downloads (prevent corrupted partial files in cache)
- Work cross-platform without manual path adjustments

### Non-Goals
- Interactive model selection (download all required models or none)
- Model update/upgrade logic (beyond initial download)
- Private model sources or authentication (HTTP-only, no auth mechanisms)
- GPU-specific model variants (all variants downloaded)
- Resume interrupted downloads in this phase (restart is acceptable)

## Decisions

### Decision: Atomic Downloads via Temp Files
**What**: Write downloads to temporary files, move atomically to cache only after checksum passes.
**Why**: Ensures cache never contains partial or corrupted models; simplifies cleanup on failures.
**Alternatives**:
- Direct cache write + checksum check: Risk of orphaned corrupted files.
- In-memory checksum: Memory overhead for large models (>5GB).

### Decision: Configuration-Driven Model Sources
**What**: Model URLs and checksums stored in YAML configuration, not hardcoded.
**Why**: Accommodates future model changes, supports custom model sources, enables testing against mock downloads.
**Alternatives**:
- Hardcoded registry: Inflexible for future model candidates under research.
- Environment variables only: Less discoverable than YAML config.

### Decision: Sequential Download with Progress Reporting
**What**: Download models one-at-a-time with progress bar (`tqdm` or similar).
**Why**: Simpler implementation; most setups involve 1-2 models. Concurrent downloads add complexity without proportional benefit for typical use cases.
**Alternatives**:
- Concurrent downloads: Adds thread pool complexity; minor speedup for typical 1-2 models.
- Silent downloads: Poor UX for large models (unclear if process hung).

### Decision: Checksum Validation Post-Download
**What**: Verify SHA256 or similar after download completes; fail with clear message if mismatch.
**Why**: Detects corruption from network errors, disk issues, or misconfigured sources.
**Alternatives**:
- No validation: Risk of undetected corrupted models causing cryptic runtime errors.
- Streaming hash: Adds implementation complexity for marginal benefit.

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| **Network timeout on large models** | Implement configurable timeout; default 300s. Retry logic with exponential backoff. |
| **Disk space exhaustion** | Pre-check available space before download. Warn if <2x model size free. |
| **Cross-platform path issues** | Use `pathlib.Path` throughout; test on Windows/macOS/Linux in CI. |
| **Outdated checksums in config** | Document checksum update process; validate config against known good checksums in tests. |
| **Model URLs become invalid** | Graceful error message + suggestion to update YAML. Fallback to manual instructions. |

## Implementation Plan: All Phases in Single Change

### Phase 1: CLI Flag and Model Manager Foundation
- Implement `--download-models` command-line flag
- Create model manager module with download, verification, and checksum validation
- Support YAML configuration of model sources with Hugging Face defaults
- Atomic downloads with temporary file handling
- Progress reporting via `tqdm`

### Phase 2: Detection Pipeline Integration
- Integrate model manager into existing detection pipeline initialization
- Detect missing models before detector instantiation
- Auto-invoke download if `--download-models` flag is set and models missing
- Seamlessly resume analysis after successful download without user intervention

### Phase 3: Model Caching and Auto-Discovery
- Implement automatic model source discovery from Hugging Face registry
- Cache model metadata (available versions, checksums, sizes)
- Support default model fallback (e.g., if LLaVA unavailable, suggest alternatives)
- Lazy initialization: detect required models from YAML at pipeline startup, auto-populate cache

All three phases ship as a cohesive feature in this change, ensuring complete model management from initial download through cached reuse and auto-discovery.

## Decisions Finalized

1. **Model source finalization**: Use Hugging Face as primary default source; documented in YAML examples with fallback configuration patterns.
2. **Checksum algorithm**: SHA256 as default algorithm; support additional algorithms that Hugging Face provides (flexible for future model sources).
3. **Timeout and retry strategy**: Fixed defaults (300s timeout, 3 retries with exponential backoff); YAML extension available post-MVP if configurability needed.
4. **Cache directory default**: Use platform-appropriate paths via `platformdirs` library—`~/.cache/video-censor/models` (Linux/macOS), `%APPDATA%\video-censor\models` (Windows).
