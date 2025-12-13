# Design: Video Extraction

## Context

The system needs to prepare video content for LLM analysis. This requires:
- Extracting individual frames from video files at configurable intervals
- Extracting and decoding audio for profanity detection
- Tracking temporal metadata (start/end times, frame indices) for accurate result mapping
- Supporting different sampling strategies based on video length and performance constraints

ffmpeg is already declared as a system dependency in the project spec. The Python ecosystem (OpenCV, ffmpeg-python) provides bindings to ffmpeg for frame extraction.

## Goals / Non-Goals

**Goals:**
- Extract frames at configurable sample rates (e.g., every 1 second, every N frames)
- Extract audio stream in a format suitable for speech-to-text or audio analysis
- Associate each frame/audio segment with precise timecode information
- Support multiple sampling strategies (uniform, scene-based, all)
- Respect parallelization settings from config (max_workers) for performance

**Non-Goals:**
- Implement custom video decoding (defer to ffmpeg)
- Optimize for streaming (assume files are local)
- Handle DRM or encrypted content
- Generate video summaries or keyframe detection beyond sampling strategy

## Decisions

**Decision 1: Use OpenCV (cv2) for frame extraction**
- Why: Already in requirements.txt, well-maintained Python binding to ffmpeg, supports VideoCapture API
- Alternatives: 
  - ffmpeg-python: More complex, requires ffmpeg binary availability
  - av (PyAV): More powerful but heavier dependency
- Rationale: OpenCV balances simplicity and capability; integrates well with existing requirements

**Decision 2: Store frames as numpy arrays with metadata**
- Why: numpy arrays are efficient for LLM pipelines (already in requirements), metadata (timecode, index) is essential for result mapping
- Rationale: Avoid serializing/deserializing frames unnecessarily; keep in memory until analysis complete

**Decision 3: Extract audio as separate byte stream**
- Why: Audio processing may use different tools than visual analysis; separating concerns allows flexibility
- Rationale: Not all detection modules need audio; extraction is independent of visual frame extraction

**Decision 4: Uniform sampling as default, others configurable**
- Why: Uniform sampling is deterministic, predictable, and covers the full video duration evenly
- Rationale: Scene-based sampling requires additional ML models; "all frames" may be expensive; start simple

**Decision 5: Lazy audio extraction (on first request)**
- Why: Not all pipelines may need audio; extracting upfront wastes I/O
- Rationale: Cache extracted audio after first request to avoid re-extraction

## Risks / Trade-offs

**Risk 1: Memory constraints with large videos**
- Large videos at high frame rates could exhaust memory if all frames extracted at once
- Mitigation: Implement streaming (yield frames) rather than loading all at once; document memory requirements

**Risk 2: ffmpeg availability (system dependency)**
- Users may not have ffmpeg installed; OpenCV requires ffmpeg at runtime
- Mitigation: Document ffmpeg installation in QUICK_START.md and README.md; add startup check in CLI

**Risk 3: Frame format compatibility with LLM**
- Different LLMs expect different input formats (BGR vs RGB, float vs uint8, shape conventions)
- Mitigation: Store frames in standard format (uint8, RGB); provide utility functions for format conversion in LLM integration layer (out of scope for this change)

## Migration Plan

No migration needed for existing deployments (new capability, no breaking changes).

## Open Questions

- Should we support extracting only key frames (I-frames) as an optimization? Defer to future enhancement.
- Should audio extraction support multiple codecs or just PCM? Start with standard AAC/MP3; document limitations.
- Should we validate video format before processing, or fail gracefully? Fail gracefully; document supported formats.
