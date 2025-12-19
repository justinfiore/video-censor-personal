## ADDED Requirements

### Requirement: Video Player Framework Integration (python-vlc + CustomTkinter)

The system SHALL integrate python-vlc (VLC's official Python bindings) with CustomTkinter to provide synchronized video and audio playback within the desktop application. The integration SHALL support seeking, volume control, and reliable playback of common video formats (MP4, MKV, AVI).

#### Scenario: Video loads and plays without errors
- **WHEN** user opens a video file via UI
- **THEN** the selected video player library loads the file successfully
- **AND** the video displays in the video player widget
- **AND** audio is synchronized with video playback (within 100ms tolerance)
- **AND** no errors or warnings are logged

#### Scenario: Video seeking works smoothly
- **WHEN** user clicks on the timeline or uses seek buttons
- **THEN** the video player seeks to the requested timestamp
- **AND** audio continues from the new position
- **AND** seeking latency is <500ms (user perceives as immediate)

#### Scenario: Volume control functional
- **WHEN** user adjusts volume slider
- **THEN** audio volume changes proportionally (0-100%)
- **AND** muted state is supported (0% = silent)

#### Scenario: Multiple video formats supported
- **WHEN** user loads MP4, MKV, or AVI files
- **THEN** all formats play without codec errors
- **AND** seeking and audio work on all formats

#### Scenario: Video playback runs on target platforms
- **WHEN** application runs on macOS, Windows, or Linux
- **THEN** video playback works identically on all platforms
- **AND** audio sync is consistent across platforms

### Requirement: UI Framework Window Container (CustomTkinter)

The system SHALL provide a modern, responsive window container using CustomTkinter (CTk) that serves as the foundation for the preview editor UI components. CustomTkinter is already integrated in the project and provides modern cross-platform styling. The framework SHALL support cross-platform deployment (Windows, macOS, Linux) using CustomTkinter's native component library (CTkFrame, CTkButton, CTkLabel, CTkSlider, CTkScrollableFrame, CTkCheckBox, CTkToplevel).

#### Scenario: Application window launches on macOS
- **WHEN** user launches the preview editor UI
- **THEN** a window appears with title "Video Censor Personal - Preview Editor"
- **AND** window size is reasonable (minimum 1024x768, default 1366x768 recommended)
- **AND** window is responsive to user interaction

#### Scenario: Application window launches on Windows
- **WHEN** user launches the preview editor UI on Windows
- **THEN** window appears with same appearance and layout as macOS
- **AND** native Windows styling is applied (if framework supports)
- **AND** window is responsive

#### Scenario: Application window launches on Linux
- **WHEN** user launches the preview editor UI on Linux (X11 or Wayland)
- **THEN** window appears with same appearance and layout as macOS
- **AND** window is responsive

#### Scenario: Window layout supports three-pane design
- **WHEN** preview editor window is created
- **THEN** window interior contains three regions: left segment list pane, center video player pane, bottom segment details pane
- **AND** layout remains stable as window is resized

### Requirement: Framework Dependency Management (python-vlc)

The system SHALL declare python-vlc as a project dependency with appropriate version constraints to ensure reproducible builds and compatibility. CustomTkinter is already declared in existing dependencies.

#### Scenario: Dependencies specified in requirements.txt
- **WHEN** project dependencies are installed
- **THEN** requirements.txt includes python-vlc with version pin (e.g., `python-vlc>=3.0.0`)
- **AND** CustomTkinter is already present in requirements
- **AND** no version conflicts exist with existing dependencies

#### Scenario: Dependencies install without errors
- **WHEN** running `pip install -r requirements.txt`
- **THEN** both UI framework and video library are installed successfully
- **AND** all imports work: `import PyQt6` (or equivalent), `import vlc` (or equivalent)

#### Scenario: No dependency regressions
- **WHEN** UI dependencies are added
- **THEN** existing CLI and analysis pipeline functionality remains unaffected
- **AND** CLI imports do not require UI framework

### Requirement: CustomTkinter Component Consistency

The system SHALL prioritize CustomTkinter components (CTk*) for all UI elements throughout the preview editor interface to maintain visual consistency and leverage the framework's modern styling capabilities.

#### Scenario: All interactive elements use CustomTkinter buttons
- **WHEN** user interacts with buttons (play/pause, skip, allow toggle, etc.)
- **THEN** all buttons are CTkButton instances
- **AND** buttons display with consistent CustomTkinter styling
- **AND** hover states and visual feedback work correctly

#### Scenario: Text displays use CTkLabel
- **WHEN** application displays text (timecode, segment info, descriptions, labels)
- **THEN** all text is rendered using CTkLabel
- **AND** text respects CustomTkinter color scheme
- **AND** text wrapping and sizing behaves consistently

#### Scenario: Container layouts use CTkFrame
- **WHEN** application creates panes or sections (segment list, video player, details panel)
- **THEN** each pane/section is a CTkFrame
- **AND** nested layouts use grid geometry manager with CTkFrame containers
- **AND** background colors and borders respect CustomTkinter theme

#### Scenario: Scrollable lists use CTkScrollableFrame
- **WHEN** segment list requires scrolling
- **THEN** segment list is implemented using CTkScrollableFrame
- **AND** scroll behavior is smooth and responsive
- **AND** styling matches CustomTkinter theme

#### Scenario: Sliders use CTkSlider
- **WHEN** user adjusts volume or timeline progress
- **THEN** sliders are CTkSlider instances
- **AND** slider appearance and interaction respect CustomTkinter styling
- **AND** value mapping (percentage to internal range) works correctly

#### Scenario: Standard Tkinter fallback for unavailable components
- **WHEN** CustomTkinter does not provide equivalent (e.g., Canvas for timeline, Menu for menu bar)
- **THEN** standard Tkinter components are used as fallback
- **AND** fallback components are documented in code comments
- **AND** styling is adapted where possible to match CustomTkinter theme
