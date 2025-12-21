import pytest
from unittest.mock import Mock, MagicMock, patch
import sys

try:
    from pyvirtualdisplay import Display
    DISPLAY_AVAILABLE = True
except ImportError:
    DISPLAY_AVAILABLE = False


@pytest.fixture(scope="module", autouse=True)
def setup_display():
    """Setup virtual display for headless testing on Linux."""
    if DISPLAY_AVAILABLE and sys.platform.startswith('linux'):
        display = Display(visible=False, size=(1024, 768))
        display.start()
        yield
        display.stop()
    else:
        yield


@pytest.fixture
def mock_tk_root():
    """Create a mock Tk root for testing."""
    with patch('customtkinter.CTk') as mock_root:
        yield mock_root()


def test_segment_list_pane_creation():
    with patch('customtkinter.CTkFrame.__init__', return_value=None):
        with patch('customtkinter.CTkScrollableFrame') as mock_scrollable:
            from video_censor_personal.ui.layout import SegmentListPane
            
            pane = SegmentListPane.__new__(SegmentListPane)
            pane.segment_frames = {}
            pane.selected_segment_id = None
            pane.segment_click_callback = None
            
            assert pane.segment_frames == {}
            assert pane.selected_segment_id is None


def test_segment_list_pane_set_callback():
    with patch('customtkinter.CTkFrame.__init__', return_value=None):
        with patch('customtkinter.CTkScrollableFrame'):
            from video_censor_personal.ui.layout import SegmentListPane
            
            pane = SegmentListPane.__new__(SegmentListPane)
            pane.segment_frames = {}
            pane.selected_segment_id = None
            pane.segment_click_callback = None
            
            callback = Mock()
            pane.set_segment_click_callback(callback)
            
            assert pane.segment_click_callback == callback


def test_segment_list_pane_clear():
    with patch('customtkinter.CTkFrame.__init__', return_value=None):
        with patch('customtkinter.CTkScrollableFrame'):
            from video_censor_personal.ui.layout import SegmentListPane
            
            pane = SegmentListPane.__new__(SegmentListPane)
            pane.segment_frames = {}
            pane.selected_segment_id = "test_id"
            
            mock_frame1 = Mock()
            mock_frame2 = Mock()
            pane.segment_frames = {"0": mock_frame1, "1": mock_frame2}
            
            pane.clear()
            
            mock_frame1.destroy.assert_called_once()
            mock_frame2.destroy.assert_called_once()
            assert pane.segment_frames == {}
            assert pane.selected_segment_id is None


def test_video_player_pane_creation():
    with patch('customtkinter.CTkFrame.__init__', return_value=None):
        with patch('customtkinter.CTkFrame') as mock_frame:
            from video_censor_personal.ui.layout import VideoPlayerPane
            
            pane = VideoPlayerPane.__new__(VideoPlayerPane)
            
            assert hasattr(VideoPlayerPane, '__init__')


def test_segment_details_pane_creation():
    with patch('customtkinter.CTkFrame.__init__', return_value=None):
        with patch('customtkinter.CTkScrollableFrame'):
            from video_censor_personal.ui.layout import SegmentDetailsPane
            
            pane = SegmentDetailsPane.__new__(SegmentDetailsPane)
            
            assert hasattr(SegmentDetailsPane, '__init__')


def test_three_pane_layout_structure():
    with patch('customtkinter.CTkFrame.__init__', return_value=None):
        with patch('customtkinter.CTkScrollableFrame'):
            from video_censor_personal.ui.layout import ThreePaneLayout, SegmentListPane, VideoPlayerPane, SegmentDetailsPane
            
            layout = ThreePaneLayout.__new__(ThreePaneLayout)
            
            mock_segment_list = Mock(spec=SegmentListPane)
            mock_video_player = Mock(spec=VideoPlayerPane)
            mock_segment_details = Mock(spec=SegmentDetailsPane)
            
            layout.segment_list_pane = mock_segment_list
            layout.video_player_pane = mock_video_player
            layout.segment_details_pane = mock_segment_details
            
            assert layout.get_segment_list_pane() == mock_segment_list
            assert layout.get_video_player_pane() == mock_video_player
            assert layout.get_segment_details_pane() == mock_segment_details


def test_three_pane_layout_getters():
    with patch('customtkinter.CTkFrame.__init__', return_value=None):
        with patch('customtkinter.CTkScrollableFrame'):
            from video_censor_personal.ui.layout import ThreePaneLayout
            
            layout = ThreePaneLayout.__new__(ThreePaneLayout)
            
            from video_censor_personal.ui.layout import SegmentListPane, VideoPlayerPane, SegmentDetailsPane
            
            layout.segment_list_pane = Mock(spec=SegmentListPane)
            layout.video_player_pane = Mock(spec=VideoPlayerPane)
            layout.segment_details_pane = Mock(spec=SegmentDetailsPane)
            
            assert layout.get_segment_list_pane() is layout.segment_list_pane
            assert layout.get_video_player_pane() is layout.video_player_pane
            assert layout.get_segment_details_pane() is layout.segment_details_pane
