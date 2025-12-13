# Parallelization Plan: Model Auto-Download Implementation

## Overview
This document outlines how to parallelize the Model Auto-Download implementation across multiple subagents and git worktrees to maximize throughput while respecting dependencies.

## Workstream Architecture

```
┌─────────────────────────────────────────────────────────┐
│          PHASE 1: FOUNDATION (Critical Path)            │
├──────────────────┬──────────────────┬──────────────────┤
│  Stream A        │   Stream B       │   Stream C       │
│  Config Schema   │   Model Manager  │   CLI Integration│
│  (1-2 days)      │   (2-3 days)     │   (1-2 days)     │
└──────────────────┴──────────────────┴──────────────────┘
                       ↓ (All complete)
┌─────────────────────────────────────────────────────────┐
│          PHASE 2: PIPELINE (Depends on P1)              │
├──────────────────┬──────────────────────────────────────┤
│  Stream E        │   Stream D (Testing)                 │
│  Pipeline Integ. │   (Parallelize throughout)           │
│  (1-2 days)      │   (2-3 days total)                   │
└──────────────────┴──────────────────────────────────────┘
                       ↓ (Phase 1 + 2 complete)
┌─────────────────────────────────────────────────────────┐
│          PHASE 3: AUTO-DISCOVERY (Depends on P1+2)      │
├──────────────────┬──────────────────────────────────────┤
│  Stream F        │   Stream D (cont.)                   │
│  HF Registry     │   Integration Tests                  │
│  (2-3 days)      │   (1-2 days)                         │
└──────────────────┴──────────────────────────────────────┘
                       ↓ (All phases complete)
┌─────────────────────────────────────────────────────────┐
│          Stream G: DOCUMENTATION (Parallel)             │
│          (Can start after Phase 1 kickoff)              │
│          (1-2 days, complete by end)                    │
└─────────────────────────────────────────────────────────┘
```

## Workstream Details

### Stream A: Configuration Schema Extension (Blocker: None)
**Owner**: Subagent A  
**Duration**: 1-2 days  
**Worktree**: `config-schema`

**Dependencies**: None (independent)

**Deliverables**:
- Extended YAML schema with `models.cache_dir`, `models.sources`
- Hugging Face default model sources (LLaVA, profanity detectors, etc.)
- Example configuration file with real model URLs and checksums
- Schema validation tests
- Type hints for configuration dataclasses

**Tasks** (from main task list):
- 1.1: Update YAML schema
- 1.2: Add model source definitions
- 1.3: Add Hugging Face defaults
- 1.4: Create example configuration
- 1.5: Add validation tests

**Success Criteria**:
- YAML parser loads configuration without errors
- Schema validates model sources (name, url, checksum, size)
- Example config is syntactically correct and realistic

**Merge blocker for**: Stream B (optional, B can proceed with mocked config), Stream C (optional), Stream E, Stream F

---

### Stream B: Model Manager Module (Blocker: Partial A)
**Owner**: Subagent B  
**Duration**: 2-3 days  
**Worktree**: `model-manager`

**Dependencies**: 
- Partial: Stream A (can proceed with basic config structure, import finalized config later)
- External: `tqdm`, `platformdirs` libraries

**Deliverables**:
- `video_censor_personal/model_manager.py` with ModelManager class
- Download logic with temp file handling (atomic)
- SHA256 checksum validation with algorithm flexibility
- Retry logic (3 retries, exponential backoff: 2s, 4s, 8s)
- Disk space pre-check (2× model size)
- Progress reporting via `tqdm`
- Unit tests for all core functions

**Tasks** (from main task list):
- 2.1: Create ModelManager class
- 2.2: Implement verify_models() method
- 2.3: Implement _download_model() with atomic handling
- 2.4: SHA256 + algorithm flexibility
- 2.5: Progress reporting via tqdm
- 2.6: Retry with exponential backoff
- 2.7: Disk space verification
- 2.8: platformdirs integration
- 8.1: Unit tests (checksum validation)
- 8.2: Unit tests (atomic download)
- 8.3: Unit tests (disk space checks)
- 8.4: Unit tests (platformdirs)
- 8.5: Unit tests (retry logic)

**Success Criteria**:
- ModelManager.verify_models() downloads missing models correctly
- Checksums validated; corrupt files deleted and re-downloaded
- All unit tests pass (8.1-8.5)
- Progress bar displays correctly with speed/ETA
- Retries work on mocked network failures

**Merge blocker for**: Stream C, Stream D, Stream E

---

