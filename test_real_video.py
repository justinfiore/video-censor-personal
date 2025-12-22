#!/usr/bin/env python3
"""Quick test to validate PyAV video playback with real files."""

import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_video_file(video_path):
    """Test loading and reading a video file with PyAV."""
    logger.info(f"Testing video: {video_path}")
    
    try:
        import av
        
        # Open container
        container = av.open(str(video_path))
        logger.info(f"✓ Container opened successfully")
        
        # Get streams
        video_stream = None
        audio_stream = None
        
        for stream in container.streams:
            if stream.type == 'video' and video_stream is None:
                video_stream = stream
            elif stream.type == 'audio' and audio_stream is None:
                audio_stream = stream
        
        # Log stream info
        if video_stream:
            logger.info(f"✓ Video stream: {video_stream.codec_context.name} {video_stream.width}x{video_stream.height} @ {video_stream.average_rate}fps")
        else:
            logger.warning("⚠ No video stream found")
        
        if audio_stream:
            logger.info(f"✓ Audio stream: {audio_stream.codec_context.name} {audio_stream.sample_rate}Hz {audio_stream.channels}ch")
        else:
            logger.warning("⚠ No audio stream found")
        
        # Get duration
        if container.duration:
            duration = float(container.duration) * av.time_base
            logger.info(f"✓ Duration: {duration:.2f}s")
        else:
            logger.warning("⚠ Duration not available")
        
        # Try decoding a few frames
        if video_stream:
            frame_count = 0
            for packet in container.demux(video_stream):
                for frame in packet.decode():
                    frame_count += 1
                    if frame_count == 1:
                        logger.info(f"✓ First frame decoded: {frame.width}x{frame.height}")
                    if frame_count >= 5:
                        break
                if frame_count >= 5:
                    break
            logger.info(f"✓ Decoded {frame_count} video frames")
        
        # Try decoding audio
        if audio_stream:
            audio_frame_count = 0
            container.seek(0)  # Reset to beginning
            for packet in container.demux(audio_stream):
                for frame in packet.decode():
                    audio_frame_count += 1
                    if audio_frame_count >= 5:
                        break
                if audio_frame_count >= 5:
                    break
            logger.info(f"✓ Decoded {audio_frame_count} audio frames")
        
        container.close()
        logger.info(f"✓ Test PASSED for {video_path.name}")
        return True
    
    except Exception as e:
        logger.error(f"✗ Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Test with available video files."""
    logger.info("=" * 60)
    logger.info("Real Video File Playback Test")
    logger.info("=" * 60)
    
    test_videos = [
        Path("/Users/justinfiore/workspace/personal/video-censor-personal/tests/fixtures/sample.mp4"),
        Path("/Users/justinfiore/workspace/personal/video-censor-personal/output-video/Psych1_1-clean.mp4"),
    ]
    
    results = {}
    for video_path in test_videos:
        if video_path.exists():
            logger.info(f"\n--- Testing {video_path.name} ---")
            results[video_path.name] = test_video_file(video_path)
        else:
            logger.warning(f"File not found: {video_path}")
    
    logger.info("\n" + "=" * 60)
    logger.info("Summary")
    logger.info("=" * 60)
    
    if results:
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        logger.info(f"Passed: {passed}/{total}")
        
        for filename, result in results.items():
            status = "✓" if result else "✗"
            logger.info(f"{status} {filename}")
        
        return 0 if passed == total else 1
    else:
        logger.error("No test videos found")
        return 1


if __name__ == "__main__":
    sys.exit(main())
