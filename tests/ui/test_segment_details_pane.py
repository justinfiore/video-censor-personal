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
                        pane.reviewed_checkbox = Mock()
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


@pytest.mark.skip(reason="Complex UI state mocking required")
def test_segment_details_pane_update_detections_display(sample_segment):
    """Skipped: Requires full widget initialization context"""
    pass


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


class TestSegmentDetailsPaneEditMode:
    """Tests for edit mode functionality in segment details pane."""
    
    @pytest.fixture
    def edit_mode_pane(self):
        """Create a pane instance with edit mode mocks."""
        with patch('customtkinter.CTkFrame.__init__', return_value=None):
            with patch('customtkinter.CTkScrollableFrame'):
                with patch('customtkinter.CTkLabel'):
                    with patch('customtkinter.CTkCheckBox'):
                        with patch('customtkinter.CTkButton'):
                            with patch('customtkinter.CTkEntry'):
                                from video_censor_personal.ui.segment_details_pane import SegmentDetailsPaneImpl
                                
                                pane = SegmentDetailsPaneImpl.__new__(SegmentDetailsPaneImpl)
                                pane._is_edit_mode = False
                                pane.action_buttons_frame = Mock()
                                pane.edit_mode_container = Mock()
                                pane.time_validation_label = Mock()
                                pane.start_time_entry = Mock()
                                pane.end_time_entry = Mock()
                                pane.edit_mode_controller = None
                                pane._label_chip_buttons = []
                                pane.label_chips_frame = Mock()
                                yield pane
    
    def test_set_edit_mode_enters_edit_mode(self, edit_mode_pane):
        """Test that set_edit_mode(True) shows edit UI."""
        edit_mode_pane.set_edit_mode(True)
        
        assert edit_mode_pane._is_edit_mode is True
        edit_mode_pane.action_buttons_frame.grid_remove.assert_called_once()
        edit_mode_pane.edit_mode_container.grid.assert_called_once()
    
    def test_set_edit_mode_exits_edit_mode(self, edit_mode_pane):
        """Test that set_edit_mode(False) hides edit UI."""
        edit_mode_pane._is_edit_mode = True
        
        edit_mode_pane.set_edit_mode(False)
        
        assert edit_mode_pane._is_edit_mode is False
        edit_mode_pane.edit_mode_container.grid_remove.assert_called_once()
        edit_mode_pane.action_buttons_frame.grid.assert_called_once()
        edit_mode_pane.time_validation_label.configure.assert_called_with(text="")
    
    def test_set_edit_mode_populates_time_fields(self, edit_mode_pane):
        """Test that entering edit mode populates time input fields."""
        mock_controller = Mock()
        mock_controller.edited_start = 10.5
        mock_controller.edited_end = 15.2
        mock_controller.edited_labels = ["Test"]
        edit_mode_pane.edit_mode_controller = mock_controller
        
        edit_mode_pane.set_edit_mode(True)
        
        edit_mode_pane.start_time_entry.delete.assert_called()
        edit_mode_pane.start_time_entry.insert.assert_called()
        edit_mode_pane.end_time_entry.delete.assert_called()
        edit_mode_pane.end_time_entry.insert.assert_called()
    
    def test_format_time_short(self, edit_mode_pane):
        """Test short time format for input fields."""
        result = edit_mode_pane._format_time_short(65.123)
        assert result == "01:05.123"
        
        result = edit_mode_pane._format_time_short(0.0)
        assert result == "00:00.000"
        
        result = edit_mode_pane._format_time_short(599.999)
        assert result == "09:59.999"
    
    def test_parse_time_input_mm_ss_mmm(self, edit_mode_pane):
        """Test parsing MM:SS.mmm format."""
        result = edit_mode_pane._parse_time_input("01:30.500")
        assert result == 90.5
    
    def test_parse_time_input_mm_ss(self, edit_mode_pane):
        """Test parsing MM:SS format."""
        result = edit_mode_pane._parse_time_input("02:15")
        assert result == 135
    
    def test_parse_time_input_ss_mmm(self, edit_mode_pane):
        """Test parsing SS.mmm format."""
        result = edit_mode_pane._parse_time_input("45.750")
        assert result == 45.75
    
    def test_parse_time_input_ss(self, edit_mode_pane):
        """Test parsing SS format."""
        result = edit_mode_pane._parse_time_input("60")
        assert result == 60.0
    
    def test_parse_time_input_invalid(self, edit_mode_pane):
        """Test parsing invalid format returns None."""
        assert edit_mode_pane._parse_time_input("invalid") is None
        assert edit_mode_pane._parse_time_input("1:2:3:4") is None
        assert edit_mode_pane._parse_time_input("") is None
    
    def test_on_cancel_edit_calls_controller(self, edit_mode_pane):
        """Test cancel button calls controller cancel."""
        mock_controller = Mock()
        edit_mode_pane.edit_mode_controller = mock_controller
        
        edit_mode_pane._on_cancel_edit()
        
        mock_controller.cancel.assert_called_once()
    
    def test_on_apply_edit_calls_controller(self, edit_mode_pane):
        """Test apply button calls controller apply."""
        mock_controller = Mock()
        mock_controller.apply.return_value = True
        edit_mode_pane.edit_mode_controller = mock_controller
        
        edit_mode_pane._on_apply_edit()
        
        mock_controller.apply.assert_called_once()
    
    def test_on_apply_edit_shows_error_on_failure(self, edit_mode_pane):
        """Test apply shows error when controller apply fails."""
        mock_controller = Mock()
        mock_controller.apply.return_value = False
        edit_mode_pane.edit_mode_controller = mock_controller
        
        edit_mode_pane._on_apply_edit()
        
        edit_mode_pane.time_validation_label.configure.assert_called()
        call_args = edit_mode_pane.time_validation_label.configure.call_args
        assert "Failed" in str(call_args)