### Stream C: CLI Integration (Blocker: B only)
**Owner**: Subagent C  
**Duration**: 1-2 days  
**Worktree**: `cli-integration`

**Dependencies**:
- Hard: Stream B (needs ModelManager class)
- Soft: Stream A (config schema, but can use mocked config initially)

**Deliverables**:
- `--download-models` flag in main CLI argument parser
- Integration in main entry point (before analysis pipeline)
- Idempotency enforcement (skip valid cached models)
- Error message handling with recovery guidance
- Integration tests with mock downloads

**Tasks** (from main task list):
- 3.1: Add --download-models flag
- 3.2: Integrate into main entry point
- 3.3: Idempotency logic
- 3.4: Error messages with guidance
- 9.1: Mock HTTP server integration tests
- 9.2: Progress reporting output tests

**Success Criteria**:
- CLI accepts --download-models flag
- Downloads trigger correctly
- Idempotent runs skip downloads
- Error messages are clear and actionable
- Integration tests pass with mock HTTP

**Merge blocker for**: Stream D (integration tests), Stream E

---

### Stream D: Testing Framework (Parallel throughout)
**Owner**: Subagent D (QA/Testing focus)  
**Duration**: 2-3 days total (incremental)  
**Worktree**: `testing`

**Dependencies**: 
- Streams A, B, C (as they deliver features)

**Deliverables**:
- Mock HTTP server for download testing
- Cross-platform path tests (Windows, macOS, Linux)
- Configuration parsing tests
- Unit test suite (grows with each stream)
- Integration test suite
- End-to-end test scenarios

**Tasks** (from main task list):
- 8.1-8.6: Unit tests (across streams)
- 9.1-9.5: Integration tests
- 10.1-10.4: End-to-end tests
- Platform-specific tests via CI/matrix

**Success Criteria**:
- >80% code coverage
- All unit tests pass on Phase 1 completion
- Integration tests pass on Phase 2 completion
- E2E tests pass on Phase 3 completion
- Cross-platform tests validate Windows/macOS/Linux paths

**Note**: This stream is asynchronous. Tests are written in parallel with implementation, blocking on each stream's delivery.

---

### Stream E: Pipeline Integration (Blocker: B + C)
**Owner**: Subagent E  
**Duration**: 1-2 days  
**Worktree**: `pipeline-integration`

**Dependencies**:
- Hard: Streams B + C (ModelManager, CLI flag)
- Soft: Stream A (config schema, for model requirement extraction)

**Deliverables**:
- Model requirement extraction from YAML (at pipeline startup)
- Missing model detection before detector instantiation
- Auto-invoke ModelManager.verify_models() if flag set
- Lazy detector initialization (wait for download completion)
- Pipeline state tracking (readiness, errors)
- Logging for download progress

**Tasks** (from main task list):
- 4.1: Extract model requirements from config
- 4.2: Check for missing models
- 4.3: Auto-invoke verify_models()
- 4.4: Seamless resume after download
- 4.5: Error messaging
- 5.1: AnalysisPipeline state tracking
- 5.2: Lazy detector initialization
- 5.3: Pipeline logging

**Success Criteria**:
- Pipeline detects missing models before instantiation
- Auto-download triggers with --download-models flag
- Analysis resumes transparently after download
- No user restart needed
- Pipeline state correctly reflects download status

**Merge blocker for**: Stream F (Phase 2 must complete), Stream D (integration tests)

---

### Stream F: Hugging Face Registry (Blocker: B + E)
**Owner**: Subagent F  
**Duration**: 2-3 days  
**Worktree**: `huggingface-registry`

**Dependencies**:
- Hard: Streams B (ModelManager foundation), E (Pipeline to integrate with)
- Soft: Stream A (config schema, for version pinning)

**Deliverables**:
- HuggingFaceRegistry class for metadata discovery
- API querying for model versions, checksums, sizes
- Metadata caching with 24h TTL
- Model availability checking (deprecation warnings)
- Version pinning support in config
- Fallback logic for unavailable models
- Auto-discovery of required models at startup

**Tasks** (from main task list):
- 6.1: HuggingFaceRegistry class
- 6.2: Query Hugging Face API
- 6.3: Cache model metadata (24h TTL)
- 6.4: Version pinning support
- 7.1: Detect required models at startup
- 7.2: Auto-populate cache
- 7.3: Model availability checking
- 7.4: Fallback suggestions
- 7.5: Lazy cache refresh
- 8.6: Unit tests (registry, caching, TTL)

