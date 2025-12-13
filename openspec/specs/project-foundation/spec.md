# project-foundation Specification

## Purpose
TBD - created by archiving change add-project-foundation. Update Purpose after archive.
## Requirements
### Requirement: Command-Line Interface

The system SHALL accept `--output-video` argument and validate it against audio remediation configuration.

#### Scenario: Add --output-video CLI argument
- **WHEN** user runs main entry point
- **THEN** `--output-video` argument is available to accept output video path

#### Scenario: Output-video is optional when remediation disabled
- **WHEN** user does not provide `--output-video` and audio remediation is disabled
- **THEN** argument is optional; analysis proceeds without video output

#### Scenario: Fail-fast if remediation enabled without output-video
- **WHEN** config has `audio.remediation.enabled: true` but `--output-video` is not provided
- **THEN** system exits immediately with exit code 1 (before analysis begins)
- **AND** error message clearly explains:
  - Audio remediation is enabled in config
  - `--output-video` argument is required
  - Example command showing correct usage
  - Alternative: how to disable remediation in config

#### Scenario: Fail-fast if output-video provided but remediation disabled
- **WHEN** user provides `--output-video` but audio remediation is disabled in config
- **THEN** system exits immediately with exit code 1 (before analysis begins)
- **AND** error message clearly explains:
  - `--output-video` requires audio remediation to be enabled
  - Enable remediation in config or remove the `--output-video` argument
  - No video file is written if remediation is not enabled

#### Scenario: Validate output-video path is writable
- **WHEN** user provides `--output-video` with path in non-existent directory
- **THEN** system raises error indicating directory does not exist

#### Scenario: Config is reusable across runs
- **WHEN** same config is used with different `--output-video` paths
- **THEN** config file contains no hardcoded paths
- **AND** remediation output path is determined by CLI argument, not config

#### Scenario: Help text documents output-video
- **WHEN** user runs with `--help`
- **THEN** help text includes `--output-video` description:
  - Purpose (output video path for audio remediation)
  - Note that it's required if remediation enabled
  - Example usage

### Requirement: Configuration File Parsing

The system SHALL parse and validate YAML configuration files before processing, enforcing both structural and semantic constraints.

#### Scenario: Valid configuration load
- **WHEN** user provides valid YAML config file with required fields and semantically valid values
- **THEN** configuration is loaded and validated successfully

#### Scenario: Invalid YAML syntax
- **WHEN** user provides YAML file with syntax errors
- **THEN** system reports parse error with line number and helpful message

#### Scenario: Missing required fields
- **WHEN** configuration file is missing required fields (e.g., `detections`, `processing`, `output`)
- **THEN** system reports validation error listing missing fields

#### Scenario: Default configuration fallback
- **WHEN** no config file specified and default location exists
- **THEN** system loads configuration from default location (e.g., `./video-censor.yaml`)

#### Scenario: Detection sensitivity out of range
- **WHEN** a detection category specifies `sensitivity` value outside [0.0, 1.0]
- **THEN** system raises ConfigError indicating valid range and the invalid value provided

#### Scenario: Detection category missing required fields
- **WHEN** a detection category under `detections.<name>` is missing `enabled`, `sensitivity`, or `model` field
- **THEN** system raises ConfigError naming the missing field and detection category

#### Scenario: No detection categories enabled
- **WHEN** configuration has detection categories defined but none have `enabled: true`
- **THEN** system raises ConfigError indicating at least one detection must be enabled

#### Scenario: Invalid output format
- **WHEN** `output.format` is set to unsupported value (e.g., "csv", "xml")
- **THEN** system raises ConfigError indicating only "json" is currently supported

#### Scenario: Invalid frame sampling strategy
- **WHEN** `processing.frame_sampling.strategy` is set to value other than "uniform", "scene_based", or "all"
- **THEN** system raises ConfigError listing valid strategies

#### Scenario: Invalid max_workers value
- **WHEN** `processing.max_workers` is set to value ≤ 0
- **THEN** system raises ConfigError indicating max_workers must be a positive integer

#### Scenario: Invalid merge_threshold value
- **WHEN** `processing.segment_merge.merge_threshold` is set to negative value
- **THEN** system raises ConfigError indicating merge_threshold must be non-negative

### Requirement: Dependencies Declaration

The system SHALL declare all Python package dependencies in a machine-readable format.

#### Scenario: Requirements file exists
- **WHEN** project is distributed to users
- **THEN** `requirements.txt` lists all direct Python dependencies with versions

#### Scenario: Installation via pip
- **WHEN** user runs `pip install -r requirements.txt`
- **THEN** all dependencies are installed and compatible with Python 3.13+

### Requirement: Setup and Installation Documentation

The system SHALL provide README documentation with complete installation and setup instructions.

#### Scenario: System requirements listed
- **WHEN** user reads README.md
- **THEN** README clearly states Python version requirement (3.13+) and external tool requirements (ffmpeg)

#### Scenario: Dependency installation instructions
- **WHEN** user reads README.md
- **THEN** README provides step-by-step instructions for:
  - Creating a Python virtual environment
  - Installing Python packages from requirements.txt
  - Verifying successful installation

#### Scenario: Model download instructions
- **WHEN** user reads README.md
- **THEN** README provides:
  - List of required AI models (e.g., LLaVA)
  - Download links and installation instructions
  - Storage location guidance (e.g., ./models directory)
  - Disk space requirements

#### Scenario: External tool setup
- **WHEN** user reads README.md
- **THEN** README includes instructions for installing ffmpeg (platform-specific: macOS, Linux, Windows)

#### Scenario: Example usage
- **WHEN** user reads README.md
- **THEN** README includes basic usage example with sample command

### Requirement: Quick Start Guide

The system SHALL provide QUICK_START.md with step-by-step user onboarding.

#### Scenario: Installation walkthrough
- **WHEN** user reads QUICK_START.md
- **THEN** guide provides numbered steps for:
  - Creating virtual environment
  - Installing dependencies
  - Verifying Python and pip versions

#### Scenario: Model setup instructions
- **WHEN** user reads QUICK_START.md "Download Models" section
- **THEN** guide includes:
  - Download URLs for required models
  - Where to place downloaded files
  - How to verify successful download
  - Expected disk usage

#### Scenario: Tool installation
- **WHEN** user reads QUICK_START.md "Install Tools" section
- **THEN** guide provides platform-specific (macOS, Linux, Windows) instructions for ffmpeg

#### Scenario: First run example
- **WHEN** user reads QUICK_START.md "First Analysis" section
- **THEN** guide provides:
  - Sample video file reference
  - Sample config file to use
  - Complete command to run first analysis
  - Expected output format

#### Scenario: Troubleshooting
- **WHEN** user encounters common setup problems
- **THEN** QUICK_START.md includes troubleshooting section covering:
  - Python version issues
  - Model download failures
  - ffmpeg not found
  - Permission errors

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

