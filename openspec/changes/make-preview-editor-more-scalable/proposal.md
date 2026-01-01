# Change: Make Preview Editor More Scalable

## Why

The preview editor UI currently hangs during initial load with large videos (1.5 hours, ~206 segments) while working fine with small videos (5 minutes, ~15 segments). The logs show audio loads successfully but the UI becomes unresponsive, suggesting the UI rendering or segment list initialization is blocking the main thread. This prevents users from using the editor on longer videos, severely limiting usability.

## What Changes

- **Identify bottlenecks** through profiling and detailed logging to pinpoint which operations cause UI blocking (segment list rendering, video initialization, data loading, etc.)
- **Implement virtualization** in the segment list to render only visible items, reducing DOM/widget creation from 206 items to ~15 visible at once
- **Optimize data loading** by deferring non-critical operations (e.g., frame caching, full audio extraction) and loading audio only on demand
- **Move blocking operations to background threads** to keep the main UI thread responsive during initialization
- **Add performance metrics and profiling** to catch future regressions and guide optimization decisions
- **Create integration tests** with large datasets (200+ segments) to validate scaling improvements and prevent regression

## Impact

- **Affected specs**: `desktop-ui`, `video-playback`, `integration-testing`
- **Affected code**: `video_censor_personal/ui/` (segment list, video player, main window), `tests/` (add integration tests for large videos)
- **Non-breaking**: All changes are internal optimizations; user-facing behavior remains identical
