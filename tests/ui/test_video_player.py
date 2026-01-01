import pytest
from unittest.mock import Mock, MagicMock, patch
from video_censor_personal.ui.video_player import VideoPlayer


class MockVideoPlayer(VideoPlayer):
    """Mock implementation for testing."""
    
    def __init__(self):
        self.video_path = None
        self.is_playing_state = False
        self.current_time = 0.0
        self.volume_level = 1.0
        self.playback_rate = 1.0
        self.duration = 100.0
        self.time_callback = None
    
    def load(self, video_path: str) -> None:
        self.video_path = video_path
    
    def play(self) -> None:
        self.is_playing_state = True
    
    def pause(self) -> None:
        self.is_playing_state = False
    
    def seek(self, seconds: float) -> None:
        self.current_time = seconds
    
    def set_volume(self, level: float) -> None:
        self.volume_level = level
    
    def get_current_time(self) -> float:
        return self.current_time
    
    def on_time_changed(self, callback) -> None:
        self.time_callback = callback
    
    def set_playback_rate(self, rate: float) -> None:
        self.playback_rate = rate
    
    def cleanup(self) -> None:
        self.is_playing_state = False
        self.video_path = None
    
    def is_playing(self) -> bool:
        return self.is_playing_state
    
    def get_duration(self) -> float:
        return self.duration


def test_mock_video_player_load():
    player = MockVideoPlayer()
    player.load("/path/to/video.mp4")
    assert player.video_path == "/path/to/video.mp4"


def test_mock_video_player_playback():
    player = MockVideoPlayer()
    assert not player.is_playing()
    
    player.play()
    assert player.is_playing()
    
    player.pause()
    assert not player.is_playing()


def test_mock_video_player_seek():
    player = MockVideoPlayer()
    player.seek(42.5)
    assert player.get_current_time() == 42.5


def test_mock_video_player_volume():
    player = MockVideoPlayer()
    player.set_volume(0.75)
    assert player.volume_level == 0.75


def test_mock_video_player_playback_rate():
    player = MockVideoPlayer()
    player.set_playback_rate(1.5)
    assert player.playback_rate == 1.5


def test_mock_video_player_time_callback():
    player = MockVideoPlayer()
    callback = Mock()
    player.on_time_changed(callback)
    assert player.time_callback == callback


def test_mock_video_player_cleanup():
    player = MockVideoPlayer()
    player.load("/path/to/video.mp4")
    player.play()
    
    player.cleanup()
    assert not player.is_playing()
    assert player.video_path is None


def test_mock_video_player_duration():
    player = MockVideoPlayer()
    assert player.get_duration() == 100.0