class TestSegmentDetailsPaneLabelEditing:
    """Tests for label editing functionality."""
    
    @pytest.fixture
    def label_edit_pane(self):
        """Create a pane instance with label editing mocks."""
        with patch('customtkinter.CTkFrame.__init__', return_value=None):
            with patch('customtkinter.CTkScrollableFrame'):
                with patch('customtkinter.CTkLabel'):
                    with patch('customtkinter.CTkCheckBox'):
                        with patch('customtkinter.CTkButton') as mock_btn:
                            with patch('customtkinter.CTkEntry'):
                                from video_censor_personal.ui.segment_details_pane import SegmentDetailsPaneImpl
                                
                                pane = SegmentDetailsPaneImpl.__new__(SegmentDetailsPaneImpl)
                                pane._label_chip_buttons = []
                                pane.label_chips_frame = Mock()
                                pane.edit_mode_controller = None
                                pane.segment_manager = None
                                pane.add_label_button = Mock()
                                yield pane
    
    def test_update_labels_display_creates_chips(self, label_edit_pane):
        """Test that updating labels creates chip buttons."""
        with patch('customtkinter.CTkButton') as mock_btn:
            mock_chip = Mock()
            mock_btn.return_value = mock_chip
            
            label_edit_pane._update_labels_display(["Label1", "Label2"])
            
            assert len(label_edit_pane._label_chip_buttons) == 2
    
    def test_update_labels_display_clears_old_chips(self, label_edit_pane):
        """Test that updating labels clears old chip buttons first."""
        old_chip = Mock()
        label_edit_pane._label_chip_buttons = [old_chip]
        
        with patch('customtkinter.CTkButton') as mock_btn:
            mock_btn.return_value = Mock()
            label_edit_pane._update_labels_display(["NewLabel"])
        
        old_chip.destroy.assert_called_once()
        assert len(label_edit_pane._label_chip_buttons) == 1
    
    def test_on_remove_label_calls_controller(self, label_edit_pane):
        """Test removing a label calls controller."""
        mock_controller = Mock()
        label_edit_pane.edit_mode_controller = mock_controller
        
        label_edit_pane._on_remove_label("TestLabel")
        
        mock_controller.remove_label.assert_called_once_with("TestLabel")
    
    def test_on_add_label_calls_controller(self, label_edit_pane):
        """Test adding a label calls controller."""
        mock_controller = Mock()
        label_edit_pane.edit_mode_controller = mock_controller
        
        label_edit_pane._on_add_label("NewLabel")
        
        mock_controller.add_label.assert_called_once_with("NewLabel")
    
    def test_get_known_labels_from_segment_manager(self, label_edit_pane):
        """Test getting known labels from segment manager."""
        mock_manager = Mock()
        seg1 = Mock()
        seg1.labels = ["Label1", "Label2"]
        seg2 = Mock()
        seg2.labels = ["Label2", "Label3"]
        mock_manager.get_all_segments.return_value = [seg1, seg2]
        label_edit_pane.segment_manager = mock_manager
        
        known = label_edit_pane._get_known_labels()
        
        assert known == {"Label1", "Label2", "Label3"}
    
    def test_get_available_labels_excludes_current(self, label_edit_pane):
        """Test available labels excludes current labels."""
        mock_manager = Mock()
        seg = Mock()
        seg.labels = ["Label1", "Label2", "Label3"]
        mock_manager.get_all_segments.return_value = [seg]
        label_edit_pane.segment_manager = mock_manager
        
        mock_controller = Mock()
        mock_controller.edited_labels = ["Label1"]
        label_edit_pane.edit_mode_controller = mock_controller
        
        available = label_edit_pane._get_available_labels()
        
        assert "Label1" not in available
        assert "Label2" in available
        assert "Label3" in available


