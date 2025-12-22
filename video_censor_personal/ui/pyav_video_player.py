"""PyAV-based video player with cross-platform support and A/V synchronization."""

import logging
import threading
import queue
import time
import numpy as np
from typing import Optional, Callable, List
from video_censor_personal.ui.video_player import VideoPlayer
from video_censor_personal.ui.audio_player import SimpleAudioPlayer

logger = logging.getLogger("video_censor_personal.ui")

try:
    import av
    PYAV_AVAILABLE = True
except ImportError:
    PYAV_AVAILABLE = False
    av = None


class PyAVVideoPlayer(VideoPlayer):
    """PyAV-based video player with cross-platform support."""
    
    def __init__(self, canvas_widget=None):
        """Initialize PyAV video player.
        
        Args:
            canvas_widget: Optional tkinter Canvas to render video frames
            
        Raises:
            RuntimeError: If PyAV is not available
        """
        if not PYAV_AVAILABLE or av is None:
            raise RuntimeError("PyAV library not available. Install PyAV (pip install PyAV)")
        
        self._canvas = canvas_widget
        self._canvas_photo_image = None
        self._container: Optional[object] = None
        self._video_stream = None
        self._audio_stream = None
        self._is_playing = False
        self._duration = 0.0
        self._current_time = 0.0
        self._playback_rate = 1.0
        self._volume = 1.0
        self._time_callback: Optional[Callable[[float], None]] = None
        
        # Threading
        self._decode_thread: Optional[threading.Thread] = None
        self._audio_thread: Optional[threading.Thread] = None
        self._render_thread: Optional[threading.Thread] = None
        self._stop_event: threading.Event = threading.Event()
        self._pause_event: threading.Event = threading.Event()
        self._seek_event: threading.Event = threading.Event()
        self._seek_target: float = 0.0
        
        # Frame queue for decoded frames (thread-safe)
        self._frame_queue: queue.Queue = queue.Queue(maxsize=30)
        self._audio_queue: queue.Queue = queue.Queue(maxsize=30)
        
        # Synchronization
        self._frame_lock = threading.RLock()
        self._audio_player: Optional[SimpleAudioPlayer] = None
        self._last_frame_time = 0.0
        self._sync_offset = 0.0  # Offset between audio and video
        self._frame_count = 0
        self._dropped_frames = 0
        
        logger.info("PyAVVideoPlayer initialized")
    
    def load(self, video_path: str) -> None:
        """Load a video file for playback."""
        try:
            logger.info(f"Loading video: {video_path}")
            
            # Close previous video if loaded
            if self._container is not None:
                self._cleanup_playback()
            
            # Open container
            try:
                self._container = av.open(video_path)
            except av.error.FileNotFoundError:
                logger.error(f"Video file not found: {video_path}")
                raise ValueError(f"Video file not found: {video_path}")
            except av.error.InvalidDataFound:
                logger.error(f"Invalid video file format: {video_path}")
                raise ValueError(f"Invalid video file format: {video_path}")
            except Exception as e:
                logger.error(f"Failed to open video file: {e}")
                raise ValueError(f"Failed to open video file: {video_path}: {e}")
            
            logger.info("Container opened")
            
            # Find streams
            self._video_stream = None
            self._audio_stream = None
            
            for stream in self._container.streams:
                if stream.type == 'video' and self._video_stream is None:
                    self._video_stream = stream
                    logger.info(f"Video stream found: {stream.codec_context.name} {stream.width}x{stream.height}")
                elif stream.type == 'audio' and self._audio_stream is None:
                    self._audio_stream = stream
                    logger.info(f"Audio stream found: {stream.codec_context.name}")
            
            # Warn if video or audio missing
            if self._video_stream is None:
                logger.warning("No video stream found in file")
            if self._audio_stream is None:
                logger.warning("No audio stream found in file")
            
            # Get duration
            if self._container.duration:
                self._duration = float(self._container.duration) * av.time_base
            else:
                self._duration = 0.0
            
            logger.info(f"Video loaded: duration={self._duration:.2f}s")
            
            # Render first frame to canvas (on next tick to ensure canvas is realized)
            if self._video_stream is not None:
                try:
                    logger.info("Scheduling first frame render")
                    # Schedule for next iteration to ensure canvas has dimensions
                    if self._canvas is not None:
                        self._canvas.after(10, self._render_first_frame)
                except Exception as e:
                    logger.warning(f"Failed to schedule first frame: {e}")
            
        except Exception as e:
            logger.error(f"Failed to load video: {e}")
            self._container = None
            self._video_stream = None
            self._audio_stream = None
            raise
    
    def play(self) -> None:
        """Start or resume playback."""
        if self._container is None:
            logger.warning("No video loaded")
            return
        
        with self._frame_lock:
            if self._is_playing:
                logger.warning("Already playing")
                return
            
            logger.info("Starting playback")
            self._is_playing = True
            self._pause_event.clear()
            self._stop_event.clear()
            
            # Initialize audio player if needed
            if self._audio_stream is not None and self._audio_player is None:
                try:
                    self._initialize_audio_player()
                except Exception as e:
                    logger.warning(f"Failed to initialize audio player: {e}")
                    self._audio_player = None
            
            # Start decode thread
            if self._decode_thread is None or not self._decode_thread.is_alive():
                self._decode_thread = threading.Thread(target=self._decode_thread_main, daemon=True)
                self._decode_thread.start()
            
            # Start audio playback if audio stream exists
            if self._audio_stream is not None and self._audio_player is not None:
                try:
                    self._audio_player.play()
                except Exception as e:
                    logger.error(f"Error starting audio playback: {e}")
    
    def pause(self) -> None:
        """Pause playback."""
        with self._frame_lock:
            if not self._is_playing:
                logger.warning("Not playing")
                return
            
            logger.info("Pausing playback")
            self._is_playing = False
            self._pause_event.set()
            
            if self._audio_player is not None:
                self._audio_player.pause()
    
    def seek(self, seconds: float) -> None:
        """Seek to a specific time position in seconds."""
        if self._container is None:
            logger.warning("No video loaded")
            return
        
        # Clamp to valid range
        seconds = max(0.0, min(seconds, self._duration))
        
        with self._frame_lock:
            logger.info(f"Seeking to {seconds:.2f}s")
            self._seek_target = seconds
            self._seek_event.set()
            self._current_time = seconds
            
            # Seek audio player
            if self._audio_player is not None:
                self._audio_player.seek(seconds)
    
    def set_volume(self, level: float) -> None:
        """Set volume level (0.0 to 1.0)."""
        level = max(0.0, min(1.0, level))
        self._volume = level
        
        if self._audio_player is not None:
            self._audio_player.set_volume(level)
    
    def get_current_time(self) -> float:
        """Get current playback position in seconds."""
        with self._frame_lock:
            if self._audio_player is not None and self._audio_player.is_playing():
                # Use audio time as source of truth during playback
                return self._audio_player.get_current_time()
            return self._current_time
    
    def on_time_changed(self, callback: Callable[[float], None]) -> None:
        """Register a callback for time change events."""
        self._time_callback = callback
    
    def set_playback_rate(self, rate: float) -> None:
        """Set playback speed."""
        self._playback_rate = rate
        logger.info(f"Setting playback rate to {rate}x")
    
    def cleanup(self) -> None:
        """Clean up resources and stop playback."""
        logger.info("Cleaning up PyAVVideoPlayer")
        self._cleanup_playback()
        
        if self._audio_player is not None:
            self._audio_player.cleanup()
            self._audio_player = None
        
        if self._container is not None:
            self._container.close()
            self._container = None
    
    def is_playing(self) -> bool:
        """Check if video is currently playing."""
        with self._frame_lock:
            return self._is_playing
    
    def get_duration(self) -> float:
        """Get total duration of loaded video in seconds."""
        return self._duration
    
    def _cleanup_playback(self) -> None:
        """Stop playback threads and clear state."""
        logger.info("Stopping playback")
        self._is_playing = False
        self._stop_event.set()
        
        if self._audio_player is not None:
            self._audio_player.pause()
        
        # Wait for threads to finish
        if self._decode_thread is not None and self._decode_thread.is_alive():
            self._decode_thread.join(timeout=2.0)
        
        if self._render_thread is not None and self._render_thread.is_alive():
            self._render_thread.join(timeout=2.0)
        
        # Clear queues
        while not self._frame_queue.empty():
            try:
                self._frame_queue.get_nowait()
            except queue.Empty:
                break
    
    def _decode_thread_main(self) -> None:
        """Main decoding thread."""
        try:
            while not self._stop_event.is_set():
                # Handle pause
                if self._pause_event.is_set():
                    self._pause_event.wait(timeout=0.1)
                    continue
                
                # Handle seek
                if self._seek_event.is_set():
                    self._seek_event.clear()
                    self._perform_seek()
                    continue
                
                # Decode frames
                try:
                    self._decode_frames()
                except Exception as e:
                    logger.error(f"Error decoding frames: {e}")
                    self._is_playing = False
                    break
                
        except Exception as e:
            logger.error(f"Decode thread error: {e}")
            self._is_playing = False
    
    def _render_first_frame(self) -> None:
        """Decode and render the first frame of the video."""
        if self._video_stream is None or self._canvas is None:
            logger.debug(f"Cannot render first frame: video_stream={self._video_stream is not None}, canvas={self._canvas is not None}")
            return
        
        try:
            logger.debug("Rendering first frame...")
            # Seek to beginning
            self._container.seek(0)
            
            # Decode first frame
            frame_rendered = False
            for packet in self._container.demux(self._video_stream):
                for frame in packet.decode():
                    self._render_frame_to_canvas(frame)
                    logger.info("First frame rendered successfully")
                    frame_rendered = True
                    return
            
            if not frame_rendered:
                logger.warning("No frames available to render")
        except Exception as e:
            logger.warning(f"Failed to render first frame: {e}")
            import traceback
            traceback.print_exc()
    
    def _perform_seek(self) -> None:
        """Perform seek operation."""
        try:
            logger.info(f"Performing seek to {self._seek_target:.2f}s")
            
            # Convert seconds to stream time base
            target_timestamp = int(self._seek_target / av.time_base)
            
            # Seek in container
            self._container.seek(target_timestamp)
            
            # Clear frame queue
            while not self._frame_queue.empty():
                try:
                    self._frame_queue.get_nowait()
                except queue.Empty:
                    break
            
            logger.info(f"Seek complete")
        except Exception as e:
            logger.error(f"Seek failed: {e}")
    
    def _decode_frames(self) -> None:
        """Decode frames from video stream."""
        if self._video_stream is None:
            logger.warning("No video stream")
            self._is_playing = False
            return
        
        # Decode a few frames
        try:
            for packet in self._container.demux(self._video_stream):
                if self._stop_event.is_set():
                    return
                
                try:
                    for frame in packet.decode():
                        if self._stop_event.is_set():
                            return
                        
                        # Extract frame info
                        frame_data = {
                            'frame': frame,
                            'pts': frame.pts,
                            'time': frame.time if hasattr(frame, 'time') else 0.0,
                        }
                        
                        # Try to put in queue, skip if full
                        try:
                            self._frame_queue.put(frame_data, block=False)
                            self._frame_count += 1
                        except queue.Full:
                            self._dropped_frames += 1
                            if self._dropped_frames % 10 == 0:
                                logger.debug(f"Frame queue full, dropped {self._dropped_frames} frames total")
                        
                        # Start render thread if not running
                        if self._render_thread is None or not self._render_thread.is_alive():
                            self._render_thread = threading.Thread(target=self._render_thread_main, daemon=True)
                            self._render_thread.start()
                
                except (ValueError, RuntimeError) as e:
                    logger.warning(f"Error decoding packet: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error during frame decoding: {e}")
            self._is_playing = False
    
    def _render_thread_main(self) -> None:
        """Main rendering thread."""
        try:
            while not self._stop_event.is_set():
                try:
                    # Get frame from queue with timeout
                    frame_data = self._frame_queue.get(timeout=0.5)
                    
                    if frame_data is None:
                        continue
                    
                    frame = frame_data['frame']
                    
                    # Skip if paused
                    if self._pause_event.is_set():
                        continue
                    
                    # Update current time
                    with self._frame_lock:
                        if hasattr(frame, 'pts') and frame.pts is not None:
                            self._current_time = float(frame.pts) * av.time_base
                        
                        if self._time_callback is not None:
                            self._time_callback(self.get_current_time())
                    
                    # Render frame to canvas if available
                    if self._canvas is not None:
                        self._render_frame_to_canvas(frame)
                
                except queue.Empty:
                    continue
                except Exception as e:
                    logger.error(f"Error rendering frame: {e}")
        
        except Exception as e:
            logger.error(f"Render thread error: {e}")
    
    def _render_frame_to_canvas(self, frame) -> None:
        """Render PyAV frame to tkinter Canvas."""
        try:
            # Ensure canvas exists
            if self._canvas is None:
                logger.warning("Canvas not available for rendering")
                return
            
            # Check canvas dimensions
            canvas_width = self._canvas.winfo_width()
            canvas_height = self._canvas.winfo_height()
            
            if canvas_width < 1 or canvas_height < 1:
                logger.debug(f"Canvas not ready: {canvas_width}x{canvas_height}, skipping frame")
                return
            
            # Convert frame to RGB
            try:
                if frame.format.name in ['yuv420p', 'yuvj420p']:
                    rgb_frame = frame.to_rgb()
                elif frame.format.name == 'rgb24':
                    rgb_frame = frame
                else:
                    rgb_frame = frame.to_rgb()
            except Exception as e:
                logger.warning(f"Failed to convert frame format {frame.format.name}: {e}")
                return
            
            # Convert to numpy array
            try:
                image_array = rgb_frame.to_ndarray()
            except Exception as e:
                logger.warning(f"Failed to convert frame to ndarray: {e}")
                return
            
            # Validate array shape
            if image_array.size == 0 or len(image_array.shape) < 2:
                logger.warning(f"Invalid frame array shape: {image_array.shape}")
                return
            
            # Convert numpy array to PIL Image
            try:
                from PIL import Image, ImageTk
                
                pil_image = Image.fromarray(image_array, mode='RGB')
                
                # Calculate aspect-preserving resize
                try:
                    frame_height, frame_width = image_array.shape[0], image_array.shape[1]
                    aspect_ratio = frame_width / frame_height
                    
                    # Fit within canvas preserving aspect
                    if (canvas_width / canvas_height) > aspect_ratio:
                        new_height = canvas_height
                        new_width = int(new_height * aspect_ratio)
                    else:
                        new_width = canvas_width
                        new_height = int(new_width / aspect_ratio)
                    
                    if new_width > 0 and new_height > 0:
                        pil_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                        logger.debug(f"Resized frame to {new_width}x{new_height}")
                except Exception as e:
                    logger.warning(f"Failed to resize frame: {e}")
                
                # Convert to PhotoImage and keep reference
                self._canvas_photo_image = ImageTk.PhotoImage(pil_image)
                
                # Update canvas on main thread
                try:
                    canvas_width = self._canvas.winfo_width()
                    canvas_height = self._canvas.winfo_height()
                    
                    if canvas_width > 0 and canvas_height > 0:
                        self._canvas.delete("all")
                        self._canvas.create_image(
                            canvas_width // 2,
                            canvas_height // 2,
                            image=self._canvas_photo_image
                        )
                        self._canvas.update_idletasks()
                        logger.debug(f"Frame rendered to canvas")
                except Exception as e:
                    logger.warning(f"Failed to update canvas: {e}")
                
            except ImportError:
                logger.error("PIL/Pillow not available for image rendering")
        
        except Exception as e:
            logger.error(f"Error rendering frame: {e}")
    
    def _initialize_audio_player(self) -> None:
        """Initialize audio player and load audio stream."""
        if self._audio_stream is None or self._audio_player is not None:
            return
        
        logger.info("Initializing audio player")
        self._audio_player = SimpleAudioPlayer()
        
        # Decode all audio frames
        audio_frames_list = []
        sample_rate = self._audio_stream.sample_rate
        channels = self._audio_stream.channels
        
        logger.info(f"Extracting audio: {sample_rate}Hz, {channels} channels")
        
        try:
            for frame in self._container.decode(self._audio_stream):
                try:
                    # Convert to numpy array (shape: (samples, channels) for multichannel or (samples,) for mono)
                    array = frame.to_ndarray()
                    
                    # Ensure int16 format
                    if array.dtype != np.int16:
                        if array.dtype in [np.float32, np.float64]:
                            # Convert float to int16
                            array = (array * 32767).astype(np.int16)
                        else:
                            array = array.astype(np.int16)
                    
                    audio_frames_list.append(array)
                except Exception as e:
                    logger.warning(f"Error decoding audio frame: {e}")
                    continue
        except Exception as e:
            logger.warning(f"Error decoding audio stream: {e}")
            self._audio_player = None
            return
        
        if not audio_frames_list:
            logger.warning("No audio frames decoded")
            self._audio_player = None
            return
        
        try:
            # Concatenate all frames
            if audio_frames_list[0].ndim == 2:
                # Multichannel audio: concatenate along samples axis
                audio_data = np.concatenate(audio_frames_list, axis=0)
            else:
                # Mono audio
                audio_data = np.concatenate(audio_frames_list, axis=0)
            
            logger.info(f"Loaded {len(audio_data)} audio samples")
            
            # Load into audio player
            self._audio_player.load_audio_data(audio_data, sample_rate, channels)
            self._audio_player.set_volume(self._volume)
        
        except Exception as e:
            logger.error(f"Error loading audio data: {e}")
            self._audio_player = None
