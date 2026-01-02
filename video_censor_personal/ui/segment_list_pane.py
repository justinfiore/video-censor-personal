import customtkinter as ctk
from typing import Optional, Callable, List, Dict
import logging
import time
from video_censor_personal.ui.segment_manager import Segment

logger = logging.getLogger("video_censor_personal.ui")


class SegmentListItem(ctk.CTkFrame):
    """Individual segment list item widget."""
    
    def __init__(self, master, segment: Segment, click_callback: Optional[Callable[[str], None]] = None, **kwargs):
        super().__init__(master, **kwargs)
        
        self.segment = segment
        self.click_callback = click_callback
        self.is_selected = False
        
        self.configure(corner_radius=5, border_width=2, border_color="gray50")
        
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self.allow_indicator = ctk.CTkLabel(
            self,
            text="✓" if segment.allow else "✗",
            width=30,
            font=("Arial", 16, "bold"),
            text_color="green" if segment.allow else "red"
        )
        self.allow_indicator.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="w")
        
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.grid(row=0, column=1, padx=(0, 10), pady=10, sticky="ew")
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
    """Enhanced segment list pane with full functionality."""
    
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.segment_click_callback: Optional[Callable[[str], None]] = None
        self.segment_items: Dict[str, SegmentListItem] = {}
        self.selected_segment_id: Optional[str] = None
        self.all_segments: List[Segment] = []
        self.filtered_segments: List[Segment] = []
        
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
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
        
        # Extract labels
        parse_start = time.time()
        unique_labels = set()
        for seg in segments:
            unique_labels.update(seg.labels)
        parse_time = time.time() - parse_start
        logger.log(5, f"[PROFILE] Segment list: parsed labels from {num_segments} segments in {parse_time:.3f}s")
        
        label_values = ["All Labels"] + sorted(list(unique_labels))
        self.label_filter.configure(values=label_values)
        
        # Render segments
        self._render_segments()
        
        elapsed = time.time() - start_time
        logger.debug(f"[PROFILE] Segment list: load_segments completed in {elapsed:.2f}s")
    
    def _render_segments(self) -> None:
        """Render filtered segments."""
        start_time = time.time()
        num_segments = len(self.filtered_segments)
        
        logger.debug(f"[PROFILE] Segment list: started parsing {num_segments} segments")
        
        # Destroy old items
        destroy_start = time.time()
        for item in self.segment_items.values():
            item.destroy()
        self.segment_items.clear()
        destroy_time = time.time() - destroy_start
        logger.debug(f"[PROFILE] Segment list: destroyed old items in {destroy_time:.3f}s")
        
        # Create new items
        logger.debug(f"[PROFILE] Segment list: widget creation started for {num_segments} items")
        create_start = time.time()
        for idx, segment in enumerate(self.filtered_segments):
            item_start = time.time()
            item = SegmentListItem(
                self.scrollable_frame,
                segment,
                click_callback=self._on_segment_clicked
            )
            item_creation_time = time.time() - item_start
            logger.log(5, f"[PROFILE] Segment list: created widget {idx+1}/{num_segments} (id: {segment.id}) in {item_creation_time:.3f}s")
            
            item.grid(row=idx, column=0, sticky="ew", pady=2, padx=2)
            self.segment_items[segment.id] = item
        
        create_time = time.time() - create_start
        logger.debug(f"[PROFILE] Segment list: {num_segments} widgets created in {create_time:.2f}s")
        
        # Layout and rendering
        layout_start = time.time()
        # Restore selection
        if self.selected_segment_id and self.selected_segment_id in self.segment_items:
            self.segment_items[self.selected_segment_id].set_selected(True)
        layout_time = time.time() - layout_start
        
        elapsed = time.time() - start_time
        logger.debug(f"[PROFILE] Segment list: layout complete in {layout_time:.3f}s")
        logger.debug(f"[PROFILE] Segment list: total rendering time {elapsed:.2f}s (destroy: {destroy_time:.3f}s, create: {create_time:.3f}s, layout: {layout_time:.3f}s)")
    
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
        
        self._render_segments()
    
    def highlight_segment_at_time(self, current_time: float) -> None:
        """Highlight segment containing current playback time."""
        for segment in self.filtered_segments:
            if segment.start_time <= current_time <= segment.end_time:
                if self.selected_segment_id != segment.id:
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
        """Select next segment in list."""
        if not self.filtered_segments:
            return None
        
        if self.selected_segment_id is None:
            next_id = self.filtered_segments[0].id
            self._on_segment_clicked(next_id)
            return next_id
        
        for idx, seg in enumerate(self.filtered_segments):
            if seg.id == self.selected_segment_id:
                if idx < len(self.filtered_segments) - 1:
                    next_id = self.filtered_segments[idx + 1].id
                    self._on_segment_clicked(next_id)
                    return next_id
                break
        
        return self.selected_segment_id
    
    def select_previous_segment(self) -> Optional[str]:
        """Select previous segment in list."""
        if not self.filtered_segments:
            return None
        
        if self.selected_segment_id is None:
            prev_id = self.filtered_segments[0].id
            self._on_segment_clicked(prev_id)
            return prev_id
        
        for idx, seg in enumerate(self.filtered_segments):
            if seg.id == self.selected_segment_id:
                if idx > 0:
                    prev_id = self.filtered_segments[idx - 1].id
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
