"""Integration tests for preview editor scaling with large segment counts.

These tests verify the segment list pane handles large numbers of segments
efficiently through pagination.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from video_censor_personal.ui.segment_manager import Segment, Detection
from video_censor_personal.ui.segment_list_pane import (
    SegmentListPaneImpl,
    SegmentListItem,
    DEFAULT_PAGE_SIZE,
)


def create_test_segments(count: int) -> list:
    """Create a list of test segments with the specified count."""
    segments = []
    labels_options = [
        ["Nudity"],
        ["Violence"],
        ["Sexual Theme"],
        ["Profanity"],
        ["Nudity", "Sexual Theme"],
        ["Violence", "Profanity"],
    ]
    
    for i in range(count):
        segment = Segment(
            id=str(i),
            start_time=i * 10.0,
            end_time=(i + 1) * 10.0,
            duration_seconds=10.0,
            labels=labels_options[i % len(labels_options)],
            description=f"Test segment {i}",
            confidence=0.5 + (i % 50) / 100.0,
            detections=[
                Detection(
                    label=labels_options[i % len(labels_options)][0],
                    confidence=0.5 + (i % 50) / 100.0,
                    reasoning=f"Test detection for segment {i}"
                )
            ],
            allow=i % 2 == 0
        )
        segments.append(segment)
    return segments


class TestSegmentListPaging:
    """Tests for segment list pagination functionality."""
    
    @pytest.fixture
    def mock_pane(self):
        """Create a mock segment list pane with pagination attributes."""
        with patch('customtkinter.CTkFrame.__init__', return_value=None):
            with patch('customtkinter.CTkScrollableFrame'):
                with patch('customtkinter.CTkLabel'):
                    with patch('customtkinter.CTkComboBox'):
                        with patch('customtkinter.CTkButton'):
                            pane = SegmentListPaneImpl.__new__(SegmentListPaneImpl)
                            pane.all_segments = []
                            pane.filtered_segments = []
                            pane.segment_items = {}
                            pane.selected_segment_id = None
                            pane.page_size = DEFAULT_PAGE_SIZE
                            pane.current_page = 0
                            pane.label_filter = Mock()
                            pane.label_filter_var = Mock()
                            pane.allow_filter_var = Mock()
                            pane._render_current_page = Mock()
                            pane._update_pagination_ui = Mock()
                            pane._on_segment_clicked = Mock()
                            return pane

    def test_default_page_size(self):
        """Test that default page size is set correctly."""
        assert DEFAULT_PAGE_SIZE == 20
    
    def test_total_pages_calculation_small(self, mock_pane):
        """Test total pages calculation for small segment count."""
        mock_pane.filtered_segments = create_test_segments(15)
        mock_pane.page_size = 20
        assert mock_pane._get_total_pages() == 1
    
    def test_total_pages_calculation_medium(self, mock_pane):
        """Test total pages calculation for medium segment count."""
        mock_pane.filtered_segments = create_test_segments(50)
        mock_pane.page_size = 20
        assert mock_pane._get_total_pages() == 3
    
    def test_total_pages_calculation_large(self, mock_pane):
        """Test total pages calculation for large segment count."""
        mock_pane.filtered_segments = create_test_segments(206)
        mock_pane.page_size = 20
        assert mock_pane._get_total_pages() == 11
    
    def test_total_pages_exact_multiple(self, mock_pane):
        """Test total pages when segment count is exact multiple of page size."""
        mock_pane.filtered_segments = create_test_segments(100)
        mock_pane.page_size = 20
        assert mock_pane._get_total_pages() == 5
    
    def test_get_page_for_segment(self, mock_pane):
        """Test finding which page contains a specific segment."""
        mock_pane.filtered_segments = create_test_segments(100)
        mock_pane.page_size = 20
        
        assert mock_pane._get_page_for_segment("0") == 0
        assert mock_pane._get_page_for_segment("19") == 0
        assert mock_pane._get_page_for_segment("20") == 1
        assert mock_pane._get_page_for_segment("99") == 4
    
    def test_get_page_for_nonexistent_segment(self, mock_pane):
        """Test finding page for segment that doesn't exist."""
        mock_pane.filtered_segments = create_test_segments(50)
        assert mock_pane._get_page_for_segment("999") is None
    
    def test_go_to_page_valid(self, mock_pane):
        """Test navigating to a valid page."""
        mock_pane.filtered_segments = create_test_segments(100)
        mock_pane.page_size = 20
        mock_pane.current_page = 0
        
        mock_pane.go_to_page(2)
        
        assert mock_pane.current_page == 2
        mock_pane._render_current_page.assert_called_once()
    
    def test_go_to_page_clamps_to_bounds(self, mock_pane):
        """Test that page navigation clamps to valid bounds."""
        mock_pane.filtered_segments = create_test_segments(100)
        mock_pane.page_size = 20
        
        mock_pane.current_page = 0
        mock_pane.go_to_page(-1)
        assert mock_pane.current_page == 0
        
        mock_pane.current_page = 0
        mock_pane.go_to_page(100)
        assert mock_pane.current_page == 4
    
    def test_go_to_page_same_page_no_render(self, mock_pane):
        """Test that navigating to current page doesn't trigger re-render."""
        mock_pane.filtered_segments = create_test_segments(100)
        mock_pane.page_size = 20
        mock_pane.current_page = 2
        
        mock_pane.go_to_page(2)
        
        mock_pane._render_current_page.assert_not_called()


