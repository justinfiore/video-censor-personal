# Implementation Tasks: Cross-Platform Application Installers

## Phase 1: Windows Installer (NSIS)

### 1. PyInstaller Setup & Windows Executable Build

- [ ] 1.1 Install PyInstaller and analyze project dependencies
- [ ] 1.2 Create PyInstaller spec file (.spec): entry point, hidden imports, excluded modules
- [ ] 1.3 Build Windows executable: `pyinstaller video-censor-personal.spec --onefile`
- [ ] 1.4 Test executable on clean Windows machine (no Python installed)
- [ ] 1.5 Verify all dependencies bundled: PyAV, pydub, simpleaudio, torch, transformers, etc.
- [ ] 1.6 Verify ffmpeg accessible to PyAV (bundled or via system PATH)
- [ ] 1.7 Verify AI models loading behavior (lazy-load from disk or download at runtime)
- [ ] 1.8 Benchmark executable size and startup time
- [ ] 1.9 Document PyInstaller configuration and hidden imports for future maintainers

### 2. NSIS Installer Script

- [ ] 2.1 Install NSIS (open-source installer creator)
- [ ] 2.2 Create NSIS script (.nsi file) with installer UI
- [ ] 2.3 Define installation directory options (default: `C:\Program Files\VideoCensorPersonal`)
- [ ] 2.4 Implement copy phase: copy executable, ffmpeg binary, models, libraries
- [ ] 2.5 Create Start Menu shortcuts (Video Censor Personal, Uninstall)
- [ ] 2.6 Create desktop shortcut option (user checkbox during install)
- [ ] 2.7 Add PATH option (optional): allow user to add app to system PATH
- [ ] 2.8 Create registry entries: Windows integration, uninstall information
- [ ] 2.9 Implement uninstaller: removes all files, registry entries, shortcuts
- [ ] 2.10 Create license display page in installer (show LICENSE.md or similar)

### 3. Windows Installer Testing & Packaging

- [ ] 3.1 Build NSIS installer (.exe file)
- [ ] 3.2 Test installer on clean Windows 10 machine (admin and non-admin user)
- [ ] 3.3 Test installer on Windows 11 machine
- [ ] 3.4 Verify shortcuts work: Start Menu → Video Censor Personal launches app
- [ ] 3.5 Verify desktop shortcut works (if created)
- [ ] 3.6 Verify uninstaller works: removes all files, not cluttering registry
- [ ] 3.7 Test upgrade scenario: run installer over existing installation
- [ ] 3.8 Verify all UI works: segment list, video playback, preview editor (if video playback complete)
- [ ] 3.9 Create SHA256 checksum for installer
- [ ] 3.10 Document Windows installation process for users

---

## Phase 1: macOS Installer (.app Bundle)

### 4. PyInstaller Setup & macOS Executable Build

- [ ] 4.1 Create PyInstaller spec file for macOS (same core spec as Windows, platform-specific)
- [ ] 4.2 Build macOS executable on macOS machine: `pyinstaller video-censor-personal.spec`
- [ ] 4.3 Test executable on Intel Mac (no Python installed)
- [ ] 4.4 Test executable on Apple Silicon Mac (M1/M2/M3) (no Python installed)
- [ ] 4.5 Verify all dependencies bundled correctly (PyAV, pydub, simpleaudio, torch, etc.)
- [ ] 4.6 Verify ffmpeg accessible (bundled or system)
- [ ] 4.7 Verify AI models loading behavior
- [ ] 4.8 Benchmark executable size and startup time
- [ ] 4.9 Document PyInstaller macOS-specific quirks (Tkinter with CustomTkinter, audio libraries)

### 5. macOS .app Bundle Creation

- [ ] 5.1 Create .app bundle directory structure: `Contents/MacOS/`, `Contents/Resources/`, etc.
- [ ] 5.2 Copy PyInstaller executable into `Contents/MacOS/video-censor-personal`
- [ ] 5.3 Create launcher script (optional): shell wrapper in `Contents/MacOS/launcher.sh`
- [ ] 5.4 Create Info.plist file: app metadata (name, version, bundle identifier, executable name)
- [ ] 5.5 Create PkgInfo file: standard macOS format (APPL + bundle identifier)
- [ ] 5.6 Copy icon file (icon.icns) into `Contents/Resources/`
- [ ] 5.7 Copy ffmpeg binary (if needed) into `Contents/Resources/ffmpeg`
- [ ] 5.8 Create `Contents/Resources/models/` directory placeholder
- [ ] 5.9 Verify .app bundle structure is correct (can be opened in Finder)

### 6. macOS Code Signing & Ad-Hoc Signing

- [ ] 6.1 Create development certificate (Ad-Hoc, free) for signing
  - Or: Use Apple Developer Account certificate ($99/year) for distribution
