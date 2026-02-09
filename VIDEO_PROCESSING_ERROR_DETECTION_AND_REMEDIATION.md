# Video Processing Error Detection and Remediation

## Overview

The Video Processing Error Detection and Remediation feature provides intelligent error handling during the video remediation pipeline. Instead of failing with raw ffmpeg errors, the system:

1. **Diagnoses** known error patterns and explains them in plain language
2. **Recovers automatically** when possible (e.g., retrying with different encoding settings)
3. **Logs actionable warnings** when recovery actions are taken
4. **Summarizes all warnings** at the end of the processing run

This ensures batch processing runs succeed as often as possible, and when they can't, users get clear guidance on how to fix the problem.

A key design principle is **error source attribution**: every error diagnosis clearly states whether the problem is in **your original input file** or in an **intermediate file produced by the pipeline**. When the pipeline itself produces a bad file, the system generates a copy-pasteable bug report you can submit directly.

## Error Pattern Registry

The error pattern registry is defined in:

```
video_censor_personal/remediation_diagnostics.py
```

It is a centralized list of `ErrorPattern` entries, each containing:

| Field | Description |
|-------|-------------|
| `pattern` | Regex to match against ffmpeg stderr output |
| `diagnosis` | Human-readable explanation of what went wrong |
| `suggested_fix` | Actionable advice for the user |
| `recovery_strategy` | Optional automatic recovery function (None if human intervention required) |
| `typical_origin` | Whether this error typically comes from user input or pipeline processing |

### Adding New Patterns

To add a new error pattern, append an `ErrorPattern` to the `ERROR_PATTERNS` list in `remediation_diagnostics.py`. No other code changes are needed — the diagnosis engine will automatically pick it up.

## Automatically Recoverable Errors

These errors are detected and resolved without user intervention. A warning is logged describing the recovery action taken.

### Corrupt Output Container (moov atom not found)

- **Cause**: A previous processing step (video remediation, muxing) produced an incomplete MP4 file. The moov atom — which contains the video's index/metadata — is missing, typically because the write was interrupted or the container wasn't finalized.
- **Recovery**: Skip metadata application and preserve the output video as-is. The video is still playable but may be missing custom metadata tags.
- **Example ffmpeg error**: `moov atom not found`

### Invalid Data / Corrupt Input

- **Cause**: The input file (or intermediate file) has corrupt sections, was truncated, or has an incompatible container format.
- **Recovery**: Retry the operation with `-err_detect ignore_err` to tell ffmpeg to skip corrupt sections rather than aborting. If that fails, retry with full re-encoding (`-c:v libx264 -c:a aac`).
- **Example ffmpeg error**: `Invalid data found when processing input`

### Corrupt H.264 Frames

- **Cause**: Individual video frames have corrupt data (damaged Parameter Sets, broken slice headers). Common with files from interrupted recordings or damaged storage.
- **Recovery**: Retry with `-err_detect ignore_err -c copy` to skip corrupt frames. The output may have brief visual glitches at the corrupt frame locations.
- **Example ffmpeg errors**: `non-existing PPS referenced`, `decode_slice_header error`, `no frame!`

### Timestamp Disorder (Non-monotonous DTS)

- **Cause**: Decoding timestamps are out of order in the output stream. Common when concatenating segments, processing transport streams, or when the input has editing discontinuities.
- **Recovery**: Retry with `-fflags +genpts` to regenerate presentation timestamps from the decode timestamps.
- **Example ffmpeg error**: `Non-monotonous DTS in output stream 0:1`

### Codec/Container Mismatch (Could Not Write Header)

- **Cause**: The video or audio codec is incompatible with the output container format (e.g., certain codec parameters not supported in MP4).
- **Recovery**: Retry with explicit re-encoding using universally compatible codecs (`-c:v libx264 -c:a aac`).
- **Example ffmpeg error**: `Could not write header for output file #0 (incorrect codec parameters ?): Invalid argument`

### Stream Copy Muxing Failure

- **Cause**: The `-c copy` (stream copy) mode fails because the input stream has issues that prevent direct copying into the output container.
- **Recovery**: Retry with full re-encoding instead of stream copy. This is slower but handles codec incompatibilities.
- **Example ffmpeg error**: Various errors during muxing with `-c copy` that succeed with re-encoding.

### Corrupt Transport Stream Data

- **Cause**: The input contains corrupted MPEG transport stream packets.
- **Recovery**: Retry with `-err_detect ignore_err` to skip corrupted packets.
- **Example ffmpeg error**: `PES packet size mismatch`

## Errors Requiring Human Intervention

These errors are diagnosed with clear explanations and suggestions, but cannot be automatically resolved.

### Encoder/Decoder Not Found

