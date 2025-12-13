# Implementation Kickoff: Model Auto-Download

## Quick Start for Subagents

This document is your entry point. **Read this first, then refer to specific guides for your stream.**

---

## Pre-Implementation Checklist

- [ ] Read `proposal.md` (why, what, impact)
- [ ] Read `design.md` (architecture, decisions, risks)
- [ ] Read `PARALLELIZATION.md` (your stream, blockers, dependencies)
- [ ] Read `API_CONTRACTS.md` (interfaces you must implement)
- [ ] Check `tasks.md` for your specific work items
- [ ] Understand the phase you're on (1, 2, or 3)

---

## Worktree & Branch Setup

### Initialize Worktrees (Run Once)
```bash
cd /Users/justinfiore/workspace/personal/video-censor-personal

# Create worktrees for each stream
git worktree add ../wt-config-schema stream-a/config-schema
git worktree add ../wt-model-manager stream-b/model-manager
git worktree add ../wt-cli-integration stream-c/cli-integration
git worktree add ../wt-testing stream-d/testing
git worktree add ../wt-pipeline-integration stream-e/pipeline-integration
git worktree add ../wt-huggingface-registry stream-f/huggingface-registry
git worktree add ../wt-documentation stream-g/documentation
```

### Per-Subagent Workflow

**Subagent A (Config Schema)**
```bash
cd ../wt-config-schema
git checkout -b stream-a/config-schema main

# Implement tasks 1.1-1.5
# When complete:
git push origin stream-a/config-schema
# Create PR, get 1 approval, merge to main
```

**Subagent B (Model Manager)**
```bash
cd ../wt-model-manager
git checkout -b stream-b/model-manager main

# Implement tasks 2.1-2.8 + 8.1-8.5
# When complete:
git push origin stream-b/model-manager
# Create PR, get 1 approval, merge to main
```

**Similar for other subagents** (C through G)

---

## Phase Timeline

### Phase 1: Foundation (Days 1-4)
- **Stream A**: Config schema (Day 1-2)
- **Stream B**: Model manager (Day 1-4, in parallel)
- **Stream C**: CLI integration (Day 3-4, after B starts)
- **Stream D**: Unit tests (Day 3-4, feeds from A/B/C)

**Exit criteria**: `python -m video_censor --download-models` downloads models without errors

### Phase 2: Pipeline Integration (Days 5-6)
- **Stream E**: Pipeline auto-invoke (after Phase 1 complete)
- **Stream D**: Integration tests (feeds from E)

**Exit criteria**: Missing models trigger auto-download during pipeline init; analysis resumes

### Phase 3: Auto-Discovery (Days 7-9)
- **Stream F**: Hugging Face registry (after Phase 1 + 2)
- **Stream D**: E2E tests (feeds from F)

**Exit criteria**: Auto-discovery populates cache; deprecation warnings display

### Documentation (Parallel, Days 2-10)
- **Stream G**: README, guides, API docs (can start after Phase 1 kickoff)

---

## Critical Dependencies

**These MUST be respected or the change will fail:**

```
Phase 1:
  Stream A (config) → BLOCKS → Stream B (model manager)
  Stream B → BLOCKS → Stream C (CLI)
  Stream B + C → BLOCKS → Phase 1 exit gate

Phase 2:
  Phase 1 complete → BLOCKS → Stream E (pipeline)
  Stream E → BLOCKS → Phase 2 exit gate

Phase 3:
  Phase 2 complete → BLOCKS → Stream F (HF registry)
  Stream F → BLOCKS → Phase 3 exit gate

Documentation:
  Parallel throughout, no critical blocks
```

**If your stream is blocked, notify the integration owner immediately.**

---

## Key Files to Know

| File | Purpose | Read First? |
|------|---------|---|
| `proposal.md` | Why & what | Yes |
| `design.md` | Architecture & decisions | Yes |
| `tasks.md` | Task checklist for your stream | Yes |
| `PARALLELIZATION.md` | Workstream definitions, timeline | Yes |
| `API_CONTRACTS.md` | Interfaces between streams | **Before coding** |
| `IMPLEMENTATION_KICKOFF.md` | This file | Yes |

