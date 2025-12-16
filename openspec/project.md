# Project Context

## Purpose

Video Censor is a personalized video censoring system that analyzes video content and identifies segments containing inappropriate or undesired material. It enables users to make informed decisions about which sections to skip or censor based on their preferences.

The system detects:
1. Nudity
2. Profanity
3. Violence
4. Sexual themes
5. Custom concepts specified in configuration

## Tech Stack

- **Language**: Python 3.13+
- **Configuration**: YAML format
- **Video Processing**: ffmpeg (or similar)
- **ML/AI**: Local LLMs and models preferred; third-party services as fallback
- **Output Format**: JSON

## Project Conventions

### Code Style

- Follow PEP 8 style guide
- Use type hints for all function signatures
- Line length: 100 characters maximum
- Use descriptive variable and function names (snake_case)
- Docstrings for all public functions/classes (Google-style format)

### Architecture Patterns

- Modular design with separation of concerns:
  - **Config Management**: YAML parsing and validation
  - **Video Processing**: Frame extraction and analysis
  - **Detection Engines**: Pluggable detection modules (nudity, profanity, violence, etc.)
  - **Output Generation**: Result serialization to JSON
- Support for local model inference as primary path
- Abstract interfaces for swapping between local and third-party services
- CLI-based entry point for flexibility

### Testing Strategy

- Unit tests for config parsing and output validation
- Integration tests for end-to-end analysis pipelines
- Test coverage minimum: 80%
- Use pytest as test framework

### Git Workflow

- Feature branches: `feature/[description]`
- Bug fixes: `fix/[description]`
- Main branch protection enabled
- Commit messages: descriptive, present tense

## Domain Context

### Video Analysis Scope

The system analyzes video content at two levels:
- **Temporal**: Precise timecode identification (start and end times)
- **Categorical**: Multi-label classification (e.g., a scene may contain both "Profanity" and "Sexual Theme")

### Detection Philosophy

- Users should have sufficient information to make their own decisions
- Multiple labels per segment enable nuanced filtering
- Descriptive text helps users understand what triggered detection

### Research Context

Extensive research on detection methodologies and model selection has been conducted. Reference: https://grok.com/share/bGVnYWN5LWNvcHk_90c99916-95b1-4e4f-8033-503598210af3

## Important Constraints

- **Processing**: Prefer local execution; minimize external API calls for privacy and cost
- **Performance**: Process videos in reasonable time (acceptable latency TBD)
- **Accuracy**: Balance detection sensitivity with false positive rates
- **Explainability**: Provide enough information for user decision-making
- **Dual Interface**: The project supports both command-line (CLI) and graphical user interface (UI) modes:
  - **CLI-First**: The command-line interface is the primary interface and must always be fully functional
  - **UI as Enhancement**: The UI is a convenience layer built on top of CLI functionality
  - **Feature Parity**: Any feature available in the UI must also be accessible via CLI
  - **No UI Lock-in**: Users should never be required to use the UI to accomplish any task
  - **Scriptability**: CLI enables automation, batch processing, and integration with other tools

## Future Enhancements

### `three-phase-workflow` - Separate Remediation Mode (Three-Phase Workflow)

Add the ability to run remediations separately from analysis, enabling a decoupled three-phase workflow. This allows users to analyze once, review and refine multiple times, and remediate only when ready—without re-running expensive analysis.

