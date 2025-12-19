# Change: Bootstrap Desktop UI with CustomTkinter

## Why

The project currently operates through CLI only, which limits accessibility for end-users who prefer graphical interfaces. Bootstrapping a Python-native desktop UI using TKinter and CustomTkinter provides a modern, cross-platform foundation for building GUI functionality on top of the existing CLI infrastructure. This maintains the CLI-first philosophy while offering a convenience layer for users.

## What Changes

- **NEW** Create a cross-platform desktop UI package using CustomTkinter for modern TKinter styling
- **NEW** Define a Desktop UI capability with initial requirements for window bootstrap and basic frame layout
- **NEW** Add CustomTkinter as a project dependency in requirements.txt
- **NEW** Establish UI module structure following the project's modular design patterns

## Impact

- **Affected specs**: New `desktop-ui` capability (non-breaking addition)
- **Affected code**: 
  - `requirements.txt` - Add CustomTkinter dependency
  - `video_censor_personal/` - New `ui/` module directory
  - `video_censor_personal/ui/main.py` - Bootstrap application entry point

## Design Rationale

CustomTkinter is chosen for its:
- Modern appearance and customization capabilities
- Cross-platform support (Windows, Linux, macOS)
- Python-native implementation requiring no separate C bindings
- Active community and documentation
- Lightweight footprint suitable for background task integration
