#\!/usr/bin/env python3
"""
不完全なバックフィルデータを修復するスクリプト
riverセクションが欠落しているデータを再取得して上書き保存
"""

import json
import argparse
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# 既存のモジュールをインポート
try:
    from backfill_missing_data import DataBackfiller
except ImportError:
    print("Error: backfill_missing_data module not found")
    sys.exit(1)

try:
    from zoneinfo import ZoneInfo
except ImportError:
    import pytz
    ZoneInfo = lambda x: pytz.timezone(x)

class DataRepairer:
    def __init__(self, dry_run: bool = False):
        self.backfiller = DataBackfiller(dry_run=dry_run)
        self.base_dir = Path(__file__).parent.parent
        self.history_dir = self.base_dir / "data" / "history"
        self.dry_run = dry_run
        self.jst = ZoneInfo('Asia/Tokyo')
    
    def find_incomplete_files(self, date_str: str = None) -> List[Path]:
        """不完全なファイルを検出"""
        incomplete = []
        
        if date_str:
            # 特定日付のみ
            year, month, day = date_str.split('-')
            search_path = self.history_dir / year / month / day
            if search_path.exists():
                json_files = search_path.glob('*.json')
            else:
                print(f"Directory not found: {search_path}")
                return []
        else:
            # 全体を検索
            json_files = self.history_dir.rglob('*.json')
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # riverセクションの確認
                if 'river' not in data:
                    incomplete.append(json_file)
                    continue
                
                # riverセクションが存在してもwater_levelがNoneの場合
                # （ただし、元々データがない時間帯もあるので注意）
                river = data.get('river', {})
                if river and river.get('water_level') is None:
                    # メタデータで判断（backfillソースで不完全なもののみ）
                    metadata = data.get('_metadata', {})
                    if metadata.get('source') == 'backfill' and not metadata.get('complete', True):
                        incomplete.append(json_file)
            
            except Exception as e:
                print(f"Error reading {json_file}: {e}")
        
        return sorted(incomplete)
    
    def repair_file(self, file_path: Path) -> bool:
        """単一ファイルを修復"""
        try:
            # 既存データを読み込み
            with open(file_path, 'r', encoding='utf-8') as f:
                old_data = json.load(f)
            
            # data_timeから観測時刻を取得
            data_time_str = old_data.get('data_time')
            if not data_time_str:
                print(f"  No data_time in {file_path.name}")
                return False
            
            # 観測時刻をパース
            obs_time = datetime.fromisoformat(data_time_str)
            
            print(f"  Repairing {file_path.name} ({obs_time.strftime('%Y-%m-%d %H:%M')})")
            
            if not self.dry_run:
                # 新しいデータを取得
                new_data = self.backfiller.fetch_historical_data(obs_time)
                
                if new_data:
                    # riverデータが取得できた場合のみ更新
                    if new_data.get('river', {}).get('water_level') is not None:
                        # バックアップ作成
                        backup_path = file_path.with_suffix('.json.backup')
                        with open(backup_path, 'w', encoding='utf-8') as f:
                            json.dump(old_data, f, ensure_ascii=False, indent=2)
                        
                        # 新データで上書き
                        with open(file_path, 'w', encoding='utf-8') as f:
                            json.dump(new_data, f, ensure_ascii=False, indent=2, default=str)
                        
                        print(f"    ✓ Repaired (river level: {new_data['river']['water_level']}m)")
                        return True
                    else:
                        print(f"    ⚠ River data still unavailable")
                        return False
                else:
                    print(f"    ✗ Failed to fetch new data")
                    return False
            else:
                print(f"    [DRY RUN] Would repair this file")
                return True
        
        except Exception as e:
            print(f"    Error: {e}")
            return False
    
    def repair_all(self, date_str: str = None, max_repairs: int = 10) -> int:
        """不完全なファイルをすべて修復"""
        print(f"Searching for incomplete files...")
        incomplete_files = self.find_incomplete_files(date_str)
        
        if not incomplete_files:
            print("No incomplete files found")
            return 0
        
        print(f"Found {len(incomplete_files)} incomplete file(s)")
        
        # 修復対象を制限
        to_repair = incomplete_files[:max_repairs]
        if len(incomplete_files) > max_repairs:
            print(f"Limiting repairs to {max_repairs} files")
        
        success_count = 0
        for i, file_path in enumerate(to_repair, 1):
            print(f"\n[{i}/{len(to_repair)}] Processing {file_path.relative_to(self.base_dir)}")
            
            if self.repair_file(file_path):
                success_count += 1
            
            # API負荷軽減
            if i < len(to_repair) and not self.dry_run:
                import time
                time.sleep(2)
        
        print(f"\n=== Summary ===")
        print(f"Successfully repaired: {success_count}/{len(to_repair)} files")
        
        if len(incomplete_files) > max_repairs:
            remaining = len(incomplete_files) - max_repairs
            print(f"Remaining incomplete files: {remaining}")
            print("Run again to repair more files")
        
        return success_count

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='Repair incomplete monitoring data')
    parser.add_argument('--date', type=str, help='Target date (YYYY-MM-DD)')
    parser.add_argument('--max', type=int, default=10, help='Maximum files to repair (default: 10)')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode')
    parser.add_argument('--list-only', action='store_true', help='List incomplete files only')
    
    args = parser.parse_args()
    
    repairer = DataRepairer(dry_run=args.dry_run)
    
    if args.list_only:
        # リストのみ表示
        incomplete = repairer.find_incomplete_files(args.date)
        if incomplete:
            print(f"Incomplete files ({len(incomplete)}):")
            for f in incomplete:
                print(f"  - {f.relative_to(repairer.base_dir)}")
        else:
            print("No incomplete files found")
        sys.exit(0)
    
    # 修復実行
    result = repairer.repair_all(date_str=args.date, max_repairs=args.max)
    sys.exit(0 if result > 0 else 1)

if __name__ == "__main__":
    main()
