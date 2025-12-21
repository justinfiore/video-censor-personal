import pytest
from unittest.mock import Mock, MagicMock, patch
from video_censor_personal.ui.segment_manager import Segment, Detection


@pytest.fixture
def sample_segment():
    return Segment(
        id="0",
        start_time=10.5,
        end_time=15.2,
        duration_seconds=4.7,
        labels=["Profanity", "Violence"],
        description="Test segment with multiple labels",
        confidence=0.92,
        detections=[
            Detection(label="Profanity", confidence=0.95, reasoning="Explicit language detected"),
            Detection(label="Violence", confidence=0.89, reasoning="Violent scene detected")
        ],
        allow=False
    )


def test_segment_details_pane_format_time():
    with patch('customtkinter.CTkFrame.__init__', return_value=None):
        with patch('customtkinter.CTkScrollableFrame'):
            with patch('customtkinter.CTkLabel'):
                with patch('customtkinter.CTkCheckBox'):
                    with patch('customtkinter.CTkButton'):
                        from video_censor_personal.ui.segment_details_pane import SegmentDetailsPaneImpl
                        
                        pane = SegmentDetailsPaneImpl.__new__(SegmentDetailsPaneImpl)
                        
                        time_str = pane._format_time(3665.567)
                        assert time_str == "01:01:05.567"
                        
                        time_str = pane._format_time(0.123)
                        assert time_str == "00:00:00.123"
                        
                        time_str = pane._format_time(125.0)
                        assert time_str == "00:02:05.000"


def test_segment_details_pane_display_segment(sample_segment):
    with patch('customtkinter.CTkFrame.__init__', return_value=None):
        with patch('customtkinter.CTkScrollableFrame'):
            with patch('customtkinter.CTkLabel') as mock_label:
                with patch('customtkinter.CTkCheckBox') as mock_checkbox:
                    with patch('customtkinter.CTkButton'):
                        from video_censor_personal.ui.segment_details_pane import SegmentDetailsPaneImpl
                        
                        pane = SegmentDetailsPaneImpl.__new__(SegmentDetailsPaneImpl)
                        pane.current_segment = None
                        pane.no_selection_label = Mock()
                        pane.details_container = Mock()
                        pane.time_label = Mock()
                        pane.duration_label = Mock()
                        pane.labels_label = Mock()
                        pane.confidence_label = Mock()
                        pane.description_label = Mock()
                        pane.allow_checkbox = Mock()
                        pane._update_detections_display = Mock()
                        
                        pane.display_segment(sample_segment)
                        
                        assert pane.current_segment == sample_segment
                        pane.no_selection_label.grid_remove.assert_called_once()
                        pane.details_container.grid.assert_called_once()
                        pane.time_label.configure.assert_called()
                        pane.duration_label.configure.assert_called()
                        pane.labels_label.configure.assert_called()
                        pane.confidence_label.configure.assert_called()
                        pane.description_label.configure.assert_called()


def test_segment_details_pane_allow_toggle_callback(sample_segment):
    with patch('customtkinter.CTkFrame.__init__', return_value=None):
        with patch('customtkinter.CTkScrollableFrame'):
            with patch('customtkinter.CTkLabel'):
                with patch('customtkinter.CTkCheckBox'):
                    with patch('customtkinter.CTkButton'):
                        from video_censor_personal.ui.segment_details_pane import SegmentDetailsPaneImpl
                        
                        pane = SegmentDetailsPaneImpl.__new__(SegmentDetailsPaneImpl)
                        pane.current_segment = sample_segment
                        pane.allow_checkbox = Mock()
                        pane.save_status_label = Mock()
                        pane.after = Mock()
                        pane.allow_toggle_callback = Mock()
                        
                        pane.allow_checkbox.get.return_value = 1
                        
                        pane._on_allow_toggled()
                        
                        pane.allow_toggle_callback.assert_called_with(sample_segment.id, True)
                        pane.save_status_label.configure.assert_called()


def test_segment_details_pane_allow_toggle_error_handling(sample_segment):
    with patch('customtkinter.CTkFrame.__init__', return_value=None):
        with patch('customtkinter.CTkScrollableFrame'):
            with patch('customtkinter.CTkLabel'):
                with patch('customtkinter.CTkCheckBox'):
                    with patch('customtkinter.CTkButton'):
                        from video_censor_personal.ui.segment_details_pane import SegmentDetailsPaneImpl
                        
                        pane = SegmentDetailsPaneImpl.__new__(SegmentDetailsPaneImpl)
                        pane.current_segment = sample_segment
                        pane.allow_checkbox = Mock()
                        pane.save_status_label = Mock()
                        pane.allow_toggle_callback = Mock(side_effect=Exception("Save failed"))
                        
                        pane.allow_checkbox.get.return_value = 1
                        
                        pane._on_allow_toggled()
                        
                        pane.allow_checkbox.deselect.assert_called()
                        args = pane.save_status_label.configure.call_args
                        assert "Error" in str(args)


