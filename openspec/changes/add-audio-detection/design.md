# Design: Audio Processing, Detection, and Remediation

## Context

The existing system performs visual-only detection. Audio analysis and remediation requires:
1. **Audio extraction**: Separate audio track from video container
2. **Audio caching**: Reuse across detectors (expensive to extract repeatedly)
3. **Audio segmentation**: Align audio chunks with video frames for per-frame detection
4. **Speech recognition**: Whisper or similar to convert speech → text for profanity matching
5. **Audio classification**: Models to detect sound effects, music, ambient content
6. **Multi-language support**: Profanity keyword databases for EN, ES, FR, etc.
7. **Audio remediation**: Silence or bleep detected inappropriate audio segments
8. **Audio output**: Write remediated audio to separate WAV file
9. **Video muxing**: Re-combine remediated audio with original video container
10. **CLI integration**: Accept --output-video argument; fail-fast if remediation enabled without output path
11. **Error handling**: Graceful fallback when audio missing or corrupted

Current analysis pipeline and detection framework already support `audio_data` parameter in `Detector.detect()`, so the plumbing exists—this change adds the implementation layer.

## Goals / Non-Goals

### Goals
- Extract audio track once per video, cache for detector reuse
- Implement speech profanity detector using Whisper + keyword matching
- Implement audio classification detector for sound effects and music categorization
- Support multi-language profanity detection (EN, ES, FR as baseline)
- Implement audio remediation (silence or bleep) for detected inappropriate audio
- Allow per-category remediation control (enable/disable silencing per category)
- Support both silence (zero amplitude) and bleep (tone generation) options
- Write remediated audio to output file with correct sync to original video
- Mux remediated audio back into video container (using ffmpeg)
- Accept `--output-video` CLI argument for specifying dubbing output path
- Fail-fast with clear error if remediation enabled but output-video not specified
- Integrate audio detectors, remediation, and video muxing into analysis pipeline
- Maintain backwards compatibility: audio detection and remediation are opt-in via config
- Provide clear error handling for missing audio, failed transcription, or muxing failures

### Non-Goals
- Real-time audio streaming (batch processing only)
- Custom model training (use pre-trained Whisper, audio classifiers)
- Audio cleanup/enhancement (use raw extraction)
- Parallel audio detector execution (sequential, per existing pattern)
- GPU optimization for audio (defer to detector implementation)
- Advanced language detection beyond configured languages
- Video re-encoding (use ffmpeg copy codec for lossless video passthrough)
- Custom bleep tone synthesis (use standard sine wave)

## Decisions

### Audio Extraction and Caching

```python
class AudioExtractor:
    """Extracts and caches audio from video."""
    
    def __init__(self, video_path: str, cache_dir: Optional[str] = None):
        self.video_path = video_path
        self.cache_dir = cache_dir or tempfile.gettempdir()
        self.audio_data = None  # Cached raw audio (numpy array)
        self.sample_rate = None
        self.duration = None
    
    def extract(self) -> Tuple[np.ndarray, int]:
        """Extract audio once, return (audio_data, sample_rate)."""
        if self.audio_data is not None:
            return self.audio_data, self.sample_rate
        
        # Use ffmpeg or librosa to extract
        # Return cached for subsequent calls
        return self.audio_data, self.sample_rate
    
    def get_audio_segment(self, start_time: float, duration: float) -> Optional[np.ndarray]:
        """Get audio chunk for frame at given timecode."""
        # Return slice of cached audio or None if no audio
        pass
    
    def cleanup(self) -> None:
        """Release cached audio."""
        self.audio_data = None
```

**Rationale**: Single extraction, cached in memory (or disk), sliced per frame. Avoids repeated ffmpeg calls.

### Speech Profanity Detector

```python
class SpeechProfanityDetector(Detector):
    """Detects profanity in speech using Whisper ASR + keyword matching."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.languages = config.get("languages", ["en"])  # Supported languages
        self.keywords = self._load_profanity_keywords()  # lang → [keywords]
        self.whisper_model = config.get("model", "base")  # Whisper model size
        self.pipe = pipeline("automatic-speech-recognition",
                            model=f"openai/whisper-{self.whisper_model}")
    
    def detect(self, frame_data=None, audio_data=None) -> List[DetectionResult]:
        """Transcribe audio, match keywords, return Profanity results."""
        if audio_data is None:
            return []  # No audio, no profanity
        
        # Transcribe using Whisper
        result = self.pipe(audio_data)
        transcription = result["text"].lower()
        
        # Check keywords in transcription
        matches = self._find_profanity(transcription)
        
        # Return DetectionResult per match
        return [
            DetectionResult(
                label="Profanity",
                confidence=0.95,  # High confidence if keyword found
                reasoning=f"Speech contains profanity: '{match}'",
                start_time=None,  # Set by pipeline
                end_time=None
            )
            for match in matches
        ]
    
    def _load_profanity_keywords(self) -> Dict[str, List[str]]:
        """Load language-specific keyword lists."""
        # Load from config or bundled data
        return {
            "en": [...],
            "es": [...],
            # etc.
        }
    
    def _find_profanity(self, text: str) -> List[str]:
        """Match keywords against transcription."""
        pass
    
    def cleanup(self) -> None:
        """Release model."""
        del self.pipe
```

