# Implementation Tasks: Update Video Metadata on Remediation

## 1. Design & Preparation
- [ ] 1.1 Determine MP4 metadata tag format (test colons, hyphens, underscores compatibility)
- [ ] 1.2 Validate ffmpeg support for custom metadata tags in MP4 container
- [ ] 1.3 Identify where in remediation pipeline output video path is finalized

## 2. Core Implementation
- [ ] 2.1 Create helper function to extract original title from input video
- [ ] 2.2 Implement title update logic with " (Censored)" suffix
- [ ] 2.3 Implement metadata tag writing to MP4 using ffmpeg
- [ ] 2.4 Integrate metadata writing into muxing process (`VideoMuxer` class)
- [ ] 2.5 Add DEBUG logging for all metadata tags and values

## 3. Integration
- [ ] 3.1 Update `remediation.py` to pass config/segment filenames and timestamps to muxer
- [ ] 3.2 Update `pipeline.py` to pass remediation configuration state to remediation manager
- [ ] 3.3 Ensure metadata is written after audio/video remediation completes but before skip chapters

## 4. Testing
- [ ] 4.1 Write unit tests for metadata tag formatting and logging
- [ ] 4.2 Write integration test: generate output video and verify metadata with ffprobe
- [ ] 4.3 Test title update with various original titles (with/without special chars)
- [ ] 4.4 Test with both audio and video remediation enabled/disabled combinations
- [ ] 4.5 Test timestamp formatting in multiple timezones

## 5. Documentation & Cleanup
- [ ] 5.1 Update project README or config guide with new metadata tags
- [ ] 5.2 Verify no temporary files left behind during metadata writing
- [ ] 5.3 Confirm all edge cases handled (missing ffmpeg, permission errors, etc.)
