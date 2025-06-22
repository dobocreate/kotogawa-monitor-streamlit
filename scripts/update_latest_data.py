#!/usr/bin/env python3
"""
最新データを手動で更新するスクリプト
"""

import json
from datetime import datetime
from pathlib import Path

# 最新データ（2025/06/23 04:50時点）
data = {
    "timestamp": datetime.now().isoformat(),
    "data_time": "2025-06-23T04:50:00",
    "dam": {
        "water_level": 36.82,
        "storage_rate": 97.9,
        "inflow": 17.22,
        "outflow": 9.25,
        "storage_change": 0.08  # 36.82 - 36.74
    },
    "river": {
        "water_level": 2.91,
        "level_change": 0.06,  # 2.91 - 2.85
        "status": "正常"
    },
    "rainfall": {
        "hourly": 0,  # 雨量データは取得できていないため0と仮定
        "cumulative": 0,
        "change": 0
    }
}

# ファイルパス
base_dir = Path(__file__).parent.parent
data_dir = base_dir / "data"
latest_file = data_dir / "latest.json"

# 最新データを保存
with open(latest_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2, default=str)

print(f"✅ 最新データを更新しました: {latest_file}")
print(f"📊 観測時刻: {data['data_time']}")
print(f"🏔️ ダム貯水位: {data['dam']['water_level']}m ({data['dam']['storage_rate']}%)")
print(f"🌊 河川水位: {data['river']['water_level']}m")