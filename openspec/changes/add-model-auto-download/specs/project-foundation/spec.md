## ADDED Requirements

### Requirement: Model Auto-Download via CLI Flag (Phase 1)
The system SHALL provide a `--download-models` command-line flag that enables automatic verification and download of required models before video analysis begins.

#### Scenario: User requests model download
- **WHEN** user invokes `python -m video_censor --input video.mp4 --output results.json --config config.yaml --download-models`
- **THEN** the system verifies all required models against configured sources, downloads any missing models to the cache directory, and validates checksums before proceeding to analysis

#### Scenario: Download succeeds with progress feedback
- **WHEN** models are missing and `--download-models` flag is provided
- **THEN** the system displays human-friendly download progress including speed (MB/s), completion percentage, and ETA for each model

#### Scenario: Checksum validation fails
- **WHEN** a downloaded model's checksum does not match the configured value
- **THEN** the system deletes the corrupted file and reports a clear error with guidance to retry or update checksums

### Requirement: Model Source Configuration (Phase 1)
The system SHALL support configurable model sources in the YAML configuration file, including download URLs, checksums, and sizes for each required model. Hugging Face SHALL be the default model source.

#### Scenario: YAML specifies model sources
- **WHEN** the configuration file contains model sources under `models.sources`
- **THEN** each model entry includes `name`, `url`, and `checksum` fields describing the download source and integrity check value

#### Scenario: Multiple models specified
- **WHEN** configuration references multiple required models (e.g., vision model, profanity detector)
- **THEN** the system downloads all missing models in sequence with progress tracking for each

### Requirement: Configurable Model Cache Directory (Phase 1)
The system SHALL support a configurable cache directory via the YAML configuration to store downloaded models.

#### Scenario: User specifies custom cache directory
- **WHEN** the YAML configuration includes `models.cache_dir: /custom/path`
- **THEN** downloaded models are stored in the specified directory instead of the default location

#### Scenario: Default cache directory on unsupported platforms
- **WHEN** no cache directory is specified in configuration
- **THEN** the system uses a platform-appropriate default: `~/.cache/video-censor/models` (Linux/macOS), `%APPDATA%\video-censor\models` (Windows)

### Requirement: Atomic Model Downloads (Phase 1)
The system SHALL prevent partial or corrupted models in the cache by using atomic file operations during download.

#### Scenario: Download interrupted
- **WHEN** a model download is interrupted (network timeout, connection drop)
- **THEN** the temporary download file is cleaned up and the cache remains unmodified; user is prompted to retry

#### Scenario: Download completes successfully
- **WHEN** a model is fully downloaded and checksum validated
- **THEN** the file is atomically moved to the cache directory in a single operation

### Requirement: Pre-Download Disk Space Verification (Phase 1)
The system SHALL check available disk space before initiating model downloads.

#### Scenario: Insufficient disk space
- **WHEN** available disk space is less than 2× the total size of models to download
- **THEN** the system reports the space requirement and available space, then exits without attempting download

#### Scenario: Sufficient disk space
- **WHEN** available disk space exceeds 2× the required model size
- **THEN** the system proceeds with download

### Requirement: Download Retry with Exponential Backoff (Phase 1)
The system SHALL implement automatic retry logic for transient network failures.

#### Scenario: Network timeout on first attempt
- **WHEN** a model download fails due to network timeout
- **THEN** the system retries up to 3 times with exponential backoff (2s, 4s, 8s between attempts) before reporting a permanent failure

### Requirement: Idempotent Model Verification (Phase 1)
The system SHALL skip downloads for models already present and valid in the cache.

#### Scenario: Model exists with correct checksum
- **WHEN** a required model is already cached with a matching checksum
- **THEN** the system skips download and proceeds to analysis without re-fetching

#### Scenario: Model exists but checksum mismatch
- **WHEN** a cached model's checksum does not match the configuration
- **THEN** the system flags it as invalid, removes the file, and re-downloads the correct version

### Requirement: Clear Error Messages for Download Failures (Phase 1)
The system SHALL provide actionable error messages when model downloads fail, including next-step guidance.

