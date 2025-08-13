"""アラートバナーコンポーネント"""
import streamlit as st
from typing import List, Optional
from datetime import datetime


class AlertBanner:
    """アラート表示バナー"""
    
    def render(self, alerts: Optional[List] = None):
        """アラートバナーを描画"""
        if not alerts:
            return
        
        # 重要度の高いアラートから表示
        critical_alerts = [a for a in alerts if a.get('level') == 'critical']
        danger_alerts = [a for a in alerts if a.get('level') == 'danger']
        warning_alerts = [a for a in alerts if a.get('level') == 'warning']
        
        # Critical アラート
        for alert in critical_alerts:
            st.error(f"⚠️ **緊急** {alert.get('message', '')}")
        
        # Danger アラート
        for alert in danger_alerts:
            st.warning(f"⚠️ **危険** {alert.get('message', '')}")
        
        # Warning アラート
        for alert in warning_alerts:
            st.info(f"ℹ️ **注意** {alert.get('message', '')}")
    
    def _format_alert_message(self, alert: dict) -> str:
        """アラートメッセージをフォーマット"""
        location = alert.get('location', '')
        message = alert.get('message', '')
        value = alert.get('value', '')
        
        if location:
            return f"[{location}] {message}"
        return message