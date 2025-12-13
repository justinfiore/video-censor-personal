# Model Auto-Download: Implementation Package

## 📋 Quick Overview

This directory contains the **complete specification, design, and implementation plan** for the Model Auto-Download feature across all 3 phases.

The feature enables users to automatically download and verify video analysis models with a single CLI flag: `python -m video_censor --download-models`

---

## 📁 Files in This Package

### Core Proposal Documents

| File | Purpose | Read When |
|------|---------|-----------|
| **proposal.md** | Executive summary: why, what, impact | First (2 min read) |
| **design.md** | Architecture, decisions, risks, migration plan | Before coding (5 min read) |
| **tasks.md** | Implementation checklist (~60 items) | While implementing |
| **specs/project-foundation/spec.md** | 13 detailed requirements with scenarios | Reference while building |

### Implementation Coordination

| File | Purpose | Read When |
|------|---------|-----------|
| **PARALLELIZATION.md** | 7 independent workstreams, timeline, merge strategy | 📌 **Before starting** (critical path planning) |
| **API_CONTRACTS.md** | Exact interfaces between streams (code-level) | 📌 **Before coding** (prevents merge conflicts) |
| **IMPLEMENTATION_KICKOFF.md** | Day-1 checklist, per-subagent workflow, troubleshooting | **Day 1** (kickoff guide) |
| **README.md** | This file — navigation guide | Right now |

---

## 🎯 Three-Phase Architecture

### Phase 1: Foundation (Days 1-4)
CLI flag + Model Manager + configuration schema

**Streams A, B, C, D (partial)**
- `--download-models` flag
- Atomic downloads with checksum validation
- Progress reporting (tqdm)
- Retry logic with exponential backoff
- Disk space pre-checks
- Hugging Face as default source

**Exit Criteria**: `python -m video_censor --download-models` downloads models successfully

### Phase 2: Pipeline Integration (Days 5-6)
Auto-invoke downloads during analysis pipeline init

**Streams E, D (partial)**
- Detect missing models at pipeline startup
- Auto-invoke downloads if flag set
- Seamless resume after download (no restart needed)
- Single unified workflow for users

**Exit Criteria**: Missing models trigger auto-download; analysis continues transparently

### Phase 3: Auto-Discovery (Days 7-9)
Hugging Face registry integration + model caching

**Streams F, D (partial)**
- Query Hugging Face for available models
- Cache metadata (24h TTL)
- Model version pinning + fallback
- Deprecation warnings

**Exit Criteria**: Auto-discovery populates cache; suggestions for deprecated models

### Documentation (Parallel, Days 2-10)
User guides, API docs, troubleshooting

**Stream G**
- README with examples
- YAML configuration guide
- Troubleshooting section
- Quick-start guide

---

## 🚀 Getting Started

### For Project Managers / Integration Owners

1. **Understand scope**: Read `proposal.md` (2 min)
2. **Review timeline**: Read `PARALLELIZATION.md` → Estimated Timeline table (2 min)
3. **Plan approval gates**: Reference `PARALLELIZATION.md` → Merge Strategy (3 min)
4. **Monitor progress**: Use `tasks.md` as checklist; mark items complete as streams deliver

### For Subagents

1. **Day 1 Kickoff**: Read `IMPLEMENTATION_KICKOFF.md` (5 min)
2. **Understand your stream**: Read `PARALLELIZATION.md` → [Stream X] section (3 min)
3. **Know the contracts**: Read `API_CONTRACTS.md` (10 min) ← **Critical before coding**
4. **Check your tasks**: Reference `tasks.md` for your stream's checklist
5. **Start implementing**: Follow tasks in order; validate with tests

### For Code Reviewers

1. **Know the spec**: Read `specs/project-foundation/spec.md` (scenarios section)
2. **Know the API contracts**: Reference `API_CONTRACTS.md` for expected interfaces
3. **Check the checklist**: Verify PR claims cover all relevant tasks.md items
4. **Validate tests**: >80% coverage, all unit + integration tests pass

---

## 📊 Parallelization Summary

**7 independent workstreams** working simultaneously on different modules:

