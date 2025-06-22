import streamlit as st
import json
from pathlib import Path

# Simple test app
st.title("🌊 厚東川監視システム - テスト版")

# Test data loading
try:
    data_file = Path("data/latest.json")
    if data_file.exists():
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        st.success("✅ データ読み込み成功")
        st.json(data)
        
        # Simple metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            river_level = data.get('river', {}).get('water_level')
            st.metric("河川水位 (m)", f"{river_level:.2f}" if river_level else "--")
        
        with col2:
            dam_level = data.get('dam', {}).get('water_level')
            st.metric("ダム水位 (m)", f"{dam_level:.2f}" if dam_level else "--")
        
        with col3:
            storage_rate = data.get('dam', {}).get('storage_rate')
            st.metric("貯水率 (%)", f"{storage_rate:.1f}" if storage_rate else "--")
            
    else:
        st.error("❌ データファイルが見つかりません")
        st.write(f"探しているファイル: {data_file.absolute()}")
        
except Exception as e:
    st.error(f"❌ エラー: {e}")
    import traceback
    st.code(traceback.format_exc())

st.write("---")
st.write("テストが成功したら、メインアプリに戻してください")