class TestSegmentDetailsPaneDeleteConfirmation:
    """Tests for delete confirmation dialog."""
    
    def test_on_delete_segment_with_no_segment(self):
        """Test delete does nothing when no segment selected."""
        with patch('customtkinter.CTkFrame.__init__', return_value=None):
            with patch('customtkinter.CTkScrollableFrame'):
                with patch('customtkinter.CTkLabel'):
                    with patch('customtkinter.CTkCheckBox'):
                        with patch('customtkinter.CTkButton'):
                            from video_censor_personal.ui.segment_details_pane import SegmentDetailsPaneImpl
                            
                            pane = SegmentDetailsPaneImpl.__new__(SegmentDetailsPaneImpl)
                            pane.current_segment = None
                            pane.delete_segment_callback = Mock()
                            
                            pane._on_delete_segment_clicked()
                            
                            pane.delete_segment_callback.assert_not_called()
    
    def test_on_delete_segment_calls_callback_on_confirm(self, sample_segment):
        """Test delete calls callback when user confirms."""
        with patch('customtkinter.CTkFrame.__init__', return_value=None):
            with patch('customtkinter.CTkScrollableFrame'):
                with patch('customtkinter.CTkLabel'):
                    with patch('customtkinter.CTkCheckBox'):
                        with patch('customtkinter.CTkButton'):
                            with patch('tkinter.messagebox.askyesno', return_value=True):
                                from video_censor_personal.ui.segment_details_pane import SegmentDetailsPaneImpl
                                
                                pane = SegmentDetailsPaneImpl.__new__(SegmentDetailsPaneImpl)
                                pane.current_segment = sample_segment
                                pane.delete_segment_callback = Mock()
                                
                                pane._on_delete_segment_clicked()
                                
                                pane.delete_segment_callback.assert_called_once_with(sample_segment.id)
    
    def test_on_delete_segment_no_callback_on_cancel(self, sample_segment):
        """Test delete doesn't call callback when user cancels."""
        with patch('customtkinter.CTkFrame.__init__', return_value=None):
            with patch('customtkinter.CTkScrollableFrame'):
                with patch('customtkinter.CTkLabel'):
                    with patch('customtkinter.CTkCheckBox'):
                        with patch('customtkinter.CTkButton'):
                            with patch('tkinter.messagebox.askyesno', return_value=False):
                                from video_censor_personal.ui.segment_details_pane import SegmentDetailsPaneImpl
                                
                                pane = SegmentDetailsPaneImpl.__new__(SegmentDetailsPaneImpl)
                                pane.current_segment = sample_segment
                                pane.delete_segment_callback = Mock()
                                
                                pane._on_delete_segment_clicked()
                                
                                pane.delete_segment_callback.assert_not_called()
