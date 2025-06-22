#!/usr/bin/env python3
"""
WebFetchで取得した現在データを保存
"""

import json
from datetime import datetime
from pathlib import Path

def save_current_data():
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / "data"
    logs_dir = data_dir / "logs"
    history_dir = data_dir / "history"
    
    # Create directories
    data_dir.mkdir(exist_ok=True)
    logs_dir.mkdir(exist_ok=True)
    history_dir.mkdir(exist_ok=True)
    
    # WebFetchで取得した2025/06/22 14:00のデータ
    current_time = datetime.now()
    
    data = {
        "timestamp": current_time.isoformat(),
        "data_time": "2025-06-22T14:00:00",
        "dam": {
            "water_level": 36.74,
            "storage_rate": 97.0,
            "inflow": 7.31,
            "outflow": 9.41,
            "storage_change": -0.02  # 36.76から36.74への変化
        },
        "river": {
            "water_level": 2.85,
            "level_change": -0.03,  # 2.88から2.85への変化
            "status": "正常"
        },
        "rainfall": {
            "hourly": 1,
            "cumulative": 2,
            "change": 1
        }
    }
    
    # 1. 最新データとして保存
    latest_file = data_dir / "latest.json"
    with open(latest_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    print(f"💾 最新データ更新: {latest_file}")
    
    # 2. 履歴データとして保存
    date_dir = (history_dir / 
               current_time.strftime("%Y") / 
               current_time.strftime("%m") / 
               current_time.strftime("%d"))
    date_dir.mkdir(parents=True, exist_ok=True)
    
    history_file = date_dir / f"{current_time.strftime('%H%M')}.json"
    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    print(f"📚 履歴データ保存: {history_file}")
    
    # 3. ログとして保存
    log_file = logs_dir / f"fetch_log_{current_time.strftime('%Y%m%d')}.json"
    
    log_entry = {
        "fetch_timestamp": current_time.isoformat(),
        "source": "webfetch_manual",
        "data": data,
        "status": "success",
        "notes": "WebFetch取得データ - 2025/06/22 14:00時点"
    }
    
    # 既存ログ読み込み
    logs = []
    if log_file.exists():
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        except:
            logs = []
    
    logs.append(log_entry)
    
    # ログ保存
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(logs, f, ensure_ascii=False, indent=2, default=str)
    print(f"📝 ログ保存: {log_file}")
    
    print("\n📊 保存されたデータ:")
    print(f"ダム貯水位: {data['dam']['water_level']}m ({data['dam']['storage_rate']}%)")
    print(f"河川水位: {data['river']['water_level']}m ({data['river']['status']})")
    print(f"雨量: {data['rainfall']['hourly']}mm/h (累積: {data['rainfall']['cumulative']}mm)")
    print(f"データ時刻: 2025-06-22 14:00")
    print(f"取得時刻: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    return data

if __name__ == "__main__":
    save_current_data()