"""Integration tests for real video file playback with PyAV."""

import logging
from pathlib import Path

import pytest

logger = logging.getLogger(__name__)


class TestRealVideoPlayback:
    """Test PyAV video and audio decoding with real files."""

    def test_video_file_container_opening(self, sample_video_path):
        """Test opening a video container with PyAV."""
        import av
        
        container = av.open(sample_video_path)
        assert container is not None
        container.close()

    def test_video_stream_detection(self, sample_video_path):
        """Test detecting video stream in a file."""
        import av

        container = av.open(sample_video_path)

        video_stream = None
        for stream in container.streams:
            if stream.type == "video":
                video_stream = stream
                break

        assert video_stream is not None, "No video stream found"
        assert video_stream.codec_context.name is not None
        assert video_stream.width > 0
        assert video_stream.height > 0
        assert video_stream.average_rate is not None

        container.close()

    def test_audio_stream_detection(self, sample_video_path):
        """Test detecting audio stream in a file."""
        import av

        container = av.open(sample_video_path)

        audio_stream = None
        for stream in container.streams:
            if stream.type == "audio":
                audio_stream = stream
                break

        # Audio stream may or may not exist, just ensure we can check
        if audio_stream:
            assert audio_stream.codec_context.name is not None
            assert audio_stream.sample_rate > 0
            assert audio_stream.channels > 0

        container.close()

    def test_video_duration(self, sample_video_path):
        """Test reading video duration."""
        import av

        container = av.open(sample_video_path)

        # Duration may be available or not, but shouldn't raise
        if container.duration:
            duration = float(container.duration) * av.time_base
            assert duration > 0

        container.close()

    def test_decode_video_frames(self, sample_video_path):
        """Test decoding video frames from a file."""
        import av

        container = av.open(sample_video_path)

        video_stream = None
        for stream in container.streams:
            if stream.type == "video":
                video_stream = stream
                break

        if video_stream is None:
            pytest.skip("No video stream in sample video")

        frame_count = 0
        max_frames = 5

        for packet in container.demux(video_stream):
            for frame in packet.decode():
                frame_count += 1
                if frame_count == 1:
                    # Validate first frame
                    assert frame.width > 0
                    assert frame.height > 0
                if frame_count >= max_frames:
                    break
            if frame_count >= max_frames:
                break

        assert frame_count > 0, "Failed to decode any video frames"
        container.close()

    def test_decode_audio_frames(self, sample_video_path):
        """Test decoding audio frames from a file."""
        import av

        container = av.open(sample_video_path)

        audio_stream = None
        for stream in container.streams:
            if stream.type == "audio":
                audio_stream = stream
                break

        if audio_stream is None:
            pytest.skip("No audio stream in sample video")

        audio_frame_count = 0
        max_frames = 5

        container.seek(0)  # Reset to beginning
        for packet in container.demux(audio_stream):
            for frame in packet.decode():
                audio_frame_count += 1
                if audio_frame_count >= max_frames:
                    break
            if audio_frame_count >= max_frames:
                break

        assert audio_frame_count > 0, "Failed to decode any audio frames"
        container.close()

    def test_full_playback_workflow(self, sample_video_path):
        """Integration test: open, detect streams, decode frames."""
        import av

        # Open
        container = av.open(sample_video_path)
        assert container is not None

        # Detect streams
        streams = {"video": None, "audio": None}
        for stream in container.streams:
            if stream.type in streams and streams[stream.type] is None:
                streams[stream.type] = stream

        # Decode at least one frame from each available stream
        if streams["video"]:
            frame_count = 0
            for packet in container.demux(streams["video"]):
                for frame in packet.decode():
                    frame_count += 1
                    break
                if frame_count > 0:
                    break
            assert frame_count > 0

        if streams["audio"]:
            container.seek(0)
            audio_frame_count = 0
            for packet in container.demux(streams["audio"]):
                for frame in packet.decode():
                    audio_frame_count += 1
                    break
                if audio_frame_count > 0:
                    break
            assert audio_frame_count > 0

        container.close()
