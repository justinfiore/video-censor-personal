import customtkinter as ctk
from typing import Optional, Callable


class SegmentListPane(ctk.CTkFrame):
    """Pane for displaying scrollable segment list."""
    
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.segment_click_callback: Optional[Callable[[str], None]] = None
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self.scrollable_frame = ctk.CTkScrollableFrame(self)
        self.scrollable_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        self.segment_frames = {}
        self.selected_segment_id: Optional[str] = None
    
    def set_segment_click_callback(self, callback: Callable[[str], None]) -> None:
        """Set callback for segment click events."""
        self.segment_click_callback = callback
    
    def clear(self) -> None:
        """Clear all segments from the list."""
        for frame in self.segment_frames.values():
            frame.destroy()
        self.segment_frames.clear()
        self.selected_segment_id = None


class VideoPlayerPane(ctk.CTkFrame):
    """Pane for video player with controls."""
    
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_columnconfigure(0, weight=1)
        
        self.video_container = ctk.CTkFrame(self, fg_color="black")
        self.video_container.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        self.controls_container = ctk.CTkFrame(self)
        self.controls_container.grid(row=1, column=0, sticky="ew", padx=5, pady=5)


class SegmentDetailsPane(ctk.CTkFrame):
    """Pane for displaying segment details."""
    
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self.details_container = ctk.CTkScrollableFrame(self)
        self.details_container.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)


class ThreePaneLayout(ctk.CTkFrame):
    """Three-pane layout: segment list (left), video player (center), details (bottom)."""
    
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.grid_rowconfigure(0, weight=7)
        self.grid_rowconfigure(1, weight=3)
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=6)
        
        self.segment_list_pane = SegmentListPane(self)
        self.segment_list_pane.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=2, pady=2)
        
        self.video_player_pane = VideoPlayerPane(self)
        self.video_player_pane.grid(row=0, column=1, sticky="nsew", padx=2, pady=2)
        
        self.segment_details_pane = SegmentDetailsPane(self)
        self.segment_details_pane.grid(row=1, column=1, sticky="nsew", padx=2, pady=2)
    
    def get_segment_list_pane(self) -> SegmentListPane:
        """Get segment list pane."""
        return self.segment_list_pane
    
    def get_video_player_pane(self) -> VideoPlayerPane:
        """Get video player pane."""
        return self.video_player_pane
    
    def get_segment_details_pane(self) -> SegmentDetailsPane:
        """Get segment details pane."""
        return self.segment_details_pane