def test_segment_details_pane_toggle_detections():
    with patch('customtkinter.CTkFrame.__init__', return_value=None):
        with patch('customtkinter.CTkScrollableFrame'):
            with patch('customtkinter.CTkLabel'):
                with patch('customtkinter.CTkCheckBox'):
                    with patch('customtkinter.CTkButton'):
                        from video_censor_personal.ui.segment_details_pane import SegmentDetailsPaneImpl
                        
                        pane = SegmentDetailsPaneImpl.__new__(SegmentDetailsPaneImpl)
                        pane.detections_expanded = False
                        pane.detections_frame = Mock()
                        pane.expand_button = Mock()
                        
                        pane._toggle_detections()
                        
                        assert pane.detections_expanded is True
                        pane.detections_frame.grid.assert_called_once()
                        
                        pane._toggle_detections()
                        
                        assert pane.detections_expanded is False
                        pane.detections_frame.grid_remove.assert_called()


def test_segment_details_pane_update_detections_display(sample_segment):
    with patch('customtkinter.CTkFrame.__init__', return_value=None):
        with patch('customtkinter.CTkScrollableFrame'):
            with patch('customtkinter.CTkLabel') as mock_label:
                with patch('customtkinter.CTkCheckBox'):
                    with patch('customtkinter.CTkButton'):
                        from video_censor_personal.ui.segment_details_pane import SegmentDetailsPaneImpl
                        
                        pane = SegmentDetailsPaneImpl.__new__(SegmentDetailsPaneImpl)
                        pane.current_segment = sample_segment
                        pane.detections_frame = Mock()
                        pane.detections_frame.winfo_children.return_value = []
                        
                        pane._update_detections_display()
                        
                        assert pane.detections_frame.winfo_children.called


def test_segment_details_pane_clear():
    with patch('customtkinter.CTkFrame.__init__', return_value=None):
        with patch('customtkinter.CTkScrollableFrame'):
            with patch('customtkinter.CTkLabel'):
                with patch('customtkinter.CTkCheckBox'):
                    with patch('customtkinter.CTkButton'):
                        from video_censor_personal.ui.segment_details_pane import SegmentDetailsPaneImpl
                        
                        pane = SegmentDetailsPaneImpl.__new__(SegmentDetailsPaneImpl)
                        pane.current_segment = Mock()
                        pane.details_container = Mock()
                        pane.no_selection_label = Mock()
                        pane.save_status_label = Mock()
                        pane.detections_expanded = False
                        pane._toggle_detections = Mock()
                        
                        pane.clear()
                        
                        assert pane.current_segment is None
                        pane.details_container.grid_remove.assert_called_once()
                        pane.no_selection_label.grid.assert_called_once()


def test_segment_details_pane_update_allow_status():
    with patch('customtkinter.CTkFrame.__init__', return_value=None):
        with patch('customtkinter.CTkScrollableFrame'):
            with patch('customtkinter.CTkLabel'):
                with patch('customtkinter.CTkCheckBox'):
                    with patch('customtkinter.CTkButton'):
                        from video_censor_personal.ui.segment_details_pane import SegmentDetailsPaneImpl
                        
                        pane = SegmentDetailsPaneImpl.__new__(SegmentDetailsPaneImpl)
                        pane.allow_checkbox = Mock()
                        
                        pane.update_allow_status(True)
                        pane.allow_checkbox.select.assert_called_once()
                        
                        pane.update_allow_status(False)
                        pane.allow_checkbox.deselect.assert_called_once()


def test_segment_details_pane_no_segment_selected():
    with patch('customtkinter.CTkFrame.__init__', return_value=None):
        with patch('customtkinter.CTkScrollableFrame'):
            with patch('customtkinter.CTkLabel'):
                with patch('customtkinter.CTkCheckBox'):
                    with patch('customtkinter.CTkButton'):
                        from video_censor_personal.ui.segment_details_pane import SegmentDetailsPaneImpl
                        
                        pane = SegmentDetailsPaneImpl.__new__(SegmentDetailsPaneImpl)
                        pane.current_segment = None
                        pane.allow_checkbox = Mock()
                        pane.save_status_label = Mock()
                        pane.allow_toggle_callback = Mock()
                        
                        pane._on_allow_toggled()
                        
                        pane.allow_toggle_callback.assert_not_called()