**Workflow Overview:**

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      THREE-PHASE WORKFLOW                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐             │
│  │   PHASE 1   │      │   PHASE 2   │      │   PHASE 3   │             │
│  │   ANALYZE   │ ──▶  │   REVIEW    │ ──▶  │  REMEDIATE  │             │
│  └─────────────┘      └─────────────┘      └─────────────┘             │
│        │                    │                    │                      │
│        ▼                    ▼                    ▼                      │
│  video.mp4 ──▶        segments.json        segments.json ──▶           │
│  config.yaml          (manual edit         (with allows)               │
│        │               or UI review)             │                      │
│        ▼                    │                    ▼                      │
│  segments.json              │              output.mp4                   │
│                             │              (remediated)                 │
│                             ▼                                           │
│                    segments.json                                        │
│                    (with "allow": true                                  │
│                     on some segments)                                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Phase 1 - Analyze Video:**
- Run detection/analysis to produce the segments JSON file
- No video output required at this stage (analysis only)
- This is the most computationally expensive phase (ML inference on video frames, audio transcription)
- Output: `segments.json` with all detected segments

**Phase 2 - Review Segments:**
- User reviews the JSON file manually (text editor) or via the UI (`preview-editor-ui`)
- User marks segments with `"allow": true` as needed (`segment-allow-override`)
- User can iterate on this step as many times as needed without re-analyzing
- This phase is purely about human decision-making
- Can be done days or weeks after analysis—no time pressure
- Output: Updated `segments.json` with allow overrides

**Phase 3 - Remediate:**
- Run remediation based on the existing JSON file
- Available remediation modes (based on config):
  - Audio bleep/silence
  - Video blanking/cutting (`video-segment-removal`)
  - Chapter generation
- Does NOT re-analyze the video—uses the segment data exactly as-is
- Respects `"allow": true` segments (skips them during remediation)
- Output: Remediated video file(s)

**CLI Interface:**

```bash
# Phase 1: Analyze only (produces JSON, no video output)
python -m video_censor \
  --input video.mp4 \
  --output segments.json \
  --config config.yaml

# Phase 2: User manually edits segments.json or uses UI
# (No CLI command - this is a manual/UI step)

# Phase 3: Remediate only (uses existing JSON, produces video output)
python -m video_censor \
  --input video.mp4 \
  --input-segments segments.json \
  --output-video output.mp4 \
  --config config.yaml
```

**New CLI Option:**

| Option | Description |
|--------|-------------|
| `--input-segments <path>` | Path to an existing segments JSON file. When provided, skips all analysis and proceeds directly to remediation using the segments from this file. |

**Requirements:**
- New `--input-segments` CLI option to specify an existing JSON file
- When `--input-segments` is provided:
  - Skip all detection/analysis (vision models, audio analysis, etc.)
  - Load segments directly from the provided JSON file
  - Proceed to remediation phase based on config settings
- Validate that the JSON file matches the input video:
  - Check `metadata.file` matches input video filename (warning if mismatch)
  - Optionally check `metadata.duration` matches video duration (within tolerance)
  - Fail gracefully with clear error message if validation fails
- All remediation modes should work: audio, video, chapters
- All segments without `"allow": true` should be remediated
- Segments with `"allow": true` should be skipped

**Benefits of Three-Phase Workflow:**
1. **Time savings**: Don't re-run expensive ML analysis when only reviewing/tweaking allows
2. **Iterative workflow**: Review → adjust → remediate → watch → adjust again → re-remediate
3. **Separation of concerns**: Analysis and remediation are logically separate operations
4. **Batch processing**: Analyze many videos overnight, review at leisure, remediate when ready
5. **Collaboration**: One person analyzes, another person reviews and approves segments

### `video-segment-removal` - Video Editing / Segment Removal

Add an option similar to chapter generation or audio remediation that actually cuts out (or blanks out) video segments identified in the JSON file. This is a new remediation mode that operates on the visual content in addition to (or instead of) audio remediation.

**Requirements:**
- Requires `--output-video` option to be specified (similar to existing audio remediation modes)
- Only segments that are NOT marked `"allow": true` should be removed or blanked (integrates with `segment-allow-override`)
- Should be configurable via YAML config file similar to existing remediation options
- Must preserve video quality and encoding settings where possible
- Should work in conjunction with audio remediation (e.g., blank video + bleep audio for same segment)
- Fits into Phase 3 (Remediate) of the `three-phase-workflow`