**Success Criteria**:
- HuggingFaceRegistry queries models successfully
- Metadata caches and respects TTL
- Deprecation warnings display correctly
- Version pinning works with fallback
- Auto-discovery populates cache correctly

**Merge blocker for**: Stream D (Phase 3 tests)

---

### Stream G: Documentation (Parallel throughout)
**Owner**: Subagent G  
**Duration**: 1-2 days total (incremental)  
**Worktree**: `documentation`

**Dependencies**: 
- Soft: Streams A, B, C, E, F (as they develop)
- Can proceed with design.md and specifications as references

**Deliverables**:
- README updates with `--download-models` examples
- YAML configuration documentation with Hugging Face defaults
- Custom model source documentation
- Troubleshooting section (network errors, disk space, corruption)
- Model fallback and version pinning docs
- Quick-start guide for first-time users
- Internal ModelManager API documentation
- HuggingFaceRegistry integration documentation
- Checksum update procedures

**Tasks** (from main task list):
- 11.1: README usage example
- 11.2: YAML config documentation
- 11.3: Custom sources documentation
- 11.4: Troubleshooting section
- 11.5: Fallback & version pinning docs
- 11.6: Quick-start guide
- 12.1: ModelManager API docs
- 12.2: HuggingFaceRegistry docs
- 12.3: Checksum update procedures

**Success Criteria**:
- Documentation is comprehensive and user-friendly
- Code examples are syntactically correct and runnable
- Troubleshooting covers common issues
- API documentation matches implementation

**Note**: Can start immediately after design approval; doesn't block main implementation.

---

## Dependency Graph

```
Stream A (Config)
  ├─→ Stream B (ModelManager)
  │     ├─→ Stream C (CLI)
  │     │     ├─→ Stream E (Pipeline)
  │     │     │     └─→ Stream F (HF Registry)
  │     └─→ Stream D (Testing) ←── All streams feed tests
  └─→ Stream E (Pipeline)
  └─→ Stream F (HF Registry)

Stream G (Documentation) ←─┐
  Parallel, feeds from all ↑
```

## Critical Path

**Longest sequence**:
1. Stream A: Config schema (1-2 days)
2. Stream B: ModelManager (2-3 days)
3. Stream C: CLI (1-2 days)
4. Stream E: Pipeline (1-2 days)
5. Stream F: HF Registry (2-3 days)

**Total critical path**: ~9-12 days (if sequential)

**With parallelization**: ~4-5 days (A, then B+G in parallel, then C+D in parallel, then E+D in parallel, then F+D in parallel)

## Merge Strategy

### Phase 1 Completion (Enable Merging)
When **A + B + C** are complete and tested:
1. Merge A → main (config schema, no code changes)
2. Merge B → main (model_manager.py, no integration yet)
3. Merge C → main (CLI flag integration)
4. All Phase 1 tests pass (unit + integration)

**Validation**: `python -m video_censor --download-models --config test.yaml` downloads models correctly.

### Phase 2 Completion (Add Pipeline)
When **E** is complete and integrated with Phase 1:
1. Merge E → main (pipeline integration)
2. Phase 2 integration tests pass

**Validation**: Missing models trigger auto-download during pipeline init; analysis resumes without restart.

### Phase 3 Completion (Add Auto-Discovery)
When **F** is complete and integrated:
1. Merge F → main (HF registry)
2. Phase 3 integration + end-to-end tests pass

**Validation**: Auto-discovery populates cache; deprecation warnings display; version pinning works.

### Documentation (Final)
When all phases complete:
1. Merge G → main (documentation)

---

## Worktree Workflow

### Setup
```bash
# Main development branch
git checkout main

# Create worktrees for each stream
git worktree add ../wt-config-schema config-schema
git worktree add ../wt-model-manager model-manager
git worktree add ../wt-cli-integration cli-integration
git worktree add ../wt-testing testing
git worktree add ../wt-pipeline-integration pipeline-integration
git worktree add ../wt-huggingface-registry huggingface-registry
git worktree add ../wt-documentation documentation
```

### Per-Stream Workflow
```bash
# Subagent A (config-schema)
cd ../wt-config-schema
git checkout -b stream-a/config-schema main

# ... implement tasks 1.1-1.5 ...

git commit -m "Add model auto-download configuration schema"
git push origin stream-a/config-schema

# Create PR for review & merge
```

### Synchronization Points
1. **After Stream A complete**: Merge to main before B starts production (B can mock config initially)
2. **After Streams B + C complete**: Merge to main before E starts
3. **After Stream E complete**: Merge to main before F starts
4. **After Stream F complete**: Merge to main before G finalizes

