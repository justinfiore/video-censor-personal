#!/usr/bin/env python3
"""Integration test for video playback with PyAV."""

import sys
import logging
import time
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_pyav_import():
    """Test PyAV availability."""
    try:
        import av
        logger.info(f"✓ PyAV {av.__version__} available")
        return True
    except ImportError as e:
        logger.error(f"✗ PyAV not available: {e}")
        return False


def test_audio_player():
    """Test audio player initialization."""
    try:
        from video_censor_personal.ui.audio_player import SimpleAudioPlayer
        import numpy as np
        
        player = SimpleAudioPlayer()
        
        # Create test audio
        sample_rate = 48000
        duration = 1.0
        samples = int(sample_rate * duration)
        
        # Generate sine wave
        t = np.linspace(0, duration, samples)
        frequency = 440  # A4 note
        audio_data = np.sin(2 * np.pi * frequency * t) * 32767
        audio_data = audio_data.astype(np.int16)
        
        # Load and test
        player.load_audio_data(audio_data, sample_rate, channels=1)
        logger.info(f"✓ Audio player loaded {len(audio_data)} samples")
        
        assert player.get_duration() > 0
        logger.info(f"✓ Audio duration: {player.get_duration():.2f}s")
        
        return True
    except Exception as e:
        logger.error(f"✗ Audio player test failed: {e}")
        return False


def test_video_player():
    """Test video player initialization."""
    try:
        from video_censor_personal.ui.pyav_video_player import PyAVVideoPlayer
        import tkinter as tk
        
        # Create minimal window
        root = tk.Tk()
        root.withdraw()
        
        player = PyAVVideoPlayer()
        logger.info(f"✓ PyAVVideoPlayer created")
        
        # Test interface methods
        assert hasattr(player, 'load')
        assert hasattr(player, 'play')
        assert hasattr(player, 'pause')
        assert hasattr(player, 'seek')
        assert hasattr(player, 'get_duration')
        logger.info(f"✓ PyAVVideoPlayer interface complete")
        
        player.cleanup()
        root.destroy()
        return True
    except Exception as e:
        logger.error(f"✗ Video player test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_video_pane():
    """Test video player pane integration."""
    try:
        from video_censor_personal.ui.video_player_pane import VideoPlayerPaneImpl
        import tkinter as tk
        
        root = tk.Tk()
        root.withdraw()
        
        pane = VideoPlayerPaneImpl(root)
        logger.info(f"✓ VideoPlayerPaneImpl created with default player")
        
        assert pane.video_player is not None
        logger.info(f"✓ Video player type: {type(pane.video_player).__name__}")
        
        pane.cleanup()
        root.destroy()
        return True
    except Exception as e:
        logger.error(f"✗ Video pane test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_dependencies():
    """Test all required dependencies."""
    dependencies = {
        'numpy': 'numpy',
        'PIL': 'Pillow',
        'pydub': 'pydub',
        'simpleaudio': 'simpleaudio',
        'av': 'PyAV',
        'customtkinter': 'customtkinter',
    }
    
    all_available = True
    for module, display_name in dependencies.items():
        try:
            __import__(module)
            logger.info(f"✓ {display_name} available")
        except ImportError as e:
            logger.error(f"✗ {display_name} not available: {e}")
            all_available = False
    
    return all_available


def main():
    """Run integration tests."""
    logger.info("=" * 60)
    logger.info("Video Playback Integration Tests")
    logger.info("=" * 60)
    
    tests = [
        ("Dependencies", test_dependencies),
        ("PyAV Import", test_pyav_import),
        ("Audio Player", test_audio_player),
        ("Video Player", test_video_player),
        ("Video Player Pane", test_video_pane),
    ]
    
    results = {}
    for test_name, test_func in tests:
        logger.info(f"\n--- {test_name} ---")
        try:
            results[test_name] = test_func()
        except Exception as e:
            logger.error(f"Test error: {e}")
            import traceback
            traceback.print_exc()
            results[test_name] = False
    
    logger.info("\n" + "=" * 60)
    logger.info("Summary")
    logger.info("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓" if result else "✗"
        logger.info(f"{status} {test_name}")
    
    logger.info(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        logger.info("✓ All tests passed!")
        return 0
    else:
        logger.error(f"✗ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
