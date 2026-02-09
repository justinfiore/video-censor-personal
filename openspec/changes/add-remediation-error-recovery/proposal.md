# Change: Add Remediation Error Recovery and Diagnostics

## Why

When remediation encounters errors (corrupt frames, invalid container data, missing moov atoms, etc.), processing currently fails with raw ffmpeg errors. Users have no guidance on why the failure occurred or how to fix it. In many cases, the system could work around the problem automatically (e.g., skipping corrupt frames) and still produce usable output.

## What Changes

- Add error diagnosis that interprets ffmpeg/processing errors and outputs human-readable root cause and suggested fix
- Add automatic recovery strategies for known error patterns (skip corrupt frames, re-encode problematic sections, handle missing moov atoms)
- When recovery is used, log warnings with specific details about what was skipped/modified
- Collect all warnings and print a summary at the end of the processing run
- Apply recovery logic to all three remediation phases: audio remediation, video remediation, and metadata application

## Impact

- Affected specs: `audio-remediation`, `video-remediation` (new capability: `remediation-error-recovery`)
- Affected code: `remediation.py`, `video_remediator.py`, `video_muxer.py`, `video_metadata.py`
