# Change: Add Segment Allow Override

## Why

Users need a mechanism to handle false positives and make informed tradeoff decisions without re-analyzing the entire video. The ability to mark detected segments as "allowed" provides a lightweight, reversible way to exclude specific segments from remediation while preserving the original detection data for future reference.

## What Changes

- Add an optional `allow` property to segment objects in the output JSON
- Segments marked with `"allow": true` are excluded from all downstream remediation (audio bleep/silence, video editing, chapter generation)
- Original detection data is always preserved regardless of allow status
- The allow property is additive—no re-analysis needed
- Multiple segments can be independently marked as allowed
- Users can toggle decisions without video reprocessing

## Impact

- **Affected specs:**
  - `output-generation`: JSON schema changes to include the `allow` property
  - `audio-remediation`: Must respect `allow` flag during processing
  - Chapter generation: Must check `allow` flag
- **Affected code:**
  - Segment output schema
  - Audio remediation pipeline
  - Chapter generation logic
  - Any downstream processing that iterates segments
