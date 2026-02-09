# Summary: Make Preview Editor More Scalable

## Change Overview

This change proposal addresses a critical usability issue where the preview editor UI hangs during initial load when handling large videos (1.5+ hours with 200+ segments). The root cause is likely segment list widget creation and rendering blocking the main UI thread. The solution involves virtualization, background threading, and profiling.

## What's Included

### 📋 Proposal & Design
- **proposal.md**: Executive summary—why, what, impact
- **design.md**: Detailed technical decisions, risks, migration plan, and open questions
- **ANALYSIS.md**: Evidence-based root cause analysis with performance targets

### 🎯 Implementation Roadmap
- **tasks.md**: 7 phases with 40+ concrete work items:
  1. Profiling & Instrumentation
  2. Virtualization of Segment List
  3. Background Threading (conditional)
  4. Audio Loading Optimization
  5. Integration Tests for Large Videos
  6. Documentation & Cleanup
  7. Final Validation

### 📝 Specification Deltas
- **specs/desktop-ui/spec.md**: Modified and new requirements:
  - Enhanced initialization performance (3s initial display, 10s full load)
  - Support for 200+ and 500+ segment videos
  - Efficient scrolling and memory usage
  - Performance monitoring and testing

## Key Findings

### Problem
- **Symptom**: UI hangs/freezes during initial load with large videos (206 segments)
- **Scale**: Works fine with 15 segments (5 minutes), fails with 206 segments (1.5 hours)
- **Root Cause**: Likely segment list widget creation (206 widgets) blocking main thread

### Solution Strategy
1. **Virtualize Segment List** (High ROI): Render only visible items + buffer (~15-30 items vs. 206)
2. **Optimize Audio Loading** (Low effort): Consolidate caching, defer non-critical ops
3. **Background Threading** (Fallback): Move segment population to background if virtualization insufficient
4. **Profiling & Testing**: Measure improvements and prevent regressions

### Performance Targets
| Metric | Target |
|--------|--------|
| Initial UI Display | < 3 seconds |
| Full Segment List Load | < 10 seconds |
| Small Video (15 segments) | < 500ms (existing performance) |
| Scroll Smoothness | 30+ fps |
| Memory Usage | < 2GB |

## Expected Impact

- ✅ **Usability**: Preview editor becomes usable for long videos (major win)
- ✅ **Scalability**: Supports 500+ segments with same responsive behavior
- ✅ **Reliability**: Integration tests prevent regressions
- ✅ **Non-breaking**: All changes are internal optimizations; user-facing behavior unchanged

## Next Steps

1. **Review & Approve** this proposal
2. **Implement Phase 1** (Profiling) to confirm bottleneck
3. **Proceed with Phase 2+** based on profiling results
4. **Validate** with real 1.5-hour video from logs
5. **Archive** change once complete and deployed

## File Structure

```
openspec/changes/make-preview-editor-more-scalable/
├── ANALYSIS.md              # Root cause analysis & evidence
├── SUMMARY.md               # This file
├── proposal.md              # High-level change description
├── design.md                # Technical design & decisions
├── tasks.md                 # Implementation checklist (40+ items)
└── specs/
    └── desktop-ui/
        └── spec.md          # Modified & new requirements
```

## Status

- ✅ Proposal scaffolded and validated
- ✅ Analysis completed with evidence from logs
- ✅ Design documented with risk mitigations
- ✅ Tasks broken down into small, verifiable units
- ✅ Specifications written with scenarios
- 🔲 **Awaiting approval to proceed with implementation**
