## ADDED Requirements

### Requirement: Error Source Attribution

The system SHALL classify every error as originating from either the **user's original input file** or an **intermediate file produced by the pipeline**, and SHALL include this classification in all diagnosis output, warnings, and bug report suggestions.

#### Scenario: Error on user's original input during audio remediation
- **WHEN** audio remediation fails while reading the user's original input video
- **THEN** the diagnosis clearly states: "Error reading your original input file: <filename>" and the suggested fix addresses the user's source file (e.g., "verify the input file is not corrupt")

#### Scenario: Error on user's original input during muxing
- **WHEN** audio muxing fails while reading the user's original input video (before any intermediate exists)
- **THEN** the diagnosis clearly states: "Error reading your original input file: <filename>" and the suggested fix addresses the user's source file

#### Scenario: Error on intermediate file during video remediation
- **WHEN** video remediation fails while reading an intermediate file that our pipeline produced (e.g., the muxed output)
- **THEN** the diagnosis clearly states: "Error reading an intermediate file produced by video-censor-personal during the '<phase>' step. This is likely a bug in our processing pipeline." and includes a bug report link

#### Scenario: Error on intermediate file during metadata application
- **WHEN** metadata application fails while reading the output video that our pipeline produced
- **THEN** the diagnosis clearly states: "Error reading an intermediate file produced by video-censor-personal during the '<previous phase>' step." and includes a bug report link

#### Scenario: Intermediate file errors are more aggressively auto-recovered
- **WHEN** an error is attributed to an intermediate file produced by the pipeline
- **THEN** the system attempts all available recovery strategies before failing, since the problem is within our control

#### Scenario: Diagnosis includes file path and origin
- **WHEN** any error diagnosis is generated
- **THEN** the diagnosis includes the absolute path of the problematic file and whether it is "original input" or "intermediate output from <phase>"

### Requirement: Bug Report Generation

The system SHALL generate a copy-pasteable bug report (title and description) when an error is attributed to an intermediate file produced by the pipeline, directing the user to https://github.com/justinfiore/video-censor-personal/issues.

#### Scenario: Bug report generated for intermediate file error
- **WHEN** an error is attributed to an intermediate file and recovery either fails or produces degraded output
- **THEN** the system outputs a formatted bug report containing:
  - A suggested issue title (e.g., "Bug: Video remediation produced corrupt output (moov atom not found)")
  - A description body with: the phase that failed, the error message, the ffmpeg command that failed (if available), the config file used, the input file name, the ffmpeg version, the video-censor-personal version (if available), and OS information
  - A direct link: "Please report this issue at: https://github.com/justinfiore/video-censor-personal/issues"
  - Formatting suitable for copy-paste into a GitHub issue form

#### Scenario: Bug report not generated for user input file errors
- **WHEN** an error is attributed to the user's original input file
- **THEN** no bug report is generated; only the diagnosis and suggested fix are shown

#### Scenario: Bug report not generated when recovery fully succeeds
- **WHEN** an error on an intermediate file is fully recovered with no degradation
- **THEN** no bug report is generated; only a warning is logged

#### Scenario: Bug report includes reproduction steps
- **WHEN** a bug report is generated
- **THEN** the description includes the full command line that was used to invoke video-censor-personal (with file paths), so the maintainer can attempt reproduction

### Requirement: Error Pattern Registry

The system SHALL maintain a centralized error pattern registry that maps known ffmpeg/processing error patterns to structured diagnosis objects containing: a regex pattern, a human-readable diagnosis, a suggested fix for the user, an optional automatic recovery strategy, and whether the error is typically caused by user input or pipeline processing.

#### Scenario: Registry contains moov atom pattern
- **WHEN** the error pattern registry is initialized
- **THEN** it contains an entry matching "moov atom not found" with diagnosis explaining the container is corrupt or incomplete

#### Scenario: Registry contains invalid data pattern
- **WHEN** the error pattern registry is initialized
- **THEN** it contains an entry matching "Invalid data found when processing input" with diagnosis explaining the file may be corrupt, truncated, or have an incompatible format

#### Scenario: Registry contains corrupt H.264 frame patterns
- **WHEN** the error pattern registry is initialized
- **THEN** it contains entries matching "non-existing PPS referenced", "decode_slice_header error", and "no frame" with diagnosis explaining corrupt video frames

