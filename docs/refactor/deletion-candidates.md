# Deletion Candidates

## 2025-08-13 CSS最適化関連

### インラインCSS（フォールバック削除待ち）
1. **streamlit_app.py内のインラインCSS（行47-142）**
   - 根拠: CSS統合モジュールに移行済み
   - 参照: src/presentation/styles/モジュールが正常動作確認後
   - 保留期間: 2週間（2025-08-27まで）
   - 削除条件: フォールバックが不要と確認後
   - サイズ: 約100行（3KB）

2. **将来的な統合候補**
   - app.pyとstreamlit_app.pyの統合
   - 根拠: 機能重複、CSS統合済み
   - 保留期間: 3-6ヶ月（ユーザー習熟度による）
   - 削除条件: 新UIの完全移行確認後

---

## 2025-08-12 latest.json Removal

## Files to be Deleted

### Primary Target
- **File**: `data/latest.json`
- **Size**: ~3-5KB
- **Last Modified**: Continuously updated every 10 minutes
- **Reason**: Redundant copy of history files
- **Dependencies**: None after refactoring complete
- **Quarantine Period**: 7 days after Phase 4 completion

### Code Sections to Remove

#### 1. scripts/collect_data.py
- **Lines**: 1025-1033
- **Code**: latest.json write operation
- **Status**: To be commented in Phase 3, removed in Phase 4
```python
# Lines to remove:
if not is_error:
    latest_file = self.data_dir / "latest.json"
    # Atomic write operation
    import os, tempfile
    with tempfile.NamedTemporaryFile('w', encoding='utf-8', delete=False, dir=latest_file.parent, suffix='.tmp') as tmp:
        json.dump(data, tmp, ensure_ascii=False, indent=2, default=str)
        tmp_path = tmp.name
    os.replace(tmp_path, latest_file)
```

#### 2. scripts/fetch_current_data.py
- **Lines**: 61-67
- **Method**: `save_as_latest()`
- **Status**: To be removed entirely
```python
def save_as_latest(self, data: Dict[str, Any]) -> None:
    """最新データとして保存（Streamlitアプリ用）"""
    latest_file = self.data_dir / "latest.json"
    # Save logic...
```

#### 3. scripts/save_current_webfetch_data.py
- **Lines**: 47-52
- **Code**: latest.json update
- **Status**: To be removed

#### 4. scripts/update_latest_data.py
- **File**: Entire script
- **Purpose**: Manual emergency update of latest.json
- **Alternative**: Update history files directly if needed
- **Status**: Candidate for complete removal or transformation

### Documentation References to Update

#### README.md
- Remove reference to `latest.json` in file structure
- Update data flow description

#### PROJECT_DETAILS.md
- Line 29: Remove `├── latest.json          # 最新データ`
- Line 109: Remove section "### データ形式（latest.json）"

#### docs/debug/*.md
- Multiple references in verification and fix proposal documents
- Update to reflect new data access pattern

### Test Files to Update

#### test_app.py
- Line 10: Update data file reference
- Status: Already handled in Phase 2

#### streamlit_app_minimal.py
- Line 21: Update to use history files
- Status: Low priority (appears to be unused/test file)

## Validation Checklist

Before deletion:
- [ ] Verify no active references: `grep -r "latest\.json" --exclude-dir=.git --exclude-dir=kotogawa_env`
- [ ] Confirm history files contain all necessary data
- [ ] Test application runs correctly without latest.json
- [ ] Check monitoring scripts don't depend on latest.json
- [ ] Verify backup/restore procedures updated

## Quarantine Process

1. **Create quarantine directory**: `mkdir -p quarantine/2025-08-12`
2. **Move file with metadata**:
   ```bash
   cp -p data/latest.json quarantine/2025-08-12/latest.json.backup
   echo "Moved: $(date)" > quarantine/2025-08-12/README.md
   echo "Reason: Redundant with history files" >> quarantine/2025-08-12/README.md
   echo "Can be deleted after: $(date -d '+7 days')" >> quarantine/2025-08-12/README.md
   ```
3. **Monitor for 7 days**
4. **Final deletion**: `rm quarantine/2025-08-12/latest.json.backup`

## Rollback Instructions

If issues arise after deletion:
1. **Immediate**: Restore from quarantine
2. **Code**: Revert git commits for each phase
3. **Data**: latest.json can be regenerated from most recent history file:
   ```python
   from utils.data_helper import load_latest_data
   from pathlib import Path
   import json
   
   data = load_latest_data(Path('data'))
   with open('data/latest.json', 'w') as f:
       json.dump(data, f, ensure_ascii=False, indent=2)
   ```

## Timeline
- **Phase 3 Start**: 2025-08-12 (parallel testing)
- **Phase 4 Start**: 2025-08-13 (after 24h monitoring)
- **Quarantine**: 2025-08-13
- **Final Deletion**: 2025-08-20 (7 days later)

## Impact Summary
- **Storage Saved**: ~3-5KB per update × 144 updates/day = ~500KB/day
- **I/O Operations Saved**: 144 file writes/day
- **Code Simplified**: ~50 lines removed
- **Maintenance Reduced**: No synchronization issues between latest and history

## UI復元に関する削除候補

### 評価結果
- **削除候補ファイル**: なし
- **理由**: 新旧UIは共存可能、クリーンアーキテクチャ版が元のUIを包含
- **状態**: 両方のUIが並行して利用可能

### 将来的な統合検討
- **streamlit_app.py**: 将来的に app.py に完全移行後、アーカイブ候補
- **タイムライン**: ユーザーの新UI習熟度による（3-6ヶ月後に再評価）
- **移行戦略**: 段階的な機能統合とユーザーフィードバック収集