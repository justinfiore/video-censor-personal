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
            labels=["Profanity", "Violence"],
            description="Test segment 1",
            confidence=0.9,
            detections=[
                Detection(label="Profanity", confidence=0.95, reasoning="Test")
            ],
            allow=False
        ),
        Segment(
            id="1",
            start_time=30.0,
            end_time=35.0,
            duration_seconds=5.0,
            labels=["Profanity"],
            description="Test segment 2",
            confidence=0.8,
            detections=[
                Detection(label="Profanity", confidence=0.8, reasoning="Test")
            ],
            allow=True
        ),
        Segment(
            id="2",
            start_time=50.0,
            end_time=55.0,
            duration_seconds=5.0,
            labels=["Violence"],
            description="Test segment 3",
            confidence=0.85,
            detections=[
                Detection(label="Violence", confidence=0.85, reasoning="Test")
            ],
            allow=False
        )
    ]


def test_segment_list_item_creation():
    with patch('customtkinter.CTkFrame.__init__', return_value=None):
        with patch('customtkinter.CTkLabel') as mock_label:
            from video_censor_personal.ui.segment_list_pane import SegmentListItem
            
            segment = Segment(
                id="0",
                start_time=10.5,
                end_time=15.2,
                duration_seconds=4.7,
                labels=["Test"],
                description="Test",
                confidence=0.9,
                detections=[],
                allow=False
            )
            
            item = SegmentListItem.__new__(SegmentListItem)
            item.segment = segment
            item.is_selected = False
            
            assert item.segment == segment
            assert item.is_selected is False


def test_segment_list_item_format_time():
    with patch('customtkinter.CTkFrame.__init__', return_value=None):
        with patch('customtkinter.CTkLabel'):
            from video_censor_personal.ui.segment_list_pane import SegmentListItem
            
            segment = Segment(
                id="0",
                start_time=0,
                end_time=0,
                duration_seconds=0,
                labels=[],
                description="",
                confidence=0,
                detections=[],
                allow=False
            )
            
            item = SegmentListItem.__new__(SegmentListItem)
            item.segment = segment
            
            time_str = item._format_time_range(3665.5, 3725.8)
            assert time_str == "01:01:05 - 01:02:05"
            
            time_str = item._format_time_range(0, 30)
            assert time_str == "00:00:00 - 00:00:30"


def test_segment_list_item_set_selected():
    with patch('customtkinter.CTkFrame.__init__', return_value=None):
        with patch('customtkinter.CTkLabel'):
            from video_censor_personal.ui.segment_list_pane import SegmentListItem
            
            segment = Segment(
                id="0",
                start_time=0,
                end_time=0,
                duration_seconds=0,
                labels=[],
                description="",
                confidence=0,
                detections=[],
                allow=False
            )
            
            item = SegmentListItem.__new__(SegmentListItem)
            item.segment = segment
            item.is_selected = False
            item.configure = Mock()
            
            item.set_selected(True)
            assert item.is_selected is True
            item.configure.assert_called()
            
            item.set_selected(False)
            assert item.is_selected is False


def test_segment_list_item_update_allow_indicator():
    with patch('customtkinter.CTkFrame.__init__', return_value=None):
        with patch('customtkinter.CTkLabel') as mock_label:
            from video_censor_personal.ui.segment_list_pane import SegmentListItem
            
            segment = Segment(
                id="0",
                start_time=0,
                end_time=0,
                duration_seconds=0,
                labels=[],
                description="",
                confidence=0,
                detections=[],
                allow=False
            )
            
            item = SegmentListItem.__new__(SegmentListItem)
            item.segment = segment
            item.allow_indicator = Mock()
            
            item.update_allow_indicator(True)
            assert item.segment.allow is True
            item.allow_indicator.configure.assert_called()
            
            item.update_allow_indicator(False)
            assert item.segment.allow is False


