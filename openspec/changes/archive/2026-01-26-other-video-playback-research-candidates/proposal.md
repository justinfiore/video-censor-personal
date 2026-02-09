# Change: Research and Document Alternative Video Playback Solutions

## Why

As part of the cross-platform video playback initiative, we evaluated multiple video player solutions against strict criteria (cross-platform support, audio+video sync, seeking, CustomTkinter integration). This document captures the research findings, candidate evaluations, and rationale for why alternatives were rejected in favor of PyAV.

This serves as a reference for future decisions: if PyAV proves unsuitable, these alternatives provide fallback options with documented trade-offs.

## What Changes

- **Document candidate evaluation matrix**: pygame, OpenCV, moviepy, VLC, Kivy with pros, cons, license
- **Capture decision rationale**: why PyAV was selected and alternatives rejected
- **Record trade-offs and risks**: document reasons other solutions didn't fit project constraints
- **Preserve research for future reference**: if PyAV fails, alternatives are well-documented for reconsideration

## Impact

- **Affected specs**: None (research documentation only, does not affect production code)
- **Affected code**: None
- **Breaking changes**: None
- **New dependencies**: None
- **Removed dependencies**: None

## Status

This is a research archive. It does not block the PyAV implementation (fix-video-playback-macos change). It serves as supporting documentation and reference material.

**Note**: This change is documentation-only and does not introduce spec deltas. It captures research findings for reference if alternatives need reconsideration in the future.