- [ ] 6.2 Code-sign the executable and all dependencies: `codesign -s - Video-Censor-Personal.app`
- [ ] 6.3 Verify signature: `codesign -vv Video-Censor-Personal.app`
- [ ] 6.4 Handle entitlements if needed (disk access, audio input, etc.): create entitlements.plist
- [ ] 6.5 Test app launches on Intel Mac (watch for "unidentified developer" warning, expected for ad-hoc)
- [ ] 6.6 Test app launches on Apple Silicon Mac
- [ ] 6.7 Document signing process and limitations of ad-hoc vs. developer certificate

### 7. macOS Notarization (Optional for Phase 1, Required for Phase 2)

- [ ] 7.1 Prepare for notarization: add "hardened runtime" entitlement to app
- [ ] 7.2 Create zip for notarization: `ditto -c -k --sequesterRsrc Video-Censor-Personal.app app.zip`
- [ ] 7.3 Submit for notarization (requires Apple Developer Account): `xcrun notarytool submit app.zip --apple-id <id> --password <password> --team-id <id>`
- [ ] 7.4 Poll notarization status (takes 10-30 seconds)
- [ ] 7.5 Staple notarization ticket to app: `xcrun stapler staple Video-Censor-Personal.app`
- [ ] 7.6 Test notarized app: should launch without "unidentified developer" warning
- [ ] 7.7 Document notarization process and Apple Developer Account requirement

### 8. macOS DMG Creation & Distribution

- [ ] 8.1 Create DMG (disk image) from .app bundle using `appdmg` or `create-dmg`
- [ ] 8.2 DMG should include: .app and "Applications" folder shortcut (drag-drop install)
- [ ] 8.3 Add custom background image (optional branding)
- [ ] 8.4 Test DMG on macOS: double-click → open → drag app to Applications
- [ ] 8.5 Verify installed app launches correctly from Applications folder
- [ ] 8.6 Create SHA256 checksum for DMG
- [ ] 8.7 Document macOS installation process for users

---

## Phase 1: Testing & Release Preparation

### 9. Model & Configuration Management

- [ ] 9.1 Decide model loading strategy: lazy-load at runtime vs. bundled
- [ ] 9.2 If lazy-load: implement model downloader in app (first-run setup, progress UI)
- [ ] 9.3 If bundled: download models during installer build, include in Resources
- [ ] 9.4 Create default configuration file: bundled in app resources
- [ ] 9.5 Verify app can find configuration and models from bundled location
- [ ] 9.6 Test first-run experience: new user downloads installer, runs, uses app (including model loading)

### 10. Cross-Platform Integration Testing

- [ ] 10.1 Create test plan: features to verify on each platform (video playback, segment list, previews)
- [ ] 10.2 Test Windows installer on clean Windows 10 machine (admin and user)
- [ ] 10.3 Test Windows installer on Windows 11 machine
- [ ] 10.4 Test macOS .app on Intel Mac (at least one OS version: 10.13+, 11.x, 12.x, 13.x)
- [ ] 10.5 Test macOS .app on Apple Silicon Mac (M1, M2, or M3)
- [ ] 10.6 Test all major features work identically on Windows and macOS
- [ ] 10.7 Document any platform-specific quirks or workarounds
- [ ] 10.8 Create test report: features tested, OS versions, results

### 11. Checksum & Release Documentation

- [ ] 11.1 Generate SHA256 checksums for all installers (Windows .exe, macOS DMG)
- [ ] 11.2 Create CHECKSUMS.txt file with all hashes and installer names
- [ ] 11.3 Create INSTALLATION_GUIDE.md: step-by-step for Windows and macOS users
- [ ] 11.4 Create TROUBLESHOOTING.md: common issues and solutions
- [ ] 11.5 Create BUILD_INSTRUCTIONS.md: how maintainers build installers locally
- [ ] 11.6 Document version numbering scheme and how to update installer versions

---

## Phase 2: Linux AppImage & CI/CD Automation

### 12. PyInstaller Setup & Linux Executable Build

- [ ] 12.1 Build PyInstaller executable on Linux (using same .spec, platform-specific tweaks)
- [ ] 12.2 Test executable on Ubuntu 20.04 machine (no Python installed)
- [ ] 12.3 Test executable on Ubuntu 22.04 machine
- [ ] 12.4 Test executable on Fedora 34+ machine
- [ ] 12.5 Verify all dependencies bundled (verify glibc version compatibility)
- [ ] 12.6 Verify ffmpeg accessible (bundled or system)
- [ ] 12.7 Verify AI models loading
- [ ] 12.8 Benchmark executable size and startup time

### 13. Linux AppImage Creation

