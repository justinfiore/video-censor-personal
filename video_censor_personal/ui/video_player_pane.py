import customtkinter as ctk
import tkinter as tk
from typing import Optional, Callable, List
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
    
    def __init__(self, master, **kwargs):
        super().__init__(master, height=40, bg="#2b2b2b", highlightthickness=0, **kwargs)
        
        self.segments: List[Segment] = []
        self.duration: float = 0.0
        self.current_time: float = 0.0
        
        self.bind("<Configure>", self._on_resize)
        self.bind("<Button-1>", self._on_click)
        
        self.seek_callback: Optional[Callable[[float], None]] = None
    
    def set_segments(self, segments: List[Segment], duration: float) -> None:
        """Set segments and video duration for timeline."""
        self.segments = segments
        self.duration = duration if duration > 0 else 100.0
        self._redraw()
    
    def set_current_time(self, current_time: float) -> None:
        """Update current playback position."""
        self.current_time = current_time
        self._redraw()
    
    def set_seek_callback(self, callback: Callable[[float], None]) -> None:
        """Set callback for timeline clicks."""
        self.seek_callback = callback
    
    def _on_resize(self, event):
        """Handle canvas resize."""
        self._redraw()
    
    def _on_click(self, event):
        """Handle timeline click to seek."""
        if self.duration <= 0:
            return
        
        width = self.winfo_width()
        if width <= 0:
            return
        
        position = event.x / width
        seek_time = position * self.duration
        
        if self.seek_callback:
            self.seek_callback(seek_time)
    
    def _redraw(self) -> None:
        """Redraw timeline."""
        self.delete("all")
        
        width = self.winfo_width()
        height = self.winfo_height()
        
        if width <= 0 or height <= 0 or self.duration <= 0:
            return
        
        self.create_rectangle(0, 0, width, height, fill="#2b2b2b", outline="")
        
        self.create_line(0, height // 2, width, height // 2, fill="#4a4a4a", width=2)
        
        for segment in self.segments:
            x_start = (segment.start_time / self.duration) * width
            x_end = (segment.end_time / self.duration) * width
            
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
        
        if self.current_time > 0:
            x_pos = (self.current_time / self.duration) * width
            self.create_line(x_pos, 0, x_pos, height, fill="#1f6aa5", width=2)


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
        
        self.timeline = TimelineCanvas(self.timeline_frame)
        self.timeline.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        self.timeline.set_seek_callback(self._on_timeline_seek)
        
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
