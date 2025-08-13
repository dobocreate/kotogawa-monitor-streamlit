#!/usr/bin/env python3
"""
古いデータファイルの自動削除スクリプト
Streamlit Cloudのリソース制限対策
"""
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
import json

def cleanup_old_data(days_to_keep=3):
    """指定日数より古いデータファイルを削除
    
    Args:
        days_to_keep (int): 保持する日数（デフォルト：3日）
    """
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    data_dir = Path("data/history")
    
    if not data_dir.exists():
        print(f"データディレクトリが見つかりません: {data_dir}")
        return
    
    deleted_count = 0
    total_size_deleted = 0
    
    print(f"=== データクリーンアップ開始 ===")
    print(f"保持期間: {days_to_keep}日")
    print(f"削除対象: {cutoff_date.strftime('%Y-%m-%d %H:%M:%S')} より前のファイル")
    
    # 年/月/日の構造でファイルを探索
    for year_dir in data_dir.iterdir():
        if not year_dir.is_dir():
            continue
            
        for month_dir in year_dir.iterdir():
            if not month_dir.is_dir():
                continue
                
            for day_dir in month_dir.iterdir():
                if not day_dir.is_dir():
                    continue
                
                # ディレクトリ名から日付を取得
                try:
                    dir_date = datetime.strptime(f"{year_dir.name}/{month_dir.name}/{day_dir.name}", "%Y/%m/%d")
                except ValueError:
                    continue
                
                # 削除対象の日付かチェック
                if dir_date < cutoff_date:
                    print(f"削除対象ディレクトリ: {day_dir}")
                    
                    # ディレクトリ内のJSONファイルを削除
                    for json_file in day_dir.glob("*.json"):
                        if json_file.is_file():
                            file_size = json_file.stat().st_size
                            json_file.unlink()
                            deleted_count += 1
                            total_size_deleted += file_size
                            print(f"  削除: {json_file.name}")
                    
                    # 空になったディレクトリを削除
                    if not any(day_dir.iterdir()):
                        day_dir.rmdir()
                        print(f"  空ディレクトリ削除: {day_dir}")
                
                # 月ディレクトリが空になったら削除
                if not any(month_dir.iterdir()):
                    month_dir.rmdir()
                    print(f"  空ディレクトリ削除: {month_dir}")
        
        # 年ディレクトリが空になったら削除
        if not any(year_dir.iterdir()):
            year_dir.rmdir()
            print(f"  空ディレクトリ削除: {year_dir}")
    
    print(f"=== クリーンアップ完了 ===")
    print(f"削除ファイル数: {deleted_count}")
    print(f"削除サイズ: {total_size_deleted / 1024:.1f} KB")
    
    # 残ったファイル数とサイズを表示
    remaining_files = list(data_dir.glob("**/*.json"))
    remaining_size = sum(f.stat().st_size for f in remaining_files)
    print(f"残存ファイル数: {len(remaining_files)}")
    print(f"残存サイズ: {remaining_size / 1024:.1f} KB")

def main():
    """メイン処理"""
    # コマンドライン引数から保持日数を取得
    days_to_keep = 3
    if len(sys.argv) > 1:
        try:
            days_to_keep = int(sys.argv[1])
        except ValueError:
            print(f"エラー: 無効な日数指定 '{sys.argv[1]}'. 数値を指定してください。")
            sys.exit(1)
    
    cleanup_old_data(days_to_keep)

if __name__ == "__main__":
    main()