**Rationale**: Whisper handles speech-to-text across languages; keyword matching is fast and interpretable; high confidence when keyword detected.

### Audio Classification Detector

```python
class AudioClassificationDetector(Detector):
    """Detects sound effects and music using audio classification models."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.model_name = config.get("model", "audioset-vit-base")  # HuggingFace model
        self.processor = AutoFeatureExtractor.from_pretrained(self.model_name)
        self.model = AutoModelForAudioClassification.from_pretrained(self.model_name)
        self.target_categories = config.get("categories", ["Violence", "Sexual Theme"])
        self.category_mapping = self._build_category_mapping()
    
    def detect(self, frame_data=None, audio_data=None) -> List[DetectionResult]:
        """Classify audio, map to detected categories."""
        if audio_data is None:
            return []
        
        # Preprocess audio
        inputs = self.processor(audio_data, sampling_rate=16000, return_tensors="pt")
        
        # Classify
        with torch.no_grad():
            outputs = self.model(**inputs)
        
        logits = outputs.logits
        predicted_class_idx = logits.argmax(-1).item()
        predicted_label = self.model.config.id2label[predicted_class_idx]
        confidence = logits.softmax(-1).max().item()
        
        # Map audio labels to content categories (e.g., "gunshot" → "Violence")
        content_category = self.category_mapping.get(predicted_label)
        
        if content_category and content_category in self.target_categories:
            return [
                DetectionResult(
                    label=content_category,
                    confidence=confidence,
                    reasoning=f"Audio contains: {predicted_label}",
                    start_time=None,  # Set by pipeline
                    end_time=None
                )
            ]
        
        return []
    
    def _build_category_mapping(self) -> Dict[str, str]:
        """Map audio labels to content detection categories."""
        return {
            "gunshot": "Violence",
            "scream": "Violence",
            "explosion": "Violence",
            "adult": "Sexual Theme",
            "moaning": "Sexual Theme",
            # etc.
        }
    
    def cleanup(self) -> None:
        """Release model."""
        del self.model, self.processor
```

**Rationale**: Pre-trained audio classifier handles diverse sound effects; mapping abstracts audio labels to content categories.

### Audio Remediation Engine

```python
class AudioRemediator:
    """Applies remediation (silence or bleep) to detected audio segments."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize remediator with remediation config.
        
        Args:
            config: Dict with:
                - enabled: bool, default False
                - mode: "silence" or "bleep"
                - categories: list of category names to remediate
                    (e.g., ["Profanity", "Violence"])
                - bleep_frequency: int Hz, default 1000 (for bleep mode)
        """
        self.enabled = config.get("enabled", False)
        self.mode = config.get("mode", "silence")  # "silence" or "bleep"
        self.categories = set(config.get("categories", []))
        self.bleep_frequency = config.get("bleep_frequency", 1000)
    
    def remediate(
        self,
        audio_data: np.ndarray,
        sample_rate: int,
        detections: List[DetectionResult]
    ) -> np.ndarray:
        """Apply remediation to audio based on detections.
        
        Args:
            audio_data: Raw audio array (mono, float32)
            sample_rate: Audio sample rate (16000 Hz assumed)
            detections: List of DetectionResult with timecodes
            
        Returns:
            Remediated audio array (same shape as input)
        """
        if not self.enabled:
            return audio_data
        
        remediated = audio_data.copy()
        
        # Filter detections to remediate (by category)
        for detection in detections:
            if detection.label not in self.categories:
                continue
            
            # Convert timecode to sample indices
            start_sample = int(detection.start_time * sample_rate)
            end_sample = int(detection.end_time * sample_rate)
            
            if self.mode == "silence":
                remediated[start_sample:end_sample] = 0
            elif self.mode == "bleep":
                # Generate bleep tone (sine wave) for duration
                duration_samples = end_sample - start_sample
                t = np.arange(duration_samples) / sample_rate
                tone = 0.2 * np.sin(2 * np.pi * self.bleep_frequency * t)
                remediated[start_sample:end_sample] = tone
        
        return remediated
    
    def write_audio(
        self,
        audio_data: np.ndarray,
        sample_rate: int,
        output_path: str
    ) -> None:
        """Write remediated audio to file.
        
        Args:
            audio_data: Audio array
            sample_rate: Sample rate
            output_path: Path to save audio (.wav or similar)
        """
        # Use librosa or soundfile to write
        import soundfile as sf
        sf.write(output_path, audio_data, sample_rate)
```

