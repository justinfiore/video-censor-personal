# Design: Desktop UI Bootstrap

## Context

The Video Censor project currently operates through a CLI interface. The project constraints specify that the CLI must remain the primary interface with feature parity, while a desktop UI serves as an enhancement layer. This bootstrap phase creates the foundation for future UI features without impacting CLI functionality.

**Key Constraint** (from `openspec/project.md`):
- **CLI-First**: The CLI is the primary interface and must always be fully functional
- **UI as Enhancement**: The UI is a convenience layer built on top of CLI functionality
- **No UI Lock-in**: Users should never be required to use the UI to accomplish any task

## Goals / Non-Goals

### Goals
- Bootstrap a cross-platform desktop application using Python
- Use CustomTkinter for modern UI appearance on Windows, Linux, and macOS
- Create a minimal, extensible foundation for future UI features
- Maintain separation of concerns: UI logic separate from CLI and analysis logic
- Enable type-safe, testable UI module structure

### Non-Goals
- Implement full video preview/editing features (future `preview-editor-ui` capability)
- Integrate with analysis pipeline in bootstrap phase
- Create complex UI layouts or animations
- Replace CLI functionality or deprecate CLI interface

## Decisions

### Decision 1: CustomTkinter for UI Framework
**What**: Use CustomTkinter (modern TKinter wrapper) for desktop UI
**Why**: 
- Meets cross-platform requirement (Windows, Linux, macOS)
- Provides modern aesthetic vs. standard Tkinter
- Pure Python implementation, no complex build dependencies
- Active maintenance and community support
- Lightweight and suitable for integration with background analysis tasks
- Good documentation for standard patterns

**Alternatives Considered**:
- PyQt6/PySide6: More heavyweight, GPL/LGPL licensing complexity
- Kivy: Better for mobile targets, overkill for desktop-only app
- wxPython: Larger footprint, less active development
- Tkinter (vanilla): Outdated appearance, less aesthetically modern

### Decision 2: Module Structure
**What**: Create `video_censor_personal/ui/` package with main entry point
**Why**: 
- Follows project modular design pattern
- Separates UI concerns from CLI and analysis logic
- Enables type hints and testing at module boundaries
- Allows future expansion (dialogs, widgets, components)

**Structure**:
```
video_censor_personal/
├── ui/
│   ├── __init__.py
│   └── main.py          # Bootstrap application window
├── cli.py               # Existing CLI interface
├── analysis/            # Existing analysis modules
└── ...
```

### Decision 3: Bootstrap Scope (Minimal Viable Window)
**What**: Start with window initialization and empty frame only
**Why**:
- Validates CustomTkinter integration before building complex features
- Provides foundation for incremental feature addition
- Reduces complexity in initial review and testing
- Aligns with project simplicity principle ("Default to <100 lines of new code")

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| CustomTkinter dependency compatibility issues on Linux/macOS | Test on all three platforms before merging; use pinned version in requirements.txt |
| Future scope creep (UI features blocking CLI parity) | Enforce architectural constraint via code review; use feature branches for UI-specific work |
| UI module tight coupling with CLI | Use clean interfaces and pass data via JSON (standard project format) |

## Migration Plan

### Phase 1: Bootstrap (This Change)
- Add CustomTkinter dependency
- Create UI module with window initialization
- Validate cross-platform window rendering
- No integration with analysis pipeline

### Phase 2: Future (`preview-editor-ui`)
- Build video player integration (ffmpeg/VLC)
- Implement segment list UI
- Add JSON file loading and segment display
- Persist allow/disallow status to JSON

### Phase 3: Future (`ui-full-workflow`)
- Integrate analysis pipeline triggering from UI
- Add remediation dialog and progress tracking
- Enable full video processing workflow from UI

## Open Questions

- Q: Should the UI module include its own logging configuration, or use the project-wide logger?
  - A (TBD): Clarify logging strategy with project maintainers
  
- Q: Should CustomTkinter be pinned to a specific version or allow minor/patch updates?
  - A (TBD): Review project dependency management conventions