#### Scenario: Registry contains timestamp disorder pattern
- **WHEN** the error pattern registry is initialized
- **THEN** it contains an entry matching "Non-monotonous DTS" with diagnosis explaining timestamp ordering issues and recovery using genpts or igndts flags

#### Scenario: Registry contains codec header error pattern
- **WHEN** the error pattern registry is initialized
- **THEN** it contains an entry matching "Could not write header" or "incorrect codec parameters" with diagnosis explaining codec-container incompatibility

#### Scenario: Registry contains filesystem error patterns
- **WHEN** the error pattern registry is initialized
- **THEN** it contains entries matching "No space left on device" and "Permission denied" with diagnoses and user instructions (no automatic recovery)

#### Scenario: Registry contains transport stream error pattern
- **WHEN** the error pattern registry is initialized
- **THEN** it contains an entry matching "PES packet size mismatch" with diagnosis explaining corrupted transport stream data

#### Scenario: Registry contains encoder not found pattern
- **WHEN** the error pattern registry is initialized
- **THEN** it contains entries matching "Unknown encoder" and "Encoder .* not found" with diagnosis explaining the required codec is not available in the installed ffmpeg build

#### Scenario: Registry is extensible
- **WHEN** a developer needs to add a new error pattern
- **THEN** they can add a new entry to the registry list without modifying any other code

### Requirement: Error Diagnosis

The system SHALL diagnose known remediation errors by matching ffmpeg stderr output against the error pattern registry and providing human-readable explanations with suggested fixes when audio remediation, video remediation, or metadata application fails. Each diagnosis SHALL clearly identify whether the problematic file is the user's original input or an intermediate file produced by the pipeline.

#### Scenario: Diagnose moov atom not found on intermediate file
- **WHEN** ffmpeg fails with "moov atom not found" while reading an intermediate file produced by the pipeline
- **THEN** the system outputs a diagnosis stating the pipeline produced a corrupt intermediate file, attempts recovery, and if recovery fails or degrades output, generates a bug report

#### Scenario: Diagnose moov atom not found on original input
- **WHEN** ffmpeg fails with "moov atom not found" while reading the user's original input file
- **THEN** the system outputs a diagnosis: "Your original input file '<filename>' has a corrupt or incomplete container (missing moov atom)." with suggested fix: "Re-download or re-acquire the source video. The file may have been truncated during download or recording."

#### Scenario: Diagnose invalid data on intermediate file
- **WHEN** ffmpeg fails with "Invalid data found when processing input" on an intermediate file
- **THEN** the system identifies this as a pipeline bug, attempts recovery, and generates a bug report if recovery fails

#### Scenario: Diagnose invalid data on original input
- **WHEN** ffmpeg fails with "Invalid data found when processing input" on the user's original input file
- **THEN** the system outputs a diagnosis explaining the user's input file may be corrupt and suggests verifying file integrity

#### Scenario: Diagnose corrupt H.264 frames
- **WHEN** ffmpeg stderr contains "non-existing PPS referenced" or "decode_slice_header error"
- **THEN** the system outputs a diagnosis explaining the video contains corrupt H.264 frames, identifies the source file, and suggests re-processing with error tolerance enabled

#### Scenario: Diagnose timestamp disorder
- **WHEN** ffmpeg stderr contains "Non-monotonous DTS in output stream"
- **THEN** the system outputs a diagnosis explaining the output has timestamp ordering issues and suggests using timestamp regeneration flags

#### Scenario: Diagnose codec not supported
- **WHEN** ffmpeg fails with "Unknown encoder", "Encoder .* not found", or "codec not currently supported"
- **THEN** the system outputs a diagnosis identifying the unsupported codec and suggests installing the required codec or re-encoding the input with a supported codec

#### Scenario: Diagnose codec header error
- **WHEN** ffmpeg fails with "Could not write header" and "incorrect codec parameters"
- **THEN** the system outputs a diagnosis explaining the video/audio codec is incompatible with the output container format and suggests re-encoding with compatible codecs

#### Scenario: Diagnose filesystem errors
- **WHEN** ffmpeg fails with "No space left on device"
- **THEN** the system outputs a diagnosis explaining insufficient disk space with suggested fix to free space or change the output directory

