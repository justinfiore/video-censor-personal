# Design: Cross-Platform Application Installers

## Context

video-censor-personal is currently distributed as a Python package (pip install). This requires users to:
- Have Python 3.10+ installed
- Understand pip and virtual environments
- Manually install system dependencies (ffmpeg, audio libraries)
- Download and configure AI models

This is unsuitable for non-technical users. We need native installers for each platform.

Constraints:
- Build tools must be free/open-source (NSIS, Inno Setup, PyInstaller, etc.)
- Installers must be self-contained (no external runtime or setup required)
- Code signing must be supported (macOS notarization, Windows code signing optional)
- Build process must be automatable (GitHub Actions)
- Total installer size acceptable (~500MB-1GB including models)

## Goals

**Goals:**
- Enable one-click installation for non-technical users
- Eliminate Python/pip knowledge requirement
- Provide native OS integration (launcher, app menu, file associations)
- Support automatic updates in future (version detection, launcher)
- Maintain code signing and security practices

**Non-Goals:**
- Multiple Python versions (target only 3.11+)
- Installer localization (English-only for now)
- Auto-update mechanism (deferred; installers can be auto-downloadable)
- System package managers (apt, brew, pacman) for initial release
- Windows 32-bit support

## Decisions

### 1. macOS: Native .app Bundle Strategy

**Approach:**
- Use `PyInstaller` to freeze Python + dependencies into standalone executable
- Create `.app` bundle structure (macOS standard format)
- Bundle ffmpeg binary (statically linked or via PyAV wheels)
- Code-sign and notarize the application

**Directory Structure:**
```
Video-Censor-Personal.app/
├── Contents/
│   ├── MacOS/
│   │   ├── video-censor-personal     (PyInstaller executable)
│   │   └── launcher.sh               (shell script wrapper, optional)
│   ├── Resources/
│   │   ├── icon.icns                 (application icon)
│   │   ├── ffmpeg                    (bundled binary, if needed)
│   │   └── models/                   (AI models, pre-downloaded)
│   ├── Frameworks/                   (dynamic libraries, if needed)
│   ├── Info.plist                    (application metadata)
│   └── PkgInfo
```

**Build Process:**
1. Create Python virtual environment with all dependencies
2. Run PyInstaller: freezes Python + code into standalone executable
3. Create .app bundle structure and copy executable
4. Code-sign app with developer certificate
5. Notarize with Apple (required for distribution, takes ~10-30 seconds)
6. Create DMG (disk image) for distribution

**Tools:**
- PyInstaller (free, widely used)
- `codesign` utility (built-in to macOS)
- `xcrun notarytool` (built-in to macOS)
- `appdmg` or `create-dmg` (creates DMG file for distribution)

**Code Signing & Notarization:**
- Requires Apple Developer Account ($99/year) OR Ad-Hoc signing (no notarization)
- For distribution: Use legitimate developer certificate
- Notarization: Upload to Apple for automated security check (~10-30 seconds)
- Users see trusted application (no "unidentified developer" warning)

**Target:** macOS 10.13+ (Intel and Apple Silicon, both supported)

### 2. Windows: Executable Installer Strategy

**Approach:**
- Use `NSIS` (Nullsoft Scriptable Install System) - free, open-source
- PyInstaller freezes Python + dependencies into .exe
- Create NSIS script for installer UI, registry entries, Start Menu shortcuts
- Optional: Code-signing with certificate (Windows SmartScreen reputation)

**Installation Flow:**
1. User downloads `video-censor-personal-setup.exe`
2. Double-click → NSIS installer runs
3. User prompted: installation directory (default: `C:\Program Files\VideoCensorPersonal`)
4. Installer copies executable, creates shortcuts, optionally adds to PATH
5. Finish → Application ready to run

**Directory Structure (installed):**
```
C:\Program Files\VideoCensorPersonal\
├── video-censor-personal.exe         (PyInstaller executable)
├── ffmpeg.exe                         (bundled ffmpeg binary)
├── models/                            (AI models)
├── lib/                               (Python dependencies, DLLs)
└── uninstall.exe                      (uninstaller)
```

**Features:**
- Start Menu shortcuts (Start → Video Censor Personal)
- Desktop shortcut (optional, user can choose)
- Add to PATH (optional, user can choose)
- Uninstall via Control Panel
- Registry entries for Windows integration

