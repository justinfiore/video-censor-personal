# project-foundation Specification

## Purpose
TBD - created by archiving change add-project-foundation. Update Purpose after archive.
## Requirements
### Requirement: Command-Line Interface

The system SHALL accept video analysis requests through a command-line interface that validates required arguments and optional parameters.

#### Scenario: Basic analysis invocation
- **WHEN** user runs `python video_censor_personal.py --input <video.mp4> --config <config.yaml> --output <results.json>`
- **THEN** the CLI parses arguments and passes them to the analysis pipeline

#### Scenario: Help text display
- **WHEN** user runs `python video_censor_personal.py --help`
- **THEN** the CLI displays usage instructions, available arguments, and examples

#### Scenario: Missing required argument
- **WHEN** user runs CLI without required `--input` or `--config` arguments
- **THEN** the CLI reports the missing argument with helpful error message

#### Scenario: Verbose logging
- **WHEN** user runs CLI with `--verbose` flag
- **WHEN** enabled, debug-level logging is written to stdout/stderr

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

