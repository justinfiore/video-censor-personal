# Implementation Tasks: Fix Chapter Writing with MKV Support

## 1. Implement MKV Chapter Generation and Writing
- [x] 1.1 Create function `_generate_chapter_xml()` to convert chapters to OGG Theora XML format
- [x] 1.2 Implement `write_skip_chapters_to_mkv()` using mkvmerge for reliable chapter embedding
- [x] 1.3 Add mkvmerge availability check with clear error message for missing tool
- [x] 1.4 Test XML generation with various chapter names (special chars, long names, confidence values)

## 2. Update Main Chapter Writing Function
- [x] 2.1 Refactor `write_skip_chapters_to_mp4()` to dispatch based on output file extension
- [x] 2.2 Detect `.mkv` extension and route to `write_skip_chapters_to_mkv()`
- [x] 2.3 Keep MP4 path for backward compatibility with degraded-support warning
- [x] 2.4 Update docstring to explain format detection and recommendations

## 3. Handle Edge Cases
- [x] 3.1 Preserve existing chapters when writing MKV (read from input, merge with skip chapters)
- [x] 3.2 Handle case where input format differs from output format (e.g., MP4 input → MKV output)
- [x] 3.3 Graceful failure: if mkvmerge unavailable for MKV, log error and continue (JSON still written)

## 4. Update Configuration and Documentation
- [x] 4.1 Update config examples to use `.mkv` extension for chapter output
- [x] 4.2 Update inline comments/docstrings to clarify MKV is preferred format
- [x] 4.3 Add warning message for MP4 output explaining chapter limitations
- [x] 4.4 Document mkvmerge requirement and installation instructions

## 5. Testing
- [x] 5.1 Test MKV chapter writing with various detection scenarios
- [x] 5.2 Test chapter merging with existing chapters (both MKV and MP4 input)
- [x] 5.3 Test MP4 output path with warning
- [x] 5.4 Test missing mkvmerge graceful failure
- [x] 5.5 Verify chapters are visible in VLC player

## 6. Update Specification
- [x] 6.1 Modify spec.md to reflect MKV as recommended format
- [x] 6.2 Update chapter requirements to explain MP4 limitations vs MKV advantages
- [x] 6.3 Document format detection behavior
