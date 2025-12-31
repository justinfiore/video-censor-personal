# Change: A/V Sync Offset Tuning System

## Why

Audio and video playback have different presentation latencies due to buffering differences in their respective pipelines (audio ~50-75ms, video ~100-130ms). This causes perceived desynchronization even when timestamps are correct. Users need a way to tune this offset without restarting the application.

## What Changes

- Add `av_sync_offset_ms` parameter to PyAVVideoPlayer initialization
- Implement `set_av_sync_offset()` method for runtime tuning
- Add UI controls (input field + Apply button) to adjust offset interactively
- Apply offset in render thread's drift calculation: `adjusted_drift = audio_time - frame_time + av_latency_offset`
- Set default offset to 1500ms (positive = delay video relative to audio)
- Document tuning process with examples and troubleshooting guide

## Impact

- Affected specs: `video-playback` (new spec for playback synchronization)
- Affected code:
  - `video_censor_personal/ui/pyav_video_player.py` - Added offset parameter, apply in render thread
  - `video_censor_personal/ui/video_player_pane.py` - Added UI controls for offset tuning
  - Created documentation: `AV_SYNC_TUNING_QUICK.md`, `AV_SYNC_TUNING.md`, etc.
