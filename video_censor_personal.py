#!/usr/bin/env python3
"""Main entry point for video-censor-personal application."""

import logging
import sys
from pathlib import Path

from video_censor_personal.cli import parse_args, setup_logging
from video_censor_personal.config import ConfigError, load_config, Config
from video_censor_personal.model_manager import ModelManager, ModelDownloadError
from video_censor_personal.pipeline import AnalysisRunner

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
        setup_logging(verbose=args.verbose)

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

        # Handle model downloading if requested
        if args.download_models:
            try:
                logger.info("Model auto-download enabled")
                # Wrap dict config in Config object for ModelManager
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

        # Validate audio remediation and output-video argument
         remediation_enabled = (
             config_dict.get("audio", {})
             .get("remediation", {})
             .get("enabled", False)
         )

         if remediation_enabled and not args.output_video:
             logger.error(
                 "ERROR: Audio remediation is enabled in config, but "
                 "--output-video argument is missing.\n\n"
                 "To use audio remediation, provide output video path:\n"
                 "  python video_censor_personal.py --input video.mp4 "
                 "--config config.yaml --output results.json "
                 "--output-video output.mp4\n\n"
                 "Or disable audio remediation in config:\n"
                 "  audio.remediation.enabled: false"
             )
             return 1

         if args.output_video and not remediation_enabled:
             logger.error(
                 "ERROR: --output-video argument provided, but audio remediation "
                 "is not enabled in config.\n\n"
                 "--output-video requires audio remediation to be enabled.\n"
                 "Enable remediation in config:\n"
                 "  audio.remediation.enabled: true\n\n"
                 "Or remove the --output-video argument."
             )
             return 1

         # Run analysis pipeline
         try:
             runner = AnalysisRunner(
                 args.input,
                 config_dict,
                 args.config,
                 output_video_path=args.output_video,
             )
            runner.run(args.output)
            logger.info("Processing complete")
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