- [ ] 13.1 Install linuxdeploy and linuxdeploy-plugin-appimage tools
- [ ] 13.2 Create AppDir directory structure (standard AppImage format)
- [ ] 13.3 Copy PyInstaller executable, dependencies, models into AppDir
- [ ] 13.4 Create `AppDir/AppRun` script: launcher that sets environment and runs executable
- [ ] 13.5 Create desktop entry file (`.desktop`): app metadata for system integration
- [ ] 13.6 Create AppImage using linuxdeploy: `linuxdeploy-x86_64.AppImage --appdir=AppDir --output=appimage`
- [ ] 13.7 Make AppImage executable: `chmod +x video-censor-personal-x86_64.AppImage`
- [ ] 13.8 Test AppImage: download, make executable, run on Ubuntu 20.04, 22.04, Fedora 34+
- [ ] 13.9 Verify desktop integration: app appears in application menu, can be launched from there
- [ ] 13.10 Benchmark AppImage size
- [ ] 13.11 Create SHA256 checksum for AppImage

### 14. Linux Desktop Integration

- [ ] 14.1 Create desktop entry file (.desktop): defines how app appears in application menu
- [ ] 14.2 Include app icon in AppImage (referenced in .desktop entry)
- [ ] 14.3 Test: AppImage extracts to temporary directory, installs desktop entry
- [ ] 14.4 Test: app appears in Activities/application menu on Ubuntu
- [ ] 14.5 Test: app appears in application menu on Fedora (GNOME or KDE)
- [ ] 14.6 Document AppImage installation for Linux users

---

## Phase 2: GitHub Actions CI/CD

### 15. Windows Build Automation

- [ ] 15.1 Create `.github/workflows/build-windows.yml` workflow
- [ ] 15.2 Trigger: on release push or manual workflow dispatch
- [ ] 15.3 Runner: windows-latest
- [ ] 15.4 Steps:
  - [ ] 15.4.1 Checkout code
  - [ ] 15.4.2 Setup Python 3.11+
  - [ ] 15.4.3 Install PyInstaller, NSIS, dependencies
  - [ ] 15.4.4 Run PyInstaller build
  - [ ] 15.4.5 Build NSIS installer
  - [ ] 15.4.6 Generate SHA256 checksum
  - [ ] 15.4.7 Upload artifact to GitHub Releases
- [ ] 15.5 Test workflow: trigger manually, verify installer builds successfully
- [ ] 15.6 Document workflow for maintainers

### 16. macOS Build Automation

- [ ] 16.1 Create `.github/workflows/build-macos.yml` workflow
- [ ] 16.2 Trigger: on release push or manual workflow dispatch
- [ ] 16.3 Runner: macos-latest (or macos-12 for Intel support)
- [ ] 16.4 Steps:
  - [ ] 16.4.1 Checkout code
  - [ ] 16.4.2 Setup Python 3.11+
  - [ ] 16.4.3 Install PyInstaller, appdmg, dependencies
  - [ ] 16.4.4 Run PyInstaller build
  - [ ] 16.4.5 Create .app bundle structure
  - [ ] 16.4.6 Ad-hoc code-sign (Phase 1) or dev certificate sign (Phase 2)
  - [ ] 16.4.7 Create DMG
  - [ ] 16.4.8 Generate SHA256 checksum
  - [ ] 16.4.9 Upload artifact to GitHub Releases
- [ ] 16.5 Optional (Phase 2): Add notarization step with Apple Developer Account
  - [ ] 16.5.1 Store Apple ID and password in GitHub Secrets
  - [ ] 16.5.2 Notarize app before creating DMG
  - [ ] 16.5.3 Staple notarization ticket
- [ ] 16.6 Test workflow: trigger manually, verify .app builds successfully
- [ ] 16.7 Document workflow and notarization setup

### 17. Linux Build Automation

- [ ] 17.1 Create `.github/workflows/build-linux.yml` workflow
- [ ] 17.2 Trigger: on release push or manual workflow dispatch
- [ ] 17.3 Runner: ubuntu-latest
- [ ] 17.4 Steps:
  - [ ] 17.4.1 Checkout code
  - [ ] 17.4.2 Setup Python 3.11+
  - [ ] 17.4.3 Install PyInstaller, linuxdeploy, dependencies
  - [ ] 17.4.4 Run PyInstaller build
  - [ ] 17.4.5 Create AppDir structure
  - [ ] 17.4.6 Build AppImage
  - [ ] 17.4.7 Generate SHA256 checksum
  - [ ] 17.4.8 Upload artifact to GitHub Releases
- [ ] 17.5 Test workflow: trigger manually, verify AppImage builds successfully
- [ ] 17.6 Document workflow for maintainers

