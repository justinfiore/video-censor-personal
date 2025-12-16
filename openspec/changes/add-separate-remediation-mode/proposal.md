# Change: Add Separate Remediation Mode (Three-Phase Workflow)

## Why

Currently, video analysis and remediation are tightly coupled—users must re-run expensive ML analysis each time they want to adjust segment allowances and re-remediate. This wastes computation and creates friction for iterative workflows where users review, refine, and remediate multiple times.

## What Changes

- Add new `--input-segments <path>` CLI option to load pre-existing segments JSON
- When `--input-segments` is provided, skip all detection/analysis phases
- Load segments directly from JSON file and proceed to remediation (audio, video, chapters)
- Validate JSON file metadata against input video (warning on mismatch)
- Respect `"allow": true` segments during remediation (skip them)

## Impact

- Affected specs: `analysis-pipeline`, `output-generation`
- Affected code: `video_censor_personal/cli.py`, `video_censor_personal.py` (main entry point)
- Related features: `segment-allow-override` (already implemented), `video-segment-removal` (future)