class TestSegmentListScaling:
    """Tests for segment list scaling with large segment counts."""
    
    def test_load_15_segments(self):
        """Test loading 15 segments (small video)."""
        with patch('customtkinter.CTkFrame.__init__', return_value=None):
            with patch('customtkinter.CTkScrollableFrame'):
                with patch('customtkinter.CTkLabel'):
                    with patch('customtkinter.CTkComboBox'):
                        pane = SegmentListPaneImpl.__new__(SegmentListPaneImpl)
                        pane.all_segments = []
                        pane.filtered_segments = []
                        pane.segment_items = {}
                        pane.selected_segment_id = None
                        pane.page_size = DEFAULT_PAGE_SIZE
                        pane.current_page = 0
                        pane.label_filter = Mock()
                        pane._render_current_page = Mock()
                        
                        segments = create_test_segments(15)
                        pane.load_segments(segments)
                        
                        assert len(pane.all_segments) == 15
                        assert pane.current_page == 0
                        pane._render_current_page.assert_called_once()
    
    def test_load_206_segments(self):
        """Test loading 206 segments (large video from logs)."""
        with patch('customtkinter.CTkFrame.__init__', return_value=None):
            with patch('customtkinter.CTkScrollableFrame'):
                with patch('customtkinter.CTkLabel'):
                    with patch('customtkinter.CTkComboBox'):
                        pane = SegmentListPaneImpl.__new__(SegmentListPaneImpl)
                        pane.all_segments = []
                        pane.filtered_segments = []
                        pane.segment_items = {}
                        pane.selected_segment_id = None
                        pane.page_size = DEFAULT_PAGE_SIZE
                        pane.current_page = 0
                        pane.label_filter = Mock()
                        pane._render_current_page = Mock()
                        
                        segments = create_test_segments(206)
                        pane.load_segments(segments)
                        
                        assert len(pane.all_segments) == 206
                        assert len(pane.filtered_segments) == 206
                        assert pane._get_total_pages() == 11
                        pane._render_current_page.assert_called_once()


class TestAutoNavigationDuringPlayback:
    """Tests for auto-navigation when playback time changes."""
    
    @pytest.fixture
    def pane_with_segments(self):
        """Create pane with 100 segments for testing."""
        with patch('customtkinter.CTkFrame.__init__', return_value=None):
            with patch('customtkinter.CTkScrollableFrame'):
                with patch('customtkinter.CTkLabel'):
                    with patch('customtkinter.CTkComboBox'):
                        pane = SegmentListPaneImpl.__new__(SegmentListPaneImpl)
                        pane.all_segments = create_test_segments(100)
                        pane.filtered_segments = pane.all_segments.copy()
                        pane.segment_items = {}
                        pane.selected_segment_id = None
                        pane.page_size = 20
                        pane.current_page = 0
                        pane._render_current_page = Mock()
                        pane._on_segment_clicked = Mock()
                        return pane
    
    def test_highlight_segment_on_same_page(self, pane_with_segments):
        """Test highlighting segment that's on the current page."""
        pane_with_segments.highlight_segment_at_time(55.0)
        
        pane_with_segments._on_segment_clicked.assert_called_with("5")
        pane_with_segments._render_current_page.assert_not_called()
    
    def test_highlight_segment_navigates_to_different_page(self, pane_with_segments):
        """Test highlighting segment on a different page causes navigation."""
        pane_with_segments.highlight_segment_at_time(255.0)
        
        assert pane_with_segments.current_page == 1
        pane_with_segments._render_current_page.assert_called_once()
        pane_with_segments._on_segment_clicked.assert_called_with("25")
    
    def test_highlight_segment_already_selected(self, pane_with_segments):
        """Test that re-highlighting same segment doesn't cause action."""
        pane_with_segments.selected_segment_id = "5"
        pane_with_segments.highlight_segment_at_time(55.0)
        
        pane_with_segments._on_segment_clicked.assert_not_called()