#### Scenario: All download retries exhausted
- **WHEN** a model download fails after all retries
- **THEN** the system reports the URL, error reason, and guidance (e.g., "Check network connectivity. Model sources may be temporarily unavailable. Please retry or manually download from <URL> to <cache_dir>.")

#### Scenario: Configuration references unreachable URL
- **WHEN** a model URL in configuration is inaccessible (404, host unreachable)
- **THEN** the system reports the status code and URL, suggesting configuration review or fallback manual setup

## ADDED Requirements (Phase 2)

### Requirement: Automatic Download Invocation in Detection Pipeline (Phase 2)
The system SHALL automatically invoke model downloads during pipeline initialization if models are missing and the `--download-models` flag is set.

#### Scenario: Pipeline detects missing models
- **WHEN** AnalysisPipeline initializes and detects required models are missing from cache
- **THEN** the system invokes ModelManager.verify_models() if `--download-models` flag is set, then resumes detector instantiation

#### Scenario: Download succeeds and pipeline continues
- **WHEN** models are successfully downloaded during pipeline initialization
- **THEN** the system resumes analysis without requiring user restart or re-invocation

#### Scenario: Download fails during pipeline initialization
- **WHEN** a model download fails during pipeline initialization
- **THEN** the system reports a clear error and exits; does not proceed to analysis

### Requirement: Seamless Workflow Integration (Phase 2)
The system SHALL provide a transparent, unified workflow where users invoke a single command with `--download-models` and analysis proceeds automatically after successful model verification.

#### Scenario: Single command workflow
- **WHEN** user invokes `python -m video_censor --input video.mp4 --config config.yaml --download-models`
- **THEN** the system verifies/downloads models, initializes pipeline, and completes analysis in one continuous operation without user intervention

## ADDED Requirements (Phase 3)

### Requirement: Hugging Face Model Registry Integration (Phase 3)
The system SHALL integrate with the Hugging Face model registry to discover available model versions, checksums, and sizes.

#### Scenario: Query model metadata from Hugging Face
- **WHEN** HuggingFaceRegistry.query_model() is called for a model name
- **THEN** the system returns available versions, checksums, and download sizes for the specified model

#### Scenario: Cache model metadata locally
- **WHEN** model metadata is retrieved from Hugging Face API
- **THEN** the system caches metadata locally with a 24-hour TTL to reduce API calls on subsequent runs

### Requirement: Model Version Pinning and Fallback (Phase 3)
The system SHALL support model version pinning in YAML configuration with automatic fallback to alternatives if a specific version is unavailable.

#### Scenario: Pin specific model version
- **WHEN** YAML configuration specifies `model_version: v2.1`
- **THEN** the system downloads the pinned version; fails with clear guidance if unavailable

#### Scenario: Fallback to alternative model
- **WHEN** a specified model version is unavailable or deprecated
- **THEN** the system queries Hugging Face for available alternatives and suggests compatible versions to user

### Requirement: Automatic Model Discovery and Population (Phase 3)
The system SHALL automatically discover required models from YAML configuration and populate the cache with correct versions.

#### Scenario: Auto-discover models at pipeline startup
- **WHEN** AnalysisPipeline initializes with `--download-models` flag
- **THEN** the system parses YAML to determine all required models, queries Hugging Face for latest compatible versions, and ensures cache is populated

#### Scenario: Warn if model deprecated
- **WHEN** a required model is no longer available on Hugging Face
- **THEN** the system warns user of deprecation and suggests available alternatives with compatibility notes

### Requirement: Model Availability and Deprecation Warnings (Phase 3)
The system SHALL check model availability and warn users of deprecated models during initialization.

#### Scenario: Deprecated model in configuration
- **WHEN** YAML configuration specifies a model that has been superseded
- **THEN** the system displays a deprecation warning with suggested replacement and option to auto-update configuration

#### Scenario: Unavailable model on Hugging Face
- **WHEN** a required model is not found on Hugging Face
- **THEN** the system provides detailed error including model name, suggests checking for typos, and lists available similar models
