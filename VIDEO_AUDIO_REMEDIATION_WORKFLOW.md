# Video and Audio Remediation Workflow

This document explains the complete remediation workflow when both audio and video remediation are enabled.

## Order of Operations

The remediation pipeline executes in this specific order to maintain audio/video sync:

```
1. Detection Analysis
   ↓
2. Model Cleanup (free GPU memory)
   ↓
3. Audio Remediation (original timings)
   - Extracts audio from input video
   - Applies bleep/silence to detected segments
   - Saves remediated audio to temporary WAV file
   ↓
4. Video Remediation (may modify timings)
   - Analyzes video based on same detection results
   - Applies blank or cut to video segments
   - Saves remediated video to temporary/output file
   ↓
5. Audio Cut Adjustment (only if video was cut)
   - If video cut segments, extract matching audio segments
   - Concatenate kept audio segments
   - Replace remediated audio with cut version
   ↓
6. Audio/Video Muxing
   - Combine remediated audio with remediated video
   - Save final output video file
```

## Why This Order?

### Audio Before Video
- **Audio** uses original timestamps for detection matches
- **Video** may shift timelines (especially with cut mode)
- If we did video first, cut mode would invalidate audio timings

### Audio Cutting for Sync
When video is cut:
- Video timeline becomes shorter (segments removed)
- Audio must be cut at the same points to stay in sync
- Example:
  - Original: 30 seconds
  - Video cut segments: [0-5s, 10-15s, 20-30s] (removed 5-10s and 15-20s)
  - Audio must also keep only [0-5s, 10-15s, 20-30s]
  - Without audio cutting: audio would be 30s, video would be 20s (out of sync)

## Remediation Modes

### Audio Remediation
- **Bleep**: Replace detected segments with sine wave tone (configurable frequency)
- **Silence**: Replace detected segments with silence

### Video Remediation
- **Blank**: Replace detected segments with solid color (configurable hex color)
- **Cut**: Remove detected segments from timeline entirely

## Configuration Examples

### Audio Only (Bleep)
```yaml
audio:
  detection:
    enabled: true

remediation:
  audio:
    enabled: true
    mode: "bleep"
    categories: ["Profanity"]
    bleep_frequency: 1000
```

### Video Only (Blank)
```yaml
remediation:
  video:
    enabled: true
    mode: "blank"
    blank_color: "#000000"  # Black
```

### Both Audio and Video
```yaml
audio:
  detection:
    enabled: true

remediation:
  audio:
    enabled: true
    mode: "bleep"
    categories: ["Profanity"]
  
  video:
    enabled: true
    mode: "blank"
    blank_color: "#000000"
```

### Mixed Video Modes (Category-Based)
```yaml
remediation:
  video:
    enabled: true
    mode: "blank"  # Global default
    blank_color: "#000000"
    category_modes:
      Nudity: "cut"          # Always cut nudity
      Violence: "blank"      # Blank violence
      Profanity: "cut"       # Cut profanity audio segments
```

## Allow Override

Segments marked with `"allow": true` in the detection JSON are skipped:
- Not remedialed in audio
- Not remediated in video
- Allows fine-grained control after reviewing detection results

## Intermediate Files

During processing, temporary files are created:
- `/tmp/remediated_audio.wav` - Remediated audio before cutting
- Temporary video file (if both audio and video remediation)
- Temporary audio segments (during cut matching)
- All cleanup after final muxing

## Audio/Video Sync Verification

Final output video sync is verified by:
1. Video remediation completes with final duration
2. If cuts were applied, audio is cut to match
3. Final muxing combines both at same duration
4. Output file should have consistent audio/video streams

## Error Handling

### Audio Remediation Failure
- Continues without audio output
- Video remediation still happens

### Video Remediation Failure
- Continues with original video (if no audio)
- Or uses remediated audio + original video (if audio remediation succeeded)

### Audio Cutting Failure
- Logs warning but continues
- May result in slightly out-of-sync audio/video
- Better to complete with sync issue than fail completely

## Limitations

- **No partial overlapping segments**: Segments must be distinct time ranges
- **No streaming output**: Entire video must be processed before output
- **No real-time preview**: Requires full analysis + remediation cycle
- **Codec limitations**: Re-encoding may reduce quality slightly

## Performance Considerations

- Audio remediation: Fast (WAV processing)
- Video blank mode: Fast (filter_complex, single pass)
- Video cut mode: Slower (segment extraction + concatenation)
- Audio cutting (if needed): Medium (segment extraction + concatenation)
- Total time: 2-5x original video duration depending on mode

## Testing Coverage

Comprehensive tests in `tests/test_remediation_permutations.py` cover:
- Audio only (bleep, silence)
- Video only (blank, cut)
- All combinations (4 permutations)
- Mixed video modes
- Edge cases (no detections, no output path, allowed segments)
- Logging verification
- Audio/video sync verification
