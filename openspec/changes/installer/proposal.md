# Change: Create Cross-Platform Application Installers

## Why

Currently, video-censor-personal is distributed as a Python package requiring users to have Python, pip, and dependencies installed manually. This creates friction:
- Non-technical users cannot easily install the application
- Platform-specific dependency management is confusing (system ffmpeg, PyAV wheels, audio libraries, etc.)
- Users expect a self-contained installer they can download and run

We need to create platform-specific installers that bundle all dependencies and provide seamless installation:
- **macOS**: Native .app bundle (double-click to install, Finder integration)
- **Windows**: Executable installer (NSIS, Inno Setup, or similar free tool)
- **Linux**: AppImage or system package (portable, self-contained)

Each platform installer must:
1. Bundle all dependencies (Python, ffmpeg, PyAV, pydub, simpleaudio, UI libraries, models)
2. Hide implementation details from users (no Python/pip knowledge required)
3. Provide clean installation path (Downloads → Run → Use)
4. Support uninstall/cleanup
5. Enable future updates (launcher script, version detection)

## What Changes

- **Create macOS .app bundle** with embedded Python runtime, ffmpeg, and all dependencies
  - Target: macOS 10.13+ (Intel and Apple Silicon)
  - Deliverable: `Video-Censor-Personal.app` (code-signed, notarized for security)
  - Launch method: Native Cocoa app wrapper or shell script launcher

- **Create Windows installer** using free open-source installer tool (NSIS or Inno Setup)
  - Target: Windows 10/11 (64-bit)
  - Deliverable: `video-censor-personal-setup.exe`
  - Features: Add to PATH, desktop shortcut, Start Menu entry, uninstall support

- **Create Linux packaging** with multiple distribution options
  - Target: Ubuntu 20.04+, Fedora 34+, other glibc-based systems
  - Deliverable: AppImage (portable, single file) and/or system package (.deb, .rpm)
  - Features: No root required, launcher icon, standard application menu integration

- **Dependency bundling strategy**: All packages compiled/bundled into installer
  - FFmpeg: Vendored statically-linked binary (or via PyAV wheels)
  - Python runtime: Embedded (Windows, macOS), system Python (Linux)
  - Python dependencies: Frozen via PyInstaller or similar tool
  - Models: Pre-downloaded during build, bundled in app

- **Build automation**: Create scripts to automate installer creation
  - GitHub Actions CI/CD for building on each platform
  - Code signing and notarization (macOS)
  - Distribution channels (GitHub Releases, website)

## Impact

- **Affected specs**: `desktop-ui`, `project-foundation`
- **Affected code**:
  - New files: Build scripts, installer config, launcher code
  - `setup.py` or `pyproject.toml` (packaging configuration)
  - GitHub Actions workflows
  - Root directory: Installer templates, build instructions
- **Breaking changes**: None (installers are additive; pip install still works)
- **New dependencies** (build-time only):
  - `PyInstaller` (freezes Python + dependencies into executable)
  - NSIS or Inno Setup (Windows installer tool)
  - `appdmg` or similar (macOS app bundling)
  - `linuxdeploy` or similar (Linux AppImage creation)
  - Code signing tools (macOS)
- **Removed dependencies**: None
- **Platform-specific concerns**:
  - macOS code signing and notarization process
  - Windows SmartScreen reputation
  - Linux glibc compatibility
  - File permissions and directory structure per platform

## Goals

1. Users can install and run the application without Python knowledge
2. Single-command installation per platform (download and run)
3. Application appears as native app in system (launcher, taskbar, app menu)
4. All dependencies bundled (no external tool requirement)
5. Clean uninstall removes all application files
6. Future updates can be delivered via same installer mechanism
7. Build process is automated and reproducible
8. Installers can be code-signed and verified

## Status

This is a foundational change that enables distribution to non-technical users. It does not depend on video playback implementation but is complementary to it. Can proceed in parallel with video playback work or after.
