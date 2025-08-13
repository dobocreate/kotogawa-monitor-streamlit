"""メトリクスカードコンポーネント"""
import streamlit as st
from typing import Optional, Union, Dict, Any
from datetime import datetime


class MetricsCard:
    """メトリクス表示カード"""
    
    def __init__(self, title: str, icon: str = "📊"):
        """
        Args:
            title: カードのタイトル
            icon: アイコン絵文字
        """
        self.title = title
        self.icon = icon
    
    def render(
        self,
        value: Union[float, int, str],
        unit: str = "",
        delta: Optional[Union[float, int]] = None,
        delta_color: str = "normal",
        help_text: Optional[str] = None,
        status: Optional[str] = None
    ):
        """メトリクスカードを描画
        
        Args:
            value: 表示する値
            unit: 単位
            delta: 変化量
            delta_color: 変化量の色 (normal, inverse, off)
            help_text: ヘルプテキスト
            status: ステータス (normal, warning, danger, critical)
        """
        # タイトル表示
        st.markdown(f"### {self.icon} {self.title}")
        
        # ステータスに応じた背景色設定
        if status:
            container = self._get_status_container(status)
        else:
            container = st.container()
        
        with container:
            # メトリクス表示
            display_value = f"{value} {unit}".strip()
            
            if delta is not None:
                delta_display = f"{delta:+.2f} {unit}" if isinstance(delta, (int, float)) else str(delta)
                st.metric(
                    label="",
                    value=display_value,
                    delta=delta_display,
                    delta_color=delta_color,
                    help=help_text
                )
            else:
                st.metric(
                    label="",
                    value=display_value,
                    help=help_text
                )
    
    def render_multiple(self, metrics: Dict[str, Any]):
        """複数のメトリクスを表示
        
        Args:
            metrics: メトリクス辞書 {label: {value, unit, delta, ...}}
        """
        st.markdown(f"### {self.icon} {self.title}")
        
        cols = st.columns(len(metrics))
        for idx, (label, data) in enumerate(metrics.items()):
            with cols[idx]:
                value = data.get('value', 0)
                unit = data.get('unit', '')
                delta = data.get('delta')
                delta_color = data.get('delta_color', 'normal')
                help_text = data.get('help')
                
                display_value = f"{value} {unit}".strip()
                
                if delta is not None:
                    delta_display = f"{delta:+.2f} {unit}" if isinstance(delta, (int, float)) else str(delta)
                    st.metric(
                        label=label,
                        value=display_value,
                        delta=delta_display,
                        delta_color=delta_color,
                        help=help_text
                    )
                else:
                    st.metric(
                        label=label,
                        value=display_value,
                        help=help_text
                    )
    
    def _get_status_container(self, status: str):
        """ステータスに応じたコンテナを取得"""
        status_colors = {
            'normal': '#d4edda',
            'warning': '#fff3cd',
            'danger': '#f8d7da',
            'critical': '#f5c6cb'
        }
        
        color = status_colors.get(status, '#f8f9fa')
        
        # カスタムCSSでスタイリング
        st.markdown(
            f"""
            <style>
            .status-{status} {{
                background-color: {color};
                padding: 1rem;
                border-radius: 0.5rem;
                margin: 0.5rem 0;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )
        
        return st.container()
    
    @staticmethod
    def create_comparison_card(
        title: str,
        current_value: Union[float, int],
        previous_value: Union[float, int],
        unit: str = "",
        icon: str = "📊"
    ):
        """比較用メトリクスカードを作成
        
        Args:
            title: タイトル
            current_value: 現在値
            previous_value: 前回値
            unit: 単位
            icon: アイコン
        """
        card = MetricsCard(title, icon)
        delta = current_value - previous_value
        
        # 変化率を計算
        if previous_value != 0:
            change_rate = (delta / previous_value) * 100
            help_text = f"前回比: {change_rate:+.1f}%"
        else:
            help_text = None
        
        card.render(
            value=current_value,
            unit=unit,
            delta=delta,
            help_text=help_text
        )