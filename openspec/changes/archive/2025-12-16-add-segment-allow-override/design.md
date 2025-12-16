# Design: Segment Allow Override

## Context

The segment allow override feature enables users to handle false positives and make informed decisions about which detected segments to remediate without requiring video re-analysis. This is a critical usability feature that bridges the gap between automated detection and user intent.

**Current Behavior:**
- Detection produces JSON with detected segments
- All segments flow through remediation (audio bleep/silence, chapters)
- No mechanism to exclude specific segments without manual JSON deletion

**Desired Behavior:**
- Users can mark segments with `"allow": true` to exclude them from remediation
- Original detection data is preserved for reference
- Remediation systems respect the allow flag and skip marked segments
- No re-analysis overhead

## Goals

- **Goals:**
  - Provide a reversible, non-destructive way to exclude segments from remediation
  - Preserve original detection data for audit trail and future changes
  - Enable multiple independent segment decisions
  - Support lightweight user feedback loop without re-analysis
  
- **Non-Goals:**
  - Per-label overrides (e.g., allow violence but not profanity in same segment)—future enhancement
  - Automatic allow/ignore logic based on rules
  - UI implementation (separate concern)

## Decisions

**Decision 1: Optional Property on Segment**
- Add optional `allow: boolean` field to segment objects
- Missing `allow` or `false` means segment will be remediated
- Rationale: Backward compatible; doesn't require modifying existing detection output

**Decision 2: Preserve All Detection Data**
- Keep original `labels`, `confidence`, `description`, `detections` array unchanged
- Allow flag is purely for remediation control
- Rationale: Enables audit trail and supports future per-label decisions

**Decision 3: Default to "Not Allowed"**
- Missing `allow` property or `"allow": false` → segment will be remediated
- Only `"allow": true` excludes from remediation
- Rationale: Conservative default prevents accidental data loss; explicit opt-in for safety

**Decision 4: Check at Remediation Time**
- Detection phase produces segments without allow logic
- Audio, video, and chapter processors independently check the flag
- Rationale: Modular; detection doesn't need to know about remediation

**Decision 5: No Config Changes Required**
- The allow override is a data-level feature, not a configuration option
- Remediation modes (bleep, silence, blanking, chapters) work unchanged
- Rationale: Simplifies implementation; allow is user data, not system configuration

**Decision 6: CLI Flag for Bulk Allow Override During Analysis**
- Add `--allow-all-segments` CLI flag to automatically populate `"allow": true` on all detected segments during analysis
- Flag only applies during analysis phase; has no effect when using `--input-segments` (remediation phase)
- Useful for preview/test runs without needing manual editing of JSON
- Rationale: Enables flexible workflow; users can do analysis with all segments pre-allowed, then manually un-allow specific ones if desired

## Alternatives Considered

**Alt 1: Exclude segments entirely (delete from JSON)**
- Rejected: Loses detection data and audit trail
- Doesn't support reversible decisions

**Alt 2: Add "remediation_modes" per segment**
- Rejected: Scope creep for first iteration; can be future enhancement
- Complexity doesn't justify the benefit now

**Alt 3: Store allow decisions in separate file**
- Rejected: Complicates workflow; JSON file should be self-contained
- Makes it harder to share results with others

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| **JSON schema change breaks existing tooling** | Backward compatible (optional field); document in changelog; test with missing/false values |
| **Users accidentally set `allow: true` and miss censoring** | Default to false (conservative); document clearly; provide validation in future UI |
| **Inconsistent handling across remediation types** | Test each remediation path (audio, video, chapters) independently; document expected behavior |
| **Performance impact of checking flag in loop** | Negligible; simple boolean check; no algorithmic complexity |

## Migration Plan

**Phase 1: Code Changes**
1. Update JSON schema and validation
2. Integrate flag checking into each remediation system
3. Full test coverage

**Phase 2: Backward Compatibility**
- Existing JSON files without `allow` field: Treated as `false` (will be remediated)
- No breaking changes to CLI or config

**Phase 3: Documentation**
- Document the feature in output format specs
- Provide use case examples
- Update QUICK_START with workflow examples

## Open Questions

- Should chapter generation have a separate mode (e.g., only mark chapter points for non-allowed segments)? _Deferred: Keep current chapter behavior independent of allow flag._