**Open Questions (Discovery Required Before Implementation):**

| Mode | Description | Pros | Cons |
|------|-------------|------|------|
| **Mode A - Blank Video Only** | Keep the audio playing but show a blank/black screen for the segment duration | Preserves timing/sync with original; no audio discontinuity; simpler to implement; viewer knows something was censored | May be jarring visually; audio context may reveal what was censored |
| **Mode B - Cut Both Audio & Video** | Remove both audio and video for the segment, resulting in a shorter output video | Cleaner removal; no trace of censored content; shorter runtime | Causes continuity issues; video duration changes; may confuse viewers with sudden jumps; harder to implement with re-encoding |
| **Mode C - Both Options Available** | Provide a YAML configuration option to let users choose their preferred mode per video | Maximum flexibility for different use cases; users can decide based on content type | More complex implementation; more testing required; more documentation needed |

**Implementation Considerations:**
- Decision on which mode(s) to implement should be made at implementation time based on user feedback and technical feasibility
- Consider ffmpeg filter chains for blanking video frames (e.g., `drawbox` or `overlay` filters)
- Consider ffmpeg segment extraction and concatenation for cutting (e.g., `-ss` and `-to` with concat demuxer)
- May need to handle keyframe alignment issues when cutting to avoid artifacts
- Should support common video codecs (H.264, H.265, VP9, AV1)
- Consider whether to re-encode or use stream copy where possible for performance

**Proposed YAML Configuration:**
```yaml
remediation:
  video_editing:
    enabled: true
    mode: "blank"  # "blank" | "cut"
    blank_color: "#000000"  # Color to show during blanked segments (hex color code)
    blank_opacity: 1.0  # 0.0 (transparent) to 1.0 (fully opaque)
```

### `preview-editor-ui` - Video Preview / Editing UI

Build a simple Python-based desktop UI application for reviewing detection results and editing segment allow/disallow status. This UI enables users to visually review detected segments, watch the actual video content, and make informed decisions about which segments to allow or remediate.

**Core Functionality:**
- Open a video file and its corresponding JSON detection file
- Play video with synchronized audio (both video and audio must be playable)
- Navigate between detected segments easily by clicking on them
- View segment metadata and mark segments as allowed/not-allowed
- Persist changes to the JSON file immediately upon user action (no "Save" button needed)
- Jump directly to any segment's timestamp in the video

**UI Layout (Three-Pane Design):**

```
+------------------+----------------------------------------+
|                  |                                        |
|  SEGMENT LIST    |           VIDEO PLAYER                 |
|  (Left Panel)    |           (Main Panel)                 |
|                  |                                        |
|  - Segment 1     |   +--------------------------------+   |
|  - Segment 2     |   |                                |   |
|  - Segment 3 ✓   |   |          [VIDEO]               |   |
|  - Segment 4     |   |                                |   |
|  - Segment 5     |   +--------------------------------+   |
|  ...             |   [|<] [<<] [▶/❚❚] [>>] [>|]  00:48:25 |
|                  |   [Volume: ████████░░]                 |
+------------------+----------------------------------------+
|                                                           |
|  SEGMENT DETAILS (Bottom Panel)                           |
|                                                           |
|  Time: 00:48:25 - 00:48:26 (1 second)                    |
|  Labels: Profanity                                        |
|  Description: Character uses mild profanity               |
|  Confidence: 0.85                                         |
|                                                           |
|  [Show Segment Details ▼]   [✓ Mark Allowed] [✗ Not Allowed]|
|                                                           |
+-----------------------------------------------------------+
```

- **Left Panel - Segment List**: 
  - Scrollable list of all detected segments
  - Each item shows: time range (e.g., "00:48:25 - 00:48:26"), primary label(s)
  - Visual indicator for allowed segments (e.g., checkmark, green highlight, or strikethrough)
  - Clicking a segment: selects it, shows details in bottom panel, and jumps video to that timestamp
  - Current segment should be highlighted as video plays

