"""End-to-end analysis pipeline for video processing.

Orchestrates video extraction, frame sampling, detection pipeline execution,
and result aggregation.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from video_censor_personal.detection import DetectionPipeline, get_detector_registry
from video_censor_personal.frame import DetectionResult
from video_censor_personal.model_manager import ModelManager, ModelDownloadError
from video_censor_personal.output import generate_json_output, merge_segments
from video_censor_personal.progress import DebugOutput, VideoProgressBar
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

        Creates DetectionPipeline if not already initialized.
        """
        if self.detection_pipeline is None:
            logger.debug("Initializing detection pipeline")
            self.detection_pipeline = DetectionPipeline(self._pipeline_config)
            logger.info(
                f"Detection pipeline initialized with "
                f"{len(self.detection_pipeline.detectors)} detector(s)"
            )

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
            
            if any(hasattr(d, "detect") for d in self.detection_pipeline.detectors):
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

            # Extract and analyze frames with progress bar
            self.debug_output.subsection("Frame Analysis")
            frame_count = 0
            
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

            # Apply audio remediation if enabled
            # Use original audio (at original sample rate) for remediation
            remediation_config = self.config.get("audio", {}).get("remediation", {})
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
                        all_results
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

            # Mux remediated audio into video if output path specified
            if self.remediated_audio_path and self.output_video_path:
                self.debug_output.subsection("Video Muxing")
                self.debug_output.step("Muxing remediated audio into video...")
                
                try:
                    from video_censor_personal.video_muxer import VideoMuxer
                    
                    muxer = VideoMuxer(str(self.video_path), self.remediated_audio_path)
                    muxer.mux_video(self.output_video_path)
                    logger.info(f"Output video saved to: {self.output_video_path}")
                    self.debug_output.step(f"Output video saved to: {self.output_video_path}")
                    
                except Exception as e:
                    logger.error(f"Video muxing failed: {e}", exc_info=True)
                    self.debug_output.info(f"ERROR: Video muxing failed: {e}")
                    raise

            return all_results

        finally:
            # Cleanup
            self.cleanup()

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
    ) -> None:
        """Initialize analysis runner.

        Args:
            video_path: Path to input video file.
            config: Configuration dictionary.
            config_path: Path to configuration file (for metadata).
            output_video_path: Optional path for output video with remediated audio.
            log_level: Logging level (INFO, DEBUG, TRACE).
        """
        self.video_path = video_path
        self.config = config
        self.config_path = config_path
        self.output_video_path = output_video_path
        self.log_level = log_level
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

            # Generate output
            output_dict = generate_json_output(
                merged_segments,
                self.video_path,
                video_duration,
                self.config_path,
                self.config,
            )

            # Write output
            from video_censor_personal.output import write_output
            write_output(output_dict, output_path, self.config)

            logger.info(f"Analysis complete. Output written to: {output_path}")
            return output_dict
