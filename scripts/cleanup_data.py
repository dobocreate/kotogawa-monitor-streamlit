#!/usr/bin/env python3
"""
厚東川監視システム データクリーンアップスクリプト
古いデータファイルを削除して容量を管理
"""

import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path

class DataCleanup:
    def __init__(self, days_to_keep: int = 7):
        self.base_dir = Path(__file__).parent.parent
        self.data_dir = self.base_dir / "data"
        self.history_dir = self.data_dir / "history"
        self.days_to_keep = days_to_keep
        self.cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
    def cleanup_history_data(self) -> int:
        """履歴データをクリーンアップ"""
        deleted_count = 0
        
        if not self.history_dir.exists():
            print("History directory does not exist")
            return deleted_count
        
        print(f"Cleaning up data older than {self.cutoff_date.strftime('%Y-%m-%d')}")
        
        # 年ディレクトリを処理
        for year_dir in self.history_dir.iterdir():
            if not year_dir.is_dir():
                continue
                
            try:
                year = int(year_dir.name)
                
                # 年全体が古い場合は削除
                if year < self.cutoff_date.year:
                    print(f"Removing entire year directory: {year_dir}")
                    shutil.rmtree(year_dir)
                    deleted_count += self._count_files_in_dir(year_dir)
                    continue
                
                # 月ディレクトリを処理
                deleted_count += self._cleanup_month_directories(year_dir, year)
                
                # 空の年ディレクトリを削除
                if not any(year_dir.iterdir()):
                    print(f"Removing empty year directory: {year_dir}")
                    year_dir.rmdir()
                    
            except (ValueError, OSError) as e:
                print(f"Error processing year directory {year_dir}: {e}")
                continue
        
        return deleted_count
    
    def _cleanup_month_directories(self, year_dir: Path, year: int) -> int:
        """月ディレクトリをクリーンアップ"""
        deleted_count = 0
        
        for month_dir in year_dir.iterdir():
            if not month_dir.is_dir():
                continue
                
            try:
                month = int(month_dir.name)
                
                # 月全体が古い場合は削除
                if (year == self.cutoff_date.year and month < self.cutoff_date.month):
                    print(f"Removing entire month directory: {month_dir}")
                    deleted_count += self._count_files_in_dir(month_dir)
                    shutil.rmtree(month_dir)
                    continue
                
                # 日ディレクトリを処理
                deleted_count += self._cleanup_day_directories(month_dir, year, month)
                
                # 空の月ディレクトリを削除
                if not any(month_dir.iterdir()):
                    print(f"Removing empty month directory: {month_dir}")
                    month_dir.rmdir()
                    
            except (ValueError, OSError) as e:
                print(f"Error processing month directory {month_dir}: {e}")
                continue
        
        return deleted_count
    
    def _cleanup_day_directories(self, month_dir: Path, year: int, month: int) -> int:
        """日ディレクトリをクリーンアップ"""
        deleted_count = 0
        
        for day_dir in month_dir.iterdir():
            if not day_dir.is_dir():
                continue
                
            try:
                day = int(day_dir.name)
                dir_date = datetime(year, month, day)
                
                # 日全体が古い場合は削除
                if dir_date < self.cutoff_date:
                    print(f"Removing old day directory: {day_dir}")
                    deleted_count += self._count_files_in_dir(day_dir)
                    shutil.rmtree(day_dir)
                    continue
                
                # 空の日ディレクトリを削除
                if not any(day_dir.iterdir()):
                    print(f"Removing empty day directory: {day_dir}")
                    day_dir.rmdir()
                    
            except (ValueError, OSError) as e:
                print(f"Error processing day directory {day_dir}: {e}")
                continue
        
        return deleted_count
    
    def _count_files_in_dir(self, directory: Path) -> int:
        """ディレクトリ内のファイル数をカウント"""
        if not directory.exists():
            return 0
        
        count = 0
        try:
            for item in directory.rglob('*'):
                if item.is_file():
                    count += 1
        except OSError:
            pass
        
        return count
    
    def cleanup_logs(self) -> int:
        """古いログファイルをクリーンアップ"""
        deleted_count = 0
        
        # エラーログファイルのクリーンアップ
        error_log = self.data_dir / "error.log"
        if error_log.exists():
            try:
                # ファイルサイズが1MBを超える場合は最新の100行のみ保持
                if error_log.stat().st_size > 1024 * 1024:  # 1MB
                    print("Truncating large error log file")
                    with open(error_log, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    
                    # 最新の100行のみ保持
                    if len(lines) > 100:
                        with open(error_log, 'w', encoding='utf-8') as f:
                            f.writelines(lines[-100:])
                        deleted_count += 1
                        
            except OSError as e:
                print(f"Error processing error log: {e}")
        
        return deleted_count
    
    def get_disk_usage(self) -> dict:
        """ディスク使用量を取得"""
        usage = {}
        
        if self.data_dir.exists():
            total_size = 0
            file_count = 0
            
            for item in self.data_dir.rglob('*'):
                if item.is_file():
                    try:
                        total_size += item.stat().st_size
                        file_count += 1
                    except OSError:
                        continue
            
            usage = {
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'file_count': file_count,
                'data_dir': str(self.data_dir)
            }
        
        return usage
    
    def run_cleanup(self) -> dict:
        """クリーンアップを実行"""
        print(f"Starting data cleanup - keeping last {self.days_to_keep} days")
        
        # クリーンアップ前の状態
        before_usage = self.get_disk_usage()
        
        # クリーンアップ実行
        deleted_files = 0
        deleted_files += self.cleanup_history_data()
        deleted_files += self.cleanup_logs()
        
        # クリーンアップ後の状態
        after_usage = self.get_disk_usage()
        
        # 結果サマリー
        result = {
            'timestamp': datetime.now().isoformat(),
            'days_kept': self.days_to_keep,
            'deleted_files': deleted_files,
            'before': before_usage,
            'after': after_usage,
            'space_freed_mb': before_usage.get('total_size_mb', 0) - after_usage.get('total_size_mb', 0)
        }
        
        print(f"Cleanup completed:")
        print(f"  - Files deleted: {deleted_files}")
        print(f"  - Space freed: {result['space_freed_mb']:.2f} MB")
        print(f"  - Remaining files: {after_usage.get('file_count', 0)}")
        print(f"  - Remaining data: {after_usage.get('total_size_mb', 0):.2f} MB")
        
        return result

def main():
    """メイン関数"""
    # デフォルトは7日間保持
    cleanup = DataCleanup(days_to_keep=7)
    
    try:
        result = cleanup.run_cleanup()
        
        # 結果をJSONファイルに保存
        import json
        cleanup_log = cleanup.data_dir / "cleanup_log.json"
        
        if cleanup_log.exists():
            # 既存のログを読み込み
            with open(cleanup_log, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        else:
            logs = []
        
        # 新しいログを追加（最新10件のみ保持）
        logs.append(result)
        logs = logs[-10:]
        
        # ログを保存
        with open(cleanup_log, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"Cleanup log saved to: {cleanup_log}")
        return 0
        
    except Exception as e:
        print(f"Error during cleanup: {e}")
        return 1

if __name__ == "__main__":
    exit(main())