### 18. Multi-Platform Automated Release

- [ ] 18.1 Create `.github/workflows/release.yml` master workflow
- [ ] 18.2 Workflow triggers Windows, macOS, Linux builds in parallel
- [ ] 18.3 Collects checksums and creates CHECKSUMS.txt
- [ ] 18.4 Creates GitHub Release with all installers and checksums
- [ ] 18.5 Optional: Posts release announcement in README or releases page
- [ ] 18.6 Test full workflow: commit version tag, trigger release, verify all installers upload

---

## Phase 2: Security & Code Signing

### 19. Windows Code Signing (Optional)

- [ ] 19.1 Research code signing options: self-signed (free but warns), or purchased certificate
- [ ] 19.2 Decision: ad-hoc signing (free, no reputation) or purchased certificate (~$100-300/year)
- [ ] 19.3 If purchased: store certificate in GitHub Secrets
- [ ] 19.4 Integrate code-signing into Windows CI/CD: sign executable and installer
- [ ] 19.5 Test signed installer: verify no SmartScreen warning (takes time to build reputation)
- [ ] 19.6 Document code-signing process and certificate management

### 20. Installer Verification Documentation

- [ ] 20.1 Create VERIFY.md: explains how users verify installer integrity via SHA256
- [ ] 20.2 Provide commands for each platform:
  - Windows: `certUtil -hashfile installer.exe SHA256`
  - macOS: `shasum -a 256 app.dmg`
  - Linux: `sha256sum appimage`
- [ ] 20.3 Document where to find official checksums (CHECKSUMS.txt in release)
- [ ] 20.4 Recommend verification before installation

---

## Phase 2: Advanced Features (Optional)

### 21. System Package Creation (.deb, .rpm)

- [ ] 21.1 Evaluate package tools: `fpm` (universal) vs. platform-specific tools
- [ ] 21.2 Decision: use `fpm` for simplicity (one tool, multiple output formats)
- [ ] 21.3 Create .deb package (Debian/Ubuntu)
- [ ] 21.4 Create .rpm package (Fedora/RHEL)
- [ ] 21.5 Test packages on respective distros
- [ ] 21.6 Publish to package repositories (future: PPA for Ubuntu, COPR for Fedora)

### 22. Auto-Update Mechanism (Deferred)

- [ ] 22.1 Design auto-update flow: launcher checks GitHub releases for new version
- [ ] 22.2 Implement version check: `app --version` returns semantic version
- [ ] 22.3 Implement update notification: "New version available. Download from [link]"
- [ ] 22.4 Test auto-update detection on all platforms
- [ ] 22.5 Document how users can disable auto-checks if desired

### 23. Bundled Models Variant (Offline Installer)

- [ ] 23.1 Create separate installer build: includes pre-downloaded AI models
- [ ] 23.2 Build differs from Phase 1: models bundled instead of lazy-loaded
- [ ] 23.3 Expect larger installer size (~1.5-2GB) due to models
- [ ] 23.4 Create offline variant builds in CI/CD (separate workflow or flag)
- [ ] 23.5 Test offline installer: works without internet on first run
- [ ] 23.6 Document offline vs. online variants for users

---

## Phase 3: Maintenance & User Support

### 24. Documentation & User Guides

- [ ] 24.1 Create INSTALLATION_GUIDE.md (comprehensive, with screenshots if possible)
- [ ] 24.2 Create TROUBLESHOOTING.md (FAQs, common errors and solutions)
- [ ] 24.3 Create UNINSTALL.md (how to cleanly remove on each platform)
- [ ] 24.4 Create BUILD_INSTRUCTIONS.md (for maintainers, how to build locally)
- [ ] 24.5 Create RELEASE_PROCESS.md (step-by-step for creating new releases)
- [ ] 24.6 Update README.md with download links and platform-specific notes

### 25. Installer Maintenance & Testing

- [ ] 25.1 Establish testing checklist for each release (functional tests on each platform)
- [ ] 25.2 Set up test matrix: Windows 10/11, macOS Intel/M1/M2, Ubuntu 20.04/22.04
- [ ] 25.3 Create automation: pre-release testing script (smoke tests, basic UI flows)
- [ ] 25.4 Monitor user feedback: GitHub Issues for installer-related problems
- [ ] 25.5 Create patch process: hotfix for installer issues without full rebuild

### 26. Final Documentation & Handoff

- [ ] 26.1 Review design.md decisions: all implemented correctly
- [ ] 26.2 Verify success criteria met (all installer types working, UI/UX seamless)
- [ ] 26.3 Update AGENTS.md with installer maintenance tips
- [ ] 26.4 Create CONTRIBUTING.md section on installer development
- [ ] 26.5 Archive this change: move to openspec/changes/archive/
