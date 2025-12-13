## ADDED Requirements

### Requirement: Video Output with Audio

The system SHALL re-mux remediated audio back into the original video container when audio remediation is enabled.

#### Scenario: Mux remediated audio into video
- **WHEN** audio remediation is enabled and completes with remediated audio file
- **THEN** system uses ffmpeg to mux remediated audio into original video container
- **AND** output video is written to user-specified path

#### Scenario: Video codec is passed through losslessly
- **WHEN** video is muxed with remediated audio
- **THEN** video codec is copied without re-encoding (using ffmpeg `-c:v copy`)
- **AND** muxing completes quickly (no video re-encoding overhead)

#### Scenario: Audio is encoded to AAC
- **WHEN** remediated audio (WAV format) is muxed into video
- **THEN** audio is encoded to AAC format for compatibility
- **AND** sample rates are automatically handled by ffmpeg

#### Scenario: Output video file is created
- **WHEN** muxing completes successfully
- **THEN** output video file is written to specified path
- **AND** file contains both original video and remediated audio

#### Scenario: Handle muxing failure gracefully
- **WHEN** ffmpeg muxing fails (disk full, corrupted video, etc.)
- **THEN** error is logged with ffmpeg stderr
- **AND** pipeline raises exception with clear message

#### Scenario: Output video path included in results
- **WHEN** video muxing completes
- **THEN** JSON results include `output_video_path` field with path to muxed file
