# Tasks: Add Segment Reviewed State

## 1. Data Model & Persistence Layer
- [x] 1.1 Add `reviewed: bool = False` field to `Segment` dataclass
- [x] 1.2 Update `Segment.from_dict()` to parse `reviewed` (default `False` if absent)
- [x] 1.3 Update `Segment.to_dict()` to include `reviewed` in output
- [x] 1.4 Create `AsyncWriteQueue` class with:
  - Dirty flag tracking
  - 5-second debounce timer
  - Thread-safe write queue
  - Callback for sync status changes
- [x] 1.5 Integrate `AsyncWriteQueue` into `SegmentManager`
- [x] 1.6 Migrate `set_allow()` to use async queue instead of synchronous writes
- [x] 1.7 Add `flush_sync()` method for synchronous flush on exit

## 2. UI - Reviewed Checkbox
- [x] 2.1 Add "Reviewed" checkbox to `SegmentDetailsPaneImpl` next to "Allowed" checkbox
- [x] 2.2 Wire checkbox to update segment's `reviewed` property via `SegmentManager`
- [x] 2.3 Update checkbox state when segment selection changes

## 3. Auto-Review Detection
- [x] 3.1 Track segment selection time in `PreviewEditor` (record when segment becomes selected)
- [x] 3.2 On segment deselection or new selection, check if >1 second elapsed → mark as reviewed
- [x] 3.3 Track video playback position relative to current segment
- [x] 3.4 When playback covers entire segment timespan, mark as reviewed

## 4. Sync Status Indicator & Exit Handling
- [x] 4.1 Add status indicator widget to bottom-right of UI (opposite JSON/Video labels)
- [x] 4.2 Display orange circle + "Pending Changes" when dirty
- [x] 4.3 Display green circle + "Synchronized" when clean
- [x] 4.4 Subscribe to `AsyncWriteQueue` status callbacks
- [x] 4.5 Hook application close event to call `flush_sync()` before exit
- [x] 4.6 Handle Ctrl+C / SIGINT to flush before termination

## 5. Review Status Filter & Bulk Actions
- [x] 5.1 Add "All Review Status" / "Reviewed" / "Unreviewed" dropdown to filter frame
- [x] 5.2 Update `_apply_filters()` to filter by `reviewed` property
- [x] 5.3 Ensure filter resets pagination to page 1
- [x] 5.4 Add "Mark All Reviewed" button to filter frame
- [x] 5.5 Add "Mark All Unreviewed" button to filter frame
- [x] 5.6 Implement bulk update in `SegmentManager` (updates all filtered segments)

## 6. Testing
- [x] 6.1 Unit tests for `reviewed` field serialization/deserialization
- [x] 6.2 Unit tests for `AsyncWriteQueue` (debouncing, dirty tracking, ordering, flush_sync)
- [x] 6.3 Integration tests for auto-review detection (click timing, playback tracking)
- [x] 6.4 Test flush-on-exit writes pending changes before shutdown
- [x] 6.5 Integration tests for sync status indicator state changes
- [x] 6.6 Integration tests for review status filter
- [x] 6.7 Integration tests for bulk mark reviewed/unreviewed actions

## 7. Validation
- [x] 7.1 Verify backwards compatibility: JSON without `reviewed` loads correctly
- [x] 7.2 Verify no data loss during async writes (test rapid operations)
- [x] 7.3 Test with large segment files (200+ segments)
