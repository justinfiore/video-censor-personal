# Design: Add Segment Reviewed State

## Context
The preview editor UI needs to track which segments a user has reviewed. This enables:
- Resuming review sessions by filtering to unreviewed segments
- Confidence that all segments have been evaluated before processing

Currently, JSON writes happen synchronously on each `allow` change. With the new `reviewed` property being set automatically (on click and playback), write frequency would increase significantly, making async batching necessary.

## Goals
- Track review state per segment with minimal user friction
- Batch JSON writes to avoid I/O bottlenecks
- Provide clear visual feedback on save status
- Maintain backwards compatibility with existing JSON files

## Non-Goals
- Multi-user collaboration or conflict resolution
- Undo/redo for review state changes
- Review state history or audit trail

## Decisions

### 1. Auto-Review Trigger: 1-Second Click Threshold
**Decision**: Mark segment as reviewed after 1 second of being selected.

**Rationale**: This strikes a balance between:
- Too short (accidental clicks marking as reviewed)
- Too long (user must wait before moving on)

One second is enough time to glance at the segment details.

### 2. Async Write Queue with 5-Second Debounce
**Decision**: Buffer all segment changes in memory and write to disk at most once every 5 seconds.

**Rationale**: 
- Prevents disk thrashing during rapid review sessions
- 5 seconds is short enough that data loss window is acceptable
- Single write includes all pending changes (reviewed, allow, etc.)

**Implementation**:
```python
class AsyncWriteQueue:
    def __init__(self, write_fn: Callable, debounce_seconds: float = 5.0):
        self._dirty = False
        self._timer: Optional[Timer] = None
        self._write_fn = write_fn
        self._debounce = debounce_seconds
        self._lock = threading.Lock()
        self._on_status_change: Optional[Callable[[bool], None]] = None
    
    def mark_dirty(self):
        with self._lock:
            was_dirty = self._dirty
            self._dirty = True
            if not was_dirty and self._on_status_change:
                self._on_status_change(True)  # dirty
            self._schedule_write()
    
    def _schedule_write(self):
        if self._timer:
            self._timer.cancel()
        self._timer = Timer(self._debounce, self._flush)
        self._timer.start()
    
    def _flush(self):
        with self._lock:
            if self._dirty:
                self._write_fn()
                self._dirty = False
                if self._on_status_change:
                    self._on_status_change(False)  # clean
```

### 3. Sync Status Indicator Position
**Decision**: Bottom-right gutter, opposite the JSON/Video file labels.

**Rationale**: Follows the existing UI pattern of status information at the bottom.

### 4. Filter Ordering
**Decision**: Add "Review Status" filter as a third dropdown, after Label and Allow filters.

**Rationale**: Review status is a workflow concern (what have I looked at?) rather than content concern (what does it contain?), so it comes last.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Data loss if app crashes with pending changes | 5-second max delay acceptable; flush-on-exit ensures clean shutdown |
| Timer threads complicate shutdown | Cancel timer and synchronous flush on app close |
| Auto-review triggers unexpectedly | 1-second threshold should prevent accidental marks |

### 5. Flush on Exit
**Decision**: Always attempt a synchronous flush when the application exits.

**Rationale**: Prevents data loss when user closes the app with pending changes.

**Implementation**:
- Hook into application close event (window close, Ctrl+C, etc.)
- Cancel any pending debounce timer
- Perform synchronous write if dirty flag is set
- Block exit until write completes or times out (10 second max)

```python
def flush_sync(self, timeout: float = 10.0) -> bool:
    """Synchronously flush pending changes. Returns True if successful."""
    with self._lock:
        if self._timer:
            self._timer.cancel()
            self._timer = None
        if self._dirty:
            try:
                self._write_fn()
                self._dirty = False
                return True
            except Exception:
                return False
        return True  # Nothing to flush
```

## Migration Plan
1. Add `reviewed` field with default `False` - backwards compatible
2. Existing JSON files without `reviewed` will load correctly (defaulting to `False`)
3. No migration script needed

### 6. Bulk Mark Reviewed/Unreviewed Buttons
**Decision**: Place buttons in the filter frame, operating on currently filtered segments.

**Rationale**: 
- Filter frame is where review workflow controls live
- Operating on filtered set allows selective bulk operations (e.g., mark all Profanity segments as reviewed)
- Matches pattern of existing batch operations in segment-review spec

**Behavior**:
- "Mark All Reviewed" sets `reviewed: true` on all segments matching current filters
- "Mark All Unreviewed" sets `reviewed: false` on all segments matching current filters
- Single async write queued after bulk update

## Open Questions
None.
