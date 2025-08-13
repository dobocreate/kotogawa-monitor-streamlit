"""チャートコンポーネント"""
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import pandas as pd


class TimeSeriesChart:
    """時系列チャートコンポーネント"""
    
    def __init__(self, title: str = "時系列データ", height: int = 400):
        """
        Args:
            title: チャートタイトル
            height: チャートの高さ
        """
        self.title = title
        self.height = height
    
    def render_single(
        self,
        data: pd.DataFrame,
        x_column: str,
        y_column: str,
        y_label: str = "値",
        color: str = "#1f77b4",
        show_markers: bool = True
    ):
        """単一系列のチャートを描画
        
        Args:
            data: データフレーム
            x_column: X軸のカラム名
            y_column: Y軸のカラム名
            y_label: Y軸のラベル
            color: 線の色
            show_markers: マーカー表示
        """
        if data is None or data.empty:
            st.info("表示するデータがありません")
            return
        
        fig = go.Figure()
        
        # データ追加
        fig.add_trace(go.Scatter(
            x=data[x_column],
            y=data[y_column],
            mode='lines+markers' if show_markers else 'lines',
            name=y_label,
            line=dict(color=color, width=2),
            marker=dict(size=6) if show_markers else None
        ))
        
        # レイアウト設定
        fig.update_layout(
            title=self.title,
            xaxis_title="時刻",
            yaxis_title=y_label,
            height=self.height,
            hovermode='x unified',
            showlegend=False
        )
        
        # グリッド表示
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
        
        st.plotly_chart(fig, use_container_width=True)
    
    def render_multiple(
        self,
        data: pd.DataFrame,
        x_column: str,
        y_columns: List[str],
        y_labels: Optional[List[str]] = None,
        colors: Optional[List[str]] = None,
        show_markers: bool = True
    ):
        """複数系列のチャートを描画
        
        Args:
            data: データフレーム
            x_column: X軸のカラム名
            y_columns: Y軸のカラム名リスト
            y_labels: Y軸のラベルリスト
            colors: 線の色リスト
            show_markers: マーカー表示
        """
        if data is None or data.empty:
            st.info("表示するデータがありません")
            return
        
        # デフォルト値設定
        if y_labels is None:
            y_labels = y_columns
        if colors is None:
            colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
        
        fig = go.Figure()
        
        # 各系列を追加
        for idx, (col, label) in enumerate(zip(y_columns, y_labels)):
            if col in data.columns:
                fig.add_trace(go.Scatter(
                    x=data[x_column],
                    y=data[col],
                    mode='lines+markers' if show_markers else 'lines',
                    name=label,
                    line=dict(color=colors[idx % len(colors)], width=2),
                    marker=dict(size=6) if show_markers else None
                ))
        
        # レイアウト設定
        fig.update_layout(
            title=self.title,
            xaxis_title="時刻",
            yaxis_title="値",
            height=self.height,
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        # グリッド表示
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
        
        st.plotly_chart(fig, use_container_width=True)
    
    def render_with_threshold(
        self,
        data: pd.DataFrame,
        x_column: str,
        y_column: str,
        thresholds: Dict[str, float],
        y_label: str = "値",
        color: str = "#1f77b4"
    ):
        """閾値線付きチャートを描画
        
        Args:
            data: データフレーム
            x_column: X軸のカラム名
            y_column: Y軸のカラム名
            thresholds: 閾値辞書 {label: value}
            y_label: Y軸のラベル
            color: 線の色
        """
        if data is None or data.empty:
            st.info("表示するデータがありません")
            return
        
        fig = go.Figure()
        
        # データ追加
        fig.add_trace(go.Scatter(
            x=data[x_column],
            y=data[y_column],
            mode='lines+markers',
            name=y_label,
            line=dict(color=color, width=2),
            marker=dict(size=6)
        ))
        
        # 閾値線を追加
        threshold_colors = {
            '注意': '#ffc107',
            '警戒': '#ff9800',
            '危険': '#f44336',
            'warning': '#ffc107',
            'danger': '#ff9800',
            'critical': '#f44336'
        }
        
        for label, value in thresholds.items():
            line_color = threshold_colors.get(label.lower(), '#808080')
            fig.add_hline(
                y=value,
                line_dash="dash",
                line_color=line_color,
                annotation_text=f"{label}: {value}",
                annotation_position="right"
            )
        
        # レイアウト設定
        fig.update_layout(
            title=self.title,
            xaxis_title="時刻",
            yaxis_title=y_label,
            height=self.height,
            hovermode='x unified',
            showlegend=True
        )
        
        # グリッド表示
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
        
        st.plotly_chart(fig, use_container_width=True)
    
    @staticmethod
    def create_subplot_chart(
        data: pd.DataFrame,
        x_column: str,
        subplot_configs: List[Dict[str, Any]],
        title: str = "複合チャート",
        height: int = 600
    ):
        """サブプロット付きチャートを作成
        
        Args:
            data: データフレーム
            x_column: X軸のカラム名
            subplot_configs: サブプロット設定リスト
            title: チャートタイトル
            height: チャートの高さ
        """
        if data is None or data.empty:
            st.info("表示するデータがありません")
            return
        
        # サブプロット作成
        fig = make_subplots(
            rows=len(subplot_configs),
            cols=1,
            subplot_titles=[cfg.get('title', '') for cfg in subplot_configs],
            shared_xaxes=True,
            vertical_spacing=0.1
        )
        
        # 各サブプロットにデータ追加
        for idx, config in enumerate(subplot_configs, 1):
            y_column = config.get('y_column')
            if y_column and y_column in data.columns:
                fig.add_trace(
                    go.Scatter(
                        x=data[x_column],
                        y=data[y_column],
                        mode='lines+markers',
                        name=config.get('label', y_column),
                        line=dict(
                            color=config.get('color', '#1f77b4'),
                            width=2
                        ),
                        marker=dict(size=6)
                    ),
                    row=idx,
                    col=1
                )
                
                # Y軸ラベル設定
                fig.update_yaxes(
                    title_text=config.get('y_label', ''),
                    row=idx,
                    col=1
                )
        
        # レイアウト設定
        fig.update_layout(
            title=title,
            height=height,
            hovermode='x unified',
            showlegend=True
        )
        
        # X軸ラベル（最下段のみ）
        fig.update_xaxes(title_text="時刻", row=len(subplot_configs), col=1)
        
        st.plotly_chart(fig, use_container_width=True)
    
    @staticmethod
    def create_demo_data(hours: int = 24) -> pd.DataFrame:
        """デモ用データを生成
        
        Args:
            hours: データ期間（時間）
        
        Returns:
            デモデータのDataFrame
        """
        import numpy as np
        
        # 時刻データ生成
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        time_range = pd.date_range(start=start_time, end=end_time, freq='10min')
        
        # ランダムデータ生成
        np.random.seed(42)
        n_points = len(time_range)
        
        data = pd.DataFrame({
            'timestamp': time_range,
            'water_level': 2.5 + np.random.randn(n_points) * 0.3 + np.sin(np.linspace(0, 4*np.pi, n_points)) * 0.5,
            'dam_storage': 65 + np.random.randn(n_points) * 2 + np.cos(np.linspace(0, 2*np.pi, n_points)) * 5,
            'inflow': 10 + np.random.exponential(2, n_points),
            'outflow': 8 + np.random.exponential(1.5, n_points)
        })
        
        return data