- **Cause**: The required codec is not compiled into the installed ffmpeg build. For example, `libx265` or a hardware encoder may not be available.
- **Diagnosis**: Identifies the missing codec and suggests installing a build of ffmpeg that includes it, or switching to an available codec.
- **Example ffmpeg error**: `Unknown encoder 'libx265'`, `Encoder hevc_videotoolbox not found`

### Insufficient Disk Space

- **Cause**: The output drive has run out of space during video processing.
- **Diagnosis**: Explains the disk space issue and suggests freeing space or redirecting output to a different drive.
- **Example ffmpeg error**: `No space left on device`

### Permission Denied

- **Cause**: The process does not have write permission to the output file or directory.
- **Diagnosis**: Identifies the permission issue and suggests checking file/directory permissions or running with appropriate privileges.
- **Example ffmpeg error**: `Permission denied`

### Corrupt Source Video (Input moov atom missing)

- **Cause**: The original input video file is fundamentally broken — the moov atom is missing from the source file itself (not just our output). This can happen with interrupted downloads, incomplete recordings, or damaged storage.
- **Diagnosis**: Explains the input file is corrupt and suggests re-downloading or re-acquiring the source video.
- **Example ffmpeg error**: `moov atom not found` (on the input file)

### Empty Input File

- **Cause**: The input file exists but has 0 bytes — it's completely empty.
- **Diagnosis**: Explains the file is empty and suggests checking the source.
- **Example**: File size is 0 bytes.

## Error Source Attribution

Every error diagnosis identifies whether the problematic file is:

1. **Your original input file** — the video you passed via `--input`
2. **An intermediate file produced by the pipeline** — a temp file or output file created during processing

### Pipeline File Flow

| Processing Phase | Reads From | File Origin |
|-----------------|-----------|-------------|
| Audio remediation | Your original input video | **User's original** |
| Audio muxing | Your original input + remediated audio | **User's original** (video side) |
| Video remediation | Muxed output from previous step | **Pipeline intermediate** |
| Metadata application | Remediated output from previous step | **Pipeline intermediate** |

### What This Means For You

- **If the error is in your original file**: The diagnosis will say something like *"Your original input file 'movie.mp4' has a corrupt container."* You'll get a suggested fix (re-download, re-encode, etc.). This is not a bug in video-censor-personal.

- **If the error is in a pipeline intermediate**: The diagnosis will say something like *"Error reading an intermediate file produced by video-censor-personal during the 'video remediation' step."* The system will attempt automatic recovery, and if it can't fully recover, it will generate a **bug report** you can submit.

## Bug Reports

When the pipeline produces a corrupt intermediate file and recovery fails or produces degraded output, the system generates a ready-to-submit bug report:

```
────────────────────────────────────────────────────────
⚠ This may be a bug in video-censor-personal.

Please report this issue at:
  https://github.com/justinfiore/video-censor-personal/issues

Copy the following into the bug report form:

Title: Bug: Video remediation produced corrupt output (moov atom not found)

Description:
## What happened
During the video_remediation step, video-censor-personal produced an
intermediate file that could not be read by the next processing step.

Error: moov atom not found
Phase: metadata_application
File: output-video/MyMovie-censored.mp4

## How to reproduce
Command: python3 ./video_censor_personal.py --input "video-samples/MyMovie.mp4" --config video-censor.yaml --output-video "output-video/MyMovie-censored.mp4"
Config: video-censor.yaml
Input: MyMovie.mp4

## Environment
- ffmpeg version: 8.0.1
- OS: macOS 15.3 (arm64)
- Python: 3.13.1
────────────────────────────────────────────────────────
```

Bug reports are **not** generated when:
- The error is in your original input file (not our fault)
- Automatic recovery fully succeeded with no degradation

## Warnings Summary

At the end of every processing run where recovery actions were taken, a consolidated warnings summary is printed. Example:

```
⚠ Processing completed with 2 warning(s):

  1. [Video Remediation] Corrupt frames detected. Retried with error-tolerant
     processing (-err_detect ignore_err). Output may have brief visual glitches.

  2. [Metadata] Failed to apply metadata to output video (moov atom not found).
     Metadata was skipped. The output video is still playable but missing custom
     metadata tags (title, config file, processing date).
```

If no warnings occurred, nothing extra is printed.

## Architecture

```
video_censor_personal/
├── remediation.py                 # Main orchestrator — calls recovery on failures
├── remediation_diagnostics.py     # Error Pattern Registry + diagnosis engine
├── video_remediator.py            # Video blanking/cutting
├── audio_remediator.py            # Audio silence/bleep
├── video_muxer.py                 # Audio-video muxing
└── video_metadata.py              # Metadata writing
```

The `RemediationManager` in `remediation.py` wraps each phase (audio, video, muxing, metadata) in error handling that consults `remediation_diagnostics.py` on failure, attempts recovery if available, and collects warnings.
