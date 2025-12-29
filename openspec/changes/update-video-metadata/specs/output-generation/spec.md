## ADDED Requirements

### Requirement: Output Video Title Update

The system SHALL append " (Censored)" to the original video title when generating remediated output video, providing clear visual indication that a video has been processed.

#### Scenario: Simple title update
- **WHEN** output video is generated for input video with title "Family Video"
- **THEN** output video metadata includes updated title "Family Video (Censored)"

#### Scenario: Title already contains suffix
- **WHEN** input video already has title "Family Video (Censored)" and is remediated again
- **THEN** output video title becomes "Family Video (Censored)"
- We don't want to repeat the suffix if it's already there

#### Scenario: No title in input
- **WHEN** input video has no title metadata
- **THEN** output video title is set to the input filename plus "(Censored)"

#### Scenario: Title with special characters preserved
- **WHEN** input title contains special characters like quotes, accents, or unicode: "La Película: Noche & Día"
- **THEN** output title is "La Película: Noche & Día (Censored)" with all special characters preserved

### Requirement: Remediation Metadata Tags

The system SHALL write custom metadata tags to the output MP4 container to track remediation configuration, timestamp, and enabled modes. Tags use underscore separator to ensure compatibility across media players.

#### Scenario: Write config filename metadata
- **WHEN** output video is generated using config file "video-censor-analysis.yaml"
- **THEN** MP4 container includes metadata tag `video_censor_personal_config_file` with value `"video-censor-analysis.yaml"`

#### Scenario: Write segment filename metadata
- **WHEN** output video is generated using segment file "results-2025-12-29.json"
- **THEN** MP4 container includes metadata tag `video_censor_personal_segment_file` with value `"results-2025-12-29.json"`

#### Scenario: Write processed date with timezone
- **WHEN** remediation starts at 2025-12-29 14:30:45.123 in timezone PST (UTC-8)
- **THEN** MP4 container includes metadata tag `video_censor_personal_processed_date` with value `"2025-12-29T14:30:45.123-08:00"` (ISO8601 format)

#### Scenario: Write audio remediation enabled flag (true)
- **WHEN** remediation is performed with audio remediation enabled
- **THEN** MP4 container includes metadata tag `video_censor_personal_audio_remediation_enabled` with value `"true"`

#### Scenario: Write audio remediation enabled flag (false)
- **WHEN** remediation is performed with audio remediation disabled
- **THEN** MP4 container includes metadata tag `video_censor_personal_audio_remediation_enabled` with value `"false"`

#### Scenario: Write video remediation enabled flag (true)
- **WHEN** remediation is performed with video remediation enabled
- **THEN** MP4 container includes metadata tag `video_censor_personal_video_remediation_enabled` with value `"true"`

#### Scenario: Write video remediation enabled flag (false)
- **WHEN** remediation is performed with video remediation disabled
- **THEN** MP4 container includes metadata tag `video_censor_personal_video_remediation_enabled` with value `"false"`

#### Scenario: Metadata tags survive codec copying
- **WHEN** output video is generated with `-c:v copy` (video passthrough without re-encoding)
- **THEN** all metadata tags are preserved in output file

#### Scenario: Only filename, not full path
- **WHEN** remediation uses `/full/path/to/config-file.yaml`
- **THEN** metadata tag stores only `"config-file.yaml"` (basename), not the full path

#### Scenario: Metadata valid in standard media players
- **WHEN** output video is opened in standard media player (VLC, Windows Media Player, Kodi)
- **THEN** metadata tags are accessible via metadata/info views (format-dependent)

### Requirement: Debug Logging of Metadata

The system SHALL log all remediation metadata tags and their values at DEBUG level to aid troubleshooting and auditing.

#### Scenario: Log all metadata during output generation
- **WHEN** output video is being generated with metadata tags
- **THEN** system logs at DEBUG level for each tag:
  - `"Setting video metadata: video_censor_personal_config_file = 'video-censor.yaml'"`
  - `"Setting video metadata: video_censor_personal_segment_file = 'results.json'"`
  - `"Setting video metadata: video_censor_personal_processed_date = '2025-12-29T14:30:45.123-08:00'"`
  - `"Setting video metadata: video_censor_personal_audio_remediation_enabled = 'true'"`
  - `"Setting video metadata: video_censor_personal_video_remediation_enabled = 'false'"`

#### Scenario: Log title update
- **WHEN** output video title is updated
- **THEN** system logs at DEBUG level: `"Updating video title: 'Original Title' → 'Original Title (Censored)'"`

#### Scenario: Logs appear before ffmpeg execution
- **WHEN** metadata is being prepared for writing
- **THEN** DEBUG logs appear before ffmpeg command is executed, enabling users to see intended metadata before processing

#### Scenario: Log ffmpeg metadata command
- **WHEN** ffmpeg is invoked to write metadata
- **THEN** system logs at DEBUG level the ffmpeg command with metadata arguments
