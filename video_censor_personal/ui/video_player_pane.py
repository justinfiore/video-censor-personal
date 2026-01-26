import customtkinter as ctk
import tkinter as tk
from typing import Optional, Callable, List, TYPE_CHECKING

if TYPE_CHECKING:
    from video_censor_personal.ui.edit_mode_controller import EditModeController
import logging
import traceback
import sys
import queue
from video_censor_personal.ui.video_player import VideoPlayer
from video_censor_personal.ui.segment_manager import Segment

logger = logging.getLogger("video_censor_personal.ui")

from video_censor_personal.ui.pyav_video_player import PyAVVideoPlayer
DEFAULT_PLAYER_CLASS = PyAVVideoPlayer
logger.info("Using PyAVVideoPlayer")


class TimelineCanvas(tk.Canvas):
    """Canvas for drawing timeline with segment markers."""
    
    PLAYHEAD_TAG = "playhead"  # Tag for the playhead line so we can update it efficiently
    START_SCRUBBER_TAG = "start_scrubber"
    END_SCRUBBER_TAG = "end_scrubber"
    SCRUBBER_REGION_TAG = "scrubber_region"
    SNAP_INCREMENT = 0.1  # Snap to 100ms increments
    MINIMUM_SEGMENT_DURATION = 0.1  # 100ms minimum
    
    def __init__(self, master, **kwargs):
        super().__init__(master, height=40, bg="#2b2b2b", highlightthickness=0, **kwargs)
        
        self.segments: List[Segment] = []
        self.duration: float = 0.0
        self.current_time: float = 0.0
        self._playhead_id: Optional[int] = None  # Canvas item ID for playhead
        
        self._visible_start: float = 0.0
        self._visible_end: float = 0.0
        self._is_zoomed: bool = False
        
        self._is_edit_mode: bool = False
        self._edit_start_time: float = 0.0
        self._edit_end_time: float = 0.0
        self._dragging_scrubber: Optional[str] = None  # "start" or "end"
        
        self._on_start_time_changed: Optional[Callable[[float], None]] = None
        self._on_end_time_changed: Optional[Callable[[float], None]] = None
        
        self.bind("<Configure>", self._on_resize)
        self.bind("<Button-1>", self._on_click)
        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<ButtonRelease-1>", self._on_release)
        
        self.seek_callback: Optional[Callable[[float], None]] = None
    
    def set_segments(self, segments: List[Segment], duration: float) -> None:
        """Set segments and video duration for timeline."""
        self.segments = segments
        self.duration = duration if duration > 0 else 100.0
        self._redraw_full()
    
    def set_current_time(self, current_time: float) -> None:
        """Update current playback position - only redraws playhead for efficiency."""
        self.current_time = current_time
        self._update_playhead_only()
    
    def set_seek_callback(self, callback: Callable[[float], None]) -> None:
        """Set callback for timeline clicks."""
        self.seek_callback = callback
    
    def set_on_start_time_changed(self, callback: Callable[[float], None]) -> None:
        """Set callback for scrubber start time changes."""
        self._on_start_time_changed = callback
    
    def set_on_end_time_changed(self, callback: Callable[[float], None]) -> None:
        """Set callback for scrubber end time changes."""
        self._on_end_time_changed = callback
    
    def set_zoom_range(self, start: float, end: float) -> None:
        """Set visible time range for zoomed view.
        
        Args:
            start: Start of visible range in seconds
            end: End of visible range in seconds
        """
        logger.info(f"[TIMELINE] set_zoom_range({start}, {end}) called")
        self._visible_start = max(0.0, start)
        self._visible_end = min(self.duration, end) if self.duration > 0 else end
        self._is_zoomed = True
        logger.info(f"[TIMELINE] Zoom set to {self._visible_start} - {self._visible_end}, is_zoomed={self._is_zoomed}")
        self._redraw_full()
        logger.info(f"[TIMELINE] set_zoom_range redraw complete")
    
    def clear_zoom(self) -> None:
        """Clear zoom and show full timeline."""
        self._visible_start = 0.0
        self._visible_end = self.duration
        self._is_zoomed = False
        self._redraw_full()
    
    def set_edit_mode(self, is_editing: bool, start_time: float = 0.0, end_time: float = 0.0) -> None:
        """Set edit mode state with scrubber positions.
        
        Args:
            is_editing: Whether edit mode is active
            start_time: Initial start scrubber position
            end_time: Initial end scrubber position
        """
        logger.info(f"[TIMELINE] set_edit_mode({is_editing}, start={start_time}, end={end_time}) called")
        self._is_edit_mode = is_editing
        self._edit_start_time = start_time
        self._edit_end_time = end_time
        self._dragging_scrubber = None
        self._redraw_full()
        logger.info(f"[TIMELINE] set_edit_mode redraw complete")
    
    def update_edit_start_time(self, time: float) -> None:
        """Update the edit start scrubber position."""
        logger.info(f"[TIMELINE] update_edit_start_time({time}) called")
        self._edit_start_time = time
        self._redraw_full()
        logger.info(f"[TIMELINE] update_edit_start_time redraw complete")
    
    def update_edit_end_time(self, time: float) -> None:
        """Update the edit end scrubber position."""
        logger.info(f"[TIMELINE] update_edit_end_time({time}) called")
        self._edit_end_time = time
        self._redraw_full()
        logger.info(f"[TIMELINE] update_edit_end_time redraw complete")
    
    @property
    def visible_start_time(self) -> float:
        """Get the visible start time."""
        return self._visible_start if self._is_zoomed else 0.0
    
    @property
    def visible_end_time(self) -> float:
        """Get the visible end time."""
        return self._visible_end if self._is_zoomed else self.duration
    
    def _on_resize(self, event):
        """Handle canvas resize."""
        self._redraw_full()
    
    def _on_click(self, event):
        """Handle timeline click to seek or start scrubber drag."""
        width = self.winfo_width()
        if width <= 0:
            return
        
        visible_duration = self.visible_end_time - self.visible_start_time
        if visible_duration <= 0:
            return
        
        if self._is_edit_mode:
            start_x = self._time_to_x(self._edit_start_time)
            end_x = self._time_to_x(self._edit_end_time)
            
            if abs(event.x - start_x) <= 10:
                self._dragging_scrubber = "start"
                return
            elif abs(event.x - end_x) <= 10:
                self._dragging_scrubber = "end"
                return
        
        click_time = self._x_to_time(event.x)
        if self.seek_callback and click_time >= 0:
            self.seek_callback(click_time)
    
    def _on_drag(self, event):
        """Handle scrubber drag."""
        if not self._is_edit_mode or not self._dragging_scrubber:
            return
        
        drag_time = self._x_to_time(event.x)
        if drag_time < 0:
            return
        
        snapped_time = round(drag_time / self.SNAP_INCREMENT) * self.SNAP_INCREMENT
        snapped_time = max(0.0, min(self.duration, snapped_time))
        
        if self._dragging_scrubber == "start":
            if snapped_time < self._edit_end_time - self.MINIMUM_SEGMENT_DURATION:
                self._edit_start_time = snapped_time
                self._redraw_full()
                if self._on_start_time_changed:
                    self._on_start_time_changed(snapped_time)
        elif self._dragging_scrubber == "end":
            if snapped_time > self._edit_start_time + self.MINIMUM_SEGMENT_DURATION:
                self._edit_end_time = snapped_time
                self._redraw_full()
                if self._on_end_time_changed:
                    self._on_end_time_changed(snapped_time)
    
    def _on_release(self, event):
        """Handle scrubber release - check if edge expansion is needed."""
        if not self._is_edit_mode or not self._dragging_scrubber:
            return
        
        width = self.winfo_width()
        if width <= 0:
            self._dragging_scrubber = None
            return
        
        if event.x <= 10 and self._dragging_scrubber == "start":
            new_start = max(0.0, self._visible_start - 30.0)
            self._visible_start = new_start
            self._redraw_full()
        elif event.x >= width - 10 and self._dragging_scrubber == "end":
            new_end = min(self.duration, self._visible_end + 30.0)
            self._visible_end = new_end
            self._redraw_full()
        
        self._dragging_scrubber = None
    
    def _time_to_x(self, time: float) -> float:
        """Convert time to x coordinate based on visible range."""
        width = self.winfo_width()
        visible_duration = self.visible_end_time - self.visible_start_time
        if visible_duration <= 0 or width <= 0:
            return 0
        return ((time - self.visible_start_time) / visible_duration) * width
    
    def _x_to_time(self, x: float) -> float:
        """Convert x coordinate to time based on visible range."""
        width = self.winfo_width()
        visible_duration = self.visible_end_time - self.visible_start_time
        if visible_duration <= 0 or width <= 0:
            return -1
        return self.visible_start_time + (x / width) * visible_duration
    
    def _update_playhead_only(self) -> None:
        """Update only the playhead position without redrawing everything.
        
        This is called frequently during playback and must be fast.
        """
        width = self.winfo_width()
        height = self.winfo_height()
        
        visible_duration = self.visible_end_time - self.visible_start_time
        if width <= 0 or height <= 0 or visible_duration <= 0:
            return
        
        self.delete(self.PLAYHEAD_TAG)
        
        if self.current_time >= self.visible_start_time and self.current_time <= self.visible_end_time:
            x_pos = self._time_to_x(self.current_time)
            self._playhead_id = self.create_line(
                x_pos, 0, x_pos, height, 
                fill="#1f6aa5", width=2,
                tags=self.PLAYHEAD_TAG
            )
    
    def _redraw_full(self) -> None:
        """Full redraw of timeline including segments, scrubbers, and playhead.
        
        This is called when segments change or canvas resizes.
        """
        self.delete("all")
        
        width = self.winfo_width()
        height = self.winfo_height()
        
        visible_start = self.visible_start_time
        visible_end = self.visible_end_time
        visible_duration = visible_end - visible_start
        
        if width <= 0 or height <= 0 or visible_duration <= 0:
            return
        
        self.create_rectangle(0, 0, width, height, fill="#2b2b2b", outline="")
        
        self.create_line(0, height // 2, width, height // 2, fill="#4a4a4a", width=2)
        
        for segment in self.segments:
            if segment.end_time < visible_start or segment.start_time > visible_end:
                continue
            
            x_start = self._time_to_x(segment.start_time)
            x_end = self._time_to_x(segment.end_time)
            
            x_start = max(0, x_start)
            x_end = min(width, x_end)
            
            if segment.allow:
                color = "#2d5f2d"
                marker_color = "#4caf50"
            else:
                color = "#5f2d2d"
                marker_color = "#f44336"
            
            self.create_rectangle(
                x_start, height * 0.3, x_end, height * 0.7,
                fill=color,
                outline=marker_color,
                width=1
            )
        
        if self._is_edit_mode:
            self._draw_scrubbers(width, height)
        
        if self.current_time >= visible_start and self.current_time <= visible_end:
            x_pos = self._time_to_x(self.current_time)
            self._playhead_id = self.create_line(
                x_pos, 0, x_pos, height, 
                fill="#1f6aa5", width=2,
                tags=self.PLAYHEAD_TAG
            )
    
    def _draw_scrubbers(self, width: int, height: int) -> None:
        """Draw edit mode scrubbers as triangular markers."""
        start_x = self._time_to_x(self._edit_start_time)
        end_x = self._time_to_x(self._edit_end_time)
        
        if 0 <= start_x <= width and 0 <= end_x <= width:
            self.create_rectangle(
                start_x, height * 0.2, end_x, height * 0.8,
                fill="#3a7ebf",
                outline="#3a7ebf",
                width=1,
                tags=self.SCRUBBER_REGION_TAG
            )
        
        if 0 <= start_x <= width:
            triangle_points = [
                start_x, 0,
                start_x - 8, 12,
                start_x + 8, 12
            ]
            self.create_polygon(
                triangle_points,
                fill="#ff9800",
                outline="#e65100",
                width=1,
                tags=self.START_SCRUBBER_TAG
            )
            self.create_line(
                start_x, 12, start_x, height,
                fill="#ff9800", width=2,
                dash=(4, 2),
                tags=self.START_SCRUBBER_TAG
            )
        
        if 0 <= end_x <= width:
            triangle_points = [
                end_x, height,
                end_x - 8, height - 12,
                end_x + 8, height - 12
            ]
            self.create_polygon(
                triangle_points,
                fill="#ff9800",
                outline="#e65100",
                width=1,
                tags=self.END_SCRUBBER_TAG
            )
            self.create_line(
                end_x, 0, end_x, height - 12,
                fill="#ff9800", width=2,
                dash=(4, 2),
                tags=self.END_SCRUBBER_TAG
            )


class VideoPlayerPaneImpl(ctk.CTkFrame):
    """Enhanced video player pane with controls and timeline."""
    
    def __init__(self, master, video_player: Optional[VideoPlayer] = None, **kwargs):
        super().__init__(master, **kwargs)
        
        # Use default player if none provided
        if video_player is None:
            try:
                video_player = DEFAULT_PLAYER_CLASS()
                logger.info(f"Created default video player: {DEFAULT_PLAYER_CLASS.__name__}")
            except Exception as e:
                logger.error(f"Failed to create default video player: {e}")
                raise
        
        self.video_player = video_player
        self.is_loaded = False
        self.time_update_callback: Optional[Callable[[float], None]] = None
        
        self._is_edit_mode: bool = False
        self._edit_mode_controller: Optional["EditModeController"] = None
        self._edit_mode_start_time: float = 0.0
        self._edit_mode_end_time: float = 0.0
        self._segment_details_pane: Optional["SegmentDetailsPaneImpl"] = None
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=0)
        self.grid_columnconfigure(0, weight=1)
        
        self.video_container = ctk.CTkFrame(self, fg_color="black")
        self.video_container.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        self.video_canvas = tk.Canvas(self.video_container, bg="black", highlightthickness=0)
        self.video_canvas.pack(fill="both", expand=True)
        
        # Create timeline frame
        self.timeline_frame = ctk.CTkFrame(self)
        self.timeline_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=(0, 5))
        self.timeline_frame.grid_columnconfigure(0, weight=1)
        self.timeline_frame.grid_columnconfigure(1, weight=0)
        
        self.timeline = TimelineCanvas(self.timeline_frame)
        self.timeline.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        self.timeline.set_seek_callback(self._on_timeline_seek)
        
        self.play_segment_button = ctk.CTkButton(
            self.timeline_frame,
            text="▶ Play Segment",
            width=120,
            command=self._on_play_segment,
            fg_color="#ff9800",
            hover_color="#e65100",
            text_color="black"
        )
        self.play_segment_button.grid(row=0, column=1, padx=5, pady=5)
        self.play_segment_button.grid_remove()
        
        # Create controls frame
        self.controls_frame = ctk.CTkFrame(self)
        self.controls_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
        self.controls_frame.grid_columnconfigure(0, weight=0)
        self.controls_frame.grid_columnconfigure(1, weight=0)
        self.controls_frame.grid_columnconfigure(2, weight=0)
        self.controls_frame.grid_columnconfigure(3, weight=0)
        self.controls_frame.grid_columnconfigure(4, weight=1)
        
        self.play_pause_button = ctk.CTkButton(
            self.controls_frame,
            text="▶ Play",
            width=100,
            command=self._on_play_pause,
            state="disabled"
        )
        self.play_pause_button.grid(row=0, column=0, padx=5, pady=5)
        
        self.skip_back_button = ctk.CTkButton(
            self.controls_frame,
            text="⏪ -10s",
            width=80,
            command=lambda: self._skip(-10),
            state="disabled"
        )
        self.skip_back_button.grid(row=0, column=1, padx=5, pady=5)
        
        self.skip_forward_button = ctk.CTkButton(
            self.controls_frame,
            text="+10s ⏩",
            width=80,
            command=lambda: self._skip(10),
            state="disabled"
        )
        self.skip_forward_button.grid(row=0, column=2, padx=5, pady=5)
        
        speed_frame = ctk.CTkFrame(self.controls_frame, fg_color="transparent")
        speed_frame.grid(row=0, column=3, padx=5, pady=5)
        
        ctk.CTkLabel(speed_frame, text="Speed:", font=("Arial", 10)).pack(side="left", padx=(0, 5))
        self.speed_var = ctk.StringVar(value="1.0x")
        self.speed_menu = ctk.CTkOptionMenu(
            speed_frame,
            variable=self.speed_var,
            values=["0.5x", "0.75x", "1.0x", "1.25x", "1.5x", "2.0x"],
            width=80,
            command=self._on_speed_changed,
            state="disabled"
        )
        self.speed_menu.pack(side="left")
        
        # A/V Sync offset control
        av_frame = ctk.CTkFrame(self.controls_frame, fg_color="transparent")
        av_frame.grid(row=1, column=0, columnspan=5, padx=5, pady=5, sticky="ew")
        av_frame.grid_columnconfigure(2, weight=1)
        
        ctk.CTkLabel(av_frame, text="A/V Sync (ms):", font=("Arial", 10)).pack(side="left", padx=(0, 5))
        self.av_sync_var = ctk.StringVar(value="1500")
        self.av_sync_entry = ctk.CTkEntry(
            av_frame,
            textvariable=self.av_sync_var,
            width=80,
            placeholder_text="1500"
        )
        self.av_sync_entry.pack(side="left", padx=(0, 5))
        self.av_sync_entry.bind("<Return>", self._on_av_sync_changed)
        
        self.av_sync_button = ctk.CTkButton(
            av_frame,
            text="Apply",
            width=60,
            height=28,
            command=self._on_av_sync_changed
        )
        self.av_sync_button.pack(side="left", padx=(0, 10))
        
        ctk.CTkLabel(av_frame, text="(positive = delay video)", font=("Arial", 8), text_color="gray").pack(side="left")
        
        self.timecode_label = ctk.CTkLabel(
            self.controls_frame,
            text="00:00:00.000 / 00:00:00.000",
            font=("Courier", 12)
        )
        self.timecode_label.grid(row=0, column=4, padx=10, pady=5)
        
        # Pass canvas to PyAV player if applicable
        if hasattr(self.video_player, '_canvas'):
            self.video_player._canvas = self.video_canvas
        
        self._update_timer_id = None
        self._start_update_timer()
    
    def _schedule_first_frame_render(self) -> None:
        """Schedule rendering of the first frame after canvas is ready."""
        if hasattr(self.video_player, 'render_first_frame'):
            try:
                self.video_player.render_first_frame()
            except Exception as e:
                logger.warning(f"Error scheduling first frame render: {e}")
    
    def load_video(self, video_path: str, segments: List[Segment]) -> None:
        """Load video file and segments."""
        try:
            logger.info(f"load_video called with path: {video_path}")
            
            if self.video_player is None:
                raise ValueError("No video player configured")
            
            # Ensure video container is realized before loading
            logger.info("Updating idle tasks to realize video container")
            self.video_container.update_idletasks()
            
            logger.info(f"Loading video: {video_path}")
            self.video_player.load(video_path)
            self.is_loaded = True
            logger.info("Video loaded successfully")
            
            self._enable_controls()
            logger.info("Controls enabled")
            
            duration = self.video_player.get_duration()
            logger.info(f"Video duration: {duration} seconds")
            self.timeline.set_segments(segments, duration)
            
            self._update_timecode()
            logger.info("Timecode updated")
            
            # Schedule first frame render after video is loaded
            self._schedule_first_frame_render()
            
        except Exception as e:
            logger.error(f"Failed to load video: {str(e)}")
            logger.error(traceback.format_exc())
            raise
    
    def _enable_controls(self) -> None:
        """Enable playback controls."""
        self.play_pause_button.configure(state="normal")
        self.skip_back_button.configure(state="normal")
        self.skip_forward_button.configure(state="normal")
        self.speed_menu.configure(state="normal")
    
    def _on_play_pause(self) -> None:
        """Handle play/pause button."""
        try:
            logger.info("_on_play_pause called")
            if not self.is_loaded or self.video_player is None:
                logger.warning(f"Cannot play: is_loaded={self.is_loaded}, has_player={self.video_player is not None}")
                return
            
            if self.video_player.is_playing():
                logger.info("Pausing video")
                self.video_player.pause()
                self.play_pause_button.configure(text="▶ Play")
            else:
                logger.info("Playing video")
                self.video_player.play()
                self.play_pause_button.configure(text="⏸ Pause")
        except Exception as e:
            logger.error(f"Error during play/pause: {str(e)}")
            logger.error(traceback.format_exc())
            raise
    
    def _skip(self, seconds: float) -> None:
        """Skip forward or backward."""
        if not self.is_loaded or self.video_player is None:
            return
        
        current = self.video_player.get_current_time()
        new_time = max(0, current + seconds)
        self.video_player.seek(new_time)
        self._update_timecode()
    
    def _on_speed_changed(self, value: str) -> None:
        """Handle playback speed change."""
        if not self.is_loaded or self.video_player is None:
            return
        
        speed = float(value.replace('x', ''))
        self.video_player.set_playback_rate(speed)
    
    def _on_av_sync_changed(self, event=None) -> None:
        """Handle A/V sync offset change."""
        if not self.is_loaded or self.video_player is None:
            return
        
        try:
            offset_ms = float(self.av_sync_var.get())
            if hasattr(self.video_player, 'set_av_sync_offset'):
                self.video_player.set_av_sync_offset(offset_ms)
                logger.info(f"A/V sync offset changed to {offset_ms:.0f}ms")
        except ValueError:
            logger.warning(f"Invalid A/V sync offset: {self.av_sync_var.get()}")
            self.av_sync_var.set("-500")
    
    def _on_timeline_seek(self, time: float) -> None:
        """Handle timeline click to seek."""
        if not self.is_loaded or self.video_player is None:
            return
        
        self.video_player.seek(time)
        self._update_timecode()
    
    def seek_to_time(self, time: float) -> None:
        """Seek to specific time."""
        if not self.is_loaded or self.video_player is None:
            return
        
        self.video_player.seek(time)
        self._update_timecode()
    
    def play(self) -> None:
        """Start playback."""
        if not self.is_loaded or self.video_player is None:
            return
        
        self.video_player.play()
        self.play_pause_button.configure(text="⏸ Pause")
    
    def pause(self) -> None:
        """Pause playback."""
        if not self.is_loaded or self.video_player is None:
            return
        
        self.video_player.pause()
        self.play_pause_button.configure(text="▶ Play")
    
    def toggle_play_pause(self) -> None:
        """Toggle play/pause state."""
        self._on_play_pause()
    
    def set_time_update_callback(self, callback: Callable[[float], None]) -> None:
        """Set callback for time updates."""
        self.time_update_callback = callback
    
    def _update_timecode(self) -> None:
        """Update timecode display and timeline."""
        try:
            if not self.is_loaded or self.video_player is None:
                return
            
            current = self.video_player.get_current_time()
            duration = self.video_player.get_duration()
            
            current_str = self._format_time(current)
            duration_str = self._format_time(duration)
            self.timecode_label.configure(text=f"{current_str} / {duration_str}")
            
            self.timeline.set_current_time(current)
            
            if self.time_update_callback:
                self.time_update_callback(current)
        except Exception as e:
            logger.error(f"Error in _update_timecode: {str(e)}")
            logger.error(traceback.format_exc())
    
    def _format_time(self, seconds: float) -> str:
        """Format seconds as HH:MM:SS.mmm."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"
    
    def _start_update_timer(self) -> None:
        """Start periodic update timer."""
        try:
            self._update_timecode()
            
            # Update canvas from queued frames (must be done on main thread for Tkinter safety)
            if hasattr(self.video_player, '_update_canvas_on_main_thread'):
                try:
                    self.video_player._update_canvas_on_main_thread()
                except Exception as e:
                    logger.warning(f"Error in canvas update: {e}")
            
            self._update_timer_id = self.after(50, self._start_update_timer)
        except Exception as e:
            logger.error(f"Error in _start_update_timer: {str(e)}")
            logger.error(traceback.format_exc())
    
    def cleanup(self) -> None:
        """Clean up resources."""
        if self._update_timer_id:
            self.after_cancel(self._update_timer_id)
        
        if self.video_player:
            self.video_player.cleanup()
    
    def update_timeline_segments(self, segments: List[Segment]) -> None:
        """Update timeline with new segment states."""
        if not self.is_loaded or self.video_player is None:
            return
        
        duration = self.video_player.get_duration()
        self.timeline.set_segments(segments, duration)
    
    def set_segment_details_pane(self, pane: "SegmentDetailsPaneImpl") -> None:
        """Set reference to segment details pane for updating UI."""
        self._segment_details_pane = pane
    
    def set_edit_mode(self, is_editing: bool, controller: Optional["EditModeController"] = None) -> None:
        """Set edit mode state and configure timeline accordingly.
        
        Args:
            is_editing: Whether edit mode is active
            controller: The edit mode controller for getting segment times
        """
        try:
            logger.info(f"[VIDEO_PLAYER] set_edit_mode called: is_editing={is_editing}, controller={controller is not None}")
            self._is_edit_mode = is_editing
            self._edit_mode_controller = controller
            
            if is_editing and controller:
                logger.info(f"[VIDEO_PLAYER] Registering controller callbacks")
                logger.info(f"[VIDEO_PLAYER] controller type={type(controller)}, has set_on_start_time_changed={hasattr(controller, 'set_on_start_time_changed')}")
                start_time = controller.edited_start or 0.0
                end_time = controller.edited_end or 0.0
                self._edit_mode_start_time = start_time
                self._edit_mode_end_time = end_time
                
                logger.info(f"[VIDEO_PLAYER] Getting video duration")
                video_duration = self.video_player.get_duration() if self.video_player else 0.0
                logger.info(f"[VIDEO_PLAYER] Getting zoom range")
                zoom_start, zoom_end = controller.get_zoom_range(video_duration)
                logger.info(f"[VIDEO_PLAYER] Setting timeline zoom range")
                self.timeline.set_zoom_range(zoom_start, zoom_end)
                logger.info(f"[VIDEO_PLAYER] Setting timeline edit mode")
                self.timeline.set_edit_mode(True, start_time, end_time)
                logger.info(f"[VIDEO_PLAYER] Timeline setup complete, about to set callbacks")
            
            try:
                logger.info(f"[VIDEO_PLAYER] About to set timeline callbacks")
                self.timeline.set_on_start_time_changed(self._on_scrubber_start_changed)
                logger.info(f"[VIDEO_PLAYER] Timeline start callback set")
                self.timeline.set_on_end_time_changed(self._on_scrubber_end_changed)
                logger.info(f"[VIDEO_PLAYER] Timeline end callback set")
            except Exception as e:
                logger.error(f"[VIDEO_PLAYER] Exception setting timeline callbacks: {e}")
                import traceback
                logger.error(traceback.format_exc())
            
            try:
                logger.info(f"[VIDEO_PLAYER] About to call controller.set_on_start_time_changed")
                controller.set_on_start_time_changed(self._on_controller_start_changed)
                logger.info(f"[VIDEO_PLAYER] set_on_start_time_changed completed")
            except Exception as e:
                logger.error(f"[VIDEO_PLAYER] Exception setting start callback: {e}")
                import traceback
                logger.error(traceback.format_exc())
            
            try:
                logger.info(f"[VIDEO_PLAYER] About to call controller.set_on_end_time_changed")
                controller.set_on_end_time_changed(self._on_controller_end_changed)
                logger.info(f"[VIDEO_PLAYER] set_on_end_time_changed completed")
            except Exception as e:
                logger.error(f"[VIDEO_PLAYER] Exception setting end callback: {e}")
                import traceback
                logger.error(traceback.format_exc())
            
            logger.info(f"[VIDEO_PLAYER] Controller callbacks registered successfully")
            self.play_segment_button.grid()
            
            if not is_editing or not controller:
                self.timeline.clear_zoom()
                self.timeline.set_edit_mode(False)
                self.timeline.set_on_start_time_changed(None)
                self.timeline.set_on_end_time_changed(None)
                self.play_segment_button.grid_remove()
        except Exception as e:
            logger.error(f"[VIDEO_PLAYER] EXCEPTION in set_edit_mode: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise
    
    def _on_play_segment(self) -> None:
        """Handle Play Segment button click - seek to start and play."""
        if not self.is_loaded or self.video_player is None:
            return
        
        if self._is_edit_mode:
            self.video_player.seek(self._edit_mode_start_time)
            self.play()
            logger.info(f"Playing segment from {self._edit_mode_start_time} to {self._edit_mode_end_time}")
    
    def _on_scrubber_start_changed(self, time: float) -> None:
        """Handle scrubber start time change."""
        self._edit_mode_start_time = time
        if self._segment_details_pane:
            self._segment_details_pane._update_start_time_display(time)
        if self._edit_mode_controller:
            self._edit_mode_controller.update_start(time)
    
    def _on_scrubber_end_changed(self, time: float) -> None:
        """Handle scrubber end time change."""
        self._edit_mode_end_time = time
        if self._segment_details_pane:
            self._segment_details_pane._update_end_time_display(time)
        if self._edit_mode_controller:
            self._edit_mode_controller.update_end(time)
    
    def _on_controller_start_changed(self, time: float) -> None:
        """Handle controller start time change (from text input)."""
        logger.info(f"[VIDEO_PLAYER] _on_controller_start_changed({time}) called")
        self._edit_mode_start_time = time
        self.timeline.update_edit_start_time(time)
        logger.info(f"[VIDEO_PLAYER] _on_controller_start_changed completed")
    
    def _on_controller_end_changed(self, time: float) -> None:
        """Handle controller end time change (from text input)."""
        logger.info(f"[VIDEO_PLAYER] _on_controller_end_changed({time}) called")
        self._edit_mode_end_time = time
        self.timeline.update_edit_end_time(time)
        logger.info(f"[VIDEO_PLAYER] _on_controller_end_changed completed")
