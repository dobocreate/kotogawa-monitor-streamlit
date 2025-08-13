"""ダッシュボードページ"""
import streamlit as st
from datetime import datetime, timedelta
import asyncio
from typing import Optional, Dict, Any
import plotly.graph_objects as go
from plotly.subplots import make_subplots


class DashboardPage:
    """メインダッシュボードページ"""
    
    def __init__(self, monitoring_service=None):
        self.monitoring_service = monitoring_service
    
    def render(self):
        """ページを描画"""
        # データ取得（サービスが設定されていれば）
        if self.monitoring_service:
            # 実データモード：サービスからデータを取得
            # monitoring_serviceがasyncの場合とsyncの場合を判別
            if hasattr(self.monitoring_service, 'get_current_data'):
                # HistoryServiceの場合（同期的）
                current_data = self.monitoring_service.get_current_data()
                display_hours = st.session_state.get('display_hours', 24)
                history_data = self.monitoring_service.get_historical_data(display_hours)
                
                # データが取得できなかった場合はデモデータにフォールバック
                if not current_data:
                    current_data = self._get_demo_current_data()
                if not history_data:
                    history_data = self._get_demo_history_data()
            else:
                # 元のMonitoringServiceの場合（非同期）
                current_data = asyncio.run(self.monitoring_service.get_current_status())
                history_data = asyncio.run(self.monitoring_service.get_historical_data())
        else:
            # デモデータを使用
            current_data = self._get_demo_current_data()
            history_data = self._get_demo_history_data()
        
        # 現在の観測状況セクション
        st.markdown("## 現在の観測状況")
        
        # 河川情報と降雨情報を横並びで表示
        river_rain_col1, river_rain_col2 = st.columns(2)
        
        # 河川情報（左側）
        with river_rain_col1:
            self._render_river_info_section(current_data)
        
        # 降雨情報（右側）
        with river_rain_col2:
            self._render_rainfall_section(current_data)
        
        # ダム情報セクション
        st.markdown("### ダム情報")
        self._render_dam_info_section(current_data)
        
        # グラフセクション
        st.markdown("---")
        self._render_charts(history_data)
    
    def _render_river_info_section(self, data: Dict[str, Any]):
        """河川情報セクションを描画（元のUI準拠）"""
        st.markdown("### 河川情報")
        
        # 更新時刻表示
        obs_time = data.get('timestamp', datetime.now())
        obs_time_str = obs_time.strftime("%H:%M") if isinstance(obs_time, datetime) else "--:--"
        st.caption(f"更新時刻 : {obs_time_str}")
        
        # 2列のメトリクス
        col1, col2 = st.columns(2)
        
        with col1:
            # 水位表示
            river_level = data.get('river', {}).get('water_level', 0)
            level_change = data.get('river', {}).get('level_change', 0)
            delta_color = "inverse" if level_change > 0 else "normal"
            st.metric(
                label="水位(m)",
                value=f"{river_level:.2f}",
                delta=f"{level_change:+.2f}" if level_change else None,
                delta_color=delta_color
            )
        
        with col2:
            # 観測地点表示
            location = data.get('river', {}).get('location', '持世寺')
            status = data.get('river', {}).get('status', '正常')
            status_emoji = {
                '正常': '🟢',
                '注意': '🟡',
                '警戒': '🟠',
                '危険': '🔴'
            }.get(status, '⚫')
            st.metric(
                label="観測地点",
                value=location,
                delta=f"{status_emoji} {status}"
            )
    
    def _render_rainfall_section(self, data: Dict[str, Any]):
        """降雨情報セクションを描画（元のUI準拠）"""
        st.markdown("### 降雨情報")
        
        # 更新時刻表示
        obs_time = data.get('timestamp', datetime.now())
        obs_time_str = obs_time.strftime("%H:%M") if isinstance(obs_time, datetime) else "--:--"
        st.caption(f"更新時刻 : {obs_time_str}")
        
        # 2列のメトリクス
        col1, col2 = st.columns(2)
        
        with col1:
            # 60分雨量
            rain_60 = data.get('rainfall', {}).get('hour_60', 0)
            st.metric(
                label="60分雨量",
                value=f"{rain_60} mm"
            )
        
        with col2:
            # 累加雨量
            rain_total = data.get('rainfall', {}).get('cumulative', 0)
            st.metric(
                label="累加雨量",
                value=f"{rain_total} mm"
            )
    
    def _render_dam_info_section(self, data: Dict[str, Any]):
        """ダム情報セクションを描画（元のUI準拠：6列表示）"""
        # 更新時刻表示
        obs_time = data.get('timestamp', datetime.now())
        obs_time_str = obs_time.strftime("%H:%M") if isinstance(obs_time, datetime) else "--:--"
        st.caption(f"更新時刻 : {obs_time_str}")
        
        if data and 'dam' in data:
            dam = data['dam']
            
            # 6列のメトリクス表示
            col1, col2, col3, col4, col5, col6 = st.columns(6)
            
            with col1:
                water_level = dam.get('water_level', 0) if isinstance(dam, dict) else dam.water_level
                st.metric("貯水位(m)", f"{water_level:.2f}")
            
            with col2:
                storage_rate = dam.get('storage_rate', 0) if isinstance(dam, dict) else dam.storage_rate
                st.metric("貯水率(%)", f"{storage_rate:.1f}")
            
            with col3:
                inflow = dam.get('inflow', 0) if isinstance(dam, dict) else dam.inflow
                st.metric("流入量(m³/s)", f"{inflow:.1f}")
            
            with col4:
                outflow = dam.get('outflow', 0) if isinstance(dam, dict) else dam.outflow
                st.metric("放流量(m³/s)", f"{outflow:.1f}")
            
            with col5:
                dam_name = dam.get('name', '厚東川ダム')
                st.metric("ダム名", dam_name)
            
            with col6:
                status = dam.get('status', '正常')
                status_emoji = {
                    '正常': '🟢',
                    '注意': '🟡',
                    '警戒': '🟠',
                    '危険': '🔴'
                }.get(status, '⚫')
                st.metric("状態", f"{status_emoji} {status}")
        else:
            st.info("データを取得中...")
    
    def _render_charts(self, history_data: Dict[str, Any]):
        """グラフを描画（元のUI準拠：5種類のグラフ+タブ機能）"""
        st.markdown("## データ分析")
        
        # セッション状態から表示期間を取得
        display_hours = st.session_state.get('display_hours', 24)
        enable_interaction = st.session_state.get('enable_graph_interaction', False)
        
        # タブによる切り替え
        tab1, tab2 = st.tabs(["グラフ", "データテーブル"])
        
        with tab1:
            self._render_graph_tab(history_data, display_hours, enable_interaction)
        
        with tab2:
            self._render_table_tab(history_data, display_hours)
    
    def _render_graph_tab(self, history_data: Dict[str, Any], display_hours: int, enable_interaction: bool = False):
        """グラフタブを描画（5種類のグラフ、元のUI準拠：2列レイアウト）"""
        if not history_data:
            st.info("履歴データがありません")
            return
        
        # Plotlyの設定（元のstreamlit_app.pyから移植）
        plotly_config = {
            'scrollZoom': enable_interaction,
            'doubleClick': 'reset' if enable_interaction else False,
            'displayModeBar': True,
            'displaylogo': False,
            'responsive': True,
            'modeBarButtonsToRemove': ['lasso2d', 'select2d'] if enable_interaction else ['pan2d', 'zoom2d', 'lasso2d', 'select2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d']
        }
        
        # 2列レイアウトでグラフを表示（元のUIと同じ）
        col1, col2 = st.columns(2)
        
        # 1. 河川水位・全放流量
        with col1:
            st.subheader("河川水位・全放流量")
            fig1 = self._create_river_discharge_chart(history_data)
            if fig1:
                st.plotly_chart(fig1, use_container_width=True, config=plotly_config, key="river_water_level_chart")
        
        # 2. ダム放流量・時間雨量
        with col2:
            st.subheader("ダム放流量・時間雨量")
            fig2 = self._create_dam_rainfall_chart(history_data)
            if fig2:
                st.plotly_chart(fig2, use_container_width=True, config=plotly_config, key="dam_discharge_rainfall_chart")
        
        # 2行目
        col3, col4 = st.columns(2)
        
        # 3. ダム貯水位・時間雨量
        with col3:
            st.subheader("ダム貯水位・時間雨量")
            fig3 = self._create_dam_level_rainfall_chart(history_data)
            if fig3:
                st.plotly_chart(fig3, use_container_width=True, config=plotly_config, key="dam_water_level_chart")
        
        # 4. ダム流入出量・累加雨量
        with col4:
            st.subheader("ダム流入出量・累加雨量")
            fig4 = self._create_inflow_outflow_chart(history_data)
            if fig4:
                st.plotly_chart(fig4, use_container_width=True, config=plotly_config, key="dam_flow_chart")
        
        # 3行目
        col5, col6 = st.columns(2)
        
        # 5. 降水強度・時間雨量
        with col5:
            st.subheader("降水強度・時間雨量")
            fig5 = self._create_rainfall_intensity_chart(history_data)
            if fig5:
                st.plotly_chart(fig5, use_container_width=True, config=plotly_config, key="precipitation_intensity_chart")
        
        with col6:
            # 空白のカラム（将来の拡張用）
            pass
    
    def _render_table_tab(self, history_data: Dict[str, Any], display_hours: int):
        """データテーブルタブを描画（元のUI準拠）"""
        st.subheader("データテーブル")
        
        if not history_data:
            st.info("表示するデータがありません")
            return
        
        # データをDataFrameに変換
        import pandas as pd
        from datetime import datetime
        
        # デモ用の統合データを作成
        table_data = []
        
        # history_dataが辞書の場合とリストの場合を考慮
        if isinstance(history_data, dict):
            # 実データモードまたは新形式（times, river_levels, dam_levelsなど）
            if 'raw_data' in history_data:
                # 実データモード：raw_dataから取得
                for item in history_data['raw_data']:
                    time_str = item.get('data_time', item.get('timestamp', ''))
                    if time_str:
                        try:
                            dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                            time_str = dt.strftime('%Y/%m/%d %H:%M')
                        except:
                            pass
                    
                    table_data.append({
                        '時刻': time_str,
                        '河川水位(m)': item.get('river', {}).get('water_level'),
                        'ダム貯水位(m)': item.get('dam', {}).get('water_level'),
                        '時間雨量(mm)': item.get('rainfall', {}).get('hourly', 0)
                    })
            else:
                # 既存の形式（times, river_levels, dam_levelsなど）
                times = history_data.get('times', [])
                river_levels = history_data.get('river_levels', [])
                dam_levels = history_data.get('dam_levels', [])
                rainfall = history_data.get('hourly_rain', [])
                
                for i in range(min(len(times), len(river_levels))):
                    table_data.append({
                        '時刻': times[i].strftime('%Y/%m/%d %H:%M') if i < len(times) else '',
                        '河川水位(m)': river_levels[i] if i < len(river_levels) else None,
                        'ダム貯水位(m)': dam_levels[i] if i < len(dam_levels) else None,
                        '時間雨量(mm)': rainfall[i] if i < len(rainfall) else None
                    })
        else:
            # リスト形式のデータを想定
            for item in history_data[-100:]:  # 最新100件のみ表示
                if isinstance(item, dict):
                    time_str = item.get('timestamp', '')
                    if time_str:
                        try:
                            dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                            time_str = dt.strftime('%Y/%m/%d %H:%M')
                        except:
                            pass
                    
                    table_data.append({
                        '時刻': time_str,
                        '河川水位(m)': item.get('river', {}).get('water_level'),
                        'ダム貯水位(m)': item.get('dam', {}).get('water_level'),
                        '時間雨量(mm)': item.get('rainfall', {}).get('hourly', 0)
                    })
        
        if table_data:
            df_table = pd.DataFrame(table_data)
            df_table = df_table.iloc[::-1]  # 新しい順に並び替え
            
            # データテーブル表示
            st.dataframe(df_table, use_container_width=True, hide_index=True)
            
            # CSVダウンロードボタン
            csv = df_table.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="CSVダウンロード",
                data=csv,
                file_name=f"kotogawa_data_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )
        else:
            st.info("表示するデータがありません")
    
    def _create_river_discharge_chart(self, data: Dict[str, Any]) -> Optional[go.Figure]:
        """河川水位・全放流量グラフを作成（元のUI準拠）"""
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # デモデータ
        times = data.get('times', [datetime.now() - timedelta(hours=i) for i in range(24, 0, -1)])
        river_levels = data.get('river_levels', [2.5 + i * 0.1 for i in range(24)])
        discharge = data.get('discharge', [10 + i * 0.5 for i in range(24)])
        
        # 河川水位（左軸）
        fig.add_trace(
            go.Scatter(
                x=times, 
                y=river_levels, 
                name='河川水位（持世寺）',
                mode='lines+markers',
                line=dict(color='#1f77b4', width=3),
                marker=dict(size=6, color='white', line=dict(width=2, color='#1f77b4'))
            ),
            secondary_y=False
        )
        
        # 全放流量（右軸）
        fig.add_trace(
            go.Scatter(
                x=times, 
                y=discharge, 
                name='全放流量（厚東川ダム）',
                mode='lines+markers',
                line=dict(color='#d62728', width=3),
                marker=dict(size=6, color='white', line=dict(width=2, color='#d62728'))
            ),
            secondary_y=True
        )
        
        # 氾濫危険水位ライン（5.5m）を追加
        fig.add_hline(
            y=5.5,
            line_dash="dash",
            line_color="red",
            line_width=2,
            secondary_y=False
        )
        
        # 氾濫危険水位のアノテーション
        fig.add_annotation(
            x=0.02,
            y=5.7,
            text="氾濫危険水位 (5.5m)",
            showarrow=False,
            xref="paper",
            yref="y",
            font=dict(color="red", size=12, weight="bold"),
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="red",
            borderwidth=1
        )
        
        # 軸の設定
        fig.update_yaxes(
            title_text="河川水位 (m)",
            range=[0, 6],
            dtick=1,
            secondary_y=False,
            title_font_size=12,
            tickfont_size=12
        )
        fig.update_yaxes(
            title_text="全放流量 (m³/s)",
            range=[0, 900],
            dtick=150,
            secondary_y=True,
            title_font_size=12,
            tickfont_size=12
        )
        
        fig.update_xaxes(
            title_text="時刻",
            title_font_size=12,
            tickfont_size=12
        )
        
        fig.update_layout(
            height=465,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.30,
                xanchor="left",
                x=0.0,
                bgcolor="rgba(255, 255, 255, 0.8)",
                bordercolor="rgba(0, 0, 0, 0.2)",
                borderwidth=1
            ),
            margin=dict(t=30, l=40, r=40, b=140),
            autosize=True,
            font=dict(size=9),
            hovermode='x unified'
        )
        
        return fig
    
    def _create_dam_rainfall_chart(self, data: Dict[str, Any]) -> Optional[go.Figure]:
        """ダム放流量・時間雨量グラフを作成（元のUI準拠）"""
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # デモデータ
        times = data.get('times', [datetime.now() - timedelta(hours=i) for i in range(24, 0, -1)])
        discharge = data.get('dam_discharge', [15 + i * 0.3 for i in range(24)])
        rainfall = data.get('hourly_rain', [0, 0, 5, 10, 15, 10, 5, 0] * 3)
        
        # ダム放流量（左軸）
        fig.add_trace(
            go.Scatter(
                x=times, 
                y=discharge, 
                name='ダム放流量',
                mode='lines+markers',
                line=dict(color='#ff7f0e', width=3),
                marker=dict(size=6, color='white', line=dict(width=2, color='#ff7f0e'))
            ),
            secondary_y=False
        )
        
        # 時間雨量（右軸・棒グラフ）
        fig.add_trace(
            go.Bar(
                x=times, 
                y=rainfall, 
                name='時間雨量',
                marker_color='rgba(135, 206, 235, 0.7)',
                marker_line_color='rgba(135, 206, 235, 1)',
                marker_line_width=1
            ),
            secondary_y=True
        )
        
        # 軸の設定
        fig.update_yaxes(
            title_text="放流量 (m³/s)",
            range=[0, 900],
            dtick=150,
            secondary_y=False,
            title_font_size=12,
            tickfont_size=12
        )
        fig.update_yaxes(
            title_text="雨量 (mm)",
            range=[0, 100],
            dtick=20,
            secondary_y=True,
            title_font_size=12,
            tickfont_size=12
        )
        
        fig.update_xaxes(
            title_text="時刻",
            title_font_size=12,
            tickfont_size=12
        )
        
        fig.update_layout(
            height=465,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.30,
                xanchor="left",
                x=0.0,
                bgcolor="rgba(255, 255, 255, 0.8)",
                bordercolor="rgba(0, 0, 0, 0.2)",
                borderwidth=1
            ),
            margin=dict(t=30, l=40, r=40, b=140),
            autosize=True,
            font=dict(size=9),
            hovermode='x unified',
            bargap=0.2
        )
        
        return fig
    
    def _create_dam_level_rainfall_chart(self, data: Dict[str, Any]) -> Optional[go.Figure]:
        """ダム貯水位・時間雨量グラフを作成（元のUI準拠）"""
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # デモデータ
        times = data.get('times', [datetime.now() - timedelta(hours=i) for i in range(24, 0, -1)])
        dam_level = data.get('dam_levels', [35 + i * 0.05 for i in range(24)])
        rainfall = data.get('hourly_rain', [0, 0, 5, 10, 15, 10, 5, 0] * 3)
        
        # ダム貯水位（左軸）
        fig.add_trace(
            go.Scatter(
                x=times, 
                y=dam_level, 
                name='ダム貯水位',
                mode='lines+markers',
                line=dict(color='#2ca02c', width=3),
                marker=dict(size=6, color='white', line=dict(width=2, color='#2ca02c'))
            ),
            secondary_y=False
        )
        
        # 時間雨量（右軸・棒グラフ）
        fig.add_trace(
            go.Bar(
                x=times, 
                y=rainfall, 
                name='時間雨量',
                marker_color='rgba(135, 206, 235, 0.7)',
                marker_line_color='rgba(135, 206, 235, 1)',
                marker_line_width=1
            ),
            secondary_y=True
        )
        
        # 警戒・危険水位ライン
        dam_warning = st.session_state.get('dam_warning', 39.2)
        dam_danger = st.session_state.get('dam_danger', 40.0)
        
        # 警戒水位ライン
        fig.add_hline(
            y=dam_warning,
            line_dash="dash",
            line_color="orange",
            line_width=2,
            secondary_y=False
        )
        
        # 危険水位ライン
        fig.add_hline(
            y=dam_danger,
            line_dash="dash",
            line_color="red",
            line_width=2,
            secondary_y=False
        )
        
        # 軸の設定
        fig.update_yaxes(
            title_text="貯水位 (m)",
            range=[25, 42],
            dtick=2,
            secondary_y=False,
            title_font_size=12,
            tickfont_size=12
        )
        fig.update_yaxes(
            title_text="雨量 (mm)",
            range=[0, 100],
            dtick=20,
            secondary_y=True,
            title_font_size=12,
            tickfont_size=12
        )
        
        fig.update_xaxes(
            title_text="時刻",
            title_font_size=12,
            tickfont_size=12
        )
        
        fig.update_layout(
            height=465,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.30,
                xanchor="left",
                x=0.0,
                bgcolor="rgba(255, 255, 255, 0.8)",
                bordercolor="rgba(0, 0, 0, 0.2)",
                borderwidth=1
            ),
            margin=dict(t=30, l=40, r=40, b=140),
            autosize=True,
            font=dict(size=9),
            hovermode='x unified',
            bargap=0.2
        )
        
        return fig
    
    def _create_inflow_outflow_chart(self, data: Dict[str, Any]) -> Optional[go.Figure]:
        """ダム流入出量・累加雨量グラフを作成（元のUI準拠）"""
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # デモデータ
        times = data.get('times', [datetime.now() - timedelta(hours=i) for i in range(24, 0, -1)])
        inflow = data.get('inflow', [12 + i * 0.4 for i in range(24)])
        outflow = data.get('outflow', [10 + i * 0.3 for i in range(24)])
        cumulative_rain = data.get('cumulative_rain', [i * 2 for i in range(24)])
        
        # 流入量（左軸）
        fig.add_trace(
            go.Scatter(
                x=times, 
                y=inflow, 
                name='流入量',
                mode='lines+markers',
                line=dict(color='#1f77b4', width=3),
                marker=dict(size=6, color='white', line=dict(width=2, color='#1f77b4'))
            ),
            secondary_y=False
        )
        
        # 放流量（左軸）
        fig.add_trace(
            go.Scatter(
                x=times, 
                y=outflow, 
                name='全放流量',
                mode='lines+markers',
                line=dict(color='#d62728', width=3),
                marker=dict(size=6, color='white', line=dict(width=2, color='#d62728'))
            ),
            secondary_y=False
        )
        
        # 累加雨量（右軸）
        fig.add_trace(
            go.Scatter(
                x=times, 
                y=cumulative_rain, 
                name='累加雨量',
                mode='lines',
                line=dict(color='rgba(135, 206, 235, 0.8)', width=2),
                fill='tozeroy',
                fillcolor='rgba(135, 206, 235, 0.3)'
            ),
            secondary_y=True
        )
        
        # 軸の設定
        fig.update_yaxes(
            title_text="流量 (m³/s)",
            range=[0, 900],
            dtick=150,
            secondary_y=False,
            title_font_size=12,
            tickfont_size=12
        )
        fig.update_yaxes(
            title_text="累加雨量 (mm)",
            range=[0, 500],
            dtick=100,
            secondary_y=True,
            title_font_size=12,
            tickfont_size=12
        )
        
        fig.update_xaxes(
            title_text="時刻",
            title_font_size=12,
            tickfont_size=12
        )
        
        fig.update_layout(
            height=465,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.30,
                xanchor="left",
                x=0.0,
                bgcolor="rgba(255, 255, 255, 0.8)",
                bordercolor="rgba(0, 0, 0, 0.2)",
                borderwidth=1
            ),
            margin=dict(t=30, l=40, r=40, b=140),
            autosize=True,
            font=dict(size=9),
            hovermode='x unified'
        )
        
        return fig
    
    def _create_rainfall_intensity_chart(self, data: Dict[str, Any]) -> Optional[go.Figure]:
        """降水強度・時間雨量グラフを作成（元のUI準拠）"""
        fig = make_subplots(specs=[[{"secondary_y": False}]])
        
        # デモデータ
        times = data.get('times', [datetime.now() - timedelta(hours=i) for i in range(24, 0, -1)])
        intensity = data.get('intensity', [0, 0, 5, 10, 20, 15, 10, 5] * 3)
        hourly_rain = data.get('hourly_rain', [0, 0, 5, 10, 15, 10, 5, 0] * 3)
        
        # 時間雨量（棒グラフ）
        fig.add_trace(
            go.Bar(
                x=times, 
                y=hourly_rain, 
                name='時間雨量（観測）',
                marker_color='rgba(135, 206, 235, 0.7)',
                marker_line_color='rgba(135, 206, 235, 1)',
                marker_line_width=1
            )
        )
        
        # 降水強度（線グラフ）※予測データがある場合
        if intensity:
            fig.add_trace(
                go.Scatter(
                    x=times, 
                    y=intensity, 
                    name='降水強度（予測）',
                    mode='lines+markers',
                    line=dict(color='#ff7f0e', width=2, dash='dash'),
                    marker=dict(size=6, color='white', line=dict(width=2, color='#ff7f0e'))
                )
            )
        
        # 軸の設定
        fig.update_yaxes(
            title_text="雨量 (mm)",
            range=[0, 100],
            dtick=20,
            title_font_size=12,
            tickfont_size=12
        )
        
        fig.update_xaxes(
            title_text="時刻",
            title_font_size=12,
            tickfont_size=12
        )
        
        # 現在時刻の縦線を追加
        fig.add_vline(
            x=datetime.now().timestamp() * 1000,
            line_dash="dash",
            line_color="gray",
            line_width=1,
            annotation_text="現在",
            annotation_position="top"
        )
        
        fig.update_layout(
            height=465,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.30,
                xanchor="left",
                x=0.0,
                bgcolor="rgba(255, 255, 255, 0.8)",
                bordercolor="rgba(0, 0, 0, 0.2)",
                borderwidth=1
            ),
            margin=dict(t=30, l=40, r=40, b=140),
            autosize=True,
            font=dict(size=9),
            hovermode='x unified',
            bargap=0.2
        )
        
        return fig
    
    
    def _get_demo_current_data(self) -> Dict[str, Any]:
        """デモ用の現在データを生成"""
        from datetime import datetime
        
        return {
            'timestamp': datetime.now(),
            'river': {
                'water_level': 2.45,
                'level_change': 0.05,
                'status': '正常',
                'location': '持世寺',
            },
            'rainfall': {
                'hour_60': 0,
                'cumulative': 10
            },
            'dam': {
                'storage_rate': 75.3,
                'water_level': 35.2,
                'inflow': 12.5,
                'outflow': 10.0,
                'name': '厚東川ダム',
                'status': '正常',
                'status': 'normal',
                'name': '厚東川ダム'
            },
            'alerts': [],
            'status': 'normal'
        }
    
    def _get_demo_history_data(self) -> Dict[str, Any]:
        """デモ用の履歴データを生成"""
        from datetime import datetime, timedelta
        import random
        
        # 仮想的な水位エンティティクラス
        class DemoWaterLevel:
            def __init__(self, time, level):
                self.observation_time = time
                self.level = level
        
        class DemoDam:
            def __init__(self, time, rate):
                self.observation_time = time
                self.storage_rate = rate
        
        now = datetime.now()
        water_levels = []
        dam_data = []
        
        for hours_ago in range(24, 0, -1):
            time = now - timedelta(hours=hours_ago)
            
            # 水位データ（ランダムに生成）
            level = 2.0 + random.uniform(-0.5, 0.5) + (24 - hours_ago) * 0.01
            water_levels.append(DemoWaterLevel(time, level))
            
            # ダムデータ（ランダムに生成）
            rate = 70.0 + random.uniform(-5, 5) + (24 - hours_ago) * 0.2
            dam_data.append(DemoDam(time, rate))
        
        return {
            'water_levels': water_levels,
            'dam_data': dam_data
        }