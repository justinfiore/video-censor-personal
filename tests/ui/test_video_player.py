import pytest
from unittest.mock import Mock, MagicMock, patch
from video_censor_personal.ui.video_player import VideoPlayer, VLCVideoPlayer


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


@patch('video_censor_personal.ui.video_player.vlc')
def test_vlc_player_initialization(mock_vlc):
    mock_instance = MagicMock()
    mock_player = MagicMock()
    mock_vlc.Instance.return_value = mock_instance
    mock_instance.media_player_new.return_value = mock_player
    
    player = VLCVideoPlayer()
    
    assert player.instance == mock_instance
    assert player.player == mock_player
    mock_vlc.Instance.assert_called_once()
    mock_instance.media_player_new.assert_called_once()


@patch('video_censor_personal.ui.video_player.vlc')
def test_vlc_player_load(mock_vlc):
    mock_instance = MagicMock()
    mock_player = MagicMock()
    mock_media = MagicMock()
    mock_vlc.Instance.return_value = mock_instance
    mock_instance.media_player_new.return_value = mock_player
    mock_instance.media_new.return_value = mock_media
    
    player = VLCVideoPlayer()
    player.load("/path/to/video.mp4")
    
    mock_instance.media_new.assert_called_once_with("/path/to/video.mp4")
    mock_player.set_media.assert_called_once_with(mock_media)
    mock_media.parse.assert_called_once()


@patch('video_censor_personal.ui.video_player.vlc')
def test_vlc_player_playback_controls(mock_vlc):
    mock_instance = MagicMock()
    mock_player = MagicMock()
    mock_vlc.Instance.return_value = mock_instance
    mock_instance.media_player_new.return_value = mock_player
    
    player = VLCVideoPlayer()
    
    player.play()
    mock_player.play.assert_called_once()
    
    player.pause()
    mock_player.pause.assert_called_once()


@patch('video_censor_personal.ui.video_player.vlc')
def test_vlc_player_seek(mock_vlc):
    mock_instance = MagicMock()
    mock_player = MagicMock()
    mock_vlc.Instance.return_value = mock_instance
    mock_instance.media_player_new.return_value = mock_player
    mock_player.get_length.return_value = 100000
    
    player = VLCVideoPlayer()
    player.seek(50.0)
    
    mock_player.set_position.assert_called_once_with(0.5)


@patch('video_censor_personal.ui.video_player.vlc')
def test_vlc_player_volume(mock_vlc):
    mock_instance = MagicMock()
    mock_player = MagicMock()
    mock_vlc.Instance.return_value = mock_instance
    mock_instance.media_player_new.return_value = mock_player
    
    player = VLCVideoPlayer()
    player.set_volume(0.75)
    
    mock_player.audio_set_volume.assert_called_once_with(75)


@patch('video_censor_personal.ui.video_player.vlc')
def test_vlc_player_get_current_time(mock_vlc):
    mock_instance = MagicMock()
    mock_player = MagicMock()
    mock_vlc.Instance.return_value = mock_instance
    mock_instance.media_player_new.return_value = mock_player
    mock_player.get_time.return_value = 45000
    
    player = VLCVideoPlayer()
    time = player.get_current_time()
    
    assert time == 45.0


@patch('video_censor_personal.ui.video_player.vlc')
def test_vlc_player_is_playing(mock_vlc):
    mock_instance = MagicMock()
    mock_player = MagicMock()
    mock_vlc.Instance.return_value = mock_instance
    mock_instance.media_player_new.return_value = mock_player
    mock_player.is_playing.return_value = 1
    
    player = VLCVideoPlayer()
    assert player.is_playing() is True


@patch('video_censor_personal.ui.video_player.vlc')
def test_vlc_player_get_duration(mock_vlc):
    mock_instance = MagicMock()
    mock_player = MagicMock()
    mock_vlc.Instance.return_value = mock_instance
    mock_instance.media_player_new.return_value = mock_player
    mock_player.get_length.return_value = 120000
    
    player = VLCVideoPlayer()
    duration = player.get_duration()
    
    assert duration == 120.0


@patch('video_censor_personal.ui.video_player.vlc')
def test_vlc_player_cleanup(mock_vlc):
    mock_instance = MagicMock()
    mock_player = MagicMock()
    mock_vlc.Instance.return_value = mock_instance
    mock_instance.media_player_new.return_value = mock_player
    
    player = VLCVideoPlayer()
    player.cleanup()
    
    mock_player.stop.assert_called_once()
    mock_player.release.assert_called_once()
    mock_instance.release.assert_called_once()
