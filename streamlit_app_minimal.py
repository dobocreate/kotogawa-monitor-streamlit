#!/usr/bin/env python3
"""
厚東川リアルタイム監視システム - 最小版テスト
"""

import json
import streamlit as st
from pathlib import Path
from datetime import datetime

# ページ設定
st.set_page_config(
    page_title="厚東川監視システム",
    page_icon="🌊",
    layout="wide"
)

def load_latest_data():
    """最新データを読み込む"""
    data_dir = Path(__file__).parent / "data"
    latest_file = data_dir / "latest.json"
    
    if not latest_file.exists():
        return None
    
    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"データ読み込みエラー: {e}")
        return None

def main():
    st.title("🌊 厚東川リアルタイム監視システム - テスト版")
    
    # データ読み込み
    latest_data = load_latest_data()
    
    if latest_data:
        st.success("✅ データ読み込み成功")
        
        # 基本情報表示
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("河川水位", f"{latest_data.get('river', {}).get('water_level', '--')} m")
        
        with col2:
            st.metric("ダム貯水率", f"{latest_data.get('dam', {}).get('storage_rate', '--')} %")
        
        with col3:
            st.metric("時間雨量", f"{latest_data.get('rainfall', {}).get('hourly', '--')} mm")
        
        # JSONデータ表示
        with st.expander("デバッグ: 生データ"):
            st.json(latest_data)
    else:
        st.error("❌ データが読み込めません")

if __name__ == "__main__":
    main()