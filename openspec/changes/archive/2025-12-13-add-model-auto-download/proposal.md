# Change: Add Model Auto-Download

## Why
Currently, users must manually download and configure models before running video analysis. This creates friction during initial setup and limits accessibility. Automating model verification and download on-demand reduces setup complexity and improves user experience, particularly for first-time users.

## What Changes

### Phase 1: CLI Flag and Model Manager Foundation
- **New CLI option**: `--download-models` flag to enable automatic model downloading
- **Pre-execution verification**: Validate all required models based on YAML configuration before analysis starts
- **Automatic downloading**: Fetch missing models from Hugging Face or configured sources to a cache directory
- **User feedback**: Display human-friendly download progress (speed, ETA, completion percentage) via `tqdm`
- **Configuration extension**: Add `models.cache_dir` (platform-appropriate defaults) and model source definitions to YAML schema
- **Atomic downloads**: Prevent partial/corrupted model files via temporary file handling
- **Checksum validation**: Verify downloaded model integrity using SHA256 or Hugging Face-provided algorithms
- **Retry logic**: Automatic retries (3 attempts) with exponential backoff on network failures
- **Disk space check**: Pre-download verification that 2× model size disk space is available

### Phase 2: Detection Pipeline Integration
- **Auto-invocation**: Seamlessly trigger model downloads during pipeline initialization if models missing and flag set
- **Lazy initialization**: Resume analysis without restart after successful download
- **Pipeline state tracking**: Monitor model readiness and provide clear error messages on download failures
- **Transparent workflow**: Users experience single unified flow from `--download-models` through analysis

### Phase 3: Model Caching and Auto-Discovery
- **Hugging Face registry integration**: Discover available model versions, checksums, and sizes from Hugging Face API
- **Metadata caching**: Cache model information locally (24-hour TTL) to reduce API calls
- **Model version pinning**: Support specific model versions in configuration with fallback alternatives
- **Auto-population**: Automatically populate cache with correct models based on YAML requirements
- **Model availability checks**: Warn if configured models are deprecated or unavailable, suggest alternatives

## Impact
- **Affected specs**: `project-foundation` (extends CLI, configuration, and model management)
- **Affected code**: 
  - Main CLI entry point (model parameter handling)
  - Configuration parser (YAML schema extensions)
  - New model manager module (download orchestration, progress reporting, checksum validation)
- **Breaking changes**: None. Feature is opt-in via `--download-models` flag; default behavior unchanged
- **Dependencies**: May require new packages for HTTP downloads and progress display (e.g., `tqdm`, `requests`)