class TestKeyboardNavigation:
    """Tests for keyboard navigation with pagination."""
    
    @pytest.fixture
    def pane_with_segments(self):
        """Create pane with segments across multiple pages."""
        with patch('customtkinter.CTkFrame.__init__', return_value=None):
            with patch('customtkinter.CTkScrollableFrame'):
                with patch('customtkinter.CTkLabel'):
                    with patch('customtkinter.CTkComboBox'):
                        pane = SegmentListPaneImpl.__new__(SegmentListPaneImpl)
                        pane.all_segments = create_test_segments(50)
                        pane.filtered_segments = pane.all_segments.copy()
                        pane.segment_items = {}
                        pane.selected_segment_id = "19"
                        pane.page_size = 20
                        pane.current_page = 0
                        pane._render_current_page = Mock()
                        pane._on_segment_clicked = Mock()
                        return pane
    
    def test_select_next_crosses_page_boundary(self, pane_with_segments):
        """Test that selecting next segment crosses page boundary."""
        next_id = pane_with_segments.select_next_segment()
        
        assert next_id == "20"
        assert pane_with_segments.current_page == 1
        pane_with_segments._render_current_page.assert_called_once()
    
    def test_select_previous_crosses_page_boundary(self, pane_with_segments):
        """Test that selecting previous segment crosses page boundary."""
        pane_with_segments.selected_segment_id = "20"
        pane_with_segments.current_page = 1
        
        prev_id = pane_with_segments.select_previous_segment()
        
        assert prev_id == "19"
        assert pane_with_segments.current_page == 0
        pane_with_segments._render_current_page.assert_called_once()


class TestFilterPaginationInteraction:
    """Tests for filter and pagination interaction."""
    
    def test_filter_resets_to_page_one(self):
        """Test that applying a filter resets pagination to page 1."""
        with patch('customtkinter.CTkFrame.__init__', return_value=None):
            with patch('customtkinter.CTkScrollableFrame'):
                with patch('customtkinter.CTkLabel'):
                    with patch('customtkinter.CTkComboBox'):
                        pane = SegmentListPaneImpl.__new__(SegmentListPaneImpl)
                        pane.all_segments = create_test_segments(100)
                        pane.filtered_segments = pane.all_segments.copy()
                        pane.segment_items = {}
                        pane.selected_segment_id = None
                        pane.page_size = 20
                        pane.current_page = 3
                        pane.label_filter_var = Mock()
                        pane.allow_filter_var = Mock()
                        pane.review_filter_var = Mock()
                        pane._render_current_page = Mock()
                        
                        pane.label_filter_var.get.return_value = "Violence"
                        pane.allow_filter_var.get.return_value = "All Segments"
                        pane.review_filter_var.get.return_value = "All Review Status"
                        
                        pane._on_filter_changed()
                        
                        assert pane.current_page == 0
                        pane._render_current_page.assert_called_once()


class TestPaginationUtilityMethods:
    """Tests for pagination utility methods."""
    
    def test_get_page_size(self):
        """Test get_page_size returns current page size."""
        with patch('customtkinter.CTkFrame.__init__', return_value=None):
            pane = SegmentListPaneImpl.__new__(SegmentListPaneImpl)
            pane.page_size = 25
            assert pane.get_page_size() == 25
    
    def test_set_page_size_triggers_rerender(self):
        """Test set_page_size updates page size and re-renders."""
        with patch('customtkinter.CTkFrame.__init__', return_value=None):
            pane = SegmentListPaneImpl.__new__(SegmentListPaneImpl)
            pane.page_size = 20
            pane.current_page = 3
            pane.filtered_segments = create_test_segments(100)
            pane._render_current_page = Mock()
            
            pane.set_page_size(30)
            
            assert pane.page_size == 30
            assert pane.current_page == 0
            pane._render_current_page.assert_called_once()
    
    def test_get_current_page(self):
        """Test get_current_page returns current page."""
        with patch('customtkinter.CTkFrame.__init__', return_value=None):
            pane = SegmentListPaneImpl.__new__(SegmentListPaneImpl)
            pane.current_page = 5
            assert pane.get_current_page() == 5
    
    def test_get_total_pages(self):
        """Test get_total_pages returns total page count."""
        with patch('customtkinter.CTkFrame.__init__', return_value=None):
            pane = SegmentListPaneImpl.__new__(SegmentListPaneImpl)
            pane.filtered_segments = create_test_segments(100)
            pane.page_size = 20
            assert pane.get_total_pages() == 5
