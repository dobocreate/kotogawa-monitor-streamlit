"""
状態表示バーコンポーネント
システムの現在の状態、最終更新時刻、API取得時刻を3列で表示
"""

import streamlit as st
from datetime import datetime
from typing import Optional, Dict, Any


class StatusBar:
    """状態表示バーコンポーネント"""
    
    def __init__(self):
        """初期化"""
        self.status_icons = {
            '正常': '🟢',
            '注意': '🟡',
            '警戒': '🟠',
            '危険': '🔴',
            '不明': '⚫'
        }
    
    def render(self, 
               status: str = '正常',
               last_update: Optional[datetime] = None,
               api_fetch_time: Optional[datetime] = None,
               alerts: Optional[Dict[str, Any]] = None):
        """
        状態表示バーを描画
        
        Args:
            status: システムの現在状態
            last_update: 最終更新時刻
            api_fetch_time: API取得時刻
            alerts: アラート情報の辞書
        """
        # 3列レイアウト作成
        col1, col2, col3 = st.columns(3)
        
        # 状態表示
        with col1:
            icon = self.status_icons.get(status, '⚫')
            if status == '正常':
                st.success(f"{icon} 現在の状況: {status}")
            elif status == '危険':
                st.error(f"{icon} 現在の状況: {status}")
            elif status in ['警戒', '注意']:
                st.warning(f"{icon} 現在の状況: {status}")
            else:
                st.info(f"{icon} 現在の状況: {status}")
        
        # 最終更新時刻
        with col2:
            if last_update:
                time_str = last_update.strftime("%H:%M")
                st.info(f"🕐 最終更新: {time_str}")
            else:
                st.info("🕐 最終更新: --:--")
        
        # API取得時刻
        with col3:
            if api_fetch_time:
                time_str = api_fetch_time.strftime("%H:%M")
                st.info(f"📡 API取得: {time_str}")
            else:
                st.info("📡 API取得: --:--")
    
    def determine_status(self, data: Dict[str, Any]) -> str:
        """
        データから現在の状態を判定
        
        Args:
            data: 監視データ
            
        Returns:
            状態文字列
        """
        if not data:
            return '不明'
        
        # 河川水位による判定
        river_level = data.get('river', {}).get('level')
        if river_level:
            if river_level >= 5.0:
                return '危険'
            elif river_level >= 3.0:
                return '警戒'
            elif river_level >= 2.0:
                return '注意'
        
        # ダム貯水率による判定
        dam_rate = data.get('dam', {}).get('storage_rate')
        if dam_rate:
            if dam_rate >= 95.0:
                return '危険'
            elif dam_rate >= 90.0:
                return '警戒'
            elif dam_rate >= 85.0:
                return '注意'
        
        # 降雨量による判定
        rainfall = data.get('rainfall', {}).get('hour_60')
        if rainfall:
            if rainfall >= 50:
                return '危険'
            elif rainfall >= 30:
                return '警戒'
            elif rainfall >= 20:
                return '注意'
        
        return '正常'