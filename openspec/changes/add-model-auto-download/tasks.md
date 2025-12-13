# Tasks: Model Auto-Download (All Phases)

## Phase 1: CLI Flag and Model Manager Foundation

### 1. Configuration Schema Extension
- [ ] 1.1 Update YAML schema to support `models.cache_dir` field with platform-appropriate defaults
- [ ] 1.2 Add model source definitions (name, url, checksum, size) to `models.sources` section
- [ ] 1.3 Add Hugging Face default model sources to schema (LLaVA, profanity detectors, etc.)
- [ ] 1.4 Create example configuration file with Hugging Face model sources and checksums
- [ ] 1.5 Add validation tests for new YAML fields and schema

### 2. Model Manager Module
- [ ] 2.1 Create `video_censor_personal/model_manager.py` with ModelManager class
- [ ] 2.2 Implement `verify_models()` method to check if models exist and checksums match
- [ ] 2.3 Implement `_download_model()` with atomic temp file handling
- [ ] 2.4 Implement SHA256 checksum validation; support additional algorithms from Hugging Face
- [ ] 2.5 Add human-friendly progress reporting via `tqdm` (speed, ETA, completion %)
- [ ] 2.6 Implement retry logic: 3 retries with exponential backoff (2s, 4s, 8s)
- [ ] 2.7 Implement pre-download disk space verification (require 2× model size free)
- [ ] 2.8 Use `platformdirs` library for cross-platform cache directory resolution

### 3. CLI Integration (Phase 1)
- [ ] 3.1 Add `--download-models` flag to main CLI argument parser
- [ ] 3.2 Add download models execution before analysis in main entry point
- [ ] 3.3 Ensure `--download-models` is idempotent (skip existing valid models)
- [ ] 3.4 Add clear error messages with recovery guidance for download failures

## Phase 2: Detection Pipeline Integration

### 4. Detection Pipeline Auto-Invoke
- [ ] 4.1 Extract model requirements from configuration at pipeline startup
- [ ] 4.2 Check for missing models before detector instantiation
- [ ] 4.3 Auto-invoke ModelManager.verify_models() if `--download-models` flag set
- [ ] 4.4 Seamlessly resume analysis after successful download (no restart needed)
- [ ] 4.5 Provide clear error messages if download fails before proceeding to analysis

### 5. Pipeline State Management
- [ ] 5.1 Update AnalysisPipeline to track model readiness state
- [ ] 5.2 Implement lazy detector initialization (wait for model download to complete)
- [ ] 5.3 Add pipeline logging for download progress and completion

## Phase 3: Model Caching and Auto-Discovery

### 6. Hugging Face Model Registry Integration
- [ ] 6.1 Implement HuggingFaceRegistry class for model metadata discovery
- [ ] 6.2 Query Hugging Face API for available model versions, checksums, and sizes
- [ ] 6.3 Cache model metadata locally (TTL: 24 hours) to reduce API calls
- [ ] 6.4 Support model version pinning and version fallback in configuration

### 7. Auto-Discovery and Caching
- [ ] 7.1 Detect required models from YAML at pipeline startup
- [ ] 7.2 Auto-populate cache directory with model metadata from Hugging Face
- [ ] 7.3 Implement model availability checking (warn if model deprecated/unavailable)
- [ ] 7.4 Support model fallback suggestions (e.g., if LLaVA unavailable, suggest alternatives)
- [ ] 7.5 Implement lazy cache refresh (invalidate metadata if >24h old)

## Testing (All Phases)

### 8. Unit Tests
- [ ] 8.1 Test model_manager: checksum validation (match, mismatch, missing checksum)
- [ ] 8.2 Test model_manager: atomic download (success, failure, partial cleanup)
- [ ] 8.3 Test model_manager: disk space checks (sufficient, insufficient, edge cases)
- [ ] 8.4 Test platformdirs integration for cache directory resolution
- [ ] 8.5 Test retry logic with mocked network failures
- [ ] 8.6 Test Hugging Face registry: metadata parsing, caching, TTL expiry

### 9. Integration Tests
- [ ] 9.1 Mock HTTP server: test full download + checksum validation flow
- [ ] 9.2 Test progress reporting output and formatting
- [ ] 9.3 Test detection pipeline auto-invoke (missing models trigger download)
- [ ] 9.4 Test YAML configuration parsing with all new model source fields
- [ ] 9.5 Test cross-platform cache directory paths (Windows, macOS, Linux)

### 10. End-to-End Tests
- [ ] 10.1 Full pipeline test: `--download-models` flag → download → analysis → output
- [ ] 10.2 Test idempotency: re-run with cached models skips download
- [ ] 10.3 Test error recovery: corrupted cache → re-download on next run
- [ ] 10.4 Test model fallback: unavailable model suggests alternative

## Documentation

### 11. User Documentation
- [ ] 11.1 Update README with `--download-models` usage example
- [ ] 11.2 Document YAML model source configuration with Hugging Face defaults
- [ ] 11.3 Document custom model source configuration (private repos, alternatives)
- [ ] 11.4 Add troubleshooting section: network errors, disk space, corrupted models
- [ ] 11.5 Document model fallback behavior and version pinning
- [ ] 11.6 Create quick-start guide for first-time users (emphasize `--download-models`)

### 12. Internal Documentation
- [ ] 12.1 Document ModelManager API and internal workflow
- [ ] 12.2 Document HuggingFaceRegistry integration and metadata caching strategy
- [ ] 12.3 Document checksum update and model refresh procedures

## Dependencies

### 13. External Dependencies
- [ ] 13.1 Add `tqdm` to `requirements.txt` for progress reporting
- [ ] 13.2 Add `platformdirs` to `requirements.txt` for cross-platform paths
- [ ] 13.3 Verify `urllib3` or `requests` availability for HTTP downloads
- [ ] 13.4 Optional: `huggingface-hub` library for native Hugging Face API support

## Parallelization & Dependencies

**Can run in parallel:**
- Tasks 8.1–8.6 (unit tests) during implementation
- Tasks 11.1–11.3 (user docs) once Phase 1 complete
- Task 6 (Hugging Face registry) after Phase 2

**Critical path:**
1. Phase 1 (tasks 1–3): CLI foundation
2. Phase 2 (tasks 4–5): Pipeline integration depends on Phase 1
3. Phase 3 (tasks 6–7): Auto-discovery depends on Phase 1 & 2
4. Testing (tasks 8–10): Can start once Phase 1 complete, expands with later phases
5. Documentation (tasks 11–12): Final phase after implementation