def test_segment_list_pane_load_segments(sample_segments):
    with patch('customtkinter.CTkFrame.__init__', return_value=None):
        with patch('customtkinter.CTkScrollableFrame'):
            with patch('customtkinter.CTkLabel'):
                with patch('customtkinter.CTkComboBox'):
                    from video_censor_personal.ui.segment_list_pane import SegmentListPaneImpl, DEFAULT_PAGE_SIZE
                    
                    pane = SegmentListPaneImpl.__new__(SegmentListPaneImpl)
                    pane.all_segments = []
                    pane.filtered_segments = []
                    pane.segment_items = {}
                    pane.selected_segment_id = None
                    pane.label_filter = Mock()
                    pane.page_size = DEFAULT_PAGE_SIZE
                    pane.current_page = 0
                    pane._render_current_page = Mock()
                    
                    pane.load_segments(sample_segments)
                    
                    assert pane.all_segments == sample_segments
                    assert pane.filtered_segments == sample_segments
                    assert pane.current_page == 0
                    pane._render_current_page.assert_called_once()


def test_segment_list_pane_filter_by_label(sample_segments):
    with patch('customtkinter.CTkFrame.__init__', return_value=None):
        with patch('customtkinter.CTkScrollableFrame'):
            with patch('customtkinter.CTkLabel'):
                with patch('customtkinter.CTkComboBox'):
                    from video_censor_personal.ui.segment_list_pane import SegmentListPaneImpl, DEFAULT_PAGE_SIZE
                    
                    pane = SegmentListPaneImpl.__new__(SegmentListPaneImpl)
                    pane.all_segments = sample_segments
                    pane.filtered_segments = sample_segments
                    pane.segment_items = {}
                    pane.selected_segment_id = None
                    pane.label_filter_var = Mock()
                    pane.allow_filter_var = Mock()
                    pane.page_size = DEFAULT_PAGE_SIZE
                    pane.current_page = 0
                    pane._render_current_page = Mock()
                    
                    pane.label_filter_var.get.return_value = "Profanity"
                    pane.allow_filter_var.get.return_value = "All Segments"
                    
                    pane._on_filter_changed()
                    
                    assert len(pane.filtered_segments) == 2
                    assert all("Profanity" in seg.labels for seg in pane.filtered_segments)
                    assert pane.current_page == 0


def test_segment_list_pane_filter_by_allow_status(sample_segments):
    with patch('customtkinter.CTkFrame.__init__', return_value=None):
        with patch('customtkinter.CTkScrollableFrame'):
            with patch('customtkinter.CTkLabel'):
                with patch('customtkinter.CTkComboBox'):
                    from video_censor_personal.ui.segment_list_pane import SegmentListPaneImpl, DEFAULT_PAGE_SIZE
                    
                    pane = SegmentListPaneImpl.__new__(SegmentListPaneImpl)
                    pane.all_segments = sample_segments
                    pane.filtered_segments = sample_segments
                    pane.segment_items = {}
                    pane.selected_segment_id = None
                    pane.label_filter_var = Mock()
                    pane.allow_filter_var = Mock()
                    pane.page_size = DEFAULT_PAGE_SIZE
                    pane.current_page = 0
                    pane._render_current_page = Mock()
                    
                    pane.label_filter_var.get.return_value = "All Labels"
                    pane.allow_filter_var.get.return_value = "Allowed Only"
                    
                    pane._on_filter_changed()
                    
                    assert len(pane.filtered_segments) == 1
                    assert all(seg.allow for seg in pane.filtered_segments)


def test_segment_list_pane_highlight_at_time(sample_segments):
    with patch('customtkinter.CTkFrame.__init__', return_value=None):
        with patch('customtkinter.CTkScrollableFrame'):
            with patch('customtkinter.CTkLabel'):
                with patch('customtkinter.CTkComboBox'):
                    from video_censor_personal.ui.segment_list_pane import SegmentListPaneImpl, DEFAULT_PAGE_SIZE
                    
                    pane = SegmentListPaneImpl.__new__(SegmentListPaneImpl)
                    pane.all_segments = sample_segments
                    pane.filtered_segments = sample_segments
                    pane.segment_items = {}
                    pane.selected_segment_id = None
                    pane.page_size = DEFAULT_PAGE_SIZE
                    pane.current_page = 0
                    pane._on_segment_clicked = Mock()
                    pane._render_current_page = Mock()
                    
                    pane.highlight_segment_at_time(12.0)
                    pane._on_segment_clicked.assert_called_with("0")
                    
                    pane.selected_segment_id = "0"
                    pane.highlight_segment_at_time(12.0)


