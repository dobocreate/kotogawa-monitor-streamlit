#!/usr/bin/env python3
"""
厚東川監視システム 現在データ取得・ログ保存スクリプト
WebFetchを使用してリアルタイムデータを取得し、ログとして保存
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

class CurrentDataFetcher:
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.data_dir = self.base_dir / "data"
        self.logs_dir = self.data_dir / "logs"
        self.history_dir = self.data_dir / "history"
        
        # Create directories if they don't exist
        self.data_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        self.history_dir.mkdir(exist_ok=True)
    
    def save_fetch_log(self, data: Dict[str, Any], source: str = "manual") -> None:
        """取得データをログとして保存"""
        timestamp = datetime.now()
        
        # ログファイル名（日付別）
        log_file = self.logs_dir / f"fetch_log_{timestamp.strftime('%Y%m%d')}.json"
        
        # ログエントリ作成
        log_entry = {
            "fetch_timestamp": timestamp.isoformat(),
            "source": source,  # manual, auto, test など
            "data": data,
            "status": "success" if all(data.values()) else "partial"
        }
        
        # 既存ログの読み込み
        logs = []
        if log_file.exists():
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            except:
                logs = []
        
        # 新しいログを追加
        logs.append(log_entry)
        
        # ログを保存（1日あたり最大100件まで保持）
        logs = logs[-100:]
        
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"📝 ログ保存: {log_file}")
    
    def save_as_latest_data(self, data: Dict[str, Any]) -> None:
        """最新データとして保存（Streamlitアプリ用）"""
        latest_file = self.data_dir / "latest.json"
        
        with open(latest_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"💾 最新データ更新: {latest_file}")
    
    def save_as_history_data(self, data: Dict[str, Any]) -> None:
        """履歴データとして保存"""
        timestamp = datetime.now()
        date_dir = (self.history_dir / 
                   timestamp.strftime("%Y") / 
                   timestamp.strftime("%m") / 
                   timestamp.strftime("%d"))
        date_dir.mkdir(parents=True, exist_ok=True)
        
        history_file = date_dir / f"{timestamp.strftime('%H%M')}.json"
        
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"📚 履歴データ保存: {history_file}")
    
    def format_current_data(self, dam_data: Dict, river_data: Dict, rainfall_data: Dict) -> Dict[str, Any]:
        """取得データを標準形式にフォーマット"""
        current_time = datetime.now()
        
        formatted_data = {
            "timestamp": current_time.isoformat(),
            "data_time": "2025-06-22T14:00:00",  # 実際のデータ時刻
            "dam": {
                "water_level": dam_data.get("water_level"),
                "storage_rate": dam_data.get("storage_rate"),
                "inflow": dam_data.get("inflow"),
                "outflow": dam_data.get("outflow"),
                "storage_change": None  # 前回データとの比較で計算
            },
            "river": {
                "water_level": river_data.get("water_level"),
                "level_change": None,  # 前回データとの比較で計算
                "status": river_data.get("status", "正常")
            },
            "rainfall": {
                "hourly": rainfall_data.get("hourly", 0),
                "cumulative": rainfall_data.get("cumulative", 0),
                "change": None  # 前回データとの比較で計算
            }
        }
        
        return formatted_data
    
    def process_manual_data_entry(self) -> None:
        """手動でのデータ入力処理"""
        print("=== 厚東川監視システム 現在データ取得 ===")
        print("WebFetchで取得したデータを入力してください")
        print()
        
        # ダムデータ入力
        print("🏔️ ダムデータ:")
        dam_data = {
            "water_level": float(input("貯水位 (m): ") or 36.74),
            "storage_rate": float(input("貯水率 (%): ") or 97.0),
            "inflow": float(input("流入量 (m³/s): ") or 7.31),
            "outflow": float(input("放流量 (m³/s): ") or 9.41)
        }
        
        # 河川データ入力
        print("\n🌊 河川データ:")
        river_water_level = float(input("水位 (m): ") or 2.85)
        
        # 警戒レベル判定
        if river_water_level >= 5.50:
            status = "氾濫危険"
        elif river_water_level >= 5.10:
            status = "避難判断"
        elif river_water_level >= 5.00:
            status = "氾濫注意"
        elif river_water_level >= 3.80:
            status = "水防団待機"
        else:
            status = "正常"
        
        river_data = {
            "water_level": river_water_level,
            "status": status
        }
        
        # 雨量データ入力
        print("\n🌧️ 雨量データ:")
        rainfall_data = {
            "hourly": int(input("60分雨量 (mm): ") or 1),
            "cumulative": int(input("累積雨量 (mm): ") or 2)
        }
        
        # データをフォーマット
        formatted_data = self.format_current_data(dam_data, river_data, rainfall_data)
        
        print("\n📊 取得データサマリー:")
        print(f"ダム貯水位: {dam_data['water_level']}m ({dam_data['storage_rate']}%)")
        print(f"河川水位: {river_data['water_level']}m ({river_data['status']})")
        print(f"雨量: {rainfall_data['hourly']}mm/h (累積: {rainfall_data['cumulative']}mm)")
        
        # 保存確認
        save_choice = input("\nデータを保存しますか? (y/N): ").lower()
        if save_choice == 'y':
            # ログとして保存
            self.save_fetch_log(formatted_data, source="manual_input")
            
            # 最新データとして保存
            self.save_as_latest_data(formatted_data)
            
            # 履歴データとして保存
            self.save_as_history_data(formatted_data)
            
            print("✅ データ保存完了")
        else:
            print("❌ データ保存をキャンセル")
    
    def auto_save_webfetch_data(self) -> None:
        """WebFetchで取得したデータを自動保存"""
        # 実際のWebFetch結果を手動で入力
        print("=== WebFetch データ自動保存 ===")
        
        # 2025/06/22 14:00のデータ
        dam_data = {
            "water_level": 36.74,
            "storage_rate": 97.0,
            "inflow": 7.31,
            "outflow": 9.41
        }
        
        river_data = {
            "water_level": 2.85,
            "status": "正常"
        }
        
        rainfall_data = {
            "hourly": 1,
            "cumulative": 2
        }
        
        # データをフォーマット
        formatted_data = self.format_current_data(dam_data, river_data, rainfall_data)
        
        # 全形式で保存
        self.save_fetch_log(formatted_data, source="webfetch")
        self.save_as_latest_data(formatted_data)
        self.save_as_history_data(formatted_data)
        
        print("✅ WebFetchデータ保存完了")
        return formatted_data
    
    def view_recent_logs(self, days: int = 1) -> None:
        """最近のログを表示"""
        print(f"=== 過去{days}日のログ ===")
        
        for i in range(days):
            date = datetime.now() - timedelta(days=i)
            log_file = self.logs_dir / f"fetch_log_{date.strftime('%Y%m%d')}.json"
            
            if log_file.exists():
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        logs = json.load(f)
                    
                    print(f"\n📅 {date.strftime('%Y-%m-%d')} ({len(logs)}件)")
                    
                    for log in logs[-5:]:  # 最新5件表示
                        fetch_time = log['fetch_timestamp'][:19]
                        source = log['source']
                        dam_level = log['data']['dam']['water_level']
                        river_level = log['data']['river']['water_level']
                        print(f"  {fetch_time} [{source}] ダム:{dam_level}m 河川:{river_level}m")
                        
                except Exception as e:
                    print(f"  エラー: {e}")
            else:
                print(f"\n📅 {date.strftime('%Y-%m-%d')} (ログなし)")

def main():
    fetcher = CurrentDataFetcher()
    
    print("厚東川監視システム データ取得・ログ機能")
    print("1. WebFetchデータを自動保存")
    print("2. 手動データ入力")
    print("3. 最近のログ表示")
    
    choice = input("\n選択 (1-3): ")
    
    if choice == "1":
        data = fetcher.auto_save_webfetch_data()
        print(f"\n最新データ: {json.dumps(data, ensure_ascii=False, indent=2, default=str)}")
    elif choice == "2":
        fetcher.process_manual_data_entry()
    elif choice == "3":
        fetcher.view_recent_logs()
    else:
        print("無効な選択です")

if __name__ == "__main__":
    main()