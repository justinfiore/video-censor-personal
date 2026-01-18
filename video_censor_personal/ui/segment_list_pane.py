"""Segment list pane with pagination for scalable UI rendering.

This module implements a paginated segment list to handle large numbers of segments
(200+) without blocking the UI during widget creation. Instead of creating all
widgets upfront, only the current page of segments is rendered.

Pagination Strategy:
- Segments are stored in memory (all_segments, filtered_segments)
- Only widgets for the current page (default 20 items) are created
- Page navigation automatically destroys old widgets and creates new ones
- Auto-navigation during playback moves to the page containing the active segment
- Selection tracking works across pages by navigating when needed

Performance Improvement:
- For a 206-segment video, widget creation is reduced from 206 to 20 widgets (~90%)
- Initial UI display time reduced from seconds to <500ms

Logging Levels:
- DEBUG: Phase transitions (load started, page rendered, filter applied)
- TRACE (level 5): Per-widget timing, detailed profiling data
"""

import customtkinter as ctk
from typing import Optional, Callable, List, Dict
import logging
import time
from video_censor_personal.ui.segment_manager import Segment

logger = logging.getLogger("video_censor_personal.ui")

DEFAULT_PAGE_SIZE = 20


class SegmentListItem(ctk.CTkFrame):
    """Individual segment list item widget."""
    
    def __init__(self, master, segment: Segment, index: int, click_callback: Optional[Callable[[str], None]] = None, **kwargs):
        super().__init__(master, **kwargs)
        
        self.segment = segment
        self.index = index
        self.click_callback = click_callback
        self.is_selected = False
        
        self.configure(corner_radius=5, border_width=2, border_color="gray50")
        
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=0)
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self.index_label = ctk.CTkLabel(
            self,
            text=f"#{index + 1}",
            width=40,
            font=("Arial", 10),
            text_color="gray60"
        )
        self.index_label.grid(row=0, column=0, padx=(5, 0), pady=10, sticky="w")
        
        self.allow_indicator = ctk.CTkLabel(
            self,
            text="✓" if segment.allow else "✗",
            width=30,
            font=("Arial", 16, "bold"),
            text_color="green" if segment.allow else "red"
        )
        self.allow_indicator.grid(row=0, column=1, padx=(5, 5), pady=10, sticky="w")
        
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.grid(row=0, column=2, padx=(0, 10), pady=10, sticky="ew")
        content_frame.grid_columnconfigure(0, weight=1)
        
        time_text = self._format_time_range(segment.start_time, segment.end_time)
        self.time_label = ctk.CTkLabel(
            content_frame,
            text=time_text,
            font=("Arial", 12, "bold"),
            anchor="w"
        )
        self.time_label.grid(row=0, column=0, sticky="ew", pady=(0, 2))
        
        labels_text = ", ".join(segment.labels) if segment.labels else "No labels"
        self.labels_label = ctk.CTkLabel(
            content_frame,
            text=labels_text,
            font=("Arial", 10),
            anchor="w",
            text_color="gray"
        )
        self.labels_label.grid(row=1, column=0, sticky="ew")
        
        self.bind("<Button-1>", self._on_click)
        self.index_label.bind("<Button-1>", self._on_click)
        self.allow_indicator.bind("<Button-1>", self._on_click)
        self.time_label.bind("<Button-1>", self._on_click)
        self.labels_label.bind("<Button-1>", self._on_click)
        content_frame.bind("<Button-1>", self._on_click)
    
    def _format_time_range(self, start: float, end: float) -> str:
        """Format time range as HH:MM:SS."""
        def format_time(seconds):
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        
        return f"{format_time(start)} - {format_time(end)}"
    
    def _on_click(self, event):
        """Handle click event."""
        if self.click_callback:
            self.click_callback(self.segment.id)
    
    def set_selected(self, selected: bool) -> None:
        """Set selection state."""
        self.is_selected = selected
        if selected:
            self.configure(border_color="#1f6aa5", fg_color="#2a2d2e")
        else:
            self.configure(border_color="gray50", fg_color="transparent")
    
    def update_allow_indicator(self, allow: bool) -> None:
        """Update allow indicator."""
        self.allow_indicator.configure(
            text="✓" if allow else "✗",
            text_color="green" if allow else "red"
        )
        self.segment.allow = allow