def test_segment_list_pane_select_next(sample_segments):
    with patch('customtkinter.CTkFrame.__init__', return_value=None):
        with patch('customtkinter.CTkScrollableFrame'):
            with patch('customtkinter.CTkLabel'):
                with patch('customtkinter.CTkComboBox'):
                    from video_censor_personal.ui.segment_list_pane import SegmentListPaneImpl, DEFAULT_PAGE_SIZE
                    
                    pane = SegmentListPaneImpl.__new__(SegmentListPaneImpl)
                    pane.all_segments = sample_segments
                    pane.filtered_segments = sample_segments
                    pane.segment_items = {}
                    pane.selected_segment_id = "0"
                    pane.page_size = DEFAULT_PAGE_SIZE
                    pane.current_page = 0
                    pane._on_segment_clicked = Mock()
                    pane._render_current_page = Mock()
                    
                    next_id = pane.select_next_segment()
                    assert next_id == "1"
                    pane._on_segment_clicked.assert_called_with("1")


def test_segment_list_pane_select_previous(sample_segments):
    with patch('customtkinter.CTkFrame.__init__', return_value=None):
        with patch('customtkinter.CTkScrollableFrame'):
            with patch('customtkinter.CTkLabel'):
                with patch('customtkinter.CTkComboBox'):
                    from video_censor_personal.ui.segment_list_pane import SegmentListPaneImpl, DEFAULT_PAGE_SIZE
                    
                    pane = SegmentListPaneImpl.__new__(SegmentListPaneImpl)
                    pane.all_segments = sample_segments
                    pane.filtered_segments = sample_segments
                    pane.segment_items = {}
                    pane.selected_segment_id = "1"
                    pane.page_size = DEFAULT_PAGE_SIZE
                    pane.current_page = 0
                    pane._on_segment_clicked = Mock()
                    pane._render_current_page = Mock()
                    
                    prev_id = pane.select_previous_segment()
                    assert prev_id == "0"
                    pane._on_segment_clicked.assert_called_with("0")


def test_segment_list_pane_update_segment_allow(sample_segments):
    with patch('customtkinter.CTkFrame.__init__', return_value=None):
        with patch('customtkinter.CTkScrollableFrame'):
            with patch('customtkinter.CTkLabel'):
                with patch('customtkinter.CTkComboBox'):
                    from video_censor_personal.ui.segment_list_pane import SegmentListPaneImpl, SegmentListItem
                    
                    pane = SegmentListPaneImpl.__new__(SegmentListPaneImpl)
                    pane.all_segments = sample_segments
                    pane.filtered_segments = sample_segments
                    
                    mock_item = Mock(spec=SegmentListItem)
                    pane.segment_items = {"0": mock_item}
                    
                    pane.update_segment_allow("0", True)
                    
                    mock_item.update_allow_indicator.assert_called_with(True)
                    assert sample_segments[0].allow is True


def test_segment_list_pane_clear(sample_segments):
    with patch('customtkinter.CTkFrame.__init__', return_value=None):
        with patch('customtkinter.CTkScrollableFrame'):
            with patch('customtkinter.CTkLabel'):
                with patch('customtkinter.CTkComboBox'):
                    from video_censor_personal.ui.segment_list_pane import SegmentListPaneImpl, DEFAULT_PAGE_SIZE
                    
                    pane = SegmentListPaneImpl.__new__(SegmentListPaneImpl)
                    pane.all_segments = sample_segments.copy()
                    pane.filtered_segments = sample_segments.copy()
                    pane.selected_segment_id = "0"
                    pane.page_size = DEFAULT_PAGE_SIZE
                    pane.current_page = 2
                    pane._update_pagination_ui = Mock()
                    
                    mock_item1 = Mock()
                    mock_item2 = Mock()
                    pane.segment_items = {"0": mock_item1, "1": mock_item2}
                    
                    pane.clear()
                    
                    mock_item1.destroy.assert_called_once()
                    mock_item2.destroy.assert_called_once()
                    assert len(pane.segment_items) == 0
                    assert len(pane.all_segments) == 0
                    assert len(pane.filtered_segments) == 0
                    assert pane.selected_segment_id is None
                    assert pane.current_page == 0
