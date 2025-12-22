# Installer Specification

## ADDED Requirements

### Requirement: Native macOS Application Bundle (.app)

The system SHALL provide a native macOS application bundle that can be installed by dragging to the Applications folder. The bundle SHALL be self-contained, requiring no external tools or Python knowledge to install or run.

#### Scenario: User downloads and installs on Intel Mac
- **WHEN** user downloads `Video-Censor-Personal.dmg` on an Intel-based Mac
- **THEN** opening the DMG displays an installer window with the .app and Applications folder shortcut
- **AND** dragging the .app to Applications installs the application
- **AND** double-clicking the .app from Applications folder launches the application
- **AND** the application functions identically to development version (UI, video playback, processing)

#### Scenario: User downloads and installs on Apple Silicon Mac
- **WHEN** user downloads `Video-Censor-Personal.dmg` on an Apple Silicon Mac (M1/M2/M3)
- **THEN** the .app is native to Apple Silicon (no Rosetta emulation required)
- **AND** dragging the .app to Applications installs the application
- **AND** launching the .app is fast (native execution)
- **AND** all UI and processing functions work correctly

#### Scenario: Application is code-signed and secure
- **WHEN** user launches the installed .app from Applications folder
- **THEN** macOS Gatekeeper recognizes the app as signed (ad-hoc or developer-signed)
- **AND** user does not see "unidentified developer" warning (with notarization)
- **AND** user can verify app integrity via codesign utility: `codesign -vv Video-Censor-Personal.app`

#### Scenario: Uninstall is simple
- **WHEN** user wants to uninstall the application
- **THEN** moving the .app to Trash removes all application files
- **AND** no configuration files or resources remain outside the .app bundle
- **AND** re-installing from fresh DMG works without conflicts

### Requirement: Windows Executable Installer (.exe)

The system SHALL provide a Windows installer executable that installs the application with system integration (Start Menu, desktop shortcut, uninstall).

#### Scenario: User downloads and installs on Windows 10
- **WHEN** user downloads `video-censor-personal-setup.exe` on Windows 10
- **THEN** double-clicking the installer launches NSIS installer wizard
- **AND** user is prompted for installation directory (default: `C:\Program Files\VideoCensorPersonal`)
- **AND** user can optionally create desktop shortcut and add to PATH
- **AND** clicking Finish completes installation
- **AND** the application is available in Start Menu: Start → Video Censor Personal
- **AND** launching from Start Menu runs the application successfully

#### Scenario: User downloads and installs on Windows 11
- **WHEN** user downloads installer on Windows 11
- **THEN** installation process is identical to Windows 10
- **AND** Start Menu integration works correctly on Windows 11
- **AND** application functions identically to Windows 10 version

#### Scenario: Uninstall removes all traces
- **WHEN** user uninstalls via Control Panel → Programs → Uninstall a program
- **THEN** selecting "Video Censor Personal" and clicking Uninstall removes:
  - Application executable and all dependencies
  - Start Menu shortcuts
  - Registry entries
  - Optional desktop shortcut
- **AND** application directory is completely removed
- **AND** re-installing works without conflicts or leftover files

#### Scenario: Application runs without Python
- **WHEN** user installs and launches application
- **THEN** Python is NOT required on the system (embedded in installer)
- **AND** no Python installation, virtual environments, or pip knowledge required
- **AND** all dependencies (PyAV, pydub, torch, transformers, etc.) bundled and functional

#### Scenario: Video playback and all features work identically to development
- **WHEN** user runs the installed Windows application
- **THEN** video playback, segment detection, audio processing, remediation all function
- **AND** video player displays video with synchronized audio
- **AND** segment list, preview editor, configuration management all work
- **AND** no performance degradation compared to pip-install version

### Requirement: Linux AppImage Installer

The system SHALL provide a portable AppImage executable for Linux that requires no installation (just download and run).

