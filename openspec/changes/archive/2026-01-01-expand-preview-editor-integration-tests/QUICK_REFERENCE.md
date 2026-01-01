# Quick Reference: Integration Testing Proposal

## View the Proposal

```bash
# List the proposal
openspec show expand-preview-editor-integration-tests

# Read complete proposal
cat openspec/changes/expand-preview-editor-integration-tests/proposal.md

# Read design decisions
cat openspec/changes/expand-preview-editor-integration-tests/design.md

# View task list
cat openspec/changes/expand-preview-editor-integration-tests/tasks.md

# View requirements
cat openspec/changes/expand-preview-editor-integration-tests/specs/ui-testing/spec.md
cat openspec/changes/expand-preview-editor-integration-tests/specs/segment-review/spec.md
```

## Key Points

| Aspect | Details |
|--------|---------|
| **Change ID** | `expand-preview-editor-integration-tests` |
| **Status** | ✅ Ready for Approval |
| **Tests** | 36+ integration tests across 5 categories |
| **Effort** | 15-22 hours (1-2 days) |
| **New Feature** | Headless/headed test mode for CI + debugging |
| **Breaking Change** | Phase 0: Removes VLC (separate commit) |
| **Validation** | ✅ Passes OpenSpec strict validation |

## Headless/Headed Mode (New Feature)

```bash
# Default (CI/Automated) - No display needed
pytest tests/ui/test_integration.py -v

# Debugging - Visual output, 500ms delays, window interaction
PYTEST_HEADED=1 pytest tests/ui/test_integration.py -v
PYTEST_HEADED=1 pytest tests/ui/test_integration.py::test_name -v --pdb

# Alternative: CLI flag
pytest tests/ui/test_integration.py --headed -v
```

## Test Categories (36+ Tests)

```
File I/O (10 tests)
  ├─ JSON loading
  ├─ JSON validation
  ├─ Error handling
  └─ Recovery scenarios

Cross-Component Sync (8 tests)
  ├─ Segment list updates
  ├─ Details pane updates
  ├─ State consistency
  └─ Rapid operations

State Consistency (8 tests)
  ├─ Large segment lists
  ├─ Concurrent operations
  ├─ Mixed JSON formats
  └─ Field preservation

Error Recovery (6 tests)
  ├─ Helpful error messages
  ├─ Graceful degradation
  ├─ File locking
  └─ Retry mechanisms

Window Lifecycle (4 tests)
  ├─ Startup/shutdown
  ├─ Resource cleanup
  ├─ Auto-load
  └─ Recent files
```

## Implementation Phases

| Phase | Hours | Focus |
|-------|-------|-------|
| 0 | 1 | Remove VLC |
| 1 | 3-4 | Headless/headed + fixtures |
| 2 | 3-4 | File I/O tests (10) |
| 3 | 2-3 | Sync tests (8) |
| 4 | 2-3 | Consistency tests (8) |
| 5 | 2-3 | Error tests (6) |
| 6 | 1-2 | Lifecycle tests (4) |
| 7 | 1-2 | Coverage validation |
| **Total** | **15-22** | **1-2 days** |

## Blocking Questions Before Approval

1. **VLC Removal**: Immediate (Phase 0) or defer?
2. **Coverage Target**: 80% (maintain) or 85-90% (higher)?
3. **Future Playback**: Add placeholder tests for new framework?

## Files to Review

1. `proposal.md` - Why this is needed (5 min read)
2. `design.md` - How it works (10 min read)
3. `tasks.md` - What to implement (5 min read)
4. `specs/` - Detailed requirements (10 min read)
5. `SUMMARY.md` - Executive summary (5 min read)

**Total Review Time**: ~30 minutes

## Supporting Documentation (This Workspace)

- `PROPOSAL_FINAL_SUMMARY.md` - Comprehensive overview
- `HEADLESS_HEADED_FEATURE.md` - Details on new headless/headed mode
- `VLCREMOVAL.md` - Context on VLC removal
- `QUICK_REFERENCE.md` - This file

## Next Actions

1. ✅ Proposal created and validated
2. ⏳ Awaiting review
3. ⏳ Answer 3 blocking questions
4. ⏳ Approval decision
5. ⏳ Phase 0 (VLC removal)
6. ⏳ Phases 1-7 (implementation)

---

**Status**: Ready for stakeholder review  
**Proposal Valid**: Yes ✅  
**Need Approval**: Yes ⏳
