## Context

During remediation, ffmpeg can fail for many reasons: corrupt input containers (missing moov atom), damaged frames, codec incompatibilities, or disk issues. Currently these surface as opaque `RuntimeError` exceptions with raw ffmpeg stderr. The user from the log saw `moov atom not found` during the metadata application phase, meaning the output video was corrupt after video remediation produced it.

Key stakeholders: CLI users running batch processing who need unattended runs to succeed when possible, and UI users who need actionable error messages.

## Goals / Non-Goals

- **Goals:**
  - Diagnose known ffmpeg error patterns and translate them to user-friendly explanations with suggested fixes
  - Automatically recover from errors when possible (e.g., re-mux with `movflags +faststart`, skip corrupt frames, retry with re-encoding)
  - Collect warnings about recovery actions taken and present a summary at the end of processing
  - Preserve the original output when recovery is not possible (don't make things worse)

- **Non-Goals:**
  - Repairing arbitrary corrupt input files (out of scope—suggest user use `ffmpeg -i input -c copy output` themselves)
  - Adding a full video validation/repair tool
  - Changing the happy-path remediation behavior

## Decisions

### Error Source Attribution

A critical design decision is distinguishing whether a failing file is:
1. **The user's original input** — the file the user passed via `--input`
2. **An intermediate file produced by our pipeline** — temp files and output files created during remediation

This distinction drives both the messaging (user action vs. bug report) and recovery aggressiveness.

The pipeline processes files in this order, and each phase's input origin is known at call time:

| Phase | Reads From | File Origin |
|-------|-----------|-------------|
| Audio remediation | `input_video_path` + audio data | **User's original** |
| Audio muxing | `input_video_path` + temp WAV → `output_video_path` | **User's original** (video) + **Pipeline** (audio WAV) |
| Video remediation | `output_video_path` (from muxing) | **Pipeline intermediate** |
| Metadata application | `output_video_path` (from video remediation) | **Pipeline intermediate** |

Each phase wrapper passes a `file_origin` enum (`USER_INPUT` or `PIPELINE_INTERMEDIATE`) to the diagnostics engine so it can tailor the message.

When the error is on a **pipeline intermediate**, the system:
1. Attempts all available recovery strategies (more aggressively than for user input errors)
2. If recovery fails or produces degraded output, generates a copy-pasteable bug report
3. Directs the user to https://github.com/justinfiore/video-censor-personal/issues

When the error is on the **user's original input**, the system:
1. Attempts recovery if available (e.g., `-err_detect ignore_err`)
2. Provides user-facing diagnosis ("your file appears to be corrupt")
3. Does NOT generate a bug report (not our fault)

### Bug Report Template

When a pipeline-intermediate error triggers a bug report, the system generates:

```
────────────────────────────────────────────────────────
⚠ This may be a bug in video-censor-personal.

Please report this issue at:
  https://github.com/justinfiore/video-censor-personal/issues

Copy the following into the bug report form:

Title: Bug: <phase> produced corrupt output (<error pattern>)

Description:
## What happened
During the <phase> step, video-censor-personal produced an intermediate
file that could not be read by the next processing step.

Error: <ffmpeg error message (first 3 lines)>
Phase: <audio_remediation | muxing | video_remediation | metadata>
File: <path to intermediate file>

## How to reproduce
Command: <full CLI command that was run>
Config: <config file path>
Input: <input file name>

## Environment
- ffmpeg version: <version>
- OS: <platform info>
- Python: <python version>
────────────────────────────────────────────────────────
```

### Error Pattern Matching

- **Error pattern matching via a registry**: A list of `ErrorPattern` dataclass instances in `remediation_diagnostics.py`, each with: regex pattern, human-readable diagnosis (templated with `{file_origin}` placeholder), suggested fix, and optional recovery strategy callable. This keeps knowledge centralized and easily extensible.
- **Recovery wraps existing operations**: Each remediation phase gets a try/except that, on failure, consults the diagnostics registry with the file origin, optionally retries with modified ffmpeg flags, and if it's a pipeline intermediate failure, generates a bug report. Recovery strategies include:
  - Skip metadata on corrupt container (preserve video without metadata)
  - Retry with `-err_detect ignore_err` for corrupt frames/data
  - Retry with full re-encoding (`-c:v libx264 -c:a aac`) when stream copy fails
  - Retry with `-fflags +genpts` for timestamp disorder
  - Detect empty output files (0 bytes) as silent failures
- **Warnings collector on RemediationManager**: A simple list attribute `self.warnings` that accumulates structured warning objects (phase, message, file_origin, bug_report). The caller (CLI main or UI) prints the summary after processing completes.
- **No new dependencies**: All diagnostics and recovery use existing ffmpeg/ffprobe tooling.

### Error Pattern Categories

| Category | Auto-Recoverable | Recovery Strategy |
|----------|:-:|---|
| moov atom not found (output) | Yes | Skip metadata; preserve video |
| Invalid data in input | Yes | `-err_detect ignore_err`, then re-encode |
| Corrupt H.264 frames | Yes | `-err_detect ignore_err -c copy` |
| Non-monotonous DTS | Yes | `-fflags +genpts` |
| Could not write header | Yes | Re-encode with `-c:v libx264 -c:a aac` |
| PES packet size mismatch | Yes | `-err_detect ignore_err` |
| Stream copy muxing failure | Yes | Re-encode instead of copy |
| Empty output file | Yes | Detect + raise with diagnosis |
| Encoder/decoder not found | No | User must install codec |
| No space left on device | No | User must free disk space |
| Permission denied | No | User must fix permissions |
| moov atom not found (input) | No | User must re-acquire source |

## Risks / Trade-offs

- Recovery strategies may mask underlying input problems → Mitigation: Always log warnings prominently; never silently succeed.
- Pattern matching on ffmpeg stderr is fragile across versions → Mitigation: Use broad regex patterns; test against ffmpeg 6.x–8.x output.
- Retry with re-encoding is slow for large files → Mitigation: Only re-encode when the faster `-c copy` approach fails; document the time cost in warnings.

## Open Questions

- Should there be a config flag to disable automatic recovery (strict mode)?
- Should recovery attempts have a retry limit (e.g., max 2 retries per phase)?