- **Main Panel - Video Player**: 
  - Video playback area with standard controls:
    - Play/Pause button
    - Seek bar/timeline (with visual markers for segment locations)
    - Skip forward/backward buttons (e.g., 10 seconds)
    - Volume control
    - Current timecode display (HH:MM:SS format)
  - Should display current timecode prominently
  - Video and audio must both play (not just video frames)

- **Bottom Panel - Segment Details**: 
  - Shows selected segment information:
    - Start time, end time, duration (in seconds)
    - Labels (comma-separated list, e.g., "Profanity, Violence")
    - Description (the human-readable description from detection)
    - Confidence score (e.g., "0.85" or "85%")
  - **"Show Segment Details" button/toggle**: Expands to show the full `detections` array:
    - Per-detection: label, confidence, reasoning
    - Useful for understanding why each label was assigned
  - Allow/Not-Allow toggle buttons or checkbox

**User Actions:**

| Action | UI Element | Behavior |
|--------|------------|----------|
| **Select Segment** | Click segment in list | Highlights segment, shows details in bottom panel, seeks video to segment start time |
| **Play Segment** | Play button or spacebar | Plays video from current position with audio |
| **Mark as Allowed** | Button or checkbox | Sets `"allow": true` on the selected segment in the JSON file |
| **Mark as Not Allowed** | Button or checkbox | Removes `allow` property or sets `"allow": false` on the segment |
| **Immediate Persistence** | Automatic | Each time user changes a segment's allow status, the JSON file is updated and saved immediately |
| **Show Full Details** | Expand button | Reveals the complete `detections` array with per-label reasoning |
| **Jump to Next/Previous Segment** | Keyboard shortcuts or buttons | Navigate between segments without using the list |
| **Launch Processing** | Button (possibly in menu or toolbar) | Triggers video processing (audio remediation, video editing, chapter generation) using the current JSON file. Opens dialog to select processing modes and output path. Processing runs in background with progress indicator. |

**Keyboard Shortcuts (Suggested):**
- `Space` - Play/Pause
- `←/→` - Seek backward/forward 5 seconds
- `↑/↓` - Previous/Next segment
- `A` - Toggle allow on current segment
- `Enter` - Jump to selected segment

**Discovery Required Before Implementation:**

| Component | Options to Evaluate | Considerations |
|-----------|---------------------|----------------|
| **Python Desktop UI Framework** | PyQt6, PySide6, Tkinter, Kivy, wxPython, Dear PyGui | Cross-platform support (Windows, macOS, Linux); Ease of use and learning curve; Video widget integration; Community support and documentation; License compatibility (GPL vs LGPL vs MIT) |
| **Python Video Playback Library** | python-vlc, opencv-python (cv2), moviepy, PyAV, pyglet, pygame | Reliable video+audio playback (not just frames); Seeking support (jump to specific timestamp); Format support (MP4, MKV, AVI, etc.); Performance with large files; Integration with chosen UI framework |
| **Framework Integration** | PyQt + VLC widget, Tkinter + pygame, etc. | Some combinations work better than others; Need to prototype to validate |

**Framework Evaluation Criteria:**
1. Must support synchronized video and audio playback
2. Must support seeking to arbitrary timestamps
3. Must work on macOS (primary development platform) and ideally Windows/Linux
4. Should have examples of video player implementations
5. Should have active maintenance and community

### `ui-full-workflow` - Full Processing Workflow in UI

Extend the Video Preview/Editing UI (`preview-editor-ui`) to support launching the full analysis and remediation workflow from within the UI. This makes the UI a complete, self-contained application for the entire video censoring workflow.

**Goal:** Users should be able to do all processing tasks from within the UI without needing to use the command line.

**Launch Analysis Dialog:**

When user wants to analyze a new video, open a dialog with the following options:

| Field | Type | Description | Default |
|-------|------|-------------|---------|
| **Config File** | File picker | Choose the YAML configuration file that defines detection settings | Last used config, or prompt to select |
| **Input Video** | File picker | Choose the video file to analyze | None (required) |
| **Output JSON File** | File picker/text input | Where to save the segments JSON file | Same directory as input video, with `.json` extension (e.g., `movie.mp4` → `movie.json`) |
| **Output Video File** | File picker/text input | Where to save the remediated video (if applicable) | Same directory as input video, with `-censored` suffix (e.g., `movie.mp4` → `movie-censored.mp4`) |

**Output Video Visibility:**
- The "Output Video File" field should only be shown/enabled if the selected config file specifies video output modes (audio remediation, video editing, chapters)
- If config doesn't require video output, this field can be hidden or disabled
- Parse the config file when selected to determine if video output is needed

**Run Analysis Button:**
- Launches the analysis process using the selected options
- Runs in background thread to keep UI responsive
- Shows progress indicator (ideally with phase information: "Extracting frames...", "Analyzing content...", "Generating segments...")
- Allows cancellation if analysis is taking too long
- Disables other UI elements during processing to prevent conflicts

**Workflow Integration - Seamless Transitions:**

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        UI WORKFLOW FLOW                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────┐                                                    │
│  │ Launch Analysis │                                                    │
│  │     Dialog      │                                                    │
│  └────────┬────────┘                                                    │
│           │ User clicks "Run Analysis"                                  │
│           ▼                                                             │
│  ┌─────────────────┐                                                    │
│  │   Processing    │  ← Progress bar, status messages                  │
│  │   (Background)  │                                                    │
│  └────────┬────────┘                                                    │
│           │ Analysis completes                                          │
│           ▼                                                             │
│  ┌─────────────────┐                                                    │
│  │ Auto-Load JSON  │  ← segments.json loaded into review UI            │
│  │   for Review    │                                                    │
│  └────────┬────────┘                                                    │
│           │ User reviews segments, marks allows                         │
│           ▼                                                             │
│  ┌─────────────────┐                                                    │
│  │ Launch Remediate│  ← User clicks "Process Video" button             │
│  │     Dialog      │                                                    │
│  └────────┬────────┘                                                    │
│           │ User confirms processing options                            │
│           ▼                                                             │
│  ┌─────────────────┐                                                    │
│  │  Remediation    │  ← Progress bar, status messages                  │
│  │  (Background)   │                                                    │
│  └────────┬────────┘                                                    │
│           │ Remediation completes                                       │
│           ▼                                                             │
│  ┌─────────────────┐                                                    │
│  │ Success! Option │  ← "Open output video" or "Open folder"           │
│  │ to open result  │                                                    │
│  └─────────────────┘                                                    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**After Analysis Completes:**
1. Show success notification
2. Automatically load the generated JSON file into the review UI (`preview-editor-ui`)
3. Video player loads the input video
4. User can immediately begin reviewing segments and marking allows

**Launch Remediation from UI:**
After reviewing segments, user can trigger remediation directly from the UI:
- "Process Video" button opens dialog to confirm/adjust:
  - Output video path
  - Which remediation modes to apply (checkboxes for: Audio, Video, Chapters)
  - Any final config overrides
- Processing runs in background with progress indicator
- Upon completion, option to open the output video or containing folder

**Error Handling:**
- Clear error messages if analysis or remediation fails
- Log file location shown for debugging
- Option to retry with different settings

**Menu/Toolbar Actions:**
| Action | Location | Description |
|--------|----------|-------------|
| **New Analysis** | File menu / Toolbar | Open the "Launch Analysis" dialog |
| **Open Video + JSON** | File menu / Toolbar | Open existing video and JSON for review |
| **Process Video** | Actions menu / Toolbar | Launch remediation on current JSON |
| **Save JSON** | File menu | Explicit save (even though auto-save happens on allow changes) |
| **Preferences** | Edit menu | Set defaults for config file, output directories, etc. |