#### Scenario: User downloads and runs on Ubuntu 20.04
- **WHEN** user downloads `video-censor-personal-x86_64.AppImage` on Ubuntu 20.04
- **THEN** user makes it executable: `chmod +x video-censor-personal-x86_64.AppImage`
- **AND** user runs directly: `./video-censor-personal-x86_64.AppImage`
- **AND** the application launches and functions correctly
- **AND** no system dependencies need to be installed (Python, ffmpeg, etc.)

#### Scenario: User downloads and runs on Ubuntu 22.04
- **WHEN** user runs AppImage on Ubuntu 22.04
- **THEN** application launches and functions identically to 20.04
- **AND** AppImage automatically extracts to temporary directory and runs
- **AND** no installation to /opt or /usr/local required (portable)

#### Scenario: User downloads and runs on Fedora 34+
- **WHEN** user runs AppImage on Fedora 34 or later
- **THEN** application launches and functions correctly
- **AND** all features (video playback, detection, remediation) work
- **AND** no system-specific dependencies required

#### Scenario: Desktop integration (optional)
- **WHEN** user integrates AppImage into application menu
- **THEN** user can run: `./video-censor-personal-x86_64.AppImage --install-desktop-entry`
- **AND** application appears in Activities menu / application launcher
- **AND** user can launch from application menu by name
- **AND** application icon is displayed in launcher

#### Scenario: glibc compatibility
- **WHEN** user runs AppImage on Linux system
- **THEN** system must have glibc 2.29 or later (most distributions support this)
- **AND** AppImage bundles dependencies to minimize system requirements
- **AND** user can verify: `ldd --version` to check glibc version

### Requirement: Installer Size and Performance

The system SHALL provide installers with acceptable size and installation time for typical users.

#### Scenario: Windows installer size
- **WHEN** user downloads Windows installer
- **THEN** installer size is less than 1GB (target: 500MB-800MB with lazy-loaded models)
- **AND** installation takes less than 5 minutes on typical internet connection
- **AND** disk space used after installation is less than 2GB (accounting for models)

#### Scenario: macOS DMG size
- **WHEN** user downloads macOS DMG
- **THEN** DMG size is less than 1GB (target: 500MB-800MB with lazy-loaded models)
- **AND** installation (drag to Applications) takes seconds
- **AND** disk space used after installation is less than 2GB

#### Scenario: Linux AppImage size
- **WHEN** user downloads AppImage
- **THEN** AppImage size is less than 1GB (target: 500MB-800MB with lazy-loaded models)
- **AND** startup time is reasonable (AppImage extracts and runs, ~3-5 seconds cold start)
- **AND** disk space used when extracted is less than 2GB

### Requirement: Dependency Bundling

The system SHALL bundle all required dependencies, allowing users to run the application without external tool installation.

#### Scenario: ffmpeg is accessible without system installation
- **WHEN** application starts and attempts to play video
- **THEN** ffmpeg is available to PyAV (either bundled in PyAV wheel or vendored binary)
- **AND** application does NOT require system ffmpeg installation
- **AND** user can play video without running `apt install ffmpeg` or `brew install ffmpeg`

#### Scenario: AI models are available
- **WHEN** user runs detection or analysis features
- **THEN** models are either:
  - Pre-downloaded and bundled in installer (offline variant), OR
  - Downloaded on first use (online variant, with progress indicator)
- **AND** user is not required to manually download models
- **AND** model loading shows progress UI
- **AND** first run completes successfully

