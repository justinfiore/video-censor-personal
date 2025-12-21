import pytest
from unittest.mock import Mock, MagicMock, patch
from video_censor_personal.ui.segment_manager import Segment, Detection


@pytest.fixture
def sample_segments():
    return [
        Segment(
            id="0",
            start_time=10.0,
            end_time=15.0,
            duration_seconds=5.0,
            labels=["Test"],
            description="Test",
            confidence=0.9,
            detections=[],
            allow=False
        ),
        Segment(
            id="1",
            start_time=30.0,
            end_time=35.0,
            duration_seconds=5.0,
            labels=["Test"],
            description="Test",
            confidence=0.8,
            detections=[],
            allow=True
        )
    ]


def test_timeline_canvas_set_segments(sample_segments):
    with patch('tkinter.Canvas.__init__', return_value=None):
        from video_censor_personal.ui.video_player_pane import TimelineCanvas
        
        canvas = TimelineCanvas.__new__(TimelineCanvas)
        canvas.segments = []
        canvas.duration = 0.0
        canvas.current_time = 0.0
        canvas._redraw = Mock()
        
        canvas.set_segments(sample_segments, 100.0)
        
        assert canvas.segments == sample_segments
        assert canvas.duration == 100.0
        canvas._redraw.assert_called_once()


def test_timeline_canvas_set_current_time():
    with patch('tkinter.Canvas.__init__', return_value=None):
        from video_censor_personal.ui.video_player_pane import TimelineCanvas
        
        canvas = TimelineCanvas.__new__(TimelineCanvas)
        canvas.segments = []
        canvas.duration = 100.0
        canvas.current_time = 0.0
        canvas._redraw = Mock()
        
        canvas.set_current_time(45.5)
        
        assert canvas.current_time == 45.5
        canvas._redraw.assert_called_once()


def test_timeline_canvas_seek_callback():
    with patch('tkinter.Canvas.__init__', return_value=None):
        from video_censor_personal.ui.video_player_pane import TimelineCanvas
        
        canvas = TimelineCanvas.__new__(TimelineCanvas)
        canvas.segments = []
        canvas.duration = 100.0
        canvas.current_time = 0.0
        canvas.winfo_width = Mock(return_value=1000)
        canvas.seek_callback = Mock()
        
        event = Mock()
        event.x = 500
        
        canvas._on_click(event)
        
        canvas.seek_callback.assert_called_once()
        called_time = canvas.seek_callback.call_args[0][0]
        assert 49 <= called_time <= 51


def test_video_player_pane_format_time():
    with patch('customtkinter.CTkFrame.__init__', return_value=None):
        with patch('tkinter.Frame'):
            with patch('customtkinter.CTkButton'):
                with patch('customtkinter.CTkLabel'):
                    with patch('customtkinter.CTkSlider'):
                        with patch('customtkinter.CTkOptionMenu'):
                            from video_censor_personal.ui.video_player_pane import VideoPlayerPaneImpl
                            
                            pane = VideoPlayerPaneImpl.__new__(VideoPlayerPaneImpl)
                            
                            time_str = pane._format_time(3665.567)
                            assert time_str == "01:01:05.567"
                            
                            time_str = pane._format_time(0.0)
                            assert time_str == "00:00:00.000"


def test_video_player_pane_load_video(sample_segments):
    with patch('customtkinter.CTkFrame.__init__', return_value=None):
        with patch('tkinter.Frame'):
            with patch('customtkinter.CTkButton'):
                with patch('customtkinter.CTkLabel'):
                    with patch('customtkinter.CTkSlider'):
                        with patch('customtkinter.CTkOptionMenu'):
                            from video_censor_personal.ui.video_player_pane import VideoPlayerPaneImpl, TimelineCanvas
                            
                            mock_player = Mock()
                            mock_player.get_duration.return_value = 120.0
                            
                            pane = VideoPlayerPaneImpl.__new__(VideoPlayerPaneImpl)
                            pane.video_player = mock_player
                            pane.is_loaded = False
                            pane.timeline = Mock(spec=TimelineCanvas)
                            pane._enable_controls = Mock()
                            pane._update_timecode = Mock()
                            
                            pane.load_video("/path/to/video.mp4", sample_segments)
                            
                            mock_player.load.assert_called_with("/path/to/video.mp4")
                            assert pane.is_loaded is True
                            pane._enable_controls.assert_called_once()
                            pane.timeline.set_segments.assert_called_with(sample_segments, 120.0)


def test_video_player_pane_play_pause():
    with patch('customtkinter.CTkFrame.__init__', return_value=None):
        with patch('tkinter.Frame'):
            with patch('customtkinter.CTkButton'):
                with patch('customtkinter.CTkLabel'):
                    with patch('customtkinter.CTkSlider'):
                        with patch('customtkinter.CTkOptionMenu'):
                            from video_censor_personal.ui.video_player_pane import VideoPlayerPaneImpl
                            
                            mock_player = Mock()
                            mock_player.is_playing.return_value = False
                            
                            pane = VideoPlayerPaneImpl.__new__(VideoPlayerPaneImpl)
                            pane.video_player = mock_player
                            pane.is_loaded = True
                            pane.play_pause_button = Mock()
                            
                            pane._on_play_pause()
                            
                            mock_player.play.assert_called_once()
                            pane.play_pause_button.configure.assert_called_with(text="⏸ Pause")
                            
                            mock_player.is_playing.return_value = True
                            pane._on_play_pause()
                            
                            mock_player.pause.assert_called_once()


