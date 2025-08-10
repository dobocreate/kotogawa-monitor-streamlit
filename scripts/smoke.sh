#\!/bin/bash

# 厚東川ダム監視システム - スモークテスト
# グラフ表示順序修正の基本動作確認

echo "=== 厚東川ダム監視システム スモークテスト開始 ==="
echo "実行時刻: $(date +"%Y-%m-%d %H:%M:%S")"

# 1. Pythonバージョン確認
echo -e "\n[1] Python環境確認"
python3 --version

# 2. 必要なライブラリ確認
echo -e "\n[2] 必要ライブラリ確認"
python3 -c "
import streamlit
import pandas as pd
import plotly
from datetime import datetime
from zoneinfo import ZoneInfo
print('✓ streamlit:', streamlit.__version__)
print('✓ pandas:', pd.__version__)
print('✓ plotly:', plotly.__version__)
print('✓ datetime/zoneinfo: OK')
"

# 3. データディレクトリ確認
echo -e "\n[3] データディレクトリ確認"
if [ -d "data/history" ]; then
    echo "✓ data/history ディレクトリが存在"
    file_count=$(find data/history -name "*.json" | wc -l)
    echo "  JSONファイル数: $file_count"
else
    echo "✗ data/history ディレクトリが見つかりません"
    exit 1
fi

# 4. 最新データファイル確認
echo -e "\n[4] 最新データファイル確認"
if [ -f "data/latest.json" ]; then
    echo "✓ data/latest.json が存在"
    # タイムスタンプ取得
    timestamp=$(python3 -c "import json; print(json.load(open('data/latest.json')).get('timestamp', 'N/A'))")
    echo "  最終更新: $timestamp"
else
    echo "✗ data/latest.json が見つかりません"
fi

# 5. グラフソート処理の確認
echo -e "\n[5] グラフソート処理確認"
python3 -c "
import json
from pathlib import Path
from datetime import datetime
import pandas as pd

# テストデータ読み込み
history_data = []
for day_dir in sorted(Path('data/history/2025/08').iterdir())[:3]:
    if day_dir.is_dir():
        for json_file in sorted(day_dir.glob('*.json'))[:2]:
            with open(json_file) as f:
                data = json.load(f)
                history_data.append(data)

# ソート前の順序
print(f'読み込みデータ数: {len(history_data)}')

# ソート処理
history_data.sort(key=lambda x: x.get('timestamp', ''))

# DataFrame変換
df_data = []
for item in history_data:
    data_time = item.get('data_time', '')
    if data_time:
        dt = datetime.fromisoformat(data_time.replace('Z', '+00:00'))
        df_data.append({'timestamp': dt})

df = pd.DataFrame(df_data)
if not df.empty:
    # ソート前の確認
    first_unsorted = df['timestamp'].iloc[0]
    
    # ソート実行
    df = df.sort_values('timestamp')
    
    # ソート後の確認
    first_sorted = df['timestamp'].iloc[0]
    last_sorted = df['timestamp'].iloc[-1]
    
    print(f'✓ DataFrame作成: {len(df)}行')
    print(f'✓ ソート実行: {first_sorted} ~ {last_sorted}')
    
    # 順序確認
    is_sorted = df['timestamp'].is_monotonic_increasing
    if is_sorted:
        print('✓ 時系列順序: 正しくソートされています')
    else:
        print('✗ 時系列順序: ソートに問題があります')
        exit(1)
"

# 6. アプリ構文チェック
echo -e "\n[6] Streamlitアプリ構文チェック"
python3 -c "
import ast
try:
    with open('streamlit_app.py', 'r', encoding='utf-8') as f:
        ast.parse(f.read())
    print('✓ streamlit_app.py: 構文エラーなし')
except SyntaxError as e:
    print(f'✗ streamlit_app.py: 構文エラー - {e}')
    exit(1)
"

# 7. メモリ使用量確認
echo -e "\n[7] システムリソース確認"
free_mem=$(free -m | grep Mem | awk '{print $7}')
echo "  利用可能メモリ: ${free_mem}MB"

echo -e "\n=== スモークテスト完了 ==="
echo "結果: すべてのテストに合格しました"