**Rationale**:
- Silence: Zero out audio samples in detection range (simple, natural-sounding)
- Bleep: Generate sine wave at specified frequency (clear audible cue for censoring)
- Per-category control: Users choose which content to remediate (e.g., silence profanity but not violence)
- Output file: Separate output enables users to test before replacing original

### Video Muxing Engine

```python
class VideoMuxer:
    """Re-muxes remediated audio into original video container."""
    
    def __init__(self, original_video_path: str, remediated_audio_path: str):
        """Initialize muxer with paths.
        
        Args:
            original_video_path: Path to original video file
            remediated_audio_path: Path to remediated audio WAV file
        """
        self.original_video_path = original_video_path
        self.remediated_audio_path = remediated_audio_path
    
    def mux_video(self, output_video_path: str) -> None:
        """Mux remediated audio into video, write to output.
        
        Args:
            output_video_path: Path where muxed video will be saved
        
        Uses ffmpeg command:
            ffmpeg -i original_video.mp4 -i remediated_audio.wav \
                   -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 \
                   -shortest output_video.mp4
        
        Flags:
            -c:v copy: Copy video codec (no re-encoding)
            -c:a aac: Encode audio as AAC
            -map 0:v:0: Use first video stream from video
            -map 1:a:0: Use first audio stream from audio file
            -shortest: Stop when shortest stream ends
        """
        import subprocess
        
        cmd = [
            "ffmpeg",
            "-i", self.original_video_path,
            "-i", self.remediated_audio_path,
            "-c:v", "copy",  # Copy video codec (fast, lossless)
            "-c:a", "aac",   # Encode audio as AAC
            "-map", "0:v:0",  # Video from first input
            "-map", "1:a:0",  # Audio from second input
            "-shortest",      # Stop at shortest stream
            "-y",            # Overwrite output file
            output_video_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(
                f"Video muxing failed: {result.stderr}"
            )
```

**Rationale**:
- Uses ffmpeg for reliable video/audio muxing
- `-c:v copy`: Fast passthrough of video (no re-encoding)
- `-c:a aac`: Standard audio codec compatible with most players
- `-shortest`: Handles any sample rate mismatches automatically
- Separate tool keeps audio remediation decoupled from muxing

### CLI Argument Handling

Add `--output-video` argument to main entry point:

```python
# In video_censor_personal.py or main entry point
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--input", required=True, help="Input video path")
parser.add_argument("--output", required=True, help="Output JSON results path")
parser.add_argument("--config", help="Config YAML path")
parser.add_argument(
    "--output-video",
    help="Output video path (required if audio remediation enabled)",
)
parser.add_argument("--verbose", action="store_true")

args = parser.parse_args()

# Validation: fail-fast if remediation enabled but no output-video
config = load_config(args.config)
remediation_enabled = (
    config.get("audio", {})
    .get("remediation", {})
    .get("enabled", False)
)

if remediation_enabled and not args.output_video:
    print(
        "ERROR: Audio remediation is enabled in config, but "
        "--output-video argument is missing.\n\n"
        "To use audio remediation, provide output video path:\n"
        "  python video_censor_personal.py ... --output-video /path/to/output.mp4\n\n"
        "Or disable audio remediation in config:\n"
        "  audio.remediation.enabled: false",
        file=sys.stderr
    )
    sys.exit(1)

# Pass output_video to pipeline
pipeline = AnalysisPipeline(args.input, config, output_video_path=args.output_video)
```

**Rationale**:
- CLI arg reusable across configs (config stays generic, path is runtime argument)
- Fail-fast validation prevents running long analysis only to fail on muxing
- Clear error message tells users exactly what's needed
- Optional when remediation disabled (backward compatible)

### Analysis Pipeline Video Muxing Integration

