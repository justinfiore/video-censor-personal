## MODIFIED Requirements

### Requirement: Time Formatting

The system SHALL support dual time formats (HH:MM:SS.mmm human-readable with millisecond precision and seconds machine-readable) to enable both user reports and downstream processing without losing timing precision.

#### Scenario: Format time as HH:MM:SS.mmm with milliseconds
- **WHEN** output generator formats 3661.456 seconds
- **THEN** result is "01:01:01.456"

#### Scenario: Format time as HH:MM:SS.000 for whole seconds
- **WHEN** output generator formats 3661.0 seconds
- **THEN** result is "01:01:01.000"

#### Scenario: Format time with partial milliseconds
- **WHEN** output generator formats 3661.5 seconds
- **THEN** result is "01:01:01.500"

#### Scenario: Format time as seconds
- **WHEN** output generator formats 3661.5 seconds with format="seconds"
- **THEN** result is "3661"

#### Scenario: Format edge cases
- **WHEN** formatting 0 seconds
- **THEN** HH:MM:SS.mmm format is "00:00:00.000" and seconds format is "0"

#### Scenario: Format large values
- **WHEN** formatting 36000.123 seconds (10 hours)
- **THEN** HH:MM:SS.mmm format is "10:00:00.123"

## ADDED Requirements

### Requirement: Segment Time Formatting

The system SHALL output segment timestamps with millisecond precision to preserve timing accuracy across analysis and remediation phases.

#### Scenario: Output segment times with milliseconds
- **WHEN** output is generated for segment spanning 10.456 to 15.789 seconds
- **THEN** output.segments[0].start_time is "00:00:10.456" and end_time is "00:00:15.789"

#### Scenario: Numeric timestamp fields remain unchanged
- **WHEN** output is generated
- **THEN** start_time_seconds and end_time_seconds continue to provide raw float values

### Requirement: Input Timestamp Parsing Flexibility

The system SHALL parse timestamp strings in both HH:MM:SS.mmm (with milliseconds) and HH:MM:SS (without milliseconds) formats to accommodate manual JSON editing.

#### Scenario: Parse HH:MM:SS.mmm format
- **WHEN** segment input contains start_time: "00:01:23.456"
- **THEN** system parses it as 83.456 seconds (1*60 + 23 + 0.456)

#### Scenario: Parse HH:MM:SS format without milliseconds
- **WHEN** segment input contains start_time: "00:01:23"
- **THEN** system parses it as 83.0 seconds (1*60 + 23)

#### Scenario: Parse MM:SS.mmm format (backward compatibility)
- **WHEN** segment input contains start_time: "01:23.456"
- **THEN** system parses it as 83.456 seconds

#### Scenario: Parse MM:SS format without milliseconds (backward compatibility)
- **WHEN** segment input contains start_time: "01:23"
- **THEN** system parses it as 83.0 seconds

#### Scenario: Numeric timestamps still supported
- **WHEN** segment input contains start_time_seconds: 83.456
- **THEN** system uses 83.456 directly (preferred over string format if both present)

#### Scenario: Invalid milliseconds rejected
- **WHEN** segment input contains start_time: "00:01:23.abc"
- **THEN** system raises SegmentsLoadError with clear message

### Requirement: Duration Always Derived from Times

The system SHALL calculate duration exclusively from start_time and end_time values; any duration field in input JSON is ignored during segment loading and recalculated.

#### Scenario: Duration recalculated from segment times
- **WHEN** segment is loaded with start_time: "00:00:10.500", end_time: "00:00:15.750"
- **THEN** system calculates duration_seconds as 5.25 (15.750 - 10.500)

#### Scenario: Input duration field ignored
- **WHEN** segment input contains duration_seconds: 999.0 but start_time: "00:00:10", end_time: "00:00:15"
- **THEN** system uses calculated duration of 5.0, ignoring the 999.0 value

#### Scenario: Duration never used in remediation
- **WHEN** remediation processes segments (audio or video)
- **THEN** remediation uses only start_time and end_time values; duration_seconds is informational only
