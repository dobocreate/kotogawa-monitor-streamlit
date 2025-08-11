# Refactoring Checklist: Remove latest.json

## Pre-Refactoring Checks
- [ ] Current tests pass: `pytest -q`
- [ ] Streamlit app loads without errors
- [ ] Backup current working state: `git status && git diff`
- [ ] Document current latest.json file size and update frequency

## Phase 1: Helper Function Implementation
- [ ] Create `utils/data_helper.py` with `get_latest_history_file()` function
- [ ] Add unit tests for helper function:
  - [ ] Test finding latest file in normal conditions
  - [ ] Test with empty history directory
  - [ ] Test with error_*.json files (should skip)
  - [ ] Test with multiple days of data
- [ ] Run tests: `pytest tests/test_data_helper.py -v`
- [ ] Verify no regressions: `pytest -q`

## Phase 2: Update Data Readers
### Streamlit App
- [ ] Backup current streamlit_app.py
- [ ] Update `load_latest_data()` to use helper function
- [ ] Test app locally: `streamlit run streamlit_app.py`
- [ ] Verify all data displays correctly
- [ ] Check caching still works (reload page, check performance)
- [ ] Commit: "refactor: Update streamlit to use history files directly"

### Test Files
- [ ] Update `test_app.py` to use new data access
- [ ] Run tests: `pytest test_app.py -v`
- [ ] Commit: "test: Update tests for new data access pattern"

## Phase 3: Parallel Testing (Keep Writing, New Reading)
- [ ] Deploy changes with latest.json still being written
- [ ] Monitor for 24 hours:
  - [ ] Check app loads correctly every hour
  - [ ] Verify data freshness matches latest.json
  - [ ] Monitor error logs
  - [ ] Check memory/CPU usage hasn't increased
- [ ] Document any issues found

## Phase 4: Stop Writing latest.json
### Comment Out Writes (Soft Disable)
- [ ] `scripts/collect_data.py`: Comment lines 1025-1033
- [ ] `scripts/fetch_current_data.py`: Comment lines 61-67
- [ ] `scripts/save_current_webfetch_data.py`: Comment lines 47-52
- [ ] Test each script individually:
  - [ ] `python scripts/collect_data.py` (dry run)
  - [ ] Verify history file created, no latest.json
- [ ] Commit: "refactor: Disable latest.json writes (commented)"

### Monitor
- [ ] Run for 6 hours with commented writes
- [ ] Verify app still works correctly
- [ ] Check no latest.json updates

### Remove Write Code
- [ ] Delete commented code blocks
- [ ] Remove imports only used for latest.json
- [ ] Update script docstrings
- [ ] Commit: "refactor: Remove latest.json write operations"

## Phase 5: Cleanup
### Archive Old File
- [ ] Create `quarantine/` directory if not exists
- [ ] Move `data/latest.json` to `quarantine/latest.json.backup`
- [ ] Add timestamp to backup filename
- [ ] Document in `quarantine/README.md`

### Code Cleanup
- [ ] Remove/update `scripts/update_latest_data.py`
- [ ] Search for any remaining "latest.json" references: `grep -r "latest\.json"`
- [ ] Update documentation files:
  - [ ] README.md
  - [ ] PROJECT_DETAILS.md
  - [ ] docs/debug/*.md
- [ ] Commit: "docs: Update documentation for latest.json removal"

## Verification Tests
- [ ] Full test suite passes: `pytest`
- [ ] Streamlit app loads current data
- [ ] Data collection runs without errors
- [ ] No latest.json file created after collection
- [ ] Performance metrics:
  - [ ] Page load time <= previous
  - [ ] Memory usage stable
  - [ ] CPU usage normal

## Performance Metrics Collection
Before refactoring:
- [ ] Time to write data: _____ ms
- [ ] Disk I/O for collection: _____ KB
- [ ] latest.json file size: _____ KB

After refactoring:
- [ ] Time to write data: _____ ms
- [ ] Disk I/O for collection: _____ KB
- [ ] Space saved per cycle: _____ KB

## Rollback Checkpoints
- [ ] After Phase 1: Can remove helper function
- [ ] After Phase 2: `git revert` reader changes
- [ ] After Phase 3: Uncomment write operations
- [ ] After Phase 4: Restore from quarantine/
- [ ] Final: Full git revert to tagged version

## Sign-off
- [ ] All tests passing
- [ ] No user-facing changes
- [ ] Performance acceptable
- [ ] Documentation updated
- [ ] Team notified of changes
- [ ] Monitoring in place for next 48 hours