#### Scenario: Python is bundled (Windows, macOS)
- **WHEN** user launches installed application
- **THEN** Python runtime is embedded and used (user's system Python is ignored)
- **AND** no Python 3.10+ requirement on user's system
- **AND** no virtual environment setup required

### Requirement: Platform-Specific Integration

The system SHALL integrate with platform-native application launchers, menus, and conventions.

#### Scenario: macOS Finder integration
- **WHEN** user views Applications folder
- **THEN** Video Censor Personal.app appears as native application
- **AND** app icon is displayed
- **AND** application can be launched from Finder (double-click or Cmd+O)
- **AND** application can be pinned to Dock

#### Scenario: Windows Start Menu integration
- **WHEN** user opens Windows Start Menu
- **THEN** "Video Censor Personal" appears in application list (searchable)
- **AND** right-click context menu shows standard options (Pin to Taskbar, etc.)
- **AND** application can be pinned to Start Menu or taskbar

#### Scenario: Linux application menu integration
- **WHEN** user integrates AppImage via desktop entry
- **THEN** application appears in system application launcher (Activities, KDE menu, etc.)
- **AND** application name and icon are displayed
- **AND** application can be searched and launched by name

### Requirement: Integrity and Security Verification

The system SHALL provide checksums and allow users to verify installer authenticity.

#### Scenario: SHA256 checksums provided
- **WHEN** installer is released on GitHub
- **THEN** a CHECKSUMS.txt file is provided alongside installers
- **AND** CHECKSUMS.txt contains SHA256 hash for each installer:
  - `video-censor-personal-setup.exe`
  - `Video-Censor-Personal.dmg`
  - `video-censor-personal-x86_64.AppImage`
- **AND** format is standard: `<hash> <filename>`

#### Scenario: User can verify installer
- **WHEN** user downloads installer and CHECKSUMS.txt
- **THEN** user can verify integrity on their platform:
  - Windows: `certUtil -hashfile installer.exe SHA256`
  - macOS: `shasum -a 256 app.dmg`
  - Linux: `sha256sum appimage`
- **AND** user can compare output to CHECKSUMS.txt
- **AND** matching hash confirms installer was not tampered with

#### Scenario: Code signing (macOS, optional Windows)
- **WHEN** user launches application on macOS
- **THEN** application is code-signed (ad-hoc or developer-signed)
- **AND** user can verify: `codesign -vv Video-Censor-Personal.app`
- **AND** notarization optional (Phase 1: ad-hoc, Phase 2: developer account)

### Requirement: Installation and Uninstallation

The system SHALL provide clear installation and uninstallation procedures for each platform.

#### Scenario: Installation documentation provided
- **WHEN** user downloads installer
- **THEN** installation documentation (INSTALLATION_GUIDE.md) is available
- **AND** documentation includes:
  - Step-by-step instructions for each platform
  - Screenshots or video (if possible)
  - Troubleshooting tips
  - System requirements
- **AND** documentation is clear and accessible to non-technical users

#### Scenario: Uninstallation is clean
- **WHEN** user uninstalls application
- **THEN** uninstall process is platform-specific:
  - macOS: Move .app to Trash
  - Windows: Control Panel → Uninstall
  - Linux: Delete AppImage and desktop entry file
- **AND** all application files are removed
- **AND** no configuration or leftover files remain (except user's own data/configs if desired)

### Requirement: Automated Build and Release

The system SHALL automate installer creation and release via CI/CD.

#### Scenario: GitHub Actions builds installers automatically
- **WHEN** developer pushes release tag (e.g., `v1.0.0`)
- **THEN** GitHub Actions workflow triggers automatically
- **AND** workflow builds installers on appropriate runners:
  - Windows installer on windows-latest
  - macOS .app on macos-latest
  - Linux AppImage on ubuntu-latest
- **AND** all three installers build in parallel
- **AND** build completes within reasonable time (target: <30 minutes)

#### Scenario: Built installers published to release
- **WHEN** build succeeds
- **THEN** all installers are automatically uploaded to GitHub Release
- **AND** CHECKSUMS.txt is generated and uploaded
- **AND** release notes can be added manually by developer
- **AND** release is ready for distribution to users

#### Scenario: Build process reproducible
- **WHEN** developer runs build locally or via CI/CD
- **THEN** build outputs are identical (same versions, same dependencies)
- **AND** build documentation allows maintainers to build independently
- **AND** secrets (code signing certs, Apple ID) are managed securely in CI/CD
