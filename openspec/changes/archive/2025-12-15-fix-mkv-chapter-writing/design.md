# Design: MKV Chapter Writing Implementation

## Context
Chapter writing with MP4 via ffmpeg's FFMETADATA format is unreliable. MP4 has limited chapter support in the spec. MKV (Matroska) format has robust, native chapter support in XML format that works consistently.

## Goals
- Implement reliable chapter writing using MKV format
- Support both MKV and MP4 output formats (MKV recommended, MP4 with degraded support)
- Clear user guidance on format choice and chapter visibility
- Handle edge cases: no mkvmerge tool, format conversions

## Non-Goals
- Automatic format conversion (user must specify output format)
- Transcoding to MKV (re-muxing only, no codec changes)

## Decisions

### Decision 1: Use mkvmerge for MKV Chapter Writing
**What**: Use `mkvmerge` tool (part of mkvtoolnix) for MKV chapter embedding instead of ffmpeg FFMETADATA.

**Why**: 
- mkvmerge natively supports Matroska chapters in XML format
- Chapters are properly embedded in MKV spec and visible in all players
- More reliable and faster than ffmpeg metadata mapping

**Alternatives considered**:
- Continue with ffmpeg FFMETADATA (current approach) - unreliable with MP4
- Use ffmpeg with re-encoding - slow, unnecessary codec changes
- Use Python libraries to write MKV directly - adds dependency, reimplements mkvmerge

### Decision 2: Detect Format from File Extension
**What**: Detect output format (MKV vs MP4) from file extension and use appropriate method.

**Why**: User explicitly specifies output path; extension determines handling strategy.

**Alternatives considered**:
- Add config option for format - more complex, user confusion
- Auto-convert to MKV - breaks expectations for user-specified format

### Decision 3: Keep MP4 Support with Clear Warning
**What**: Continue supporting MP4 with explicit warnings about chapter reliability.

**Why**: 
- Users may have workflow constraints requiring MP4
- Clear warning lets user make informed decision
- Graceful degradation

**Alternatives considered**:
- Drop MP4 support entirely - breaks existing workflows
- Auto-convert to MKV - violates user file path expectation

### Decision 4: Chapters XML Format for MKV
**What**: Generate chapters in OGG Theora XML format used by mkvmerge.

**Why**: 
- Standard format for mkvmerge
- Well-defined, simple structure
- No dependency on custom formatting

Example structure:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<Chapters>
  <EditionEntry>
    <ChapterAtom>
      <ChapterTimeStart>00:00:00.000</ChapterTimeStart>
      <ChapterTimeEnd>00:00:05.000</ChapterTimeEnd>
      <ChapterDisplay>
        <ChapterString>skip: Nudity [92%]</ChapterString>
      </ChapterDisplay>
    </ChapterAtom>
  </EditionEntry>
</Chapters>
```

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| `mkvmerge` not installed | Detect and provide clear install instructions; degrade gracefully |
| Large file processing slow | mkvmerge is fast (re-muxing), not re-encoding |
| User confusion about format choice | Clear documentation, examples, warnings |
| Existing MP4 workflows break | MP4 still supported with warnings; user controls output format |

## Migration Plan

1. Implement MKV chapter writing with `mkvmerge`
2. Detect output format from file extension
3. For MKV: use mkvmerge (reliable)
4. For MP4: use existing ffmpeg method with strong warning
5. Update config examples to show `.mkv` extension
6. Update documentation to explain format choice

## Open Questions

1. Should we require mkvmerge or make it optional? → Make optional with clear error message
2. Should we auto-copy chapters for MP4 even if writing fails? → Log warning but continue (graceful degradation)
3. Should we support re-muxing to MKV on-the-fly if user provides .mp4? → No, respect user's format choice