#### Scenario: Diagnose permission errors
- **WHEN** ffmpeg fails with "Permission denied"
- **THEN** the system outputs a diagnosis explaining file or directory permission issues with suggested fix to check write permissions on the output path

#### Scenario: Diagnose empty output file
- **WHEN** an intermediate output file exists but has 0 bytes after a processing step
- **THEN** the system identifies this as a pipeline failure, outputs a diagnosis explaining the processing step failed silently, and generates a bug report

#### Scenario: Unknown error provides raw stderr with source attribution
- **WHEN** ffmpeg fails with an unrecognized error pattern
- **THEN** the system outputs the raw ffmpeg error, identifies whether the failing file is original input or an intermediate, and if intermediate, generates a bug report

### Requirement: Automatic Error Recovery

The system SHALL attempt automatic recovery from known error conditions during remediation, falling back to degraded output rather than failing entirely when possible. Recovery SHALL only be attempted for error patterns that have an associated automatic recovery strategy in the error pattern registry. Errors on intermediate files produced by the pipeline SHALL be recovered more aggressively than errors on the user's original input.

#### Scenario: Recover from corrupt intermediate during metadata application
- **WHEN** metadata application fails because the intermediate output video has a corrupt container (e.g., moov atom not found)
- **THEN** the system skips metadata application, preserves the output video without metadata, and logs a warning explaining metadata was not applied and why, and generates a bug report since the pipeline produced the corrupt file

#### Scenario: Recover from copy-mode muxing failure
- **WHEN** audio muxing with stream copy (`-c copy`) fails
- **THEN** the system retries muxing with full re-encoding (`-c:v libx264 -c:a aac`) and logs a warning that re-encoding was required, which may take longer

#### Scenario: Recover from corrupt frames during video remediation
- **WHEN** video remediation fails due to corrupt or unreadable frames in an intermediate file
- **THEN** the system retries with `-err_detect ignore_err` to skip corrupt frames, produces output, logs a warning, and generates a bug report since the intermediate was pipeline-produced

#### Scenario: Recover from timestamp disorder
- **WHEN** a processing step produces "Non-monotonous DTS" warnings or fails due to timestamp issues
- **THEN** the system retries with `-fflags +genpts` to regenerate timestamps and logs a warning

#### Scenario: Recover from codec header mismatch
- **WHEN** ffmpeg fails with "Could not write header" due to codec parameter mismatch
- **THEN** the system retries with explicit codec re-encoding (`-c:v libx264 -c:a aac`) and logs a warning

#### Scenario: No recovery possible
- **WHEN** a remediation phase fails and no recovery strategy applies (e.g., disk full, permission denied, encoder not found)
- **THEN** the system outputs the diagnosis with suggested fix (and bug report if intermediate file), and raises the error

#### Scenario: Recovery attempt also fails
- **WHEN** an automatic recovery attempt itself fails
- **THEN** the system outputs both the original error diagnosis and the recovery failure, generates a bug report if intermediate file, then raises the error

### Requirement: Remediation Warnings Summary

The system SHALL collect all warnings generated during remediation (including recovery actions, skipped steps, degraded output notices, and bug report suggestions) and output a consolidated summary at the end of the processing run.

#### Scenario: Single warning during processing
- **WHEN** one recovery action is taken during remediation (e.g., metadata skipped)
- **THEN** a warnings summary is printed after "Remediation complete" showing the single warning with its details

#### Scenario: Multiple warnings during processing
- **WHEN** multiple recovery actions are taken (e.g., re-encoding required AND metadata skipped)
- **THEN** a warnings summary is printed listing all warnings in chronological order

#### Scenario: No warnings during processing
- **WHEN** remediation completes without any errors or recovery actions
- **THEN** no warnings summary is printed

#### Scenario: Warning details include specific context
- **WHEN** a warning is generated for a recovery action
- **THEN** the warning includes: the phase where the error occurred (audio/video/muxing/metadata), the file that caused the error (with origin attribution), the error encountered, the recovery action taken, and the outcome

#### Scenario: Bug report links included in summary
- **WHEN** the warnings summary contains entries where a bug report was generated
- **THEN** the summary includes the bug report link and a note that the user can copy-paste the details into a GitHub issue
