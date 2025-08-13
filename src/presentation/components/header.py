"""ヘッダーコンポーネント"""
import streamlit as st
from datetime import datetime
from typing import Optional


class Header:
    """アプリケーションヘッダー"""
    
    def __init__(self, title: str = "厚東川監視システム"):
        self.title = title
    
    def render(self, last_update: Optional[datetime] = None):
        """ヘッダーを描画"""
        # カスタムCSS
        st.markdown(self._get_custom_css(), unsafe_allow_html=True)
        
        # タイトル
        st.markdown(f"<h1 style='text-align: center;'>{self.title}</h1>", unsafe_allow_html=True)
        
        # 最終更新時刻
        if last_update:
            st.caption(f"最終更新: {last_update.strftime('%Y-%m-%d %H:%M:%S')}")
    
    def _get_custom_css(self) -> str:
        """カスタムCSSを返す"""
        return """
        <style>
            .main .block-container {
                padding-top: 0rem !important;
                margin-top: 0rem !important;
            }
            
            /* Streamlitのデフォルト上部マージンを除去 */
            .main .block-container > div:first-child {
                margin-top: 0 !important;
                padding-top: 0 !important;
            }
            
            /* ヘッダーのスタイル */
            h1 {
                color: #1f77b4;
                font-size: 2.5rem;
                margin-bottom: 1rem;
            }
        </style>
        """