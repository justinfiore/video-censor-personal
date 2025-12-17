"""End-to-end analysis pipeline for video processing.

Orchestrates video extraction, frame sampling, detection pipeline execution,
and result aggregation.
"""

import logging
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from video_censor_personal.detection import DetectionPipeline, get_detector_registry
from video_censor_personal.frame import DetectionResult
from video_censor_personal.model_manager import ModelManager, ModelDownloadError
from video_censor_personal.output import generate_json_output, merge_segments
from video_censor_personal.progress import DebugOutput, VideoProgressBar
from video_censor_personal.segments_loader import (
    load_segments_from_json,
    segments_to_detections,
    SegmentsLoadError,
)
from video_censor_personal.video_extraction import VideoExtractor

logger = logging.getLogger(__name__)


class AnalysisPipeline:
    """Orchestrates end-to-end video analysis workflow.

    Coordinates:
    1. Video frame extraction at configured sample rate
    2. Detection pipeline execution on sampled frames
    3. Result aggregation and merging
    4. JSON output generation

    Attributes:
        video_path: Path to the input video file.
        config: Configuration dictionary with detectors and processing settings.
        extractor: VideoExtractor instance for frame/audio extraction.
        detection_pipeline: DetectionPipeline instance for detector orchestration.
    """

    def __init__(
        self,
        video_path: str,
        config: Dict[str, Any],
        detector_list: Optional[List[Dict[str, Any]]] = None,
        output_video_path: Optional[str] = None,
        skip_model_check: bool = False,
        log_level: str = "INFO",
    ) -> None:
        """Initialize the analysis pipeline.

        Args:
            video_path: Path to the input video file.
            config: Configuration dictionary with analysis settings.
            detector_list: Optional list of detector configs. If None, uses config['detectors'].
            output_video_path: Optional path for output video with remediated audio.
            skip_model_check: If True, skip model verification (legacy behavior).
            log_level: Logging level (INFO, DEBUG, TRACE).

        Raises:
            FileNotFoundError: If video file does not exist.
            ValueError: If configuration or detectors are invalid.
        """
        self.video_path = Path(video_path)
        if not self.video_path.exists():
            raise FileNotFoundError(f"Video file not found: {self.video_path}")

        self.config = config
        self.output_video_path = output_video_path
        self.log_level = log_level
        self.trace_enabled = log_level == "TRACE"
        self.debug_output = DebugOutput(enabled=self.trace_enabled)
        self.extractor: Optional[VideoExtractor] = None
        self.detection_pipeline: Optional[DetectionPipeline] = None
        self.remediated_audio_path: Optional[str] = None
        self.video_remediated_path: Optional[str] = None
        self._model_manager: Optional[ModelManager] = None
        self._models_verified = False

        # Prepare detector configuration
        detector_configs = detector_list or config.get("detectors")
        if not detector_configs:
            # Fall back to auto-discovery from detections section
            detector_configs = self._auto_discover_detectors(config)

        # Create pipeline config with detectors
        self._pipeline_config = {"detectors": detector_configs}
        
        # Initialize detection pipeline immediately
        self._ensure_detection_pipeline()

        logger.info(
            f"Initialized AnalysisPipeline for video: {self.video_path} "
            f"with {len(self.detection_pipeline.detectors)} detector(s)"
        )

    def verify_models(self, download: bool = False) -> bool:
        """Verify required models are available.

        Extracts model requirements from configuration and verifies availability.
        Optionally downloads missing models.

        Args:
            download: If True, auto-download missing models.

        Returns:
            True if all required models verified, False if optional models missing.

        Raises:
            ModelDownloadError: If required model download fails.
        """
        if self._models_verified:
            logger.debug("Models already verified, skipping")
            return True

        try:
            # Extract model requirements from config
            required_models = self._extract_model_requirements()
            if not required_models:
                logger.debug("No models required in configuration")
                self._models_verified = True
                return True

            logger.info(f"Verifying {len(required_models)} model(s)")

            # Create Config wrapper for ModelManager
            from video_censor_personal.config import Config, ModelsConfig, ModelSource

            config_obj = Config()
            sources = []
            for model_name in required_models:
                # Find model in config.models.sources
                if "models" in self.config and "sources" in self.config["models"]:
                    for source_data in self.config["models"]["sources"]:
                        if source_data.get("name") == model_name:
                            sources.append(
                                ModelSource(
                                    name=source_data["name"],
                                    url=source_data["url"],
                                    checksum=source_data["checksum"],
                                    size_bytes=source_data["size_bytes"],
                                    algorithm=source_data.get("algorithm", "sha256"),
                                    optional=source_data.get("optional", False),
                                )
                            )
                            break

            if sources:
                config_obj.models = ModelsConfig(
                    cache_dir=self.config.get("models", {}).get("cache_dir"),
                    sources=sources,
                )

                self._model_manager = ModelManager(config_obj)

                if download:
                    # Auto-download missing models
                    logger.info("Auto-downloading missing models")
                    results = self._model_manager.verify_models()

                    # Check if any required models failed
                    failed = [
                        name for name, success in results.items() if not success
                    ]
                    if failed:
                        raise ModelDownloadError(
                            f"Required models failed to verify: {', '.join(failed)}"
                        )
                    logger.info("All models verified successfully")
                else:
                    # Just check existence
                    all_valid = all(
                        self._model_manager.is_model_valid(source.name)
                        for source in sources
                    )
                    if not all_valid:
                        raise ModelDownloadError(
                            "Required models missing. Use --download-models to auto-download."
                        )
                    logger.info("All models verified successfully")

            self._models_verified = True
            return True

        except ModelDownloadError:
            logger.error("Model verification failed")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during model verification: {e}")
            raise

    def _extract_model_requirements(self) -> List[str]:
        """Extract model names required by detectors from configuration.

        Returns:
            List of model names required by detectors.
        """
        required_models = []

        # Check detectors section for model references
        detectors = self.config.get("detectors", [])
        for detector_config in detectors:
            model_name = detector_config.get("model_name")
            if model_name:
                required_models.append(model_name)

        # Also check models.sources for referenced models
        if "models" in self.config and "sources" in self.config["models"]:
            for source in self.config["models"]["sources"]:
                name = source.get("name")
                if name and not source.get("optional", False):
                    required_models.append(name)

        return list(set(required_models))  # Remove duplicates

    def _ensure_detection_pipeline(self) -> None:
        """Lazily initialize detection pipeline (after model verification).

        Creates DetectionPipeline with lazy_init=True to defer model loading.
        Models are loaded on-demand to avoid having audio and video models
        in memory simultaneously.
        """
        if self.detection_pipeline is None:
            logger.debug("Initializing detection pipeline with lazy loading")
            self.detection_pipeline = DetectionPipeline(
                self._pipeline_config,
                lazy_init=True,
            )
            logger.info("Detection pipeline initialized (lazy loading enabled)")

    def _auto_discover_detectors(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Auto-discover detector configuration from detections section.

        Generates a default LLaVA detector covering all enabled categories.

        Args:
            config: Configuration dictionary.

        Returns:
            List of detector configuration dictionaries.
        """
        detections = config.get("detections", {})
        enabled_categories = [
            cat for cat, cat_config in detections.items()
            if isinstance(cat_config, dict) and cat_config.get("enabled")
        ]

        if not enabled_categories:
            logger.warning("No enabled detection categories found; using empty detector list")
            return []

        # Capitalize category names for detector
        categories = [cat.capitalize() for cat in enabled_categories]

        # Return default LLaVA detector
        return [
            {
                "type": "llava",
                "name": "llava-vision",
                "categories": categories,
                "model_name": "liuhaotian/llava-v1.5-7b",
            }
        ]

    def analyze(self) -> List[DetectionResult]:
        """Run end-to-end analysis pipeline on video.

        Extracts frames at configured sample rate, runs detection pipeline
        on each frame, applies audio remediation if enabled, and muxes
        remediated audio back into video if output path specified.

        Returns:
            List of DetectionResult objects from all frames.

        Raises:
            RuntimeError: If video extraction or detection fails.
        """
        logger.info(f"Starting analysis of video: {self.video_path}")
        all_results: List[DetectionResult] = []

        try:
            # Lazy initialize detection pipeline (after any model verification)
            self._ensure_detection_pipeline()

            # Initialize extractor
            self.extractor = VideoExtractor(str(self.video_path))
            
            video_duration = self.extractor.get_duration_seconds()
            video_fps = self.extractor.get_fps()
            video_frame_count = self.extractor.get_frame_count()
            
            logger.debug(
                f"Video info: {video_frame_count} frames, "
                f"{video_fps:.2f} fps, "
                f"{video_duration:.2f} seconds"
            )
            
            # Debug output for video info
            self.debug_output.section("Video Analysis Started")
            self.debug_output.detail("Input file", str(self.video_path))
            self.debug_output.detail("Duration", f"{video_duration:.2f} seconds")
            self.debug_output.detail("FPS", f"{video_fps:.2f}")
            self.debug_output.detail("Total frames", video_frame_count)
            self.debug_output.detail("Detectors", len(self.detection_pipeline.detectors))
            for detector in self.detection_pipeline.detectors:
                self.debug_output.detail(f"  - {detector.name}", detector.categories)

            # Get sample rate from config
            from video_censor_personal.config import get_sample_rate_from_config
            sample_rate = get_sample_rate_from_config(self.config)
            logger.debug(f"Frame sample rate: {sample_rate} seconds")
            
            # Calculate estimated frame count for progress
            estimated_frames = int(video_duration / sample_rate) if sample_rate > 0 else video_frame_count
            self.debug_output.detail("Sample rate", f"{sample_rate} seconds")
            self.debug_output.detail("Estimated frames to analyze", estimated_frames)

            # Extract audio once for all detectors
            # Keep original audio for remediation; use downsampled copy for detection
            audio_data_original = None
            audio_sample_rate_original = None
            audio_data_for_detection = None
            
            # Check if we have any detector configs (lazy loading means detectors list may be empty)
            has_detectors = len(self.detection_pipeline._detector_configs) > 0
            
            if has_detectors:
                try:
                    audio_segment = self.extractor.extract_audio()
                    audio_data_original = audio_segment.data
                    audio_sample_rate_original = audio_segment.sample_rate
                    logger.debug(
                        f"Extracted audio: {audio_segment.duration():.2f} seconds, "
                        f"sample rate: {audio_sample_rate_original} Hz"
                    )
                except Exception as e:
                    logger.warning(f"Failed to extract audio (continuing without it): {e}")

            # Convert audio to numpy array if needed
            if audio_data_original is not None:
                try:
                    import numpy as np
                    import soundfile as sf
                    import io
                    import librosa
                    
                    # If audio_data is bytes (from WAV file), convert to numpy
                    if isinstance(audio_data_original, bytes):
                        audio_np, sr = sf.read(
                            io.BytesIO(audio_data_original),
                            dtype='float32'
                        )
                        audio_sample_rate_original = sr
                        
                        # Log channel count
                        if len(audio_np.shape) > 1:
                            num_channels = audio_np.shape[1]
                            logger.debug(f"Audio has {num_channels} channels")
                        else:
                            logger.debug("Audio is mono")
                    else:
                        audio_np = audio_data_original
                    
                    # Keep original multi-channel audio for remediation
                    audio_data_original = audio_np
                    
                    # For detection: downsample to 16kHz and convert to mono
                    # Whisper and audio classification models expect 16kHz mono
                    audio_for_detection = audio_np
                    
                    # Convert to mono if needed
                    if len(audio_for_detection.shape) > 1:
                        logger.debug(
                            f"Converting {audio_for_detection.shape[1]}-channel audio "
                            f"to mono for detection"
                        )
                        audio_for_detection = audio_for_detection.mean(axis=1)
                    
                    # Resample to 16kHz if needed
                    if audio_sample_rate_original and audio_sample_rate_original != 16000:
                        logger.debug(
                            f"Downsampling audio from {audio_sample_rate_original} Hz "
                            f"to 16000 Hz for detection"
                        )
                        audio_data_for_detection = librosa.resample(
                            audio_for_detection,
                            orig_sr=audio_sample_rate_original,
                            target_sr=16000
                        )
                    else:
                        audio_data_for_detection = audio_for_detection
                        
                except Exception as e:
                    logger.warning(f"Failed to convert audio to numpy: {e}")
                    audio_data_original = None
                    audio_data_for_detection = None

            # Run full-audio detectors once (e.g., speech-profanity)
            # Initialize audio detectors first (lazy loading)
            if audio_data_for_detection is not None:
                self.debug_output.subsection("Full Audio Analysis")
                self.detection_pipeline.initialize_audio_detectors()
                audio_results = self.detection_pipeline.analyze_full_audio(
                    audio_data_for_detection,
                    sample_rate=16000,
                )
                all_results.extend(audio_results)
                if audio_results:
                    logger.info(f"Full audio analysis found {len(audio_results)} detections")

                # Clean up audio detectors to free GPU memory before loading video models
                logger.debug("Cleaning up audio detectors to free GPU memory")
                self.detection_pipeline.cleanup_audio_detectors()

            # Initialize frame detectors (lazy loading - after audio cleanup)
            self.detection_pipeline.initialize_frame_detectors()
            frame_detectors = self.detection_pipeline.get_frame_detectors()

            self.debug_output.subsection("Frame Analysis")
            frame_count = 0

            if not frame_detectors:
                logger.info("No frame-based detectors configured; skipping frame analysis")
            else:
                # Create progress bar (disable in TRACE mode to avoid cluttering output)
                with VideoProgressBar(
                    total_duration=video_duration,
                    description="Analyzing video",
                    disable=self.trace_enabled,
                ) as progress:
                    for frame in self.extractor.extract_frames(sample_rate=sample_rate):
                        try:
                            frame_count += 1
                            logger.debug(f"Analyzing frame {frame.index} at {frame.timestamp_str()}")
                            
                            # Update progress bar
                            progress.update(frame.timecode)

                            # Run detection pipeline on frame (using downsampled audio for detection)
                            results = self.detection_pipeline.analyze_frame(
                                frame,
                                audio_data=audio_data_for_detection
                            )
                            all_results.extend(results)

                            # Trace output for frame (only in TRACE mode)
                            if self.trace_enabled:
                                self.debug_output.frame_info(
                                    frame.index,
                                    frame.timecode,
                                    len(results),
                                )
                                for result in results:
                                    self.debug_output.detector_result(
                                        getattr(result, 'detector_name', None) or "unknown",
                                        result.label,
                                        result.confidence,
                                    )

                            if results:
                                logger.debug(
                                    f"Frame {frame.index}: {len(results)} detection(s) found"
                                )

                        except Exception as e:
                            logger.error(
                                f"Error analyzing frame {frame.index}: {e}",
                                exc_info=True,
                            )
                            self.debug_output.info(f"ERROR on frame {frame.index}: {e}")
                            # Continue with next frame
                            continue

            logger.info(
                f"Analysis complete: {frame_count} frames analyzed, "
                f"{len(all_results)} total detections found"
            )
            
            # Debug summary
            self.debug_output.subsection("Analysis Summary")
            self.debug_output.detail("Frames analyzed", frame_count)
            self.debug_output.detail("Total detections", len(all_results))
            
            # Count detections by label
            label_counts: Dict[str, int] = {}
            for result in all_results:
                label_counts[result.label] = label_counts.get(result.label, 0) + 1
            for label, count in sorted(label_counts.items()):
                self.debug_output.detail(f"  {label}", count)

        finally:
            # Cleanup detectors BEFORE post-processing to free model memory
            # This ensures large models (CLIP, LLaVA) are unloaded before audio remediation
            # and video muxing, which don't require ML models
            # BUT: Don't close the extractor yet - we need it for video remediation
            logger.debug("Cleaning up detection models before post-processing")
            if self.detection_pipeline is not None:
                try:
                    self.detection_pipeline.cleanup()
                    logger.debug("Cleaned up detection pipeline")
                except Exception as e:
                    logger.error(f"Error cleaning up detection pipeline: {e}")
        
        # Post-processing happens AFTER models are unloaded
        # Order is important: audio first (original timings), then video (may shift timings)
        # This includes audio remediation, video remediation and video muxing (I/O operations that don't need models)
        try:
            # Merge detection segments for video remediation
            merge_threshold = self.config.get("processing", {}).get(
                "segment_merge", {}
            ).get("merge_threshold", 2.0)
            merged_segments = merge_segments(all_results, threshold=merge_threshold)
            
            self._apply_audio_remediation(
                audio_data_original,
                audio_sample_rate_original,
                all_results
            )
            self._apply_video_remediation(merged_segments)
            self._mux_remediated_audio()
        except Exception as e:
            logger.error(f"Post-processing failed: {e}", exc_info=True)
            self.debug_output.info(f"ERROR: Post-processing failed: {e}")
            raise
        finally:
            # NOW close the extractor after video remediation is done
            if self.extractor is not None:
                try:
                    self.extractor.close()
                    logger.debug("Closed video extractor")
                except Exception as e:
                    logger.error(f"Error closing extractor: {e}")
                self.extractor = None

        return all_results

    def _apply_video_remediation(
        self,
        segments: List[Dict[str, Any]],
    ) -> None:
        """Apply video remediation if enabled and output video path specified.

        This is called AFTER audio remediation, so we can apply matching cuts to audio.
        Video remediation modifies the output video file (or creates it if not yet existing).

        Args:
            segments: List of merged segment dictionaries to use for video remediation.
        """
        # Check if video remediation is enabled
        video_config = self.config.get("remediation", {}).get("video", {})
        if not video_config.get("enabled", False):
            logger.debug("Video remediation disabled")
            return

        if not self.output_video_path:
            logger.warning(
                "Video remediation enabled but --output-video not specified. Skipping."
            )
            return

        try:
            from video_censor_personal.video_remediator import VideoRemediator
            from video_censor_personal.frame import DetectionResult

            # Get video dimensions
            if not self.extractor:
                logger.error("Video extractor not initialized for video remediation")
                return

            try:
                video_width = self.extractor.get_video_width()
                video_height = self.extractor.get_video_height()
                video_duration = self.extractor.get_duration_seconds()
            except Exception as e:
                logger.error(f"Failed to get video metadata: {e}")
                return

            self.debug_output.subsection("Video Remediation")
            self.debug_output.step(f"Applying video remediation...")
            self.debug_output.detail("Mode", video_config.get("mode", "blank"))
            self.debug_output.detail("Output video", self.output_video_path)

            logger.info(f"Using {len(segments)} merged segments for video remediation")
            self.debug_output.detail("Segments", len(segments))

            # Convert merged segments (with float times) to remediator format (with string timecodes)
            remediation_segments = self._format_segments_for_remediation(segments)

            if not remediation_segments:
                logger.info("No segments to remediate; copying input video to output")
                import shutil
                shutil.copy2(str(self.video_path), self.output_video_path)
                self.debug_output.step("No segments to remediate; video copied")
                return

            # Initialize VideoRemediator
            remediator = VideoRemediator(video_config)

            import tempfile
            from pathlib import Path

            # Determine input video for video remediation
            if self.remediated_audio_path:
                # Audio was remediated; we need to apply video remediation to a video
                # that will later have the remediated audio muxed into it
                # Use a temp file to avoid modifying intermediate state
                with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
                    video_temp_path = tmp.name

                self.video_remediated_path = video_temp_path
                logger.debug(f"Using temp path for video remediation (after audio): {video_temp_path}")

                # Apply video remediation to original video
                # (audio was already extracted and remediated separately)
                remediator.apply(
                    str(self.video_path),
                    video_temp_path,
                    remediation_segments,
                    video_duration,
                    video_width,
                    video_height,
                )

                logger.info(f"Video remediation saved to temporary file: {video_temp_path}")
                self.debug_output.step(f"Video remediation complete (temporary file)")

                # If video was cut, apply the same cuts to remediated audio to maintain sync
                grouped = remediator.group_segments_by_mode(remediator.filter_allowed_segments(remediation_segments))
                if len(grouped["cut"]) > 0:
                    self.debug_output.step("Applying matching cuts to remediated audio...")
                    self._apply_matching_cuts_to_audio(grouped["cut"], video_duration)

            else:
                # No audio remediation; write directly to output
                remediator.apply(
                    str(self.video_path),
                    self.output_video_path,
                    remediation_segments,
                    video_duration,
                    video_width,
                    video_height,
                )

                logger.info(f"Video remediation saved to: {self.output_video_path}")
                self.debug_output.step(f"Video remediation complete")

        except Exception as e:
            logger.error(f"Video remediation failed: {e}", exc_info=True)
            self.debug_output.info(f"ERROR: Video remediation failed: {e}")
            raise

    def _apply_matching_cuts_to_audio(
        self,
        cut_segments: List[Dict[str, Any]],
        video_duration: float,
    ) -> None:
        """Apply matching cuts to remediated audio to maintain video/audio sync.

        When video is cut, the audio must be cut at the same points to avoid sync issues.

        Args:
            cut_segments: List of segments marked for cutting.
            video_duration: Total video duration in seconds.
        """
        if not self.remediated_audio_path:
            logger.debug("No remediated audio to cut")
            return

        if not Path(self.remediated_audio_path).exists():
            logger.warning(f"Remediated audio file not found: {self.remediated_audio_path}")
            return

        try:
            from video_censor_personal.video_remediator import VideoRemediator
            import tempfile

            # Create a temporary VideoRemediator just to use its segment extraction logic
            remediator = VideoRemediator({"enabled": True, "mode": "cut"})

            # Extract non-censored segments (keep segments)
            keep_segments = remediator.extract_non_censored_segments(cut_segments, video_duration)

            logger.info(f"Cutting audio at same points as video: keeping {len(keep_segments)} segments")
            self.debug_output.detail("Audio segments to keep", len(keep_segments))

            if not keep_segments:
                logger.warning("No audio segments to keep; all audio will be removed")
                return

            # Create temp file for cut audio
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                cut_audio_path = tmp.name

            # Extract and concatenate audio segments
            segment_files = []

            try:
                for i, segment in enumerate(keep_segments):
                    segment_file = Path(tempfile.gettempdir()) / f"audio_segment_{i}.wav"

                    # Extract audio segment using ffmpeg
                    cmd = [
                        "ffmpeg",
                        "-i", self.remediated_audio_path,
                        "-ss", str(segment["start"]),
                        "-to", str(segment["end"]),
                        "-y",
                        str(segment_file)
                    ]

                    logger.debug(f"Extracting audio segment {i}: {segment['start']}-{segment['end']}")
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=300
                    )

                    if result.returncode != 0:
                        raise RuntimeError(f"Failed to extract audio segment {i}: {result.stderr}")

                    segment_files.append(segment_file)

                # Concatenate audio segments
                concat_file = Path(tempfile.gettempdir()) / "audio_concat.txt"
                with open(concat_file, "w") as f:
                    for segment_file in segment_files:
                        f.write(f"file '{segment_file}'\n")

                cmd = [
                    "ffmpeg",
                    "-f", "concat",
                    "-safe", "0",
                    "-i", str(concat_file),
                    "-c", "copy",
                    "-y",
                    cut_audio_path
                ]

                logger.debug(f"Concatenating {len(segment_files)} audio segments")
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300
                )

                if result.returncode != 0:
                    raise RuntimeError(f"Failed to concatenate audio segments: {result.stderr}")

                # Replace remediated audio with cut version
                import shutil
                shutil.move(cut_audio_path, self.remediated_audio_path)
                logger.info(f"Updated remediated audio with cuts: {self.remediated_audio_path}")
                self.debug_output.step(f"Audio cuts applied")

            finally:
                # Clean up temporary files
                for segment_file in segment_files:
                    try:
                        segment_file.unlink(missing_ok=True)
                    except Exception as e:
                        logger.warning(f"Failed to clean up temp audio segment: {e}")

                try:
                    concat_file.unlink(missing_ok=True)
                except Exception as e:
                    logger.warning(f"Failed to clean up temp concat file: {e}")

        except Exception as e:
            logger.error(f"Failed to apply matching cuts to audio: {e}", exc_info=True)
            self.debug_output.info(f"WARNING: Audio cuts failed (continuing): {e}")
            # Don't raise - continue with mismatched audio/video rather than fail completely

    def _format_segments_for_remediation(
        self,
        merged_segments: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Format merged segments for video remediator.

        The video remediator's _parse_timecode method handles both float seconds
        and HH:MM:SS format, so we pass through the float seconds directly to preserve
        precision for short segments (e.g., 0.033 seconds).

        Args:
            merged_segments: List of merged segment dicts with float times.

        Returns:
            List of segments with start_time/end_time as floats.
        """
        formatted = []
        for segment in merged_segments:
            formatted_segment = {
                "start_time": segment["start_time"],  # Keep as float (seconds)
                "end_time": segment["end_time"],      # Keep as float (seconds)
                "labels": segment.get("labels", []),
            }
            
            # Copy over other fields if present
            if "confidence" in segment:
                formatted_segment["confidence"] = segment["confidence"]
            if "allow" in segment:
                formatted_segment["allow"] = segment["allow"]
            if "detections" in segment:
                formatted_segment["detections"] = segment["detections"]
                
            formatted.append(formatted_segment)
        
        return formatted

    def _detections_to_segments(
        self,
        detections: List[DetectionResult],
    ) -> List[Dict[str, Any]]:
        """Convert DetectionResult objects to segment dictionaries.

        Args:
            detections: List of DetectionResult objects from analysis.

        Returns:
            List of segment dictionaries with start_time, end_time, labels, etc.
        """
        segments = []

        for detection in detections:
            # Skip if timecode is invalid
            if not hasattr(detection, 'timecode') or detection.timecode is None:
                continue

            segment = {
                "start_time": detection.timecode,
                "end_time": detection.timecode,  # Point detection; end == start
                "labels": detection.categories if hasattr(detection, 'categories') else [],
            }

            # Add confidence if available
            if hasattr(detection, 'confidence') and detection.confidence is not None:
                segment["confidence"] = detection.confidence

            # Add detector name if available
            if hasattr(detection, 'detector_name') and detection.detector_name:
                segment["detector"] = detection.detector_name

            segments.append(segment)

        return segments

    def _apply_audio_remediation(
        self,
        audio_data_original: Optional[Any],
        audio_sample_rate_original: Optional[int],
        detections: List[DetectionResult],
    ) -> None:
        """Apply audio remediation if enabled and audio data is available.

        This is called AFTER detection models are unloaded to minimize memory usage.

        Args:
            audio_data_original: Original audio data at native sample rate.
            audio_sample_rate_original: Original sample rate of audio.
            detections: List of detection results to use for remediation.
        """
        # Apply audio remediation if enabled
        remediation_config = self.config.get("remediation", {}).get("audio", {})
        if remediation_config.get("enabled", False) and audio_data_original is not None:
            self.debug_output.subsection("Audio Remediation")
            self.debug_output.step("Applying audio remediation...")
            self.debug_output.detail("Method", remediation_config.get("method", "silence"))
            self.debug_output.detail("Sample rate", f"{audio_sample_rate_original or 48000} Hz")
            
            try:
                from video_censor_personal.audio_remediator import AudioRemediator
                
                remediator = AudioRemediator(remediation_config)
                remediated_audio = remediator.remediate(
                    audio_data_original,
                    audio_sample_rate_original or 48000,
                    detections
                )
                
                # Write remediated audio at original sample rate
                output_audio_path = remediation_config.get(
                    "output_path",
                    "/tmp/remediated_audio.wav"
                )
                remediator.write_audio(
                    remediated_audio,
                    audio_sample_rate_original or 48000,
                    output_audio_path
                )
                self.remediated_audio_path = output_audio_path
                logger.info(
                    f"Remediated audio saved to: {output_audio_path} "
                    f"({audio_sample_rate_original or 48000} Hz)"
                )
                self.debug_output.step(f"Audio saved to: {output_audio_path}")
                
            except Exception as e:
                logger.error(f"Audio remediation failed: {e}", exc_info=True)
                self.debug_output.info(f"ERROR: Audio remediation failed: {e}")
                raise

    def _mux_remediated_audio(self) -> None:
        """Mux remediated audio into video if enabled.

        This is called AFTER detection models are unloaded to minimize memory usage.
        
        If video_remediated_path exists, uses that as the video source (video remediation was applied).
        Otherwise, if output_video_path already exists (pre-created), uses that.
        Otherwise uses the original video.
        """
        # Mux remediated audio into video if output path specified
        if self.remediated_audio_path and self.output_video_path:
            self.debug_output.subsection("Video Muxing")
            self.debug_output.step("Muxing remediated audio into video...")
            
            try:
                from video_censor_personal.video_muxer import VideoMuxer
                from pathlib import Path
                import tempfile
                import shutil
                
                # Determine video source based on what's been applied:
                # 1. If video was remediated, use that file
                # 2. If output video pre-created (for skip chapters), use that
                # 3. Otherwise use original
                if self.video_remediated_path:
                    video_source = self.video_remediated_path
                    logger.debug("Using video-remediated file as source for audio muxing")
                elif Path(self.output_video_path).exists():
                    video_source = self.output_video_path
                    logger.debug("Using pre-existing output video file as source for audio muxing")
                else:
                    video_source = str(self.video_path)
                    logger.debug("Using original video as source for audio muxing")
                
                muxer = VideoMuxer(video_source, self.remediated_audio_path)
                
                # Always use a temp file to avoid ffmpeg's limitation of not being able
                # to read and write the same file in-place
                # Create temporary output
                with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
                    temp_output = tmp.name
                
                muxer.mux_video(temp_output)
                
                # Replace the output file with the muxed version
                shutil.move(temp_output, self.output_video_path)
                logger.debug(f"Moved temp muxed video to: {self.output_video_path}")
                
                logger.info(f"Output video saved to: {self.output_video_path}")
                self.debug_output.step(f"Output video saved to: {self.output_video_path}")
                
                # Clean up temporary video remediation file if it exists
                if self.video_remediated_path:
                    try:
                        Path(self.video_remediated_path).unlink(missing_ok=True)
                        logger.debug(f"Cleaned up temporary video remediation file")
                    except Exception as e:
                        logger.warning(f"Failed to clean up temp video file: {e}")
                
            except Exception as e:
                logger.error(f"Video muxing failed: {e}", exc_info=True)
                self.debug_output.info(f"ERROR: Video muxing failed: {e}")
                raise

    def cleanup(self) -> None:
        """Clean up pipeline resources (extractor, detectors).

        Called automatically at end of analyze(), but can be called explicitly
        to free resources early.
        """
        if self.extractor is not None:
            try:
                self.extractor.close()
                logger.debug("Closed video extractor")
            except Exception as e:
                logger.error(f"Error closing extractor: {e}")
            self.extractor = None

        if self.detection_pipeline is not None:
            try:
                self.detection_pipeline.cleanup()
                logger.debug("Cleaned up detection pipeline")
            except Exception as e:
                logger.error(f"Error cleaning up detection pipeline: {e}")

    def __enter__(self) -> "AnalysisPipeline":
        """Context manager entry.

        Returns:
            Self for use in with statement.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit.

        Ensures cleanup happens even if exceptions occur.
        """
        self.cleanup()


class AnalysisRunner:
    """Helper class to run analysis pipeline from CLI.

    Wraps AnalysisPipeline to handle end-to-end execution including
    output generation.
    """

    def __init__(
        self,
        video_path: str,
        config: Dict[str, Any],
        config_path: str,
        output_video_path: Optional[str] = None,
        log_level: str = "INFO",
        allow_all_segments: bool = False,
    ) -> None:
        """Initialize analysis runner.

        Args:
            video_path: Path to input video file.
            config: Configuration dictionary.
            config_path: Path to configuration file (for metadata).
            output_video_path: Optional path for output video with remediated audio.
            log_level: Logging level (INFO, DEBUG, TRACE).
            allow_all_segments: If True, mark all detected segments with 'allow: true' in output.
        """
        self.video_path = video_path
        self.config = config
        self.config_path = config_path
        self.output_video_path = output_video_path
        self.log_level = log_level
        self.allow_all_segments = allow_all_segments
        self.trace_enabled = log_level == "TRACE"
        self.debug_output = DebugOutput(enabled=self.trace_enabled)

    def run(self, output_path: str) -> Dict[str, Any]:
        """Run analysis and generate JSON output.

        Args:
            output_path: Path where JSON output should be written.

        Returns:
            Output dictionary that was written to file.

        Raises:
            Exception: If analysis or output generation fails.
        """
        logger.info(f"Running analysis: {self.video_path} -> {output_path}")
        if self.output_video_path:
            logger.info(f"Output video: {self.output_video_path}")
            
        # Debug output for configuration
        self.debug_output.section("Configuration")
        self.debug_output.detail("Input video", self.video_path)
        self.debug_output.detail("Output JSON", output_path)
        self.debug_output.detail("Output video", self.output_video_path or "None")
        self.debug_output.detail("Config file", self.config_path)

        with AnalysisPipeline(
            self.video_path,
            self.config,
            output_video_path=self.output_video_path,
            log_level=self.log_level,
        ) as pipeline:
            # Run analysis
            detections = pipeline.analyze()

            # Get video duration
            extractor = VideoExtractor(str(self.video_path))
            try:
                video_duration = extractor.get_duration_seconds()
            finally:
                extractor.close()

            # Merge detection segments
            merge_threshold = self.config.get("processing", {}).get(
                "segment_merge", {}
            ).get("merge_threshold", 2.0)
            merged_segments = merge_segments(detections, threshold=merge_threshold)

            # Apply allow flag to all segments if requested
            if self.allow_all_segments:
                logger.info(f"Marking all {len(merged_segments)} detected segments as allowed")
                for segment in merged_segments:
                    segment["allow"] = True

            # Generate output
            output_dict = generate_json_output(
                merged_segments,
                self.video_path,
                video_duration,
                self.config_path,
                self.config,
            )

            # Store raw merged segments for skip chapter writing
            # (before they get formatted as strings in JSON output)
            output_dict["_raw_merged_segments"] = merged_segments

            # Write output (excluding internal fields like _raw_merged_segments)
            from video_censor_personal.output import write_output
            output_to_write = {k: v for k, v in output_dict.items() if not k.startswith("_")}
            write_output(output_to_write, output_path, self.config)

            logger.info(f"Analysis complete. Output written to: {output_path}")
            return output_dict


class RemediationRunner:
    """Runner for remediation-only mode (no analysis).

    Loads segments from a pre-existing JSON file and applies remediation
    (audio, video, chapters) without running detection.
    """

    def __init__(
        self,
        video_path: str,
        segments_path: str,
        config: Dict[str, Any],
        output_video_path: Optional[str] = None,
        log_level: str = "INFO",
    ) -> None:
        """Initialize remediation runner.

        Args:
            video_path: Path to input video file.
            segments_path: Path to segments JSON from previous analysis.
            config: Configuration dictionary.
            output_video_path: Path for output video with remediated audio.
            log_level: Logging level (INFO, DEBUG, TRACE).
        """
        self.video_path = video_path
        self.segments_path = segments_path
        self.config = config
        self.output_video_path = output_video_path
        self.log_level = log_level
        self.trace_enabled = log_level == "TRACE"
        self.debug_output = DebugOutput(enabled=self.trace_enabled)

    def run(self) -> Dict[str, Any]:
        """Run remediation using loaded segments.

        Returns:
            Dictionary with loaded segments and metadata.

        Raises:
            SegmentsLoadError: If segments file is invalid.
            Exception: If remediation fails.
        """
        logger.info(f"Running remediation-only mode")
        logger.info(f"  Video: {self.video_path}")
        logger.info(f"  Segments: {self.segments_path}")
        if self.output_video_path:
            logger.info(f"  Output video: {self.output_video_path}")

        self.debug_output.section("Remediation-Only Mode")
        self.debug_output.detail("Input video", self.video_path)
        self.debug_output.detail("Segments file", self.segments_path)
        self.debug_output.detail("Output video", self.output_video_path or "None")

        extractor = VideoExtractor(str(self.video_path))
        try:
            video_duration = extractor.get_duration_seconds()
        finally:
            extractor.close()

        loaded = load_segments_from_json(
            self.segments_path,
            video_path=self.video_path,
            video_duration=video_duration,
        )

        segments = loaded["segments"]
        metadata = loaded["metadata"]

        logger.info(f"Loaded {len(segments)} segments from JSON")
        self.debug_output.detail("Segments loaded", len(segments))

        allowed_count = sum(1 for s in segments if s.get("allow", False))
        if allowed_count > 0:
            logger.info(f"  {allowed_count} segment(s) marked as allowed (will be skipped)")
            self.debug_output.detail("Allowed segments", allowed_count)

        detections = segments_to_detections(segments)

        self._apply_remediation(detections, segments)

        return {
            "segments": segments,
            "metadata": metadata,
            "_raw_merged_segments": segments,
        }

    def _apply_remediation(
        self,
        detections: List[DetectionResult],
        segments: List[Dict[str, Any]],
    ) -> None:
        """Apply audio remediation and mux video.

        Args:
            detections: Detection results for remediation.
            segments: Original segments (for allow flag checking).
        """
        remediation_config = self.config.get("audio", {}).get("remediation", {})
        if not remediation_config.get("enabled", False):
            logger.info("Audio remediation is disabled in config")
            if not self.output_video_path:
                logger.warning("No output video path specified and remediation is disabled. Nothing to do.")
                return

        audio_data_original = None
        audio_sample_rate_original = None
        remediated_audio_path = None

        if remediation_config.get("enabled", False):
            self.debug_output.subsection("Audio Extraction")
            extractor = VideoExtractor(str(self.video_path))
            try:
                audio_segment = extractor.extract_audio()
                audio_data_original = audio_segment.data
                audio_sample_rate_original = audio_segment.sample_rate
                logger.debug(
                    f"Extracted audio: {audio_segment.duration():.2f} seconds, "
                    f"sample rate: {audio_sample_rate_original} Hz"
                )
            except Exception as e:
                logger.error(f"Failed to extract audio: {e}")
                raise
            finally:
                extractor.close()

            if audio_data_original is not None:
                import numpy as np
                import soundfile as sf
                import io

                if isinstance(audio_data_original, bytes):
                    audio_np, sr = sf.read(
                        io.BytesIO(audio_data_original),
                        dtype='float32'
                    )
                    audio_sample_rate_original = sr
                else:
                    audio_np = audio_data_original

                audio_data_original = audio_np

                self.debug_output.subsection("Audio Remediation")
                self.debug_output.step("Applying audio remediation...")
                self.debug_output.detail("Method", remediation_config.get("mode", "silence"))
                self.debug_output.detail("Sample rate", f"{audio_sample_rate_original} Hz")

                from video_censor_personal.audio_remediator import AudioRemediator

                remediator = AudioRemediator(remediation_config)
                remediated_audio = remediator.remediate(
                    audio_np,
                    audio_sample_rate_original,
                    detections,
                    segments=segments,
                )

                output_audio_path = remediation_config.get(
                    "output_path",
                    "/tmp/remediated_audio.wav"
                )
                remediator.write_audio(
                    remediated_audio,
                    audio_sample_rate_original,
                    output_audio_path
                )
                remediated_audio_path = output_audio_path
                logger.info(f"Remediated audio saved to: {output_audio_path}")
                self.debug_output.step(f"Audio saved to: {output_audio_path}")

        if remediated_audio_path and self.output_video_path:
            self._mux_video(remediated_audio_path)
        elif self.output_video_path and not remediated_audio_path:
            import shutil
            shutil.copy2(self.video_path, self.output_video_path)
            logger.info(f"Copied video to: {self.output_video_path} (no audio remediation)")

    def _mux_video(self, remediated_audio_path: str) -> None:
        """Mux remediated audio into output video.

        Args:
            remediated_audio_path: Path to remediated audio file.
        """
        self.debug_output.subsection("Video Muxing")
        self.debug_output.step("Muxing remediated audio into video...")

        from video_censor_personal.video_muxer import VideoMuxer

        muxer = VideoMuxer(str(self.video_path), remediated_audio_path)
        muxer.mux_video(self.output_video_path)

        logger.info(f"Output video saved to: {self.output_video_path}")
        self.debug_output.step(f"Output video saved to: {self.output_video_path}")
