#!/bin/bash
# 時系列ソート処理最適化リファクタリング検証スクリプト

echo "================================"
echo "リファクタリング検証開始"
echo "================================"

# Python構文チェック
echo ""
echo "1. Python構文チェック..."
python3 -m py_compile streamlit_app.py
if [ $? -eq 0 ]; then
    echo "✓ 構文チェック: OK"
else
    echo "✗ 構文チェック: エラー"
    exit 1
fi

# インポートチェック
echo ""
echo "2. インポートチェック..."
python3 -c "import streamlit_app" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✓ インポート: OK"
else
    echo "✗ インポート: エラー"
    exit 1
fi

# 基本的な機能チェック
echo ""
echo "3. 基本機能チェック..."
python3 -c "
import sys
sys.path.insert(0, '.')
from streamlit_app import KotogawaMonitorApp
app = KotogawaMonitorApp()
print('✓ KotogawaMonitorAppインスタンス生成: OK')

# load_history_dataメソッドの存在確認
if hasattr(app, 'load_history_data'):
    print('✓ load_history_dataメソッド: 存在')
else:
    print('✗ load_history_dataメソッド: 不在')
    sys.exit(1)

# 各グラフメソッドの存在確認
methods = [
    'create_river_water_level_graph',
    'create_dam_water_level_graph',
    'create_dam_discharge_rainfall_graph',
    'create_dam_flow_graph'
]

for method in methods:
    if hasattr(app, method):
        print(f'✓ {method}メソッド: 存在')
    else:
        print(f'✗ {method}メソッド: 不在')
        sys.exit(1)
"

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ 基本機能チェック: 完了"
else
    echo ""
    echo "✗ 基本機能チェック: エラー"
    exit 1
fi

# ソート処理の確認
echo ""
echo "4. ソート処理の重複チェック..."
echo ""

# load_history_dataのソート処理
echo "load_history_data()内のソート:"
grep -n "history_data.sort\|df.sort_values\|sort_values" streamlit_app.py | grep -A2 -B2 "load_history_data" | grep "sort" || echo "（該当なし）"

# 各グラフメソッドのソート処理
echo ""
echo "create_river_water_level_graph()内のソート:"
sed -n '/def create_river_water_level_graph/,/def [a-z]/p' streamlit_app.py | grep -n "sort_values" || echo "（該当なし）"

echo ""
echo "create_dam_water_level_graph()内のソート:"
sed -n '/def create_dam_water_level_graph/,/def [a-z]/p' streamlit_app.py | grep -n "sort_values" || echo "（該当なし）"

echo ""
echo "create_dam_discharge_rainfall_graph()内のソート:"
sed -n '/def create_dam_discharge_rainfall_graph/,/def [a-z]/p' streamlit_app.py | grep -n "sort_values" || echo "（該当なし）"

echo ""
echo "create_dam_flow_graph()内のソート:"
sed -n '/def create_dam_flow_graph/,/def [a-z]/p' streamlit_app.py | grep -n "sort_values" || echo "（該当なし）"

echo ""
echo "================================"
echo "検証完了"
echo "================================"