```
Stream A: Config Schema       (1-2 days) ─→ blocks B
Stream B: Model Manager       (2-3 days) ─┬─→ blocks C, E
Stream C: CLI Integration     (1-2 days) ─┤─→ blocks E
Stream D: Testing             (2-3 days) ← feeds from A-G (parallel)
Stream E: Pipeline Integration(1-2 days) ← blocks F
Stream F: HF Registry         (2-3 days) ← feeds E
Stream G: Documentation       (1-2 days) ← parallel, no blocks

Critical Path: A → B → C → E → F (9-10 days)
With Parallelization: ~4-5 days actual calendar time
```

**Key**: Streams 1-7 don't wait for each other (except where noted).

---

## 📋 Decision Log

**Answers to open questions from design.md:**

| Question | Answer | Rationale |
|----------|--------|-----------|
| Model sources? | Hugging Face (primary) + configurable fallback | Well-maintained registry; flexibility for custom sources |
| Checksum algorithm? | SHA256 + support Hugging Face alternatives | Industry standard; extensible for future sources |
| Timeout strategy? | Fixed defaults (300s, 3 retries, 2/4/8s backoff) | Reasonable for typical models; YAML extension available post-MVP |
| Cache directory? | Platform defaults via `platformdirs` library | Cross-platform consistency; respects OS conventions |
| Phases in this change? | All 3 (CLI, Pipeline, Auto-Discovery) | Cohesive feature; users get full benefit immediately |

---

## ✅ Success Criteria

When all 3 phases complete:

- ✅ Users run `python -m video_censor --download-models` once
- ✅ Models auto-download to platform-appropriate cache
- ✅ Progress bar shows speed/ETA/completion
- ✅ Corrupted models re-download automatically
- ✅ Pipeline auto-invokes if flag set
- ✅ Analysis resumes without restart
- ✅ Hugging Face models auto-discovered
- ✅ Deprecated models trigger helpful suggestions
- ✅ >80% test coverage
- ✅ No regressions to existing functionality

---

## 📖 Reading Order

### For Different Roles

**Project Manager / Owner**
1. proposal.md (why + what)
2. PARALLELIZATION.md (timeline, streams, gates)
3. tasks.md (checklist to track)

**Subagent (Developer)**
1. IMPLEMENTATION_KICKOFF.md (start here!)
2. PARALLELIZATION.md (your stream)
3. API_CONTRACTS.md (before coding)
4. tasks.md (your tasks)
5. design.md (reference for decisions)

**QA / Code Reviewer**
1. specs/project-foundation/spec.md (requirements)
2. API_CONTRACTS.md (interfaces to verify)
3. tasks.md (coverage areas)
4. design.md (risk mitigation strategies)

**Future Maintainer**
1. design.md (why things are this way)
2. API_CONTRACTS.md (module boundaries)
3. specs/project-foundation/spec.md (behavior spec)
4. source code (implementation details)

---

## 🔗 Integration Points

| Component | Location | Owner | Notes |
|-----------|----------|-------|-------|
| Config schema | `video_censor_personal/config.py` | Stream A | Must include `.models` field |
| ModelManager | `video_censor_personal/model_manager.py` | Stream B | Core download logic |
| CLI flag | `video_censor_personal/__main__.py` | Stream C | Calls `pipeline.verify_models()` |
| Pipeline integration | `video_censor_personal/analysis_pipeline.py` | Stream E | Calls `ModelManager.verify_models()` |
| HF Registry | `video_censor_personal/huggingface_registry.py` | Stream F | Optional; used by Pipeline for warnings |
| Tests | `tests/unit/` + `tests/integration/` | Stream D | Validates all phases |
| Documentation | `README.md`, `.md` files in docs/ | Stream G | User guides + API docs |

---

## 🚨 Critical Blockers

**These must be respected:**

1. **Stream A must merge before Stream B** production code (B can use mocks initially)
2. **Streams B + C must complete Phase 1** before Stream E begins
3. **Stream E must complete Phase 2** before Stream F begins
4. **All tests must pass** before each phase exit gate
5. **No breaking API changes** to existing modules (backward compatible)