```python
class AnalysisPipeline:
    def __init__(self, video_path: str, config: Dict, output_video_path: Optional[str] = None):
        # ... existing init ...
        self.output_video_path = output_video_path
    
    def analyze(self) -> DetectionResults:
        """Analyze with optional audio remediation and video muxing."""
        # ... audio detection and remediation ...
        
        # Mux remediated audio back into video if enabled
        if self.audio_remediator.enabled and self.remediated_audio_path:
            if not self.output_video_path:
                raise ValueError(
                    "Audio remediation enabled but output_video_path not specified"
                )
            
            muxer = VideoMuxer(self.video_path, self.remediated_audio_path)
            try:
                muxer.mux_video(self.output_video_path)
                results["output_video_path"] = self.output_video_path
            except Exception as e:
                logger.error(f"Video muxing failed: {e}")
                raise
        
        return results
```

### Configuration Schema for Remediation

```yaml
# Extended audio detection section with remediation
audio:
  detection:
    enabled: true
    detectors:
      - type: "speech-profanity"
        enabled: true
        languages: ["en", "es"]
      - type: "audio-classification"
        enabled: true
        categories: ["Violence", "Sexual Theme"]
  
  remediation:
    enabled: false  # Optional audio censoring
    mode: "silence"  # "silence" or "bleep"
    categories:  # Which detected categories to remediate
      - "Profanity"
      # "Violence" not in list, so violence sounds are detected but not silenced
    bleep_frequency: 1000  # Hz, for bleep mode
    output_path: "./output_audio_remediated.wav"  # Where to save if enabled
```

**Rationale**: Granular per-category control allows users to:
- Silence profanity but keep violence sounds (or vice versa)
- Test with either silence or bleep
- Save output separately before integrating back to video

### Model Download and Caching

Whisper and HuggingFace models are downloaded automatically on first use, but users can pre-cache models:

```bash
# Pre-download Whisper model (recommended before first run)
python -c "import whisper; whisper.load_model('base')"

# Pre-download audio classification model
python -c "from transformers import AutoModelForAudioClassification; \
  AutoModelForAudioClassification.from_pretrained('audioset-vit-base')"

# Models cached in: ~/.cache/huggingface/, ~/.cache/torch/, ~/.whisper/
```

**Model Sizes** (reference):
- Whisper tiny: ~40 MB
- Whisper base: ~140 MB (recommended for most uses)
- Whisper small: ~500 MB
- Whisper medium: ~1.5 GB
- Whisper large: ~3 GB
- Audio classification (audioset-vit-base): ~300 MB

**Cache Locations**:
- Whisper: `~/.cache/torch/hub/` or `~/.whisper/`
- HuggingFace: `~/.cache/huggingface/hub/`
- Users can override with env vars: `TRANSFORMERS_CACHE`, `HF_HOME`

### Analysis Pipeline Audio and Remediation Support

```python
class AnalysisPipeline:
    def __init__(self, video_path: str, config: Dict):
        # ... existing init ...
        self.audio_extractor = AudioExtractor(video_path) if self._has_audio_detectors(config) else None
        self.audio_remediator = AudioRemediator(config.get("audio", {}).get("remediation", {}))
        self.remediated_audio_path = None
    
    def analyze(self) -> DetectionResults:
        """Analyze with optional audio remediation."""
        audio_data = None
        sample_rate = None
        
        if self.audio_extractor:
            raw_audio, sr = self.audio_extractor.extract()
            audio_data = librosa.resample(raw_audio, orig_sr=sr, target_sr=16000)
            sample_rate = 16000
        
        # ... frame analysis loop ...
        all_results = self._analyze_frames(audio_data)
        
        # Apply remediation if enabled
        if self.audio_remediator.enabled and audio_data is not None:
            remediated = self.audio_remediator.remediate(audio_data, sample_rate, all_results)
            output_path = self.audio_remediator.config.get("output_path", "output_audio.wav")
            self.audio_remediator.write_audio(remediated, sample_rate, output_path)
            self.remediated_audio_path = output_path
        
        return self._aggregate_results(all_results)
```

### Backward Compatibility Note

The refactored `AnalysisPipeline` now optionally handles audio extraction, detection, and remediation:
- If no audio detectors configured: `audio_extractor` is None, pipeline behaves as before (visual-only)
- If audio detectors configured but remediation disabled: audio is detected but not modified
- If remediation enabled: remediated audio written to separate file; original video unchanged

This preserves existing behavior while adding optional audio capabilities.

### Configuration Schema

