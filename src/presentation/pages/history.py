"""履歴ページ"""
import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
from typing import Optional
import asyncio


class HistoryPage:
    """履歴データ表示ページ"""
    
    def __init__(self, monitoring_service=None):
        """
        Args:
            monitoring_service: モニタリングサービス
        """
        self.monitoring_service = monitoring_service
    
    def render(self):
        """ページを描画"""
        st.header("📊 履歴データ")
        
        # 期間選択
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            start_date = st.date_input(
                "開始日",
                value=datetime.now() - timedelta(days=7),
                max_value=datetime.now().date()
            )
        
        with col2:
            end_date = st.date_input(
                "終了日",
                value=datetime.now().date(),
                max_value=datetime.now().date()
            )
        
        with col3:
            if st.button("データ取得", type="primary"):
                self._load_data(start_date, end_date)
        
        # タブ表示
        tab1, tab2, tab3 = st.tabs(["河川水位", "ダム情報", "統計"])
        
        with tab1:
            self._render_water_level_history()
        
        with tab2:
            self._render_dam_history()
        
        with tab3:
            self._render_statistics()
    
    def _load_data(self, start_date, end_date):
        """データを読み込み"""
        with st.spinner("データを取得中..."):
            if self.monitoring_service:
                # サービスからデータ取得
                start_dt = datetime.combine(start_date, datetime.min.time())
                end_dt = datetime.combine(end_date, datetime.max.time())
                
                data = asyncio.run(
                    self.monitoring_service.get_historical_data(
                        start_dt, end_dt
                    )
                )
                st.session_state['history_data'] = data
            else:
                # デモデータを使用
                st.session_state['history_data'] = self._generate_demo_data(
                    start_date, end_date
                )
            
            st.success("データを取得しました")
    
    def _render_water_level_history(self):
        """河川水位履歴を表示"""
        st.subheader("🌊 河川水位（持世寺）の推移")
        
        data = st.session_state.get('history_data')
        if not data:
            st.info("データを取得してください")
            return
        
        # グラフ表示
        if 'water_levels' in data and data['water_levels']:
            df = pd.DataFrame(data['water_levels'])
            
            # チャート表示
            import plotly.graph_objects as go
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df['timestamp'],
                y=df['level'],
                mode='lines+markers',
                name='水位',
                line=dict(color='#1f77b4', width=2)
            ))
            
            # 閾値線
            fig.add_hline(y=3.0, line_dash="dash", line_color="yellow",
                         annotation_text="注意水位")
            fig.add_hline(y=4.0, line_dash="dash", line_color="orange",
                         annotation_text="警戒水位")
            fig.add_hline(y=5.0, line_dash="dash", line_color="red",
                         annotation_text="危険水位")
            
            fig.update_layout(
                title="河川水位の推移",
                xaxis_title="時刻",
                yaxis_title="水位 (m)",
                height=400,
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # データテーブル
            with st.expander("詳細データ"):
                st.dataframe(df, use_container_width=True)
    
    def _render_dam_history(self):
        """ダム情報履歴を表示"""
        st.subheader("🏞️ 厚東川ダムの推移")
        
        data = st.session_state.get('history_data')
        if not data:
            st.info("データを取得してください")
            return
        
        # グラフ表示
        if 'dam_data' in data and data['dam_data']:
            df = pd.DataFrame(data['dam_data'])
            
            # 複数項目のグラフ
            import plotly.graph_objects as go
            from plotly.subplots import make_subplots
            
            fig = make_subplots(
                rows=3, cols=1,
                subplot_titles=('貯水率', '流入量・放流量', '貯水位'),
                shared_xaxes=True,
                vertical_spacing=0.1
            )
            
            # 貯水率
            fig.add_trace(
                go.Scatter(x=df['timestamp'], y=df['storage_rate'],
                          name='貯水率', line=dict(color='#2ca02c')),
                row=1, col=1
            )
            
            # 流入量・放流量
            fig.add_trace(
                go.Scatter(x=df['timestamp'], y=df['inflow'],
                          name='流入量', line=dict(color='#1f77b4')),
                row=2, col=1
            )
            fig.add_trace(
                go.Scatter(x=df['timestamp'], y=df['outflow'],
                          name='放流量', line=dict(color='#ff7f0e')),
                row=2, col=1
            )
            
            # 貯水位
            fig.add_trace(
                go.Scatter(x=df['timestamp'], y=df['water_level'],
                          name='貯水位', line=dict(color='#9467bd')),
                row=3, col=1
            )
            
            # レイアウト更新
            fig.update_yaxes(title_text="貯水率 (%)", row=1, col=1)
            fig.update_yaxes(title_text="流量 (m³/s)", row=2, col=1)
            fig.update_yaxes(title_text="貯水位 (m)", row=3, col=1)
            fig.update_xaxes(title_text="時刻", row=3, col=1)
            
            fig.update_layout(height=700, hovermode='x unified')
            
            st.plotly_chart(fig, use_container_width=True)
            
            # データテーブル
            with st.expander("詳細データ"):
                st.dataframe(df, use_container_width=True)
    
    def _render_statistics(self):
        """統計情報を表示"""
        st.subheader("📈 統計情報")
        
        data = st.session_state.get('history_data')
        if not data:
            st.info("データを取得してください")
            return
        
        # 河川水位統計
        if 'water_levels' in data and data['water_levels']:
            df_water = pd.DataFrame(data['water_levels'])
            
            st.markdown("#### 河川水位統計")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("最高水位", f"{df_water['level'].max():.2f} m")
            with col2:
                st.metric("最低水位", f"{df_water['level'].min():.2f} m")
            with col3:
                st.metric("平均水位", f"{df_water['level'].mean():.2f} m")
            with col4:
                st.metric("標準偏差", f"{df_water['level'].std():.2f} m")
        
        # ダム統計
        if 'dam_data' in data and data['dam_data']:
            df_dam = pd.DataFrame(data['dam_data'])
            
            st.markdown("#### ダム統計")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("最高貯水率", f"{df_dam['storage_rate'].max():.1f} %")
            with col2:
                st.metric("最低貯水率", f"{df_dam['storage_rate'].min():.1f} %")
            with col3:
                st.metric("平均貯水率", f"{df_dam['storage_rate'].mean():.1f} %")
            with col4:
                total_inflow = df_dam['inflow'].sum()
                total_outflow = df_dam['outflow'].sum()
                st.metric("純流入量", f"{(total_inflow - total_outflow):.0f} m³")
    
    def _generate_demo_data(self, start_date, end_date):
        """デモデータを生成"""
        import numpy as np
        
        # 日付範囲を作成
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())
        
        # 10分間隔でデータポイントを作成
        timestamps = pd.date_range(start=start_dt, end=end_dt, freq='10min')
        n_points = len(timestamps)
        
        # ランダムシード設定
        np.random.seed(42)
        
        # 河川水位データ
        water_levels = []
        base_level = 2.5
        for i, ts in enumerate(timestamps):
            level = base_level + np.sin(i * 0.01) * 0.5 + np.random.randn() * 0.2
            water_levels.append({
                'timestamp': ts,
                'level': max(0, level),
                'status': 'normal' if level < 3 else 'warning' if level < 4 else 'danger'
            })
        
        # ダムデータ
        dam_data = []
        base_storage = 65
        for i, ts in enumerate(timestamps):
            storage = base_storage + np.cos(i * 0.005) * 10 + np.random.randn() * 2
            inflow = 10 + np.random.exponential(2)
            outflow = 8 + np.random.exponential(1.5)
            
            dam_data.append({
                'timestamp': ts,
                'storage_rate': max(0, min(100, storage)),
                'water_level': 120 + storage * 0.3,
                'inflow': max(0, inflow),
                'outflow': max(0, outflow)
            })
        
        return {
            'water_levels': water_levels,
            'dam_data': dam_data
        }