**Tools:**
- PyInstaller (free)
- NSIS (free, open-source, ~1MB installer overhead)
- Optional: Signtool (code-signing, requires certificate)

**Target:** Windows 10/11 64-bit

### 3. Linux: AppImage + System Package Strategy

**Approach:**
- Primary distribution: AppImage (single self-contained file, no root required)
- Secondary (future): .deb (Debian/Ubuntu) and .rpm (Fedora/RHEL)
- PyInstaller freezes Python + dependencies
- Bundle ffmpeg and all system libraries into AppImage

**Installation Flow (AppImage):**
1. User downloads `video-censor-personal-x86_64.AppImage`
2. Make executable: `chmod +x video-censor-personal-x86_64.AppImage`
3. Run directly: `./video-censor-personal-x86_64.AppImage`
4. Optional: integrate into application menu (create desktop entry)

**Tools:**
- PyInstaller (freeze Python)
- `appimagetool` (creates AppImage from directory)
- `linuxdeploy` or `linuxdeploy-plugin-appimage` (handles library bundling)

**Supported Distributions:**
- Ubuntu 20.04+ (tested primary)
- Fedora 34+
- Debian 11+
- Any glibc 2.29+ system (AppImage is portable)

**System Packages (Future):**
- `.deb` for Ubuntu/Debian via `stdeb` or `fpm`
- `.rpm` for Fedora/RHEL via `fpm` or `rpmbuild`
- Requires more build infrastructure (multiplatform build VMs)
- Deferred to Phase 2 if AppImage proves insufficient

**Target:** Linux x86_64, glibc 2.29+ (covers most modern distributions)

### 4. Dependency Bundling Strategy

**What to Bundle:**
- Python runtime (macOS: embedded, Windows: embedded, Linux: system Python assumed)
- PyAV + bundled FFmpeg (handled by PyInstaller via wheel dependencies)
- pydub, simpleaudio (Python packages, frozen by PyInstaller)
- CustomTkinter, tkinter, other UI deps (frozen by PyInstaller)
- numpy, torch, transformers, librosa (frozen by PyInstaller)
- AI models: LLaVA, CLIP, audio detection models (pre-downloaded, bundled in Resources/)

**FFmpeg Strategy:**
- Use PyAV's bundled FFmpeg (4.4.1+ included in wheels)
- Optionally add statically-linked ffmpeg binary if system version unreliable
- macOS: PyAV wheel handles it; optionally bundle system ffmpeg
- Windows: PyAV wheel handles it; optionally bundle ffmpeg.exe
- Linux: PyAV wheel handles it; linuxdeploy handles system library bundling

**Models:**
- Download at build time (ci/cd script)
- Place in `app/models/` or `app/resources/models/`
- Application loads from bundled location (relative path or resource API)

**Size Estimates:**
- Python 3.11 minimal: ~100MB (frozen)
- Dependencies (PyAV, numpy, torch, transformers, librosa): ~400-600MB
- AI models (LLaVA, CLIP, audio models): ~4-6GB total
  - **Issue**: Models are very large; consider:
    - Lazy-load models on first use (download from CDN at runtime)
    - Offer minimal model set in installer (smaller download)
    - Compress with better compression (xz, 7z)
- ffmpeg: ~50-100MB (static binary)
- **Total for installer: ~1.5-2GB** (models dominate; consider lazy-load)

**Model Handling Decision:**
- **Phase 1 (Initial Release)**: Lazy-load models at runtime (user downloads on first use)
  - Reduces installer to ~500MB-1GB
  - First run takes longer (download models from CDN)
  - Better UX for users with small drives or slow internet
  
- **Phase 2 (Bundled Models)**: Create offline installer with pre-bundled models (~2GB+)
  - For users with offline access or stable internet
  - Separate "offline" installer builds

**Recommendation**: Phase 1 with lazy-load, Phase 2 for offline variant.

### 5. Build & Distribution Infrastructure

**Build Process (Automated via GitHub Actions):**

```
trigger: Release push or manual workflow dispatch
  |
  ├─→ macOS build (runs on macOS runner)
  │   ├─ PyInstaller freeze
  │   ├─ Create .app bundle
  │   ├─ Code-sign (requires cert in secrets)
  │   ├─ Notarize (requires Apple ID in secrets)
  │   ├─ Create DMG
  │   └─ Upload to release
  |
  ├─→ Windows build (runs on Windows runner)
  │   ├─ PyInstaller freeze
  │   ├─ Create NSIS installer
  │   ├─ Optional code-sign (requires cert)
  │   └─ Upload to release
  |
  └─→ Linux build (runs on Linux runner)
      ├─ PyInstaller freeze
      ├─ Create AppImage via linuxdeploy
      └─ Upload to release
```

**Distribution:**
- GitHub Releases (primary)
- Optional: Website downloads
- Future: Auto-update mechanism (launcher checks version)

### 6. Security Considerations

**Code Signing:**
- macOS: Required for Gatekeeper (notarization adds ~$99 dev account cost or ad-hoc free)
- Windows: Optional but recommended (builds reputation with SmartScreen)
- Linux: Not applicable (AppImage integrity via hash)

**Installer Verification:**
- Provide SHA256 checksums on releases
- Users can verify: `sha256sum video-censor-personal-x86_64.AppImage`

**Notarization (macOS):**
- Apple scans app for malware/security issues
- Required for non-developer distribution (avoid "unidentified developer" warning)
- Takes 10-30 seconds, automated in CI/CD
- Requires Apple Developer Account

### 7. Version & Update Strategy

**Version Reporting:**
- Store version in `__version__.py` or similar
- Launcher script checks: `./video-censor-personal --version`
- Future: launcher can check GitHub releases for updates

**Rollback:**
- Users can keep multiple installer versions
- Each installer is self-contained (no shared system state)

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|-----------|
| **macOS notarization required** | Users can't run app on Big Sur+ without notarization | Requires $99/year Apple Dev account (acceptable cost) or use ad-hoc free signing (single-dev, loses notarization) |
| **Model size bloat (4-6GB)** | Installers too large (user can't download) | Phase 1: Lazy-load models at runtime; Phase 2: Separate offline variant |
| **Platform-specific bugs** | Installer breaks on specific OS/version combo | Comprehensive testing matrix (macOS Intel/M1, Windows 10/11, Ubuntu 20.04/22.04) |
| **Code signing cert management** | Lost/expired cert breaks build pipeline | Store cert in GitHub Secrets with backup; rotate annually |
| **Windows SmartScreen reputation** | Windows warns "unknown publisher" on first install | Build reputation over time with legitimate cert; users can bypass easily |
| **Linux glibc compatibility** | AppImage fails on older glibc versions | Require glibc 2.29+; document minimum distro versions |
| **FFmpeg binary conflicts** | Bundled ffmpeg conflicts with system ffmpeg | Use absolute path to bundled version, or LD_LIBRARY_PATH isolation |

## Migration Plan

### Phase 1: MVP Installers (Windows + macOS)
- PyInstaller setup for both platforms
- NSIS installer for Windows
- .app bundle for macOS (ad-hoc signing, no notarization)
- Lazy-load AI models (download at runtime)
- Manual builds (no CI/CD initially)
- GitHub Releases distribution

### Phase 2: Production Hardening (All Platforms + CI/CD)
- macOS notarization automation (requires dev account)
- Windows code-signing (optional but recommended)
- Linux AppImage build
- GitHub Actions CI/CD automation
- Comprehensive testing on all platforms
- Documentation for users and maintainers

### Phase 3: Advanced Features (Optional)
- .deb and .rpm system packages
- Auto-update mechanism
- Bundled models variant (offline installer)
- Platform-specific icons/branding

## Success Criteria

- [ ] Windows installer can install and launch application successfully
- [ ] macOS .app can install and launch application successfully (Intel + Apple Silicon)
- [ ] Linux AppImage can run on Ubuntu 20.04, 22.04, Fedora 34+
- [ ] Installer size acceptable (<1GB for Phase 1 with lazy-load models)
- [ ] Installation takes <5 minutes on typical internet connection
- [ ] Uninstall removes all application files completely
- [ ] No external tools or Python knowledge required by end-user
- [ ] Application appears as native app (launcher, taskbar, app menu)
- [ ] Code-signing and notarization working (macOS)
- [ ] SHA256 checksums provided for all releases
- [ ] CI/CD builds and distributes installers automatically
