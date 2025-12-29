# Change: Update Video Metadata on Remediation

## Why

When a video is remediated (censored), it's important to track metadata about the remediation process for traceability and auditing. Users should be able to see:
- The config file and segment file used for remediation
- When the remediation was performed (timestamp with timezone)
- Which remediation modes were enabled

Additionally, appending "(Censored)" to the video title makes it clear at a glance that a video has been processed.

## What Changes

### Title/Name Update
- When output video is generated, update the title/name metadata by appending ` (Censored)` to the original title

### Custom MP4 Metadata Tags
Add five new metadata tags to MP4 container (using underscore or hyphen if colons not allowed):
1. `video_censor_personal_config_file`: The config filename used for remediation
2. `video_censor_personal_segment_file`: The segment filename used for remediation  
3. `video_censor_personal_processed_date`: ISO8601 timestamp with timezone of when remediation started
4. `video_censor_personal_audio_remediation_enabled`: Boolean flag (true/false)
5. `video_censor_personal_video_remediation_enabled`: Boolean flag (true/false)

### Logging
- All metadata key-value pairs SHALL be logged at DEBUG level during output video generation

## Impact

- **Affected specs**: `output-generation` (video output)
- **Affected code**: `video_muxer.py`, `remediation.py`, `pipeline.py`
- **No breaking changes**: Existing video output behavior unchanged; metadata is additive
