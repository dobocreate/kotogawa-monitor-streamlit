# Refactoring Plan: Remove latest.json Redundancy

## Executive Summary
The `data/latest.json` file is **redundant and can be safely removed**. It's an exact duplicate of the most recent historical data file with no unique transformations or aggregations. Removing it will eliminate data duplication, reduce maintenance burden, and simplify the data flow.

## Current State Analysis

### 1. Data Structure
- **latest.json**: Exact copy of the most recent historical file (e.g., `data/history/2025/08/12/0450.json`)
- **No unique data**: Contains identical content to the corresponding historical file
- **No transformations**: Direct copy without any processing or aggregation

### 2. Usage Analysis
Primary consumers of `latest.json`:
- `streamlit_app.py`: Lines 149, 190 - loads latest data for display
- `scripts/collect_data.py`: Line 1027 - updates latest.json after successful collection
- `scripts/fetch_current_data.py`: Line 62 - saves latest data
- `scripts/save_current_webfetch_data.py`: Line 47 - updates latest data
- `scripts/update_latest_data.py`: Manual update script (appears to be emergency/test utility)

### 3. Performance Considerations
- **Current**: Two file writes per data collection (history + latest)
- **Proposed**: Single file write (history only)
- **Cache impact**: Streamlit already uses file mtime-based caching, works equally well with history files

## Refactoring Strategy

### Option Selected: **Remove latest.json**
Replace all references to `latest.json` with a function that finds and reads the most recent historical file.

### Why This Option
1. **Eliminates redundancy**: No duplicate data storage
2. **Reduces I/O**: One less file write per collection cycle
3. **Simplifies maintenance**: Single source of truth
4. **Preserves behavior**: Application functionality unchanged

## Impact Analysis

### Breaking Changes
- **None for end users**: UI and functionality remain identical
- **Internal API change**: `load_latest_data()` implementation changes

### Affected Components
1. **streamlit_app.py**: Modify data loading logic
2. **collect_data.py**: Remove latest.json write operation
3. **fetch_current_data.py**: Remove latest.json save
4. **save_current_webfetch_data.py**: Remove latest.json update
5. **update_latest_data.py**: May become obsolete or need refactoring
6. **test_app.py**: Update test to use new data access method

### Risk Assessment
- **Low Risk**: All changes are internal, no external APIs affected
- **Rollback**: Easy - changes are isolated and can be reverted independently

## Implementation Plan

### Phase 1: Create Helper Function
1. Add `get_latest_history_file()` function to find most recent data
2. Add comprehensive tests for the helper function
3. Verify edge cases (empty directory, corrupted files)

### Phase 2: Update Readers
1. Modify `streamlit_app.py` to use new helper
2. Update test files
3. Run smoke tests after each change

### Phase 3: Stop Writing latest.json
1. Comment out latest.json writes in collectors
2. Test for 24 hours in parallel mode
3. Remove write operations after verification

### Phase 4: Cleanup
1. Archive existing latest.json to quarantine/
2. Update documentation
3. Remove obsolete code paths

## Rollback Plan
Each phase can be independently rolled back:
1. **Phase 1**: Remove helper function (no impact)
2. **Phase 2**: Revert reader changes, restore latest.json dependency
3. **Phase 3**: Re-enable latest.json writes
4. **Phase 4**: Restore latest.json from quarantine/

## Success Criteria
- [ ] All existing tests pass
- [ ] Streamlit app loads data correctly
- [ ] Data collection continues without errors
- [ ] No performance degradation
- [ ] File I/O reduced by ~50% for write operations
- [ ] No latest.json file created after refactoring

## Timeline
- Phase 1: 30 minutes
- Phase 2: 1 hour
- Phase 3: 24-hour verification period
- Phase 4: 15 minutes
- Total: ~2 days with verification

## Metrics
- Before: 2 file writes per collection (history + latest)
- After: 1 file write per collection (history only)
- Storage saved: ~3-5KB per collection cycle
- Maintenance effort: Reduced by eliminating synchronization issues