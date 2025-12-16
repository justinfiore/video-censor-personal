# Design: Native MP4 Chapter Writing at Container Level

## Context
Sample MP4 files contain properly embedded chapters using native MP4 atoms with:
- `time_base`: Fractional representation (e.g., "1/1000" = milliseconds)
- `start`/`end`: Integer values in timebase units (e.g., 13901 ms = 13.901 seconds)
- `tags.title`: Chapter name (e.g., "Video", "Advertisement")

Current FFMETADATA approach works but is marked unreliable. Research into sample files shows native MP4 chapters are the proper solution.

## Goals
- Implement native MP4 chapter embedding that matches container-level structure
- Make MP4 chapters as reliable as MKV (remove "deprecated" status)
- Support equal quality for both MKV and MP4 output formats
- Validate implementation against sample files

## Non-Goals
- Automatic format conversion (user specifies output format)
- Transcoding (re-muxing only, preserve codecs)
- Support for non-chapter MP4 metadata

## Decisions

### Decision 1: Chapter Writing Method (Native MP4 Only)
**What**: Use ffmpeg with `mov_text` codec to generate native MP4 chapter atoms. No FFMETADATA fallback.

**Why**:
- ffmpeg supports native MP4 chapter atoms via subtitle track
- `mov_text` is standard MP4 subtitle codec for chapters
- No external library dependencies
- Same tool already used for extraction and validation
- Native-only approach forces correct implementation and removes technical debt

**Alternatives considered**:
- Direct atom manipulation (mp4box library) - adds dependency, overkill
- FFMETADATA format (current) - unreliable, marked deprecated, we are replacing it
- FFMETADATA as fallback - rejected; native-only forces correct implementation
- Python MP4 libraries - adds dependencies, not widely available

### Decision 2: Timebase Handling
**What**: Use millisecond timebase (1/1000) matching sample files.

**Why**:
- ffprobe output uses 1/1000 timebase for MP4 chapters
- Consistent with sample files structure
- Ffmpeg handles conversion automatically
- Preserves precision for accurate seeking

### Decision 3: Validation Strategy
**What**: Validate generated chapters using ffprobe against sample files.

**Why**:
- ffprobe is already available (comes with ffmpeg)
- Can verify time_base, start, end, and tags match structure
- Tests can be automated to ensure reliability

### Decision 4: FFmpeg Version Requirement
**What**: Require ffmpeg >= 8.0 for native MP4 chapter support. Fail with clear error message if version is insufficient.

**Why**:
- ffmpeg 8.0+ has stable native MP4 container atom support
- Earlier versions have limited or unreliable mov_text implementation
- Clear version requirement prevents silent failures with older ffmpeg versions
- User gets actionable error message with installation instructions

### Decision 5: Deprecation Removal
**What**: Remove warnings about MP4 unreliability once native method is validated.

**Why**:
- Native MP4 chapters work reliably in all players
- Matches sample file structure exactly
- Enables equal support for MKV and MP4

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| ffmpeg chapter atom generation differs from samples | Validate generated output against sample files; test in VLC, Plex, Windows Media Player |
| User has ffmpeg < 8.0 installed | Version check fails early with clear error message and installation instructions |
| Removing FFMETADATA fallback leaves no escape hatch | Native MP4 is the right solution; clear error messages guide users to install ffmpeg 8.0+ |
| Performance impact on large files | mux-only operation (no re-encoding), fast on modern systems |
| **ffmpeg MKV→MP4 conversion forces first chapter to 0.0** | **Documented limitation; chapters remain accurate and playable in all media players. Padding chapters added when merging with existing chapters to preserve all timing.** |

## Migration Plan

1. Analyze sample file structure (Boston Blue, Shifting Gears)
2. Implement new MP4 chapter writing method using ffmpeg mov_text
3. Create validation tests using ffprobe to verify atom structure
4. Replace current FFMETADATA implementation with native method
5. Remove deprecation warnings and update documentation
6. Test in multiple players (VLC, Plex, Kodi) to ensure compatibility
7. Verify existing chapters are preserved and merged correctly

## Open Questions (RESOLVED)

1. **What ffmpeg parameters produce MP4 chapters matching sample files?** 
   - Action: Research and test during implementation to discover correct parameters
   - Target: Match sample file structure with time_base="1/1000", integer start/end in milliseconds, tags.title with chapter names
   - Validation: Use ffprobe to verify generated output structure

2. **Should we keep FFMETADATA as fallback if native method fails?** 
   - Decision: No. Implement native MP4 chapters only.
   - Rationale: FFMETADATA is the old unreliable approach we're replacing. Going native-only forces correct implementation and removes technical debt.
   - Approach: If native method fails, raise error with clear message (no silent fallback)

3. **How to handle differences between ffmpeg versions?**
   - Decision: Require ffmpeg >= 8.0 (minimum version supporting native MP4 container atoms)
   - Implementation: Add version check before chapter writing; fail with clear message if version is insufficient
   - User message: "ffmpeg 8.0 or later is required for native MP4 chapter support. Install newer version via: brew install ffmpeg (macOS) or apt install ffmpeg (Linux)"
