#!/usr/bin/env python3
"""Main entry point for video-censor-personal application."""

import logging
import sys
import time
from pathlib import Path

from video_censor_personal.cli import parse_args, setup_logging, validate_cli_args
from video_censor_personal.config import ConfigError, load_config, Config, is_skip_chapters_enabled
from video_censor_personal.model_manager import ModelManager, ModelDownloadError
from video_censor_personal.pipeline import AnalysisRunner
from video_censor_personal.video_metadata_writer import write_skip_chapters, VideoMetadataError

logger = logging.getLogger(__name__)


def main() -> int:
    """Main application entry point.

    Returns:
        Exit code (0 for success, non-zero for errors).
    """
    try:
        # Parse command-line arguments
        args = parse_args()

        # Setup logging
        setup_logging(log_level=args.log_level)

        start_time = time.perf_counter()
        logger.info("Starting video-censor-personal")
        logger.debug(f"Input file: {args.input}")
        logger.debug(f"Output file: {args.output}")
        logger.debug(f"Config file: {args.config}")
        if args.output_video:
            logger.debug(f"Output video file: {args.output_video}")

        # Validate input file exists
        input_path = Path(args.input)
        if not input_path.exists():
            logger.error(f"Input file not found: {args.input}")
            return 1

        # Load and validate configuration
        try:
            config_dict = load_config(args.config)
            logger.info("Configuration loaded and validated successfully")
        except ConfigError as e:
            logger.error(f"Configuration error: {e}")
            return 1
        
        # Validate CLI arguments against configuration
        try:
            validate_cli_args(args, config_dict)
        except SystemExit as e:
            return e.code if isinstance(e.code, int) else 1

        # Handle model downloading if requested
        if args.download_models:
            try:
                logger.info("Model auto-download enabled")
                
                # Download detector models (CLIP, LLaVA, etc.)
                from video_censor_personal.detection import DetectionPipeline
                detection_pipeline = DetectionPipeline(config_dict, lazy_init=True)
                detection_pipeline.download_models()
                detection_pipeline.cleanup()
                
                # Also handle external model sources if configured
                config_obj = Config()
                
                # Parse models section from config_dict
                if "models" in config_dict:
                    from video_censor_personal.config import ModelsConfig, ModelSource
                    models_data = config_dict["models"]
                    sources = []
                    if "sources" in models_data and models_data["sources"]:
                        for source_data in models_data["sources"]:
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
                    config_obj.models = ModelsConfig(
                        cache_dir=models_data.get("cache_dir"),
                        sources=sources,
                        auto_download=models_data.get("auto_download", False),
                    )

                    manager = ModelManager(config_obj)
                    results = manager.verify_models()
                    
                    # Check if any required models failed
                    failed_required = [
                        name for name, success in results.items() if not success
                    ]
                    if failed_required:
                        logger.error(
                            f"Required models failed to download: {', '.join(failed_required)}"
                        )
                        return 1
                    
                logger.info("Model verification complete")
                
            except ModelDownloadError as e:
                logger.error(f"Model download error: {e}")
                return 1
            except Exception as e:
                logger.error(f"Unexpected error during model download: {e}", exc_info=True)
                return 1



        # Run analysis pipeline
        try:
            runner = AnalysisRunner(
                args.input,
                config_dict,
                args.config,
                output_video_path=args.output_video,
                log_level=args.log_level,
            )
            output_dict = runner.run(args.output)
            
            # Write skip chapters to video if enabled
            if is_skip_chapters_enabled(config_dict) and args.output_video:
                try:
                    # Use raw merged segments (with numeric timestamps) instead of JSON formatted ones
                    merged_segments = output_dict.get("_raw_merged_segments", [])
                    if merged_segments:
                        logger.info(
                            f"Writing skip chapters to output video: {args.output_video}"
                        )
                        write_skip_chapters(
                            args.input,
                            args.output_video,
                            merged_segments,
                        )
                    else:
                        logger.info(
                            "No detection segments found. Copying video without new chapters."
                        )
                        write_skip_chapters(
                            args.input,
                            args.output_video,
                            [],
                        )
                except VideoMetadataError as e:
                    logger.error(f"Failed to write skip chapters: {e}")
                    # Don't fail the entire pipeline, just log the warning
                    logger.warning(
                        "Continuing with JSON output despite chapter writing failure"
                    )
            
            elapsed_time = time.perf_counter() - start_time
            minutes, seconds = divmod(elapsed_time, 60)
            if minutes >= 1:
                logger.info(f"Processing complete in {int(minutes)}m {seconds:.1f}s")
            else:
                logger.info(f"Processing complete in {elapsed_time:.1f}s")
            return 0

        except Exception as e:
            logger.error(f"Analysis pipeline failed: {e}", exc_info=True)
            return 1

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return 130
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