**If blocked, escalate immediately to integration owner.**

---

## 📞 Communication & Review

### Standup Format
Post daily by EOD in shared channel:
```
Stream X (Your Name)
✅ Completed: Tasks X.1, X.2
🚧 In Progress: Task X.3 (ETA tomorrow)
🔴 Blockers: [if any]
➡️ Next: Task X.4
```

### PR Review Gates
- 1 approval for documentation/testing
- 2 approvals for core API changes (B, E, F)
- Reference completed tasks.md items
- >80% code coverage required

### Integration Syncs
- Weekly or at phase exit gates
- Verify no merge conflicts
- Run full test suite
- Unlock next phase

---

## 📚 Appendix: Document Map

```
add-model-auto-download/
├── README.md ← You are here
├── proposal.md
│   └── Why: Reduce setup friction
│   └── What: 3 phases of model management
│   └── Impact: Affected specs/code
├── design.md
│   └── Context & constraints
│   └── Architecture decisions (5)
│   └── Risk mitigation
│   └── Implementation plan (all 3 phases)
├── tasks.md
│   └── 60+ items across 13 sections
│   └── Organized by phase + stream
│   └── Dependencies noted
├── PARALLELIZATION.md ← **Critical for coordination**
│   └── 7 workstreams defined
│   └── Dependencies, timeline, critical path
│   └── Merge strategy & gates
│   └── 4-5 day actual duration
├── API_CONTRACTS.md ← **Critical for coding**
│   └── Exact interface contracts
│   └── Code signatures, docstring formats
│   └── Integration sequences
│   └── Approval gates per stream
├── IMPLEMENTATION_KICKOFF.md ← **Day 1 for subagents**
│   └── Quick start checklist
│   └── Worktree setup commands
│   └── Per-stream workflows
│   └── Testing strategy
│   └── Error handling
│   └── Code quality standards
│   └── Troubleshooting
└── specs/
    └── project-foundation/
        └── spec.md
            └── 13 ADDED requirements
            └── 30+ scenarios
            └── Phase labels (P1, P2, P3)
```

---

## 🎓 How to Use This Package

### Scenario: "I'm the project manager, what do I need to know?"
→ Read: proposal.md (2 min) + PARALLELIZATION.md timeline table (2 min)  
→ Use: tasks.md as your tracking checklist

### Scenario: "I'm assigned Stream B, where do I start?"
→ Read: IMPLEMENTATION_KICKOFF.md (5 min) + PARALLELIZATION.md (Stream B section)  
→ Then: API_CONTRACTS.md → ModelManager section  
→ Finally: tasks.md → Section 2 (your tasks)  
→ Code: Implement using API_CONTRACTS.md as interface spec

### Scenario: "I'm reviewing a PR from Stream C"
→ Check: API_CONTRACTS.md → Stream A + B → Stream C section  
→ Verify: PR implements all required methods with exact signatures  
→ Test: Run `pytest tests/integration/test_download_flow.py -v`  
→ Approve: If tests pass, interfaces match, >80% coverage

### Scenario: "We're blocked on Stream B, what do we do?"
→ Check: PARALLELIZATION.md → Stream B section → dependencies  
→ Escalate: If dependency (Stream A) not merging, contact Stream A owner  
→ Workaround: If unblockable, request early review/approval to merge partial

---

## ✨ Final Checklist Before Implementation Starts

- [ ] All team members have read IMPLEMENTATION_KICKOFF.md
- [ ] Worktrees created (`git worktree add ...` commands)
- [ ] API_CONTRACTS.md reviewed by all developers
- [ ] Design decisions understood (design.md finalized section)
- [ ] Phase 1 exit criteria defined and agreed
- [ ] Code review process established (PR template, approval process)
- [ ] Test framework setup (tqdm for progress, mock HTTP server ready)
- [ ] Dependency versions agreed (tqdm, platformdirs, requests, etc.)
- [ ] CI/CD configured for >80% coverage requirement
- [ ] Standup schedule set (async daily or sync 3x/week)
- [ ] Integration owner assigned and available

**Ready to build! 🚀**