---

## Testing Strategy

### Stream B Unit Tests (Model Manager)
```bash
# After implementing model_manager.py
python -m pytest tests/unit/test_model_manager.py -v

# Must pass before merging:
# - test_checksum_validation_pass
# - test_checksum_validation_fail
# - test_atomic_download_temp_cleanup
# - test_disk_space_check_sufficient
# - test_disk_space_check_insufficient
# - test_retry_with_backoff
```

### Stream C Integration Tests
```bash
# After implementing CLI integration
python -m pytest tests/integration/test_download_flow.py -v

# Must pass before merging:
# - test_cli_download_models_flag
# - test_idempotent_downloads
# - test_progress_reporting
# - test_error_messages
```

### All Phases: Cross-Platform Tests
```bash
# CI will run on Windows, macOS, Linux
# Local: Test on your primary OS; CI validates others
python -m pytest tests/ -v --cov=video_censor_personal --cov-min-percentage=80
```

---

## Communication Protocol

### Daily Standup (Async)
Post in shared channel by **EOD** with:
```
🚀 Stream X (Your Name)

✅ Completed:
- Task X.1: [brief description]
- Task X.2: [brief description]

🚧 In Progress:
- Task X.3: [current focus, estimated completion]

🔴 Blockers (if any):
- [Describe blocker, who needs to unblock you]

➡️ Next:
- Task X.4: [tomorrow's focus]
```

### PR Review Cycle
1. Implement tasks for your stream
2. All tests pass locally + CI
3. Push to `stream-X/[name]` branch
4. Create PR with:
   - Description of what changed
   - Reference to tasks completed (e.g., "Closes tasks 2.1-2.8")
   - Test results summary
5. Assign reviewers (2 for critical streams, 1 for others)
6. Approve = Merge to main (no "request changes" → merge)
7. Delete branch after merge

### Integration Sync (Weekly or at gates)
- Review all merged PRs
- Run full test suite (Phase tests)
- Verify no conflicts between streams
- Unlock next phase if exit criteria met

---

## Error Handling Best Practices

### ModelDownloadError Hierarchy
```python
class ModelDownloadError(Exception):
    """Base error for download failures."""
    pass

class ModelChecksumError(ModelDownloadError):
    """Raised when checksum validation fails."""
    pass

class DiskSpaceError(ModelDownloadError):
    """Raised when insufficient disk space."""
    pass

# In Stream B, raise these with helpful context:
raise DiskSpaceError(
    f"Insufficient disk space. Required: {needed_gb}GB, Available: {available_gb}GB. "
    f"Free up space or set models.cache_dir to a different location in {config_file}."
)

# In Stream C, catch and display:
except ModelChecksumError as e:
    print(f"❌ Model integrity check failed: {e}")
    print(f"   The downloaded file may be corrupted.")
    print(f"   Try again: python -m video_censor --download-models --config {config}")
    sys.exit(1)
```

---

## Code Quality Standards

### Type Hints
```python
# ✅ Good
def verify_models(
    self,
    sources: Optional[List[ModelSource]] = None,
    progress_callback: Optional[Callable[[str, int, int], None]] = None
) -> Dict[str, bool]:
    """Verify and download missing models..."""
    pass

# ❌ Bad
def verify_models(self, sources=None, progress_callback=None):
    pass
```

### Docstrings (Google Style)
```python
def get_model_path(self, model_name: str) -> Path:
    """Get cached path for a model.
    
    Args:
        model_name: Name of model (matches ModelSource.name)
    
    Returns:
        Path to model file (may not exist)
    
    Raises:
        ModelNotFoundError: If model name invalid
    """
    pass
```

### Line Length
- Max 100 characters (project standard)
- Break long lines at sensible boundaries

### Testing
- Unit tests: 1 test per logical behavior
- Integration tests: 1 test per scenario
- E2E tests: 1 test per user workflow
- >80% code coverage minimum