def test_video_player_pane_skip():
    with patch('customtkinter.CTkFrame.__init__', return_value=None):
        with patch('tkinter.Frame'):
            with patch('customtkinter.CTkButton'):
                with patch('customtkinter.CTkLabel'):
                    with patch('customtkinter.CTkSlider'):
                        with patch('customtkinter.CTkOptionMenu'):
                            from video_censor_personal.ui.video_player_pane import VideoPlayerPaneImpl
                            
                            mock_player = Mock()
                            mock_player.get_current_time.return_value = 50.0
                            
                            pane = VideoPlayerPaneImpl.__new__(VideoPlayerPaneImpl)
                            pane.video_player = mock_player
                            pane.is_loaded = True
                            pane._update_timecode = Mock()
                            
                            pane._skip(10)
                            mock_player.seek.assert_called_with(60.0)
                            
                            pane._skip(-10)
                            mock_player.seek.assert_called_with(40.0)


def test_video_player_pane_volume_change():
    with patch('customtkinter.CTkFrame.__init__', return_value=None):
        with patch('tkinter.Frame'):
            with patch('customtkinter.CTkButton'):
                with patch('customtkinter.CTkLabel'):
                    with patch('customtkinter.CTkSlider'):
                        with patch('customtkinter.CTkOptionMenu'):
                            from video_censor_personal.ui.video_player_pane import VideoPlayerPaneImpl
                            
                            mock_player = Mock()
                            
                            pane = VideoPlayerPaneImpl.__new__(VideoPlayerPaneImpl)
                            pane.video_player = mock_player
                            pane.volume_label = Mock()
                            
                            pane._on_volume_changed(75.0)
                            
                            mock_player.set_volume.assert_called_with(0.75)
                            pane.volume_label.configure.assert_called_with(text="75%")


def test_video_player_pane_speed_change():
    with patch('customtkinter.CTkFrame.__init__', return_value=None):
        with patch('tkinter.Frame'):
            with patch('customtkinter.CTkButton'):
                with patch('customtkinter.CTkLabel'):
                    with patch('customtkinter.CTkSlider'):
                        with patch('customtkinter.CTkOptionMenu'):
                            from video_censor_personal.ui.video_player_pane import VideoPlayerPaneImpl
                            
                            mock_player = Mock()
                            
                            pane = VideoPlayerPaneImpl.__new__(VideoPlayerPaneImpl)
                            pane.video_player = mock_player
                            pane.is_loaded = True
                            
                            pane._on_speed_changed("1.5x")
                            mock_player.set_playback_rate.assert_called_with(1.5)
                            
                            pane._on_speed_changed("0.5x")
                            mock_player.set_playback_rate.assert_called_with(0.5)


def test_video_player_pane_seek_to_time():
    with patch('customtkinter.CTkFrame.__init__', return_value=None):
        with patch('tkinter.Frame'):
            with patch('customtkinter.CTkButton'):
                with patch('customtkinter.CTkLabel'):
                    with patch('customtkinter.CTkSlider'):
                        with patch('customtkinter.CTkOptionMenu'):
                            from video_censor_personal.ui.video_player_pane import VideoPlayerPaneImpl
                            
                            mock_player = Mock()
                            
                            pane = VideoPlayerPaneImpl.__new__(VideoPlayerPaneImpl)
                            pane.video_player = mock_player
                            pane.is_loaded = True
                            pane._update_timecode = Mock()
                            
                            pane.seek_to_time(45.5)
                            
                            mock_player.seek.assert_called_with(45.5)
                            pane._update_timecode.assert_called_once()


def test_video_player_pane_update_timeline_segments(sample_segments):
    with patch('customtkinter.CTkFrame.__init__', return_value=None):
        with patch('tkinter.Frame'):
            with patch('customtkinter.CTkButton'):
                with patch('customtkinter.CTkLabel'):
                    with patch('customtkinter.CTkSlider'):
                        with patch('customtkinter.CTkOptionMenu'):
                            from video_censor_personal.ui.video_player_pane import VideoPlayerPaneImpl, TimelineCanvas
                            
                            mock_player = Mock()
                            mock_player.get_duration.return_value = 120.0
                            
                            pane = VideoPlayerPaneImpl.__new__(VideoPlayerPaneImpl)
                            pane.video_player = mock_player
                            pane.is_loaded = True
                            pane.timeline = Mock(spec=TimelineCanvas)
                            
                            pane.update_timeline_segments(sample_segments)
                            
                            pane.timeline.set_segments.assert_called_with(sample_segments, 120.0)


def test_video_player_pane_cleanup():
    with patch('customtkinter.CTkFrame.__init__', return_value=None):
        with patch('tkinter.Frame'):
            with patch('customtkinter.CTkButton'):
                with patch('customtkinter.CTkLabel'):
                    with patch('customtkinter.CTkSlider'):
                        with patch('customtkinter.CTkOptionMenu'):
                            from video_censor_personal.ui.video_player_pane import VideoPlayerPaneImpl
                            
                            mock_player = Mock()
                            
                            pane = VideoPlayerPaneImpl.__new__(VideoPlayerPaneImpl)
                            pane.video_player = mock_player
                            pane._update_timer_id = 123
                            pane.after_cancel = Mock()
                            
                            pane.cleanup()
                            
                            pane.after_cancel.assert_called_with(123)
                            mock_player.cleanup.assert_called_once()
