# VLC Removal from Integration Test Proposal

## Context

The `expand-preview-editor-integration-tests` proposal has been updated to remove all VLC references and add Phase 0 (VLC removal task).

## Changes Made

### Proposal Document Updates
1. **proposal.md** - Removed references to VLC failures and video playback issues
2. **design.md** - Removed VLC mocking strategy; simplified to "real implementations" only
3. **tasks.md** - Added Phase 0 with 6 specific tasks to remove VLC code and tests
4. **specs** - Updated error scenarios to be generic (not VLC-specific)
5. **SUMMARY.md** - Updated gap analysis to focus on JSON/segment workflows, not video playback

### Phase 0: VLC Removal (NEW - Separate Commit)

This phase **must run first** before any other integration testing work:

```
Phase 0 Tasks:
- [ ] 0.1 Remove all VLC-related imports and code from video_player.py
- [ ] 0.2 Remove VLC-related test mocks from tests/ui/conftest.py and test files
- [ ] 0.3 Remove python-vlc dependency from requirements.txt
- [ ] 0.4 Update PREVIEW_EDITOR_IMPLEMENTATION_SUMMARY.md to remove VLC references
- [ ] 0.5 Verify all unit tests pass with VLC removed
- [ ] 0.6 Commit with message: "Remove VLC video playback (no longer used)"
```

## What This Means

**Before Implementation of Integration Tests:**
1. VLC code is completely removed in Phase 0
2. UI tests focus on segment review (JSON, list, details pane)
3. Video playback tests deferred until a replacement framework is chosen
4. No references to video player in integration test scenarios

**Integration Tests Still Cover (36+ tests):**
- File I/O (JSON loading, validation, error handling)
- Cross-component synchronization (segment list ↔ details pane)
- State consistency (concurrent operations, atomic writes)
- Error recovery (helpful errors, graceful degradation)
- Window lifecycle (startup, shutdown, resource cleanup)

## Modified File List

### Documents Updated
- openspec/changes/expand-preview-editor-integration-tests/proposal.md
- openspec/changes/expand-preview-editor-integration-tests/design.md
- openspec/changes/expand-preview-editor-integration-tests/tasks.md
- openspec/changes/expand-preview-editor-integration-tests/specs/segment-review/spec.md
- openspec/changes/expand-preview-editor-integration-tests/specs/ui-testing/spec.md
- openspec/changes/expand-preview-editor-integration-tests/SUMMARY.md

### Validation
✅ Proposal passes strict validation (openspec validate expand-preview-editor-integration-tests --strict)

## Approval Gate

The proposal is **ready for review** with these three blocking questions:

1. **Confirm VLC removal timing**: Should Phase 0 run immediately in this change, or defer to separate work?
2. **Coverage target**: Maintain 80% (current standard) or aim higher (85-90%)?
3. **Future playback testing**: Add placeholder tests for video playback when a replacement framework is chosen?