---

## Troubleshooting Common Issues

### "Circular import" or "Module not found"
- Ensure imports match API_CONTRACTS.md paths
- Don't import submodules before parent module initialized
- Use TYPE_CHECKING for forward references if needed

### "TypeError: verify_models() got unexpected keyword"
- Check method signature matches API_CONTRACTS.md exactly
- Check all Streams have updated their imports

### "ModuleNotFoundError: No module named 'tqdm'"
- Run `pip install -r requirements.txt` after Stream A merges
- Add to requirements.txt in your PR if new dependency

### Tests fail on CI but pass locally
- CI runs on Linux; test Windows paths with `pathlib.Path.cwd()` on Windows
- Use `platformdirs` to ensure cross-platform compatibility
- Check CI logs for specific OS mismatch

---

## Merge & Release Checklist

### After Phase 1 Complete (Gate 1)
- [ ] Config schema merged
- [ ] ModelManager merged
- [ ] CLI integration merged
- [ ] Unit tests passing (8.1-8.5)
- [ ] Manual test: `python -m video_censor --download-models --config test.yaml` works
- [ ] No regressions in existing functionality

### After Phase 2 Complete (Gate 2)
- [ ] Pipeline integration merged
- [ ] Integration tests passing (9.1-9.5)
- [ ] Manual test: Pipeline auto-downloads on init
- [ ] Manual test: Analysis resumes without restart

### After Phase 3 Complete (Gate 3)
- [ ] HF registry merged
- [ ] E2E tests passing (10.1-10.4)
- [ ] Manual test: Auto-discovery works
- [ ] Manual test: Deprecation warnings display

### Final: Documentation & Release
- [ ] Documentation merged
- [ ] README updated with examples
- [ ] All tests passing (>80% coverage)
- [ ] No open PRs or TODOs
- [ ] Ready for release tag

---

## Resources

- **Spec**: `openspec/changes/add-model-auto-download/specs/project-foundation/spec.md`
- **Design Decisions**: `design.md` → Decisions Finalized section
- **API Reference**: `API_CONTRACTS.md`
- **Test Fixtures**: `tests/fixtures/mock_http_server.py`, `tests/fixtures/mock_models/`
- **Example Config**: `video-censor.yaml.example` (update during Phase 1)

---

## Getting Help

1. **Questions about spec or design**: Read design.md section or ask integration owner
2. **Questions about your stream**: Check PARALLELIZATION.md for your stream details
3. **API incompatibility**: Cross-reference API_CONTRACTS.md with your code
4. **Test failures**: Check test files in `tests/` directory; debug with `-vv` flag
5. **Blocker preventing progress**: Post in standup channel; ping integration owner

---

## Success Criteria

When all streams complete and merge:

- ✅ `python -m video_censor --download-models` downloads missing models
- ✅ Models cached in platform-appropriate directory
- ✅ Progress bar shows speed, ETA, completion %
- ✅ Corrupted models re-downloaded automatically
- ✅ Pipeline auto-invokes if flag set; analysis resumes seamlessly
- ✅ Hugging Face models discovered automatically
- ✅ Deprecated models trigger warnings with suggestions
- ✅ >80% test coverage
- ✅ Documentation comprehensive and accurate
- ✅ No regressions in existing functionality

**You're done when all 10 criteria are met and tests pass.**

---

## Next Steps

1. ✅ **Read this document** → You are here
2. ⏭️ **Read your stream guide** (PARALLELIZATION.md section)
3. ⏭️ **Read API_CONTRACTS.md** (understand interfaces)
4. ⏭️ **Check tasks.md** (your specific work items)
5. ⏭️ **Set up worktree** (git worktree commands above)
6. ⏭️ **Start implementing** (follow your stream tasks in order)
7. ⏭️ **Run tests** (pytest for your stream)
8. ⏭️ **Create PR** (with clear description)
9. ⏭️ **Get approval** (1-2 reviewers depending on stream)
10. ⏭️ **Merge** (delete worktree after merge)

**Good luck! 🚀**