class SegmentListPaneImpl(ctk.CTkFrame):
    """Enhanced segment list pane with paging for scalability.
    
    Paging Strategy:
    ----------------
    To handle large videos (200+ segments) without UI blocking, this pane uses
    pagination instead of rendering all segments at once:
    
    1. All segment data is stored in `all_segments` and `filtered_segments`
    2. Only widgets for the current page are rendered (default: 20 per page)
    3. When navigating pages, old widgets are destroyed and new ones created
    4. Auto-navigation: During playback, automatically navigates to the page
       containing the currently playing segment
    5. Filter integration: Filters reset to page 1 and recalculate pagination
    
    This provides ~90% reduction in widget creation for 206-segment videos
    (20 widgets vs 206), keeping the UI responsive during initial load.
    
    Key methods:
    - `load_segments()`: Stores all segments, renders first page
    - `go_to_page(n)`: Navigate to specific page, re-renders widgets
    - `_render_current_page()`: Destroys old widgets, creates page widgets
    - `highlight_segment_at_time()`: Auto-navigates to correct page during playback
    """
    
    def __init__(self, master, page_size: int = DEFAULT_PAGE_SIZE, **kwargs):
        super().__init__(master, **kwargs)
        
        self.segment_click_callback: Optional[Callable[[str], None]] = None
        self.segment_items: Dict[str, SegmentListItem] = {}
        self.selected_segment_id: Optional[str] = None
        self.all_segments: List[Segment] = []
        self.filtered_segments: List[Segment] = []
        
        self.page_size = page_size
        self.current_page = 0
        
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)
        self.grid_columnconfigure(0, weight=1)
        
        self.filter_frame = ctk.CTkFrame(self)
        self.filter_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        self.filter_frame.grid_columnconfigure(0, weight=1)
        
        filter_label = ctk.CTkLabel(self.filter_frame, text="Filters", font=("Arial", 12, "bold"))
        filter_label.grid(row=0, column=0, sticky="w", padx=10, pady=(5, 2))
        
        self.label_filter_var = ctk.StringVar(value="All Labels")
        self.label_filter = ctk.CTkComboBox(
            self.filter_frame,
            variable=self.label_filter_var,
            values=["All Labels"],
            command=self._on_filter_changed,
            state="readonly"
        )
        self.label_filter.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 5))
        
        self.allow_filter_var = ctk.StringVar(value="All Segments")
        self.allow_filter = ctk.CTkComboBox(
            self.filter_frame,
            variable=self.allow_filter_var,
            values=["All Segments", "Allowed Only", "Not Allowed Only"],
            command=self._on_filter_changed,
            state="readonly"
        )
        self.allow_filter.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 5))
        
        self.scrollable_frame = ctk.CTkScrollableFrame(self)
        self.scrollable_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.scrollable_frame.grid_columnconfigure(0, weight=1)
        
        self._create_pagination_controls()
    
    def _create_pagination_controls(self) -> None:
        """Create the pagination UI controls."""
        self.pagination_frame = ctk.CTkFrame(self)
        self.pagination_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
        self.pagination_frame.grid_columnconfigure(1, weight=1)
        
        self.prev_button = ctk.CTkButton(
            self.pagination_frame,
            text="◀ Previous",
            width=90,
            command=self._go_to_previous_page
        )
        self.prev_button.grid(row=0, column=0, padx=5, pady=5)
        
        self.page_label = ctk.CTkLabel(
            self.pagination_frame,
            text="Page 1 of 1",
            font=("Arial", 11)
        )
        self.page_label.grid(row=0, column=1, padx=5, pady=5)
        
        self.next_button = ctk.CTkButton(
            self.pagination_frame,
            text="Next ▶",
            width=90,
            command=self._go_to_next_page
        )
        self.next_button.grid(row=0, column=2, padx=5, pady=5)
    
    def _get_total_pages(self) -> int:
        """Calculate total number of pages."""
        if not self.filtered_segments:
            return 1
        return (len(self.filtered_segments) + self.page_size - 1) // self.page_size
    
    def _update_pagination_ui(self) -> None:
        """Update pagination controls state."""
        total_pages = self._get_total_pages()
        self.page_label.configure(text=f"Page {self.current_page + 1} of {total_pages}")
        self.prev_button.configure(state="normal" if self.current_page > 0 else "disabled")
        self.next_button.configure(state="normal" if self.current_page < total_pages - 1 else "disabled")
    
    def _go_to_previous_page(self) -> None:
        """Navigate to previous page."""
        if self.current_page > 0:
            self.go_to_page(self.current_page - 1)
    
    def _go_to_next_page(self) -> None:
        """Navigate to next page."""
        if self.current_page < self._get_total_pages() - 1:
            self.go_to_page(self.current_page + 1)
    
    def go_to_page(self, page_number: int) -> None:
        """Navigate to a specific page number (0-indexed)."""
        total_pages = self._get_total_pages()
        page_number = max(0, min(page_number, total_pages - 1))
        
        if page_number != self.current_page:
            self.current_page = page_number
            self._render_current_page()
    
    def _get_page_for_segment(self, segment_id: str) -> Optional[int]:
        """Get the page number containing a specific segment."""
        for idx, segment in enumerate(self.filtered_segments):
            if segment.id == segment_id:
                return idx // self.page_size
        return None
    
    def set_segment_click_callback(self, callback: Callable[[str], None]) -> None:
        """Set callback for segment click events."""
        self.segment_click_callback = callback
    
    def load_segments(self, segments: List[Segment]) -> None:
        """Load and display segments."""
        start_time = time.time()
        num_segments = len(segments)
        logger.debug(f"[PROFILE] Segment list: load_segments started with {num_segments} segments")
        
        self.all_segments = segments
        self.filtered_segments = segments
        self.current_page = 0
        
        parse_start = time.time()
        unique_labels = set()
        for seg in segments:
            unique_labels.update(seg.labels)
        parse_time = time.time() - parse_start
        logger.log(5, f"[PROFILE] Segment list: parsed labels from {num_segments} segments in {parse_time:.3f}s")
        
        label_values = ["All Labels"] + sorted(list(unique_labels))
        self.label_filter.configure(values=label_values)
        
        self._render_current_page()
        
        elapsed = time.time() - start_time
        logger.debug(f"[PROFILE] Segment list: load_segments completed in {elapsed:.2f}s")
    
    def _render_current_page(self) -> None:
        """Render only the current page of segments."""
        start_time = time.time()
        num_total = len(self.filtered_segments)
        
        start_idx = self.current_page * self.page_size
        end_idx = min(start_idx + self.page_size, num_total)
        page_segments = self.filtered_segments[start_idx:end_idx]
        num_page = len(page_segments)
        
        logger.debug(f"[PROFILE] Segment list: rendering page {self.current_page + 1} ({num_page} of {num_total} segments)")
        
        destroy_start = time.time()
        for item in self.segment_items.values():
            item.destroy()
        self.segment_items.clear()
        destroy_time = time.time() - destroy_start
        logger.debug(f"[PROFILE] Segment list: destroyed old items in {destroy_time:.3f}s")
        
        logger.debug(f"[PROFILE] Segment list: widget creation started for {num_page} items")
        create_start = time.time()
        for row_idx, segment in enumerate(page_segments):
            global_idx = start_idx + row_idx
            item_start = time.time()
            item = SegmentListItem(
                self.scrollable_frame,
                segment,
                index=global_idx,
                click_callback=self._on_segment_clicked
            )
            item_creation_time = time.time() - item_start
            logger.log(5, f"[PROFILE] Segment list: created widget {row_idx+1}/{num_page} (id: {segment.id}) in {item_creation_time:.3f}s")
            
            item.grid(row=row_idx, column=0, sticky="ew", pady=2, padx=2)
            self.segment_items[segment.id] = item
        
        create_time = time.time() - create_start
        logger.debug(f"[PROFILE] Segment list: {num_page} widgets created in {create_time:.2f}s")
        
        layout_start = time.time()
        if self.selected_segment_id and self.selected_segment_id in self.segment_items:
            self.segment_items[self.selected_segment_id].set_selected(True)
        layout_time = time.time() - layout_start
        
        self._update_pagination_ui()
        
        elapsed = time.time() - start_time
        logger.debug(f"[PROFILE] Segment list: layout complete in {layout_time:.3f}s")
        logger.debug(f"[PROFILE] Segment list: total page rendering time {elapsed:.2f}s (destroy: {destroy_time:.3f}s, create: {create_time:.3f}s, layout: {layout_time:.3f}s)")
    
    def _on_segment_clicked(self, segment_id: str) -> None:
        """Handle segment click."""
        if self.selected_segment_id and self.selected_segment_id in self.segment_items:
            self.segment_items[self.selected_segment_id].set_selected(False)
        
        self.selected_segment_id = segment_id
        if segment_id in self.segment_items:
            self.segment_items[segment_id].set_selected(True)
        
        if self.segment_click_callback:
            self.segment_click_callback(segment_id)
    
    def _on_filter_changed(self, value=None) -> None:
        """Handle filter change."""
        label_filter = self.label_filter_var.get()
        allow_filter = self.allow_filter_var.get()
        
        self.filtered_segments = self.all_segments
        
        if label_filter != "All Labels":
            self.filtered_segments = [
                seg for seg in self.filtered_segments
                if label_filter in seg.labels
            ]
        
        if allow_filter == "Allowed Only":
            self.filtered_segments = [seg for seg in self.filtered_segments if seg.allow]
        elif allow_filter == "Not Allowed Only":
            self.filtered_segments = [seg for seg in self.filtered_segments if not seg.allow]
        
        self.current_page = 0
        self._render_current_page()
    
    def highlight_segment_at_time(self, current_time: float) -> None:
        """Highlight segment containing current playback time and navigate to its page."""
        for idx, segment in enumerate(self.filtered_segments):
            if segment.start_time <= current_time <= segment.end_time:
                if self.selected_segment_id != segment.id:
                    target_page = idx // self.page_size
                    if target_page != self.current_page:
                        self.current_page = target_page
                        self._render_current_page()
                    self._on_segment_clicked(segment.id)
                return
    
    def update_segment_allow(self, segment_id: str, allow: bool) -> None:
        """Update allow indicator for a segment."""
        if segment_id in self.segment_items:
            self.segment_items[segment_id].update_allow_indicator(allow)
        
        for segment in self.all_segments:
            if segment.id == segment_id:
                segment.allow = allow
                break
        
        for segment in self.filtered_segments:
            if segment.id == segment_id:
                segment.allow = allow
                break
    
    def select_next_segment(self) -> Optional[str]:
        """Select next segment in list, navigating pages as needed."""
        if not self.filtered_segments:
            return None
        
        if self.selected_segment_id is None:
            self.current_page = 0
            self._render_current_page()
            next_id = self.filtered_segments[0].id
            self._on_segment_clicked(next_id)
            return next_id
        
        for idx, seg in enumerate(self.filtered_segments):
            if seg.id == self.selected_segment_id:
                if idx < len(self.filtered_segments) - 1:
                    next_idx = idx + 1
                    next_id = self.filtered_segments[next_idx].id
                    target_page = next_idx // self.page_size
                    if target_page != self.current_page:
                        self.current_page = target_page
                        self._render_current_page()
                    self._on_segment_clicked(next_id)
                    return next_id
                break
        
        return self.selected_segment_id
    
    def select_previous_segment(self) -> Optional[str]:
        """Select previous segment in list, navigating pages as needed."""
        if not self.filtered_segments:
            return None
        
        if self.selected_segment_id is None:
            self.current_page = 0
            self._render_current_page()
            prev_id = self.filtered_segments[0].id
            self._on_segment_clicked(prev_id)
            return prev_id
        
        for idx, seg in enumerate(self.filtered_segments):
            if seg.id == self.selected_segment_id:
                if idx > 0:
                    prev_idx = idx - 1
                    prev_id = self.filtered_segments[prev_idx].id
                    target_page = prev_idx // self.page_size
                    if target_page != self.current_page:
                        self.current_page = target_page
                        self._render_current_page()
                    self._on_segment_clicked(prev_id)
                    return prev_id
                break
        
        return self.selected_segment_id
    
    def get_selected_segment_id(self) -> Optional[str]:
        """Get currently selected segment ID."""
        return self.selected_segment_id
    
    def clear(self) -> None:
        """Clear all segments."""
        for item in self.segment_items.values():
            item.destroy()
        self.segment_items.clear()
        self.all_segments.clear()
        self.filtered_segments.clear()
        self.selected_segment_id = None
        self.current_page = 0
        self._update_pagination_ui()
    
    def handle_page_up(self, event=None) -> None:
        """Handle Page Up key press."""
        self._go_to_previous_page()
    
    def handle_page_down(self, event=None) -> None:
        """Handle Page Down key press."""
        self._go_to_next_page()
    
    def get_page_size(self) -> int:
        """Get current page size."""
        return self.page_size
    
    def set_page_size(self, size: int) -> None:
        """Set page size and re-render."""
        if size > 0 and size != self.page_size:
            self.page_size = size
            self.current_page = 0
            self._render_current_page()
    
    def get_current_page(self) -> int:
        """Get current page number (0-indexed)."""
        return self.current_page
    
    def get_total_pages(self) -> int:
        """Get total number of pages."""
        return self._get_total_pages()
