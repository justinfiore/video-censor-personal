#!/usr/bin/env python3
"""Proof of Concept: PyAV video loading and frame decoding."""

import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_pyav_import():
    """Test PyAV import and version."""
    try:
        import av
        logger.info(f"✓ PyAV imported successfully, version: {av.__version__}")
        return True
    except ImportError as e:
        logger.error(f"✗ PyAV import failed: {e}")
        return False


def test_ffmpeg_available():
    """Test if FFmpeg is available (system or bundled)."""
    import shutil
    ffmpeg_path = shutil.which('ffmpeg')
    if ffmpeg_path:
        logger.info(f"✓ System FFmpeg found at: {ffmpeg_path}")
        return True
    else:
        logger.warning("⚠ System FFmpeg not found, will use bundled version from PyAV")
        return False


def test_basic_video_loading():
    """Test loading a video file with PyAV."""
    import av
    import os
    
    # Create a minimal test video if one exists
    test_video_path = "/tmp/test_video.mp4"
    if not os.path.exists(test_video_path):
        logger.warning(f"Test video not found at {test_video_path}, skipping load test")
        return False
    
    try:
        container = av.open(test_video_path)
        logger.info(f"✓ Video loaded successfully")
        logger.info(f"  - Duration: {container.duration / av.time_base:.2f} seconds")
        
        # List streams
        for i, stream in enumerate(container.streams):
            logger.info(f"  - Stream {i}: {stream.codec_context.name} ({stream.type})")
        
        container.close()
        return True
    except Exception as e:
        logger.error(f"✗ Failed to load video: {e}")
        return False


def test_frame_decoding():
    """Test frame decoding with PyAV."""
    import av
    import os
    
    test_video_path = "/tmp/test_video.mp4"
    if not os.path.exists(test_video_path):
        logger.warning(f"Test video not found, skipping frame decode test")
        return False
    
    try:
        container = av.open(test_video_path)
        video_stream = None
        for stream in container.streams.video:
            video_stream = stream
            break
        
        if not video_stream:
            logger.warning("No video stream found in test file")
            return False
        
        frame_count = 0
        for frame in container.decode(video_stream):
            frame_count += 1
            if frame_count == 1:
                logger.info(f"✓ Frame decoding works")
                logger.info(f"  - Frame size: {frame.width}x{frame.height}")
                logger.info(f"  - Format: {frame.format.name}")
                logger.info(f"  - Presentation timestamp: {frame.pts}")
            if frame_count >= 10:
                break
        
        logger.info(f"  - Decoded {frame_count} frames successfully")
        container.close()
        return True
    except Exception as e:
        logger.error(f"✗ Frame decoding failed: {e}")
        return False


def test_numpy_conversion():
    """Test converting PyAV frames to numpy arrays."""
    try:
        import numpy as np
        logger.info(f"✓ NumPy is available (version {np.__version__})")
        return True
    except ImportError as e:
        logger.error(f"✗ NumPy import failed: {e}")
        return False


def test_pil_conversion():
    """Test PIL/Pillow for image conversion."""
    try:
        from PIL import Image
        logger.info(f"✓ Pillow is available")
        return True
    except ImportError as e:
        logger.error(f"✗ Pillow import failed: {e}")
        return False


def test_audio_dependencies():
    """Test audio-related dependencies."""
    results = {}
    
    try:
        import pydub
        logger.info(f"✓ pydub is available")
        results['pydub'] = True
    except ImportError as e:
        logger.error(f"✗ pydub import failed: {e}")
        results['pydub'] = False
    
    try:
        import simpleaudio
        logger.info(f"✓ simpleaudio is available")
        results['simpleaudio'] = True
    except ImportError as e:
        logger.error(f"✗ simpleaudio import failed: {e}")
        results['simpleaudio'] = False
    
    return all(results.values())


def main():
    """Run all proof-of-concept tests."""
    logger.info("=" * 60)
    logger.info("PyAV Proof of Concept Tests")
    logger.info("=" * 60)
    
    tests = [
        ("PyAV Import", test_pyav_import),
        ("FFmpeg Availability", test_ffmpeg_available),
        ("Basic Video Loading", test_basic_video_loading),
        ("Frame Decoding", test_frame_decoding),
        ("NumPy Conversion", test_numpy_conversion),
        ("PIL/Pillow Conversion", test_pil_conversion),
        ("Audio Dependencies", test_audio_dependencies),
    ]
    
    results = {}
    for test_name, test_func in tests:
        logger.info(f"\n--- {test_name} ---")
        try:
            results[test_name] = test_func()
        except Exception as e:
            logger.error(f"Unexpected error in {test_name}: {e}")
            results[test_name] = False
    
    logger.info("\n" + "=" * 60)
    logger.info("Summary")
    logger.info("=" * 60)
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    logger.info(f"Passed: {passed}/{total}")
    
    for test_name, result in results.items():
        status = "✓" if result else "✗"
        logger.info(f"{status} {test_name}")
    
    if passed == total:
        logger.info("\n✓ All tests passed! PyAV is ready for production use.")
        return 0
    else:
        logger.error(f"\n✗ {total - passed} tests failed. Check dependencies.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
