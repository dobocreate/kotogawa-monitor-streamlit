#\!/bin/bash
# 河川水位データ品質スモークテスト

echo "=== 河川水位データ品質チェック ==="
echo "実行時刻: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 1. 最新データファイルの確認
echo "[1] 最新データファイル確認"
latest_dir=$(ls -d data/history/2025/08/* 2>/dev/null | tail -1)
if [ -z "$latest_dir" ]; then
    echo "✗ データディレクトリが見つかりません"
    exit 1
fi

latest_file=$(ls -t "$latest_dir"/*.json 2>/dev/null | head -1)
if [ -z "$latest_file" ]; then
    echo "✗ JSONファイルが見つかりません"
    exit 1
fi

echo "✓ 最新ファイル: $(basename $latest_file)"

# 2. 河川水位データの取得と検証
echo ""
echo "[2] 河川水位データ検証"

# Python で JSON を解析
python3 << PYTHON_EOF
import json
import sys
from pathlib import Path

try:
    with open('$latest_file', 'r') as f:
        data = json.load(f)
    
    river_level = data.get('river', {}).get('water_level')
    river_status = data.get('river', {}).get('status')
    data_time = data.get('data_time')
    
    print(f"  データ時刻: {data_time}")
    print(f"  河川水位: {river_level}m")
    print(f"  状態: {river_status}")
    
    if river_level is None:
        print("⚠ 河川水位データなし")
    elif 0.5 <= river_level <= 10:
        print("✓ 河川水位は正常範囲内")
    else:
        print(f"✗ 河川水位が異常範囲: {river_level}m")
        sys.exit(1)
        
except Exception as e:
    print(f"✗ エラー: {e}")
    sys.exit(1)
PYTHON_EOF

if [ $? -ne 0 ]; then
    echo "データ検証に失敗しました"
    exit 1
fi

# 3. 最近のデータの統計
echo ""
echo "[3] 最近24時間のデータ統計"

python3 << PYTHON_EOF
import json
from pathlib import Path
from datetime import datetime, timedelta

data_dir = Path('data/history/2025/08')
now = datetime.now()
cutoff = now - timedelta(hours=24)

river_levels = []
for json_file in data_dir.rglob('*.json'):
    try:
        # ファイルの更新時刻をチェック
        if json_file.stat().st_mtime < cutoff.timestamp():
            continue
            
        with open(json_file, 'r') as f:
            data = json.load(f)
        level = data.get('river', {}).get('water_level')
        if level is not None:
            river_levels.append(level)
    except:
        pass

if river_levels:
    print(f"  データ数: {len(river_levels)}")
    print(f"  最小値: {min(river_levels):.2f}m")
    print(f"  最大値: {max(river_levels):.2f}m")
    print(f"  平均値: {sum(river_levels)/len(river_levels):.2f}m")
    
    # 急激な変化をチェック
    if max(river_levels) - min(river_levels) > 3:
        print("⚠ 24時間で3m以上の変動あり")
else:
    print("⚠ 24時間以内のデータなし")
PYTHON_EOF

# 4. 警告ファイルの確認
echo ""
echo "[4] 警告ファイル確認"
warning_count=$(find data/history -name "*.warning.json" -mtime -1 2>/dev/null | wc -l)
if [ $warning_count -gt 0 ]; then
    echo "⚠ 過去24時間の警告ファイル: ${warning_count}件"
    find data/history -name "*.warning.json" -mtime -1 -exec basename {} \; 2>/dev/null | head -5
else
    echo "✓ 警告ファイルなし"
fi

# 5. エラーファイルの確認
echo ""
echo "[5] エラーファイル確認"
error_count=$(find data/history -name "*.error.json" -mtime -1 2>/dev/null | wc -l)
if [ $error_count -gt 0 ]; then
    echo "✗ 過去24時間のエラーファイル: ${error_count}件"
    find data/history -name "*.error.json" -mtime -1 -exec basename {} \; 2>/dev/null | head -5
else
    echo "✓ エラーファイルなし"
fi

echo ""
echo "=== スモークテスト完了 ==="
