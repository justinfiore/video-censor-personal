"""VLC player using subprocess with HTTP interface communication."""

import subprocess
import logging
import traceback
import time
import os
import requests
import json
from typing import Callable, Optional
from threading import Thread, Event
from video_censor_personal.ui.video_player import VideoPlayer

logger = logging.getLogger("video_censor_personal.ui")


class SubprocessVLCPlayer(VideoPlayer):
    """VLC-based video player using subprocess with HTTP interface.
    
    Launches VLC as a separate process to avoid tkinter/OpenGL rendering conflicts on macOS.
    Communicates with VLC via HTTP socket interface for control and status.
    """
    
    def __init__(self, http_port: int = 8080):
        """Initialize subprocess VLC player.
        
        Args:
            http_port: Port for VLC HTTP interface (default 8080)
            
        Raises:
            RuntimeError: If VLC is not available in PATH
        """
        self.http_port = http_port
        self.process: Optional[subprocess.Popen] = None
        self.http_base_url = f"http://127.0.0.1:{http_port}"
        self._time_callback: Optional[Callable[[float], None]] = None
        self._last_time = 0.0
        self._is_playing = False
        self._duration = 0.0
        self._current_time = 0.0
        self._playback_rate = 1.0
        self._stop_monitor = Event()
        self._monitor_thread: Optional[Thread] = None
        
        # Check if VLC is available
        if not self._check_vlc_available():
            raise RuntimeError("VLC not found in PATH. Install VLC or add to PATH.")
    
    @staticmethod
    def _check_vlc_available() -> bool:
        """Check if VLC is available in PATH."""
        try:
            result = subprocess.run(
                ["vlc", "--version"],
                capture_output=True,
                timeout=5,
                text=True
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def load(self, video_path: str) -> None:
        """Load a video file for playback."""
        try:
            logger.info(f"Loading video: {video_path}")
            
            # Stop any existing VLC process
            self._stop_vlc_process()
            
            # Start VLC with HTTP interface
            self._start_vlc_process(video_path)
            
            # Wait for VLC to start and parse media
            time.sleep(2)
            
            # Start status monitoring thread
            if self._monitor_thread is None or not self._monitor_thread.is_alive():
                self._stop_monitor.clear()
                self._monitor_thread = Thread(target=self._monitor_vlc_status, daemon=True)
                self._monitor_thread.start()
            
            logger.info("Video loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load video: {str(e)}")
            logger.error(traceback.format_exc())
            raise
    
    def _start_vlc_process(self, video_path: str) -> None:
        """Start VLC subprocess with HTTP interface."""
        try:
            # Resolve absolute path
            abs_path = os.path.abspath(video_path)
            if not os.path.exists(abs_path):
                raise FileNotFoundError(f"Video file not found: {abs_path}")
            
            # Build VLC command
            # --http-host 127.0.0.1: Bind only to localhost for security
            # --http-port: Enable HTTP interface on specific port
            # --no-osd: Disable on-screen display
            # --fullscreen: Start in fullscreen (user can exit with escape)
            cmd = [
                "vlc",
                "--http-host", "127.0.0.1",
                f"--http-port={self.http_port}",
                "--no-osd",
                "--fullscreen",
                "--play-and-exit",
                abs_path
            ]
            
            logger.info(f"Starting VLC process: {' '.join(cmd)}")
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            logger.info(f"VLC process started with PID {self.process.pid}")
            
        except Exception as e:
            logger.error(f"Failed to start VLC process: {str(e)}")
            logger.error(traceback.format_exc())
            raise
    
    def _stop_vlc_process(self) -> None:
        """Stop the VLC subprocess."""
        if self.process:
            try:
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    logger.warning("VLC process did not terminate, killing it")
                    self.process.kill()
                    self.process.wait()
                logger.info("VLC process stopped")
            except Exception as e:
                logger.error(f"Error stopping VLC process: {str(e)}")
            finally:
                self.process = None
    
    def _http_get(self, endpoint: str, params: Optional[dict] = None) -> dict:
        """Make HTTP GET request to VLC interface.
        
        Args:
            endpoint: API endpoint (e.g., '/requests/status.json')
            params: Optional query parameters
            
        Returns:
            Response JSON as dictionary
        """
        try:
            url = f"{self.http_base_url}{endpoint}"
            response = requests.get(url, params=params, timeout=2)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.debug(f"HTTP request failed: {str(e)}")
            return {}
        except json.JSONDecodeError:
            logger.debug("Failed to parse VLC HTTP response")
            return {}
    
    def _get_status(self) -> dict:
        """Get current VLC status."""
        return self._http_get("/requests/status.json")
    
    def play(self) -> None:
        """Start or resume playback."""
        try:
            logger.info("Sending play command to VLC")
            self._http_get("/requests/status.json", {"command": "pl_play"})
            self._is_playing = True
        except Exception as e:
            logger.error(f"Failed to play: {str(e)}")
            logger.error(traceback.format_exc())
            raise
    
    def pause(self) -> None:
        """Pause playback."""
        try:
            logger.info("Sending pause command to VLC")
            self._http_get("/requests/status.json", {"command": "pl_pause"})
            self._is_playing = False
        except Exception as e:
            logger.error(f"Failed to pause: {str(e)}")
            logger.error(traceback.format_exc())
            raise
    
    def seek(self, seconds: float) -> None:
        """Seek to a specific time position in seconds."""
        try:
            position_ms = int(seconds * 1000)
            logger.debug(f"Seeking to {seconds}s ({position_ms}ms)")
            self._http_get("/requests/status.json", {"command": "seek", "val": position_ms})
        except Exception as e:
            logger.error(f"Failed to seek: {str(e)}")
            logger.error(traceback.format_exc())
    
    def set_volume(self, level: float) -> None:
        """Set volume level (0.0 to 1.0)."""
        try:
            volume = int(level * 100)
            volume = max(0, min(100, volume))
            logger.debug(f"Setting volume to {volume}%")
            self._http_get("/requests/status.json", {"command": "volume", "val": volume})
        except Exception as e:
            logger.error(f"Failed to set volume: {str(e)}")
            logger.error(traceback.format_exc())
    
    def get_current_time(self) -> float:
        """Get current playback position in seconds."""
        try:
            status = self._get_status()
            if status and "time" in status:
                return float(status["time"])
            return self._current_time
        except Exception as e:
            logger.debug(f"Error getting current time: {str(e)}")
            return self._current_time
    
    def on_time_changed(self, callback: Callable[[float], None]) -> None:
        """Register a callback for time change events."""
        self._time_callback = callback
    
    def _monitor_vlc_status(self) -> None:
        """Periodically poll VLC status and trigger callbacks."""
        while not self._stop_monitor.is_set():
            try:
                status = self._get_status()
                
                if not status:
                    time.sleep(0.1)
                    continue
                
                # Update internal state
                if "time" in status:
                    self._current_time = float(status["time"])
                
                if "length" in status:
                    self._duration = float(status["length"])
                
                if "state" in status:
                    self._is_playing = status["state"] == "playing"
                
                # Trigger callback if time changed significantly
                if self._time_callback and self._is_playing:
                    if abs(self._current_time - self._last_time) > 0.05:
                        self._last_time = self._current_time
                        self._time_callback(self._current_time)
                
                time.sleep(0.1)
            except Exception as e:
                logger.debug(f"Error monitoring VLC status: {str(e)}")
                time.sleep(0.5)
    
    def set_playback_rate(self, rate: float) -> None:
        """Set playback speed (1.0 = normal, 0.5 = half speed, 2.0 = double speed)."""
        try:
            logger.debug(f"Setting playback rate to {rate}x")
            self._playback_rate = rate
            self._http_get("/requests/status.json", {"command": "rate", "val": rate})
        except Exception as e:
            logger.error(f"Failed to set playback rate: {str(e)}")
            logger.error(traceback.format_exc())
    
    def cleanup(self) -> None:
        """Clean up resources and stop playback."""
        try:
            logger.info("Cleaning up SubprocessVLCPlayer")
            
            # Stop monitoring thread
            self._stop_monitor.set()
            if self._monitor_thread and self._monitor_thread.is_alive():
                self._monitor_thread.join(timeout=2)
            
            # Stop VLC process
            self._stop_vlc_process()
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
    
    def is_playing(self) -> bool:
        """Check if video is currently playing."""
        try:
            status = self._get_status()
            if status and "state" in status:
                self._is_playing = status["state"] == "playing"
            return self._is_playing
        except Exception as e:
            logger.debug(f"Error checking if playing: {str(e)}")
            return self._is_playing
    
    def get_duration(self) -> float:
        """Get total duration of loaded video in seconds."""
        try:
            status = self._get_status()
            if status and "length" in status:
                self._duration = float(status["length"])
            return self._duration
        except Exception as e:
            logger.debug(f"Error getting duration: {str(e)}")
            return self._duration
