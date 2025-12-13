# Change: Add Project Foundation

## Why

The video-censor project needs a foundational structure to be usable by end users. This includes the entry point script, configuration management, command-line interface, and comprehensive documentation for setup and quick start.

## What Changes

- **ADDED**: Main Python entry point script (`video_censor_personal.py`) with CLI argument parsing
- **ADDED**: Configuration file parsing and validation (YAML support) in `video_censor_personal` module
- **ADDED**: `requirements.txt` with Python dependencies
- **ADDED**: `README.md` with project overview, installation, and model/tool setup instructions
- **ADDED**: `QUICK_START.md` with step-by-step user guide for installation, model download, and basic usage

## Impact

- Affected specs: `project-foundation` (new capability)
- Affected code: `video_censor_personal.py`, `video_censor_personal/` module, `video_censor_personal/config.py`, `video_censor_personal/cli.py`, `requirements.txt`, `README.md`, `QUICK_START.md`
- Users can now install dependencies, download required models and tools, and run the application via `python video_censor_personal.py`