```yaml
# Extended audio detection and remediation section in video-censor.yaml
audio:
  detection:
    enabled: true
    detectors:
      - type: "speech-profanity"
        name: "speech-detector"
        enabled: true
        model: "base"  # Whisper model size: tiny, base, small, medium, large
        categories:
          - "Profanity"
        languages:
          - "en"
          - "es"
        confidence_threshold: 0.8
      
      - type: "audio-classification"
        name: "audio-classifier"
        enabled: true
        model: "audioset-vit-base"  # HuggingFace model identifier
        categories:
          - "Violence"
          - "Sexual Theme"
        confidence_threshold: 0.6
  
  remediation:
    enabled: false  # Set to true to generate remediated audio
    mode: "silence"  # "silence" or "bleep"
    categories:  # Which detected categories to remediate
      - "Profanity"
      # Note: "Violence" not listed, so violence sounds are detected but not silenced
    bleep_frequency: 1000  # Hz, frequency for bleep tone (if mode = "bleep")
    output_path: "./remediated_audio.wav"  # Where to save the cleaned audio
```

**Rationale**: 
- Nested `audio` section groups detection and remediation configs
- Per-category remediation control: silence what you want, detect the rest
- Choice of silence or bleep tone
- Output path allows testing before integration

## Risks / Trade-offs

- **Risk**: Whisper model size impacts memory and speed (base ≈ 140MB, large ≈ 3GB)
  - **Mitigation**: Make model size configurable; document performance trade-offs; default to "base"

- **Risk**: Speech recognition fails or is inaccurate for accented/noisy audio
  - **Mitigation**: Fall back to audio classification for sound detection; log transcription confidence

- **Risk**: Audio classification labels don't map cleanly to content categories
  - **Mitigation**: Build comprehensive mapping; allow user-defined category mappings in config (future)

- **Risk**: Audio extraction is slow for long videos
  - **Mitigation**: Cache once; reuse; parallelize frame analysis if needed (future)

- **Risk**: Language-specific profanity keywords are incomplete/outdated
  - **Mitigation**: Use open-source keyword lists (e.g., Better Profanity library); allow user extensions

- **Risk**: Audio-only detection misses visual context (e.g., violence sound without violence action)
  - **Mitigation**: Combine audio + visual via multi-modal detector (future); document current behavior

- **Risk**: Remediation (silence/bleep) may cause audio discontinuities or sync issues
  - **Mitigation**: Ensure silence and bleep use same sample rate as original; test sync with video; output separate file to test before integration

- **Risk**: Bleep frequency may be inaudible or too loud depending on system audio
  - **Mitigation**: Make bleep frequency and amplitude configurable; recommend 1000 Hz at 0.2 amplitude as default; document that user may need to adjust per use case

- **Risk**: Per-category remediation granularity may be too coarse (e.g., overlapping speech and violence sounds)
  - **Mitigation**: Start with category-level control; future enhancement could support time-range filtering or AI-based source separation

## Migration Plan

1. **Phase 1**: Audio extraction infrastructure
   - Implement `AudioExtractor` with ffmpeg/librosa integration
   - Unit tests for extraction, resampling, segmentation
   - Integration tests with sample videos

2. **Phase 2**: Speech profanity detector
   - Implement `SpeechProfanityDetector` with Whisper integration
   - Bundle baseline profanity keyword lists (EN, ES)
   - Tests: mock Whisper, test keyword matching, test multi-language

3. **Phase 3**: Audio classification detector
    - Implement `AudioClassificationDetector` with HuggingFace models
    - Build audio label → content category mapping
    - Tests: mock model, test mapping, test confidence scores

4. **Phase 4**: Pipeline integration
    - Modify `AnalysisPipeline.analyze()` to extract and cache audio
    - Pass audio segments to detectors
    - Error handling for missing/corrupted audio
    - Integration tests end-to-end

5. **Phase 5**: Audio remediation engine
    - Implement `AudioRemediator` with silence and bleep modes
    - Support per-category remediation control
    - Write remediated audio to output file
    - Tests: mock detections, test silence mode, test bleep mode, test per-category filtering

6. **Phase 6**: Pipeline remediation integration
    - Modify `AnalysisPipeline.analyze()` to apply remediation after detection
    - Output remediated audio path in detection results (optional)
    - Error handling for audio write failures
    - Integration tests with real Whisper + remediation

7. **Phase 7**: Configuration and documentation
    - Update YAML schema validation for remediation config
    - CLI documentation for audio detection and remediation
    - Example configs with audio + remediation enabled/disabled
    - User guide for remediation workflow

## Open Questions

1. Should audio-only frames (no speech for N seconds) skip speech detector? Current design always runs.
2. How to handle audio codec detection/transcoding? Currently assumes supported format.
3. Should we allow custom profanity keyword files per user? (Scope for future)
4. Multi-language profanity: start with EN, ES, FR or broader set?