## External Dependencies

- **ffmpeg**: Video frame extraction and metadata
- **Local LLMs**: Vision models (to be determined; candidates under research)
- **Third-party fallback**: APIs for specific detection tasks if local models insufficient

---

## Configuration Format (Proposed YAML)

```yaml
# video-censor.yaml - Analysis configuration

version: 1.0

# Detection enabled/disabled toggles
detections:
  nudity:
    enabled: true
    sensitivity: 0.7  # 0.0 (permissive) to 1.0 (strict)
    model: "local"    # "local" or specific model name
  
  profanity:
    enabled: true
    sensitivity: 0.8
    model: "local"
    # Optional language specification
    languages:
      - en
      - es
  
  violence:
    enabled: true
    sensitivity: 0.6
    model: "local"
  
  sexual_themes:
    enabled: true
    sensitivity: 0.75
    model: "local"
  
  # Custom detection categories
  custom_concepts:
    - name: "logos"
      enabled: false
      sensitivity: 0.5
      description: "Brand logos and product placement"
    
    - name: "spoilers"
      enabled: false
      sensitivity: 0.6
      description: "Movie/show spoiler content"

# Video processing settings
processing:
  # Frame sampling strategy
  frame_sampling:
    strategy: "uniform"  # "uniform", "scene_based", "all"
    sample_rate: 1.0    # seconds between frame analysis (1.0 = every second)
  
  # Temporal aggregation
  segment_merge:
    enabled: true
    merge_threshold: 2.0  # merge segments within N seconds
  
  # Performance tuning
  max_workers: 4        # parallel processing

# Output settings
output:
  format: "json"        # "json", "csv" (extensible)
  include_frames: false # include base64 encoded frame images
  include_confidence: true  # include confidence scores
  pretty_print: true    # human-readable JSON

# Model configuration
models:
  local:
    # TBD: specific model identifiers and paths
    vision_model: "llava-7b"  # example
    cache_dir: "./models"
  
  third_party:
    enabled_fallback: false
    # Credentials loaded from environment variables
    providers:
      - name: "example_api"
        enabled: false
```

---

## Output Format Specification

### JSON Output Structure

```json
{
  "metadata": {
    "file": "input_video.mp4",
    "duration": "1:23:45",
    "processed_at": "2025-12-13T14:30:00Z",
    "config": "video-censor.yaml"
  },
  "segments": [
    {
      "start_time": "00:48:25",
      "end_time": "00:48:26",
      "duration_seconds": 1,
      "labels": ["Profanity", "Sexual Theme"],
      "description": "A character uses explicit language in a sexual context",
      "confidence": 0.92,
      "detections": [
        {
          "label": "Profanity",
          "confidence": 0.95,
          "reasoning": "Detected strong profanity in audio"
        },
        {
          "label": "Sexual Theme",
          "confidence": 0.88,
          "reasoning": "Visual content combined with dialogue suggests sexual context"
        }
      ]
    },
    {
      "start_time": "01:12:30",
      "end_time": "01:12:45",
      "duration_seconds": 15,
      "labels": ["Violence"],
      "description": "Physical fight scene with impact sounds",
      "confidence": 0.87,
      "detections": [
        {
          "label": "Violence",
          "confidence": 0.87,
          "reasoning": "Rapid motion, impact sounds, and physical contact detected"
        }
      ]
    }
  ],
  "summary": {
    "total_segments_detected": 2,
    "total_flagged_duration": 16,
    "detection_counts": {
      "Profanity": 1,
      "Sexual Theme": 1,
      "Violence": 1
    }
  }
}
```

### Command-Line Interface

```bash
python -m video_censor \
  --input /path/to/video.mp4 \
  --output /path/to/results.json \
  --config /path/to/video-censor.yaml \
  [--verbose]
```