---

## Communication Plan

### Daily Standup (async)
- Posted in shared channel by EOD
- Each stream reports:
  - ✅ What completed
  - 🚧 What's in progress
  - 🔴 Blockers (if any)
  - ➡️ Next tasks

### PR Review Cycle
- Subagent submits PR when tasks for stream complete
- Cross-review by 1-2 other subagents (QA + peer)
- Approval triggers merge to integration branch (or main if no blocker)

### Integration Points
- **After Phase 1**: Run all Phase 1 tests; ensure --download-models works standalone
- **After Phase 2**: Run Phase 1 + 2 tests; ensure pipeline auto-invoke works
- **After Phase 3**: Run all tests; ensure Hugging Face discovery works
- **Final**: E2E test full workflow; validate documentation

---

## Estimated Timeline

| Phase | Stream | Duration | Start | End | Critical Path |
|-------|--------|----------|-------|-----|---|
| 1 | A | 1-2d | Day 1 | Day 2 | Yes |
| 1 | B | 2-3d | Day 1 | Day 4 | Yes |
| 1 | C | 1-2d | Day 3 | Day 4 | Yes |
| 1 | D (P1) | 1d | Day 3 | Day 4 | No |
| 2 | E | 1-2d | Day 5 | Day 6 | Yes |
| 2 | D (P2) | 1d | Day 5 | Day 6 | No |
| 3 | F | 2-3d | Day 7 | Day 9 | Yes |
| 3 | D (P3) | 1d | Day 7 | Day 8 | No |
| * | G | 1-2d | Day 2 | Day 10 | No |

**Total: 9-10 calendar days** (with 6-7 subagents working in parallel)

**vs. Sequential**: ~15-20 days with single developer

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Stream A delays (config) | B proceeds with mocked config; merge A early to unblock |
| Stream B incomplete (ModelManager) | C mocks ModelManager; merge B as soon as tested |
| Stream D (testing) lags | Early unit tests for A/B/C; integration tests async |
| Merge conflicts | Frequent small commits; separate concerns by module |
| API changes between streams | Synchronous API design doc before implementation |
| Platform-specific issues | CI matrix tests all platforms; caught early |

---

## Definition of Done Per Stream

**Stream A (Config)**
- [ ] YAML schema updated with models.cache_dir, models.sources
- [ ] Hugging Face defaults documented
- [ ] Example config file realistic and valid
- [ ] Schema validation tests pass
- [ ] PR approved, merged to main

**Stream B (ModelManager)**
- [ ] ModelManager class implements verify_models(), _download_model()
- [ ] Atomic downloads with temp file handling
- [ ] SHA256 validation + algorithm flexibility
- [ ] Retry logic (3x, exponential backoff)
- [ ] Disk space checks
- [ ] Progress reporting via tqdm
- [ ] Unit tests 8.1-8.5 pass
- [ ] PR approved, merged to main

**Stream C (CLI)**
- [ ] --download-models flag added
- [ ] Main entry point integration
- [ ] Idempotency logic
- [ ] Error handling with guidance
- [ ] Integration tests 9.1-9.2 pass
- [ ] PR approved, merged to main

**Stream D (Testing)**
- [ ] Unit test suite passes (8.1-8.6, grows per phase)
- [ ] Integration test suite passes (9.1-9.5)
- [ ] E2E test suite passes (10.1-10.4)
- [ ] >80% code coverage
- [ ] Cross-platform tests validated

**Stream E (Pipeline)**
- [ ] Model requirement extraction implemented
- [ ] Missing model detection works
- [ ] Auto-invoke verify_models() on flag set
- [ ] Lazy detector initialization
- [ ] Pipeline state tracking
- [ ] Logging integrated
- [ ] Phase 2 integration tests pass
- [ ] PR approved, merged to main

**Stream F (HF Registry)**
- [ ] HuggingFaceRegistry class implemented
- [ ] Hugging Face API querying works
- [ ] Metadata caching (24h TTL)
- [ ] Version pinning + fallback
- [ ] Auto-discovery at startup
- [ ] Deprecation warnings
- [ ] Unit tests 8.6 pass
- [ ] Phase 3 integration tests pass
- [ ] PR approved, merged to main

**Stream G (Documentation)**
- [ ] README updated with examples
- [ ] YAML config docs complete
- [ ] Troubleshooting section
- [ ] API documentation
- [ ] Quick-start guide
- [ ] Examples tested and runnable
