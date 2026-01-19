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
    
    def __init__(self, canvas_widget=None, av_sync_offset_ms: float = 1500.0):
        """Initialize PyAV video player.
        
        Args:
            canvas_widget: Optional tkinter Canvas to render video frames
            av_sync_offset_ms: A/V sync offset in milliseconds. Positive means delay video relative to audio.
                             This accounts for presentation latency differences. Default 1500ms (typical latency mismatch).
            
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
        # Canvas update queue size of 3 gives render thread some buffer while main thread polls
        self._canvas_update_queue: queue.Queue = queue.Queue(maxsize=3)
        
        # Synchronization
        self._frame_lock = threading.RLock()
        self._container_lock = threading.RLock()  # Protect container access from multiple threads
        self._audio_player: Optional[SimpleAudioPlayer] = None
        self._last_frame_time = 0.0
        self._sync_offset = 0.0  # Offset between audio and video
        self._frame_count = 0
        self._dropped_frames = 0
        
        # Cached canvas dimensions (updated on main thread, read by render thread)
        # This avoids calling winfo_width/height from background threads which can hang
        self._cached_canvas_width = 0
        self._cached_canvas_height = 0
        
        # A/V drift statistics for debugging
        self._drift_samples: List[float] = []  # Track last 100 drift values
        self._max_drift_buffer_size = 100
        
        # Presentation latency offset (in seconds)
        # This accounts for the difference in buffering between audio and video pipelines
        # Negative offset means video is advanced (played earlier) relative to audio
        # This is useful when audio output has less latency than video display
        self._av_latency_offset = av_sync_offset_ms / 1000.0
        
        logger.info(f"PyAVVideoPlayer initialized with A/V sync offset={av_sync_offset_ms:.0f}ms")
    
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
            
            # Get duration (convert from AV_TIME_BASE units to seconds)
            # av.time_base is 1/1000000, so duration is in microseconds
            if self._container.duration:
                self._duration = float(self._container.duration) / av.time_base
            else:
                self._duration = 0.0
            
            logger.info(f"Video loaded: duration={self._duration:.2f}s")
            
            # Audio Loading Optimization:
            # --------------------------
            # Audio extraction is deferred to avoid blocking the main thread during video load.
            # For large videos (1+ hours), audio extraction can take 5+ seconds.
            # 
            # Strategy:
            # 1. On load(): Only detect audio stream presence, don't extract
            # 2. On render_first_frame(): Schedule audio extraction on background thread
            # 3. On play(): If audio not ready, extract synchronously (fallback)
            #
            # This allows the UI to remain responsive - user sees first frame immediately
            # while audio extraction happens in background. See _initialize_audio_player().
            
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
            self._stop_event.clear()
            
            # Determine playback start position:
            # - If a seek was pending (_seek_event set), use _seek_target
            # - Otherwise use _current_time
            # This ensures audio and video start from the same position
            if self._seek_event.is_set():
                playback_start_pos = self._seek_target
                logger.info(f"Play starting from pending seek target: {playback_start_pos:.2f}s")
            else:
                playback_start_pos = self._current_time
                logger.info(f"Play starting from current position: {playback_start_pos:.2f}s")
            
            # Sync audio to the playback start position
            if self._audio_player is not None:
                logger.info(f"Syncing audio to playback position: {playback_start_pos:.2f}s")
                self._audio_player.seek(playback_start_pos)
            
            # Check if we're resuming from pause (decode thread still alive)
            is_resuming = self._decode_thread is not None and self._decode_thread.is_alive()
            
            if is_resuming:
                # Trigger a seek to current position before resuming
                # This is needed because the container may have advanced while paused
                # (render thread was consuming frames from queue)
                logger.info(f"Resuming playback - triggering seek to {playback_start_pos:.2f}s")
                self._seek_target = playback_start_pos
                self._seek_event.set()
                
                # Restart audio playback (was paused)
                if self._audio_player is not None:
                    logger.info("Restarting audio playback on resume")
                    self._audio_player.play()
            
            # Clear pause event AFTER setting up seek (so decode thread handles seek first)
            self._pause_event.clear()
            
            # Clear any stale frames in queue from first frame render
            # (first frame might have been queued before a seek was requested)
            while not self._frame_queue.empty():
                try:
                    self._frame_queue.get_nowait()
                except queue.Empty:
                    break
            
            # Initialize and start audio SYNCHRONOUSLY before starting video threads
            # This ensures audio is ready when render thread checks is_playing()
            if self._audio_stream is not None and self._audio_player is None:
                logger.info("Initializing audio BEFORE video playback (synchronous)")
                self._initialize_audio_player()
                if self._audio_player is not None:
                    logger.info("Audio initialized, starting playback")
                    self._audio_player.play()
                    # Verify audio is actually playing
                    if not self._audio_player.is_playing():
                        logger.warning("Audio start failed, but continuing with video playback")
            elif self._audio_player is not None and not self._audio_player.is_playing():
                # Audio was paused, resume it
                logger.info("Resuming audio playback")
                self._audio_player.play()
            
            # NOW start video decode/render threads (audio is ready and playing)
            # Start decode thread if not already running
            if not is_resuming:
                logger.info(f"Starting decode thread with seek_target={self._seek_target:.2f}s")
                self._decode_thread = threading.Thread(target=self._decode_thread_main, daemon=True)
                self._decode_thread.start()
    
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
    
    def get_current_time(self) -> float:
        """Get current playback position in seconds.
        
        NOTE: We check audio player FIRST (without _frame_lock) to avoid
        deadlocks. The audio player has its own lock for thread safety.
        """
        # Check audio player first (doesn't need _frame_lock)
        audio_player = self._audio_player  # Local ref to avoid race
        if audio_player is not None and audio_player.is_playing():
            # Use audio time as source of truth during playback
            return audio_player.get_current_time()
        
        # Fall back to video time (needs lock for thread-safe read)
        with self._frame_lock:
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
    
    def set_av_sync_offset(self, offset_ms: float) -> None:
        """Set A/V sync offset in milliseconds.
        
        Negative offset advances video (plays it earlier).
        Positive offset delays video (plays it later).
        """
        self._av_latency_offset = offset_ms / 1000.0
        logger.info(f"A/V sync offset changed to {offset_ms:.0f}ms")
    
    def render_first_frame(self) -> None:
        """Render the first frame to canvas (call after canvas is assigned and ready)."""
        if self._video_stream is None or self._canvas is None:
            logger.warning("Cannot render first frame: video_stream or canvas not available")
            return
        
        try:
            logger.info("Rendering first frame in background")
            first_frame_thread = threading.Thread(target=self._render_first_frame_bg, daemon=True)
            first_frame_thread.start()
        except Exception as e:
            logger.warning(f"Failed to render first frame: {e}")
    
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
            # Check if there's a pending seek event from the main thread
            # This can happen if seek() was called before play()
            seek_target = None
            with self._frame_lock:
                if self._seek_event.is_set():
                    seek_target = self._seek_target
                    self._seek_event.clear()
                else:
                    seek_target = self._current_time
            
            # Always seek to start position to ensure we're at the right place
            # (container may be at a different position from previous playback)
            logger.info(f"Seeking video to start position: {seek_target:.2f}s")
            target_timestamp = int(seek_target * av.time_base)
            with self._container_lock:
                self._container.seek(target_timestamp)
                # CRITICAL: Flush decoder buffers after seeking to discard pre-seek frames
                # PyAV keeps internal buffers that may contain frames from before the seek
                for _ in self._container.demux(self._video_stream):
                    # Just consume packets to flush buffers
                    try:
                        for frame in _.decode():
                            # Discard flushed frames
                            pass
                    except:
                        # Ignore decode errors during flush
                        pass
                    # Only flush a few packets worth
                    break
            
            # Clear any stale frames in queues
            while not self._frame_queue.empty():
                try:
                    self._frame_queue.get_nowait()
                except queue.Empty:
                    break
            
            # Also clear canvas update queue to avoid showing stale frames
            while not self._canvas_update_queue.empty():
                try:
                    self._canvas_update_queue.get_nowait()
                except queue.Empty:
                    break
            
            # Wait briefly for audio player to be initialized (may be initializing in background)
            # This fixes the race condition where decode thread starts before audio init completes
            audio_wait_start = time.time()
            audio_wait_timeout = 5.0  # Wait up to 5 seconds for audio init
            while self._audio_stream is not None and self._audio_player is None:
                if time.time() - audio_wait_start > audio_wait_timeout:
                    logger.warning("Timeout waiting for audio player initialization, starting video without audio sync")
                    break
                if self._stop_event.is_set():
                    return
                time.sleep(0.1)
            
            # Audio should already be initialized and playing from play() method
            # No need to start it here
            
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
    
    def _render_first_frame_bg(self) -> None:
        """Decode and prepare the first frame of the video (background thread).
        
        Note: First frame is displayed when playback starts or on demand.
        This method decodes it to ensure video is valid and shows a frame preview.
        """
        if self._video_stream is None or self._canvas is None:
            logger.debug(f"Cannot render first frame: video_stream={self._video_stream is not None}, canvas={self._canvas is not None}")
            return
        
        # Don't run while playback is active (container access is not thread-safe)
        if self._is_playing:
            logger.debug("Skipping first frame render: playback is active")
            return
        
        try:
            logger.debug("Decoding first frame...")
            # Wait for cached canvas dimensions to be set (updated by main thread)
            # Don't call winfo_width/height directly from background thread - it can hang!
            start_time = time.time()
            canvas_ready = False
            while time.time() - start_time < 2.0:  # Reduced timeout from 5s to 2s
                if self._cached_canvas_width > 0 and self._cached_canvas_height > 0:
                    canvas_ready = True
                    break
                time.sleep(0.05)
            
            if not canvas_ready:
                logger.warning("Canvas dimensions not cached after 2s timeout, proceeding anyway")
            
            # Protect container access with lock (container is not thread-safe for multiple operations)
            with self._container_lock:
                # Seek to beginning
                self._container.seek(0)
                
                # Decode first frame and queue it
                frame_queued = False
                for packet in self._container.demux(self._video_stream):
                    for frame in packet.decode():
                        # Queue frame for rendering (will be displayed on play or demand)
                        try:
                            # Convert to RGB numpy array immediately
                            image_array = frame.to_rgb().to_ndarray()
                            self._frame_queue.put({
                                'image_array': image_array,
                                'pts': frame.pts,
                                'time': frame.time if hasattr(frame, 'time') else 0.0,
                            }, block=False)
                            logger.info("First frame queued for display")
                            frame_queued = True
                            
                            # After first frame is queued, schedule audio decoding in background
                            # This prevents blocking the UI while extracting all audio frames
                            if self._audio_stream is not None:
                                try:
                                    logger.info("Scheduling audio decoding after first frame")
                                    audio_thread = threading.Thread(target=self._initialize_audio_player, daemon=True)
                                    audio_thread.start()
                                except Exception as e:
                                    logger.warning(f"Failed to schedule audio decoding: {e}")
                            
                            return
                        except queue.Full:
                            logger.debug("Frame queue full, skipping first frame")
                            return
                        except Exception as e:
                            logger.warning(f"Failed to queue first frame: {e}")
                            return
                
                if not frame_queued:
                    logger.warning("No frames available to decode")
        except Exception as e:
            logger.warning(f"Failed to decode first frame: {e}")
    
    def _perform_seek(self) -> None:
        """Perform seek operation."""
        try:
            logger.info(f"Performing seek to {self._seek_target:.2f}s")
            
            # Convert seconds to container timestamp (in AV_TIME_BASE units, which is microseconds)
            target_timestamp = int(self._seek_target * av.time_base)
            
            # Protect container access with lock
            with self._container_lock:
                # Seek in container
                self._container.seek(target_timestamp)
            
            # Clear frame queue
            while not self._frame_queue.empty():
                try:
                    self._frame_queue.get_nowait()
                except queue.Empty:
                    break
            
            # Clear canvas update queue too - stale frames should not be displayed
            while not self._canvas_update_queue.empty():
                try:
                    self._canvas_update_queue.get_nowait()
                except queue.Empty:
                    break
            
            logger.info(f"Seek complete")
        except Exception as e:
            logger.error(f"Seek failed: {e}")
    
    def _decode_frames(self) -> None:
        """Decode frames from video stream (yielding to other threads)."""
        if self._video_stream is None:
            logger.warning("No video stream")
            self._is_playing = False
            return
        
        # Decode just a few frames at a time and yield control
        frames_decoded = 0
        max_frames_per_batch = 3
        seek_target_time = None
        frames_skipped_for_seek = 0
        
        # If we just did a seek, we may need to skip frames until we reach the target time
        with self._frame_lock:
            if self._seek_target > 0:
                seek_target_time = self._seek_target
                current = self._current_time
                logger.info(f"[FRAME_SKIP] Decode starting - _seek_target={self._seek_target:.3f}s, _current_time={self._current_time:.3f}s, will skip pre-seek frames")
            else:
                logger.info(f"[FRAME_SKIP] Decode starting - _seek_target={self._seek_target:.3f}s (no skipping needed)")
        
        try:
            # Protect container access with lock
            with self._container_lock:
                # Create demux iterator AFTER seeking has been handled in _decode_thread_main
                # This is critical: the iterator must be created after any seeks to respect the new position
                demux_iter = self._container.demux(self._video_stream)
            
            for packet in demux_iter:
                if self._stop_event.is_set():
                    return
                
                # Check for pause/seek events frequently to allow responsive control
                if self._pause_event.is_set() or self._seek_event.is_set():
                    return  # Exit decode loop to handle pause/seek in main thread loop
                
                try:
                    for frame in packet.decode():
                        if self._stop_event.is_set():
                            return
                        
                        # Check pause/seek inside inner loop too for responsiveness
                        if self._pause_event.is_set() or self._seek_event.is_set():
                            return
                        
                        # Skip frames if we're catching up from a seek
                        if seek_target_time is not None:
                            frame_time = float(frame.pts) * float(self._video_stream.time_base)
                            skip_threshold = seek_target_time - 0.033  # 33ms = 1 frame at 30fps
                            if frame_time < skip_threshold:
                                frames_skipped_for_seek += 1
                                if frames_skipped_for_seek <= 5:  # Log first few skips
                                    logger.info(f"[FRAME_SKIP] Skip #{frames_skipped_for_seek}: frame_time={frame_time:.3f}s < threshold={skip_threshold:.3f}s (target={seek_target_time:.3f}s)")
                                continue
                            else:
                                # Reached target time, stop skipping
                                if frames_skipped_for_seek > 0:
                                    logger.info(f"[FRAME_SKIP] Caught up: skipped {frames_skipped_for_seek} total frames, first frame at {frame_time:.3f}s (target was {seek_target_time:.3f}s)")
                                seek_target_time = None  # Clear seek target to stop skipping
                        
                        # Extract frame info and convert to numpy immediately
                        # (PyAV frames become invalid after they go out of scope)
                        try:
                            image_array = frame.to_rgb().to_ndarray()
                            frame_data = {
                                'image_array': image_array,
                                'pts': frame.pts,
                                'time': frame.time if hasattr(frame, 'time') else 0.0,
                            }
                        except Exception as e:
                            logger.warning(f"Failed to convert frame to array: {e}")
                            continue
                        
                        # Put in queue - BLOCK if full to throttle decode speed
                        # This prevents buffer overflow by letting render thread keep pace
                        try:
                            self._frame_queue.put(frame_data, block=True, timeout=0.1)
                            self._frame_count += 1
                            frames_decoded += 1
                            if frames_decoded == 1:
                                logger.info(f"First frame enqueued: pts={frame.pts}, time={frame.time if hasattr(frame, 'time') else 'N/A'}")
                        except queue.Full:
                            # Queue still full after timeout - skip this frame to keep decoding
                            self._dropped_frames += 1
                            if self._dropped_frames % 10 == 0:
                                logger.debug(f"Frame queue full, dropped {self._dropped_frames} frames total")
                        
                        # Start render thread if not running
                        if self._render_thread is None or not self._render_thread.is_alive():
                            self._render_thread = threading.Thread(target=self._render_thread_main, daemon=True)
                            self._render_thread.start()
                        
                        # Yield control every few frames to prevent thread starvation
                        if frames_decoded >= max_frames_per_batch:
                            time.sleep(0.001)  # Tiny sleep to yield to other threads
                            frames_decoded = 0
                
                except (ValueError, RuntimeError) as e:
                    logger.warning(f"Error decoding packet: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error during frame decoding: {e}")
            self._is_playing = False
    
    def _render_thread_main(self) -> None:
        """Main rendering thread - decode, convert, and resize frames for display.
        
        A/V Synchronization Strategy:
        - Audio is the master clock
        - For each video frame, compare its PTS to audio time
        - If video is ahead of audio: wait until it's time to display
        - If video is behind audio: drop the frame to catch up
        - This keeps video in sync with audio playback
        """
        try:
            from PIL import Image, ImageTk

            logger.info("Render thread started")
            frames_skipped_total = 0
            frames_rendered = 0
            canvas_ready_warned = False
            # Maximum allowed drift before we drop frames (100ms - audio can be max 100ms ahead)
            max_drift_behind = 0.1
            # How far ahead we allow video to be before waiting (30ms - video can be max 30ms ahead)
            max_drift_ahead = 0.03
            
            while not self._stop_event.is_set():
                try:
                    # Wait while paused - don't consume frames from queue
                    # This prevents the decode thread from advancing while we're paused
                    if self._pause_event.is_set():
                        time.sleep(0.05)
                        continue
                    
                    # Check for seek event - if seek is pending, skip processing and let decode handle it
                    # The decode thread will clear the frame queue after seek
                    if self._seek_event.is_set():
                        time.sleep(0.01)  # Brief sleep to let decode thread handle seek
                        continue
                    
                    # Get frame from queue with SHORT timeout to allow other work
                    logger.debug(f"[RENDER_LOOP] Attempting to get frame from queue (frames_rendered={frames_rendered})")
                    frame_data = self._frame_queue.get(timeout=0.05)
                    logger.debug(f"[RENDER_LOOP] Got frame from queue")
                    
                    # After getting frame, check again if a seek happened
                    # (seek can occur between queue.get and now)
                    if self._seek_event.is_set():
                        logger.debug("Discarding frame - seek event pending")
                        continue
                    
                    if frames_rendered == 0:
                        logger.info("Render thread received first frame from queue")
                    
                    if frame_data is None:
                        logger.debug("Frame data is None, skipping")
                        continue
                    
                    image_array = frame_data.get('image_array')
                    logger.debug(f"Frame #{frames_rendered + 1}: image_array type={type(image_array)}, size={image_array.shape if image_array is not None else 'None'}")
                    
                    # Calculate frame time from PTS
                    pts = frame_data.get('pts')
                    frame_time = 0.0
                    if pts is not None and self._video_stream is not None:
                        frame_time = float(pts) * float(self._video_stream.time_base)
                    
                    # Update current time
                    with self._frame_lock:
                        self._current_time = frame_time
                    
                    # A/V SYNC: Compare frame time to audio time
                    audio_player = self._audio_player
                    if audio_player is not None and audio_player.is_playing():
                        audio_time = audio_player.get_current_time()
                        # Apply presentation latency offsets: audio has ~50ms latency, video has ~100ms latency
                        # So we adjust: effective_audio = audio_time - 50ms, effective_video = frame_time - 100ms
                        # drift = effective_audio - effective_video = (audio - 50ms) - (frame - 100ms) = audio - frame + 50ms
                        adjusted_drift = audio_time - frame_time + self._av_latency_offset
                        drift_ms = adjusted_drift * 1000
                        
                        # Track drift statistics
                        self._drift_samples.append(drift_ms)
                        if len(self._drift_samples) > self._max_drift_buffer_size:
                            self._drift_samples.pop(0)
                        
                        # Log drift info frequently to understand sync issues
                        if frames_rendered < 10 or frames_rendered % 24 == 0 or abs(drift_ms) > 100:
                            avg_drift = np.mean(self._drift_samples) if self._drift_samples else 0
                            logger.info(f"A/V DRIFT: frame#{frames_rendered+1} video={frame_time:.3f}s audio={audio_time:.3f}s drift={drift_ms:+.1f}ms (avg={avg_drift:+.1f}ms)")
                        
                        if adjusted_drift > max_drift_behind:
                            # Audio is too far ahead - drop this frame to catch up
                            frames_skipped_total += 1
                            if frames_skipped_total % 10 == 0:
                                logger.info(f"A/V sync: dropped {frames_skipped_total} frames (audio ahead by {drift_ms:.0f}ms, adjusted={adjusted_drift*1000:.0f}ms)")
                            continue
                        elif adjusted_drift < -max_drift_ahead:
                            # Video is ahead of audio - wait for audio to catch up
                            # BUT cap wait time and check for seek/pause/stop events
                            # If drift is huge (<-1s), it means a seek happened and this frame is stale
                            wait_time = -adjusted_drift - max_drift_ahead
                            if wait_time > 1.0:
                                # Drift too large - likely a seek happened, discard this frame
                                logger.info(f"A/V sync: discarding stale frame (drift={drift_ms:.0f}ms, likely seek)")
                                continue
                            if wait_time > 0.001:  # Only sleep if > 1ms
                                logger.debug(f"A/V sync: waiting {wait_time*1000:.0f}ms (video ahead)")
                                # Break sleep into small chunks to check for events
                                sleep_chunk = 0.02  # 20ms chunks
                                slept = 0.0
                                while slept < wait_time:
                                    if self._stop_event.is_set() or self._seek_event.is_set() or self._pause_event.is_set():
                                        logger.debug("A/V sync wait interrupted by event")
                                        break
                                    chunk = min(sleep_chunk, wait_time - slept)
                                    time.sleep(chunk)
                                    slept += chunk
                    
                    logger.debug(f"Frame #{frames_rendered + 1}: frame_time={frame_time:.3f}s")
                    
                    # Call time callback OUTSIDE the lock to prevent deadlocks
                    # The callback might try to acquire locks or interact with UI
                    
                    # Convert frame to RGB and prepare for display
                    canvas_status = "None" if self._canvas is None else "NOT None"
                    logger.debug(f"Frame #{frames_rendered + 1}: self._canvas is {canvas_status}")
                    if self._canvas is not None:
                        try:
                            logger.debug(f"Frame #{frames_rendered + 1}: Starting render pipeline")
                            # Use cached canvas dimensions (updated by main thread)
                            # NEVER call winfo_width/height from render thread - it can hang!
                            canvas_width = self._cached_canvas_width
                            canvas_height = self._cached_canvas_height
                            
                            logger.debug(f"Frame #{frames_rendered + 1}: Canvas size={canvas_width}x{canvas_height} (cached)")
                            
                            if canvas_width < 1 or canvas_height < 1:
                                if not canvas_ready_warned:
                                    logger.warning(f"Canvas not ready: {canvas_width}x{canvas_height}, dropping frames until canvas is realized")
                                    canvas_ready_warned = True
                                logger.debug(f"Frame #{frames_rendered + 1}: Canvas not ready {canvas_width}x{canvas_height}, dropping frame")
                                # Drop this frame - canvas will be ready eventually
                                continue
                            
                            canvas_ready_warned = False  # Reset warning flag once canvas is ready
                            
                            # Image array already converted to RGB in decode thread
                            if image_array is None:
                                logger.warning(f"Frame #{frames_rendered + 1}: No image array in frame data, skipping")
                                continue
                            
                            # Convert to PIL and resize (this is the slow part, OK on render thread)
                            logger.debug(f"Frame #{frames_rendered + 1}: Converting to PIL Image")
                            pil_image = Image.fromarray(image_array, mode='RGB')
                            logger.debug(f"Frame #{frames_rendered + 1}: PIL Image created")
                            
                            # Calculate aspect-preserving resize
                            frame_height, frame_width = image_array.shape[0], image_array.shape[1]
                            aspect_ratio = frame_width / frame_height
                            
                            if (canvas_width / canvas_height) > aspect_ratio:
                                new_height = canvas_height
                                new_width = int(new_height * aspect_ratio)
                            else:
                                new_width = canvas_width
                                new_height = int(new_width / aspect_ratio)
                            
                            if new_width > 0 and new_height > 0:
                                if frames_rendered == 0:
                                    logger.debug(f"Resizing frame to {new_width}x{new_height}")
                                resize_start = time.time()
                                pil_image = pil_image.resize((new_width, new_height), Image.Resampling.BILINEAR)
                                resize_duration = time.time() - resize_start
                                if frames_rendered < 5 or resize_duration > 0.05:  # Log first 5 frames or slow resizes
                                    logger.info(f"Frame #{frames_rendered + 1}: BILINEAR resize took {resize_duration*1000:.1f}ms")
                            
                            # Queue PIL Image for main thread (main thread will create PhotoImage)
                            # A/V sync timing is handled above - no wall-clock throttling needed here
                            try:
                                if frames_rendered == 0:
                                    logger.debug("Queueing first PIL Image for main thread PhotoImage conversion")
                                self._canvas_update_queue.put({
                                    'pil_image': pil_image,
                                    'canvas_width': canvas_width,
                                    'canvas_height': canvas_height
                                }, block=False)
                                
                                frames_rendered += 1
                                if frames_rendered <= 5 or frames_rendered % 30 == 0:
                                    logger.info(f"*** FRAME RENDERED: frames_rendered now = {frames_rendered}")
                                
                                if frames_rendered == 1:
                                    logger.info("First frame queued for canvas update")
                                
                                # NOTE: We do NOT call canvas.after() from the render thread
                                # because Tkinter's after() is not thread-safe!
                                # Instead, the main thread's _start_update_timer will periodically
                                # call _update_canvas_on_main_thread to check the queue.
                            
                            except queue.Full:
                                logger.info(f"Frame #{frames_rendered + 1}: Canvas update queue FULL - frame dropped (UI thread too slow)")
                        
                        except Exception as e:
                            logger.error(f"Error preparing frame for rendering: {e}", exc_info=True)
                
                except queue.Empty:
                    logger.debug(f"[RENDER_LOOP] Queue empty (frames_rendered={frames_rendered})")
                    continue
                except Exception as e:
                    logger.error(f"[RENDER_LOOP] Error in render thread: {e}", exc_info=True)
        
        except ImportError:
            logger.error("PIL/Pillow not available for rendering")
        except Exception as e:
            logger.error(f"Render thread error: {e}")
    
    def _update_canvas_on_main_thread(self) -> None:
        """Update canvas with queued PIL Image (runs on main thread periodically).
        
        The render thread prepares PIL Images, this method converts to PhotoImage and displays.
        PhotoImage creation must happen on main thread since it's not thread-safe.
        
        Called periodically from the main thread's update timer (every 50ms).
        """
        logger.log(5, "_update_canvas_on_main_thread() called on main thread")
        
        if self._canvas is None:
            logger.warning("Canvas is None in _update_canvas_on_main_thread")
            return
        
        # Update cached canvas dimensions (safe to call from main thread)
        # The render thread reads these cached values instead of calling winfo directly
        try:
            self._cached_canvas_width = self._canvas.winfo_width()
            self._cached_canvas_height = self._canvas.winfo_height()
        except Exception:
            pass  # Canvas might not be ready
        
        try:
            from PIL import ImageTk
            
            # Get queued image data (non-blocking)
            try:
                logger.log(5, "Attempting to get frame from canvas update queue")
                frame_data = self._canvas_update_queue.get_nowait()
                logger.info("*** CANVAS UPDATE: Received queued frame (queue size now: %d) ***", self._canvas_update_queue.qsize())
            except queue.Empty:
                logger.log(5, "Canvas update queue is empty")
                return  # No work to do
            
            pil_image = frame_data.get('pil_image')
            canvas_width = frame_data['canvas_width']
            canvas_height = frame_data['canvas_height']
            
            logger.info("Received frame from queue: %dx%d", canvas_width, canvas_height)
            
            if canvas_width < 1 or canvas_height < 1:
                logger.warning("Invalid canvas dimensions: %dx%d", canvas_width, canvas_height)
                return
            
            if pil_image is None:
                logger.warning("PIL image is None")
                return
            
            # Convert PIL Image to PhotoImage on main thread (thread-safe)
            logger.debug("Converting PIL Image to PhotoImage on main thread")
            photo_image = ImageTk.PhotoImage(pil_image)
            logger.debug("PhotoImage created successfully")
            
            # Store reference to prevent garbage collection
            self._canvas_photo_image = photo_image
            
            # Update canvas (very fast, just swapping image reference)
            logger.debug("Deleting old canvas content")
            self._canvas.delete("all")
            logger.debug("Creating new image on canvas")
            self._canvas.create_image(
                canvas_width // 2,
                canvas_height // 2,
                image=self._canvas_photo_image
            )
            logger.info("*** CANVAS UPDATED SUCCESSFULLY ***")
        
        except Exception as e:
            logger.error(f"Error updating canvas: {e}", exc_info=True)
    

    def _initialize_audio_player(self) -> None:
        """Initialize audio player and load audio stream (runs on background thread)."""
        if self._audio_stream is None or self._audio_player is not None:
            return
        
        overall_start = time.time()
        logger.info("Initializing audio player (background thread)")
        self._audio_player = SimpleAudioPlayer()
        
        # Decode all audio frames
        audio_frames_list = []
        sample_rate = self._audio_stream.sample_rate
        channels = self._audio_stream.channels
        
        logger.info(f"Extracting audio: {sample_rate}Hz, {channels} channels")
        
        extraction_start = time.time()
        try:
            frame_count = 0
            for frame in self._container.decode(self._audio_stream):
                try:
                    # Convert to numpy array
                    # PyAV returns shape (samples, channels) for multichannel or (samples,) for mono
                    array = frame.to_ndarray()
                    
                    frame_count += 1
                    # Only log at TRACE level to avoid spam (was every 50 frames at DEBUG)
                    if frame_count % 100 == 0:
                        logger.log(5, f"[PROFILE] Audio frame #{frame_count}: shape={array.shape}, dtype={array.dtype}")
                    
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
        
        extraction_time = time.time() - extraction_start
        logger.debug(f"[PROFILE] Audio extraction: {frame_count} frames decoded in {extraction_time:.2f}s")
        
        if not audio_frames_list:
            logger.warning("No audio frames decoded")
            self._audio_player = None
            return
        
        try:
            # PyAV returns frames with shape (channels, frame_size)
            # We need to concatenate along axis 1 (the frame_size axis) to get (channels, total_samples)
            concat_start = time.time()
            logger.debug("[PROFILE] Audio: concatenating frames...")
            if len(audio_frames_list) > 0 and audio_frames_list[0].ndim == 2:
                # Multichannel: concatenate along the samples axis (axis 1)
                audio_data = np.concatenate(audio_frames_list, axis=1)
                # Transpose to (total_samples, channels) for simpleaudio
                audio_data = audio_data.T
            else:
                # Mono: concatenate along axis 0
                audio_data = np.concatenate(audio_frames_list, axis=0)
            
            concat_time = time.time() - concat_start
            logger.debug(f"[PROFILE] Audio: frames concatenated in {concat_time:.2f}s, shape={audio_data.shape}, dtype={audio_data.dtype}")
            
            # Load into audio player
            load_start = time.time()
            logger.debug("[PROFILE] Audio: loading into player...")
            self._audio_player.load_audio_data(audio_data, sample_rate, channels)
            load_time = time.time() - load_start
            logger.debug(f"[PROFILE] Audio: loaded into player in {load_time:.2f}s")
            
            overall_time = time.time() - overall_start
            logger.debug(f"[PROFILE] Audio player initialization complete in {overall_time:.2f}s")
        
        except Exception as e:
            logger.error(f"Error loading audio data: {e}")
            self._audio_player = None
