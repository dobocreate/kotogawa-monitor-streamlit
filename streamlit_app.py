#!/usr/bin/env python3
"""
厚東川リアルタイム監視システム - Streamlitアプリケーション
山口県宇部市の厚東川ダムおよび厚東川（持世寺）の監視データを表示
"""

import json
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
try:
    from zoneinfo import ZoneInfo
except ImportError:
    # Python 3.8以前の場合
    import pytz
    ZoneInfo = lambda x: pytz.timezone(x)
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

# ページ設定
st.set_page_config(
    page_title="厚東川監視システム",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

class KotogawaMonitor:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.data_dir = self.base_dir / "data"
        self.history_dir = self.data_dir / "history"
        
        # アラート閾値（デフォルト値）
        self.default_thresholds = {
            'river_warning': 3.0,
            'river_danger': 5.0,
            'dam_warning': 90.0,
            'dam_danger': 95.0
        }
    
    def load_latest_data(_self) -> Optional[Dict[str, Any]]:
        """最新データを読み込む（ファイル更新時刻ベースのキャッシュ）"""
        latest_file = _self.data_dir / "latest.json"
        
        if not latest_file.exists():
            st.warning("⚠️ データファイルが見つかりません。データ収集スクリプトを実行してください。")
            return None
        
        try:
            # ファイル更新時刻をキャッシュキーとして使用
            file_mtime = latest_file.stat().st_mtime
            return _self._load_latest_data_cached(str(latest_file), file_mtime)
        except Exception as e:
            st.error(f"❌ データ読み込みエラー: {e}")
            return None
    
    @st.cache_data(ttl=300)  # ファイル更新時刻が変わるまでキャッシュ
    def _load_latest_data_cached(_self, file_path: str, file_mtime: float) -> Optional[Dict[str, Any]]:
        """ファイル更新時刻をキーとするキャッシュされたデータ読み込み"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # データの整合性チェック
                if not data or 'timestamp' not in data:
                    st.error("❌ データファイルの形式が正しくありません")
                    return None
                
                return data
        except json.JSONDecodeError as e:
            st.error(f"❌ JSONファイルの形式エラー: {e}")
            return None
        except FileNotFoundError:
            st.warning("⚠️ データファイルが見つかりません")
            return None
        except Exception as e:
            st.error(f"❌ データ読み込みエラー: {e}")
            return None
    
    def get_cache_key(self) -> str:
        """キャッシュキー用の最新ファイル時刻を取得"""
        try:
            # latest.jsonの更新時刻を取得
            latest_file = self.data_dir / "latest.json"
            if latest_file.exists():
                return str(latest_file.stat().st_mtime)
            return "no_file"
        except Exception:
            return "error"
    
    @st.cache_data(ttl=300)  # 5分間キャッシュ（短縮）
    def load_history_data(_self, hours: int = 24, cache_key: str = None) -> List[Dict[str, Any]]:
        """履歴データを読み込む"""
        history_data = []
        # JST（日本標準時）で現在時刻を取得
        end_time = datetime.now(ZoneInfo('Asia/Tokyo'))
        start_time = end_time - timedelta(hours=hours)
        
        if not _self.history_dir.exists():
            st.info("📁 履歴データディレクトリがありません。データが蓄積されるまでお待ちください。")
            return history_data
        
        error_count = 0
        processed_files = 0
        max_files = 100  # 最大処理ファイル数制限
        
        # JST時刻で日付ディレクトリを処理（新しいデータから逆順で処理）
        current_time = end_time
        while current_time >= start_time and processed_files < max_files:
            date_dir = (_self.history_dir / 
                       current_time.strftime("%Y") / 
                       current_time.strftime("%m") / 
                       current_time.strftime("%d"))
            
            if date_dir.exists():
                # ファイルを降順でソートして新しいものから処理
                json_files = sorted(date_dir.glob("*.json"), reverse=True)
                for file_path in json_files:
                    if processed_files >= max_files:
                        break
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            
                            # データの基本検証とJST時刻での範囲チェック
                            if data and 'timestamp' in data:
                                # タイムスタンプをJSTで解析
                                try:
                                    data_timestamp = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
                                    if data_timestamp.tzinfo is None:
                                        data_timestamp = data_timestamp.replace(tzinfo=ZoneInfo('Asia/Tokyo'))
                                    else:
                                        data_timestamp = data_timestamp.astimezone(ZoneInfo('Asia/Tokyo'))
                                    
                                    # 指定期間内のデータのみ追加
                                    if start_time <= data_timestamp <= end_time:
                                        history_data.append(data)
                                        processed_files += 1
                                    
                                except Exception as e:
                                    # タイムスタンプ解析エラーの場合も追加（後方互換性）
                                    history_data.append(data)
                                    processed_files += 1
                            else:
                                error_count += 1
                                
                    except json.JSONDecodeError:
                        error_count += 1
                        if error_count <= 3:  # 最初の3回だけ警告表示
                            st.warning(f"⚠️ 破損した履歴ファイル: {file_path.name}")
                    except Exception as e:
                        error_count += 1
                        if error_count <= 3:
                            st.warning(f"⚠️ 履歴データエラー: {file_path.name}")
            
            current_time -= timedelta(days=1)
        
        # エラーサマリー表示
        if error_count > 3:
            st.warning(f"⚠️ 履歴データの読み込みで {error_count} 件のエラーがありました")
        
        # 時系列順にソート
        try:
            history_data.sort(key=lambda x: x.get('timestamp', ''))
        except Exception as e:
            st.error(f"❌ 履歴データソートエラー: {e}")
            
        return history_data
    
    def check_alert_status(self, data: Dict[str, Any], thresholds: Dict[str, float]) -> Dict[str, str]:
        """アラート状態をチェック"""
        alerts = {
            'river': '正常',
            'dam': '正常',
            'rainfall': '正常',
            'overall': '正常'
        }
        
        if not data:
            alerts['overall'] = 'データなし'
            return alerts
        
        alert_level = 0  # 0=正常, 1=注意, 2=警戒, 3=危険
        
        # 河川水位チェック（実際のステータスを使用）
        river_status = data.get('river', {}).get('status', '正常')
        river_level = data.get('river', {}).get('water_level')
        
        if river_status in ['氾濫危険']:
            alerts['river'] = '危険'
            alert_level = max(alert_level, 3)
        elif river_status in ['避難判断']:
            alerts['river'] = '避難判断'
            alert_level = max(alert_level, 3)
        elif river_status in ['氾濫注意']:
            alerts['river'] = '警戒'
            alert_level = max(alert_level, 2)
        elif river_status in ['水防団待機']:
            alerts['river'] = '注意'
            alert_level = max(alert_level, 1)
        else:
            alerts['river'] = '正常'
        
        # ダム水位チェック
        dam_level = data.get('dam', {}).get('water_level')
        
        if dam_level is not None:
            # ダム水位による判定
            if dam_level >= thresholds['dam_danger']:  # 設計最高水位
                alerts['dam'] = '危険'
                alert_level = max(alert_level, 3)
            elif dam_level >= thresholds['dam_warning']:  # 洪水時最高水位
                alerts['dam'] = '警戒'
                alert_level = max(alert_level, 2)
        
        # 雨量チェック
        hourly_rain = data.get('rainfall', {}).get('hourly', 0)
        cumulative_rain = data.get('rainfall', {}).get('cumulative', 0)
        
        if hourly_rain >= 50 or cumulative_rain >= 200:
            alerts['rainfall'] = '危険'
            alert_level = max(alert_level, 3)
        elif hourly_rain >= 30 or cumulative_rain >= 100:
            alerts['rainfall'] = '警戒'
            alert_level = max(alert_level, 2)
        elif hourly_rain >= 10 or cumulative_rain >= 50:
            alerts['rainfall'] = '注意'
            alert_level = max(alert_level, 1)
        
        # 総合アラートレベル設定
        if alert_level >= 3:
            alerts['overall'] = '危険'
        elif alert_level >= 2:
            alerts['overall'] = '警戒'
        elif alert_level >= 1:
            alerts['overall'] = '注意'
        else:
            alerts['overall'] = '正常'
        
        return alerts
    
    def create_weather_forecast_display(self, data: Dict[str, Any]) -> None:
        """天気予報情報を表示する"""
        st.markdown("## 🌤️ 天気予報（宇部市）")
        
        weather_data = data.get('weather', {})
        
        if not weather_data or not weather_data.get('today', {}).get('weather_text'):
            st.info("⚠️ 天気予報データが利用できません")
            return
        
        # 更新時刻の表示
        if weather_data.get('update_time'):
            try:
                update_time = datetime.fromisoformat(weather_data['update_time'])
                st.caption(f"予報更新時刻: {update_time.strftime('%Y-%m-%d %H:%M')} JST")
            except:
                pass
        
        # 今日・明日・明後日の天気予報を横並びで表示
        col1, col2, col3 = st.columns(3)
        
        # 今日の天気
        with col1:
            st.markdown("### 今日")
            today = weather_data.get('today', {})
            
            # 天気
            weather_text = today.get('weather_text', 'データなし')
            st.markdown(f"**天気:** {weather_text}")
            
            # 気温
            temp_max = today.get('temp_max')
            temp_min = today.get('temp_min')
            if temp_max is not None and temp_min is not None:
                st.markdown(f"**気温:** {temp_max}°C / {temp_min}°C")
            elif temp_max is not None:
                st.markdown(f"**最高気温:** {temp_max}°C")
            elif temp_min is not None:
                st.markdown(f"**最低気温:** {temp_min}°C")
            
            # 時間別降水確率
            precip_prob = today.get('precipitation_probability', [])
            precip_times = today.get('precipitation_times', [])
            if precip_prob and precip_times:
                st.markdown(f"**降水確率:**")
                for time, prob in zip(precip_times, precip_prob):
                    if prob is not None:
                        st.markdown(f"　{time}: {prob}%")
                    else:
                        st.markdown(f"　{time}: --")
        
        # 明日の天気
        with col2:
            st.markdown("### 明日")
            tomorrow = weather_data.get('tomorrow', {})
            
            # 天気
            weather_text = tomorrow.get('weather_text', 'データなし')
            st.markdown(f"**天気:** {weather_text}")
            
            # 気温
            temp_max = tomorrow.get('temp_max')
            temp_min = tomorrow.get('temp_min')
            if temp_max is not None and temp_min is not None:
                st.markdown(f"**気温:** {temp_max}°C / {temp_min}°C")
            elif temp_max is not None:
                st.markdown(f"**最高気温:** {temp_max}°C")
            elif temp_min is not None:
                st.markdown(f"**最低気温:** {temp_min}°C")
            
            # 時間別降水確率
            precip_prob = tomorrow.get('precipitation_probability', [])
            precip_times = tomorrow.get('precipitation_times', [])
            if precip_prob and precip_times:
                st.markdown(f"**降水確率:**")
                for time, prob in zip(precip_times, precip_prob):
                    if prob is not None:
                        st.markdown(f"　{time}: {prob}%")
                    else:
                        st.markdown(f"　{time}: --")
        
        # 明後日の天気
        with col3:
            st.markdown("### 明後日")
            day_after = weather_data.get('day_after_tomorrow', {})
            
            # 天気
            weather_text = day_after.get('weather_text', 'データなし')
            st.markdown(f"**天気:** {weather_text}")
            
            # 気温
            temp_max = day_after.get('temp_max')
            temp_min = day_after.get('temp_min')
            if temp_max is not None and temp_min is not None:
                st.markdown(f"**気温:** {temp_max}°C / {temp_min}°C")
            elif temp_max is not None:
                st.markdown(f"**最高気温:** {temp_max}°C")
            elif temp_min is not None:
                st.markdown(f"**最低気温:** {temp_min}°C")
            
            # 降水確率（週間予報は日中のみ）
            precip_prob = day_after.get('precipitation_probability', [])
            precip_times = day_after.get('precipitation_times', [])
            if precip_prob and precip_times:
                st.markdown(f"**降水確率:**")
                for time, prob in zip(precip_times, precip_prob):
                    if prob is not None:
                        st.markdown(f"　{time}: {prob}%")
                    else:
                        st.markdown(f"　{time}: --")
        
        # 警戒メッセージ
        today_precip = weather_data.get('today', {}).get('precipitation_probability', [])
        tomorrow_precip = weather_data.get('tomorrow', {}).get('precipitation_probability', [])
        day_after_precip = weather_data.get('day_after_tomorrow', {}).get('precipitation_probability', [])
        
        # 3日間の最大降水確率を取得
        max_today = max([p for p in today_precip if p is not None], default=0)
        max_tomorrow = max([p for p in tomorrow_precip if p is not None], default=0)
        max_day_after = max([p for p in day_after_precip if p is not None], default=0)
        
        if max_today >= 70 or max_tomorrow >= 70 or max_day_after >= 70:
            st.warning("⚠️ 降水確率が高くなっています。水位の変化にご注意ください。")
        elif max_today >= 50 or max_tomorrow >= 50 or max_day_after >= 50:
            st.info("💧 降水の可能性があります。河川・ダムの状況を定期的にご確認ください。")
        
        st.markdown("---")
        
        # 週間予報の表示
        self.create_weekly_forecast_display(data)
    
    def create_weekly_forecast_display(self, data: Dict[str, Any]) -> None:
        """週間予報情報を表示する"""
        weather_data = data.get('weather', {})
        weekly_forecast = weather_data.get('weekly_forecast', [])
        
        if not weekly_forecast:
            return
        
        st.markdown("## 📅 週間天気予報（山口県）")
        
        # 週間予報を表形式で表示
        if len(weekly_forecast) >= 7:
            # 7列に分けて表示
            cols = st.columns(7)
            
            for i, day_data in enumerate(weekly_forecast[:7]):
                with cols[i]:
                    # 日付と曜日
                    try:
                        date_obj = datetime.strptime(day_data['date'], '%Y-%m-%d')
                        month_day = date_obj.strftime('%m/%d')
                        day_of_week = day_data.get('day_of_week', date_obj.strftime('%a'))
                        
                        # 今日・明日・明後日のラベル
                        jst = ZoneInfo('Asia/Tokyo')
                        today = datetime.now(jst).date()
                        target_date = date_obj.date()
                        
                        if target_date == today:
                            day_label = "今日"
                        elif target_date == today + timedelta(days=1):
                            day_label = "明日"
                        elif target_date == today + timedelta(days=2):
                            day_label = "明後日"
                        else:
                            day_label = day_of_week
                        
                        st.markdown(f"**{month_day}**")
                        st.markdown(f"**{day_label}**")
                    except:
                        st.markdown(f"**{day_data.get('date', '')}**")
                    
                    # 天気
                    weather_text = day_data.get('weather_text', 'データなし')
                    # 長い天気予報文を短縮
                    if len(weather_text) > 8:
                        weather_short = weather_text.replace('時々', '時々').replace('一時', '一時')[:8] + "..."
                    else:
                        weather_short = weather_text
                    st.markdown(f"{weather_short}")
                    
                    # 降水確率
                    precip_prob = day_data.get('precipitation_probability')
                    if precip_prob is not None:
                        # 高い降水確率は色を変える
                        if precip_prob >= 70:
                            st.markdown(f"🌧️ **{precip_prob}%**")
                        elif precip_prob >= 50:
                            st.markdown(f"☔ **{precip_prob}%**")
                        elif precip_prob >= 30:
                            st.markdown(f"🌤️ {precip_prob}%")
                        else:
                            st.markdown(f"☀️ {precip_prob}%")
                    else:
                        st.markdown("--")
        
        st.markdown("---")
    
    def create_metrics_display(self, data: Dict[str, Any]) -> None:
        """現在の状況表示を作成"""
        if not data:
            st.warning("表示するデータがありません")
            return
        
        # 観測時刻の取得（日本時間で表示）
        observation_time = data.get('data_time')
        if observation_time:
            try:
                # ISOフォーマットから日時を解析
                dt = datetime.fromisoformat(observation_time.replace('Z', '+00:00'))
                # タイムゾーンがない場合は日本時間として扱う
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=ZoneInfo('Asia/Tokyo'))
                else:
                    # UTCから日本時間に変換
                    dt = dt.astimezone(ZoneInfo('Asia/Tokyo'))
                obs_time_str = dt.strftime('%Y/%m/%d %H:%M')
            except:
                obs_time_str = observation_time
        else:
            obs_time_str = "不明"
        
        # 3つのセクションに分けて表示
        st.subheader("📊 現在の観測状況")
        
        # 降雨情報
        st.markdown("### 🌧️ 降雨情報")
        rain_col1, rain_col2, rain_col3 = st.columns(3)
        
        with rain_col1:
            hourly_rain = data.get('rainfall', {}).get('hourly')
            if hourly_rain is not None:
                rain_color = "normal"
                if hourly_rain > 20:
                    rain_color = "inverse"
                st.metric(
                    label="60分雨量 (mm)",
                    value=f"{hourly_rain}",
                    delta=data.get('rainfall', {}).get('change'),
                    delta_color=rain_color
                )
                if hourly_rain > 30:
                    st.error("🌧️ 大雨注意")
                elif hourly_rain > 10:
                    st.warning("🌦️ 雨量多め")
            else:
                st.metric(label="60分雨量 (mm)", value="--")
        
        with rain_col2:
            cumulative_rain = data.get('rainfall', {}).get('cumulative')
            if cumulative_rain is not None:
                st.metric(
                    label="累積雨量 (mm)",
                    value=f"{cumulative_rain}"
                )
            else:
                st.metric(label="累積雨量 (mm)", value="--")
        
        with rain_col3:
            st.metric(
                label="観測日時",
                value=obs_time_str
            )
        
        # 河川情報
        st.markdown("### 🌊 河川情報（持世寺）")
        river_col1, river_col2, river_col3 = st.columns(3)
        
        with river_col1:
            river_level = data.get('river', {}).get('water_level')
            river_status = data.get('river', {}).get('status', '正常')
            if river_level is not None:
                delta_color = "normal"
                level_change = data.get('river', {}).get('level_change')
                if level_change and level_change > 0:
                    delta_color = "inverse"
                elif level_change and level_change < 0:
                    delta_color = "normal"
                
                st.metric(
                    label="水位 (m)",
                    value=f"{river_level:.2f}",
                    delta=f"{level_change:.2f}" if level_change is not None else None,
                    delta_color=delta_color
                )
                
                # ステータス表示
                if river_status != '正常':
                    if river_status in ['氾濫危険', '避難判断']:
                        st.error(f"🚨 {river_status}")
                    elif river_status in ['氾濫注意', '水防団待機']:
                        st.warning(f"⚠️ {river_status}")
                else:
                    st.success(f"✅ {river_status}")
            else:
                st.metric(label="水位 (m)", value="--")
        
        with river_col2:
            st.metric(
                label="観測地点",
                value="持世寺"
            )
        
        with river_col3:
            st.metric(
                label="観測日時",
                value=obs_time_str
            )
        
        # ダム情報
        st.markdown("### 🏔️ ダム情報（厚東川ダム）")
        dam_col1, dam_col2, dam_col3, dam_col4, dam_col5 = st.columns(5)
        
        with dam_col1:
            dam_level = data.get('dam', {}).get('water_level')
            if dam_level is not None:
                st.metric(
                    label="貯水位 (m)",
                    value=f"{dam_level:.2f}",
                    delta=data.get('dam', {}).get('storage_change')
                )
            else:
                st.metric(label="貯水位 (m)", value="--")
        
        with dam_col2:
            storage_rate = data.get('dam', {}).get('storage_rate')
            if storage_rate is not None:
                st.metric(
                    label="貯水率 (%)",
                    value=f"{storage_rate:.1f}"
                )
            else:
                st.metric(label="貯水率 (%)", value="--")
        
        with dam_col3:
            inflow = data.get('dam', {}).get('inflow')
            if inflow is not None:
                st.metric(
                    label="流入量 (m³/s)",
                    value=f"{inflow:.2f}"
                )
            else:
                st.metric(label="流入量 (m³/s)", value="--")
        
        with dam_col4:
            outflow = data.get('dam', {}).get('outflow')
            if outflow is not None:
                st.metric(
                    label="全放流量 (m³/s)",
                    value=f"{outflow:.2f}"
                )
            else:
                st.metric(label="全放流量 (m³/s)", value="--")
        
        with dam_col5:
            st.metric(
                label="観測日時",
                value=obs_time_str
            )
    
    def create_river_water_level_graph(self, history_data: List[Dict[str, Any]]) -> go.Figure:
        """河川水位グラフを作成（河川水位 + ダム全放流量の二軸表示）"""
        if not history_data:
            fig = go.Figure()
            fig.add_annotation(
                text="表示するデータがありません",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig
        
        # データをDataFrameに変換
        df_data = []
        for item in history_data:
            # 観測時刻（data_time）を使用、なければtimestampを使用
            data_time = item.get('data_time') or item.get('timestamp', '')
            try:
                dt = datetime.fromisoformat(data_time.replace('Z', '+00:00'))
                # タイムゾーンがない場合はJSTとして扱う
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=ZoneInfo('Asia/Tokyo'))
                else:
                    dt = dt.astimezone(ZoneInfo('Asia/Tokyo'))
            except:
                continue
                
            row = {'timestamp': dt}
            
            # 河川水位
            river_level = item.get('river', {}).get('water_level')
            if river_level is not None:
                row['river_level'] = river_level
            
            # ダム全放流量
            outflow = item.get('dam', {}).get('outflow')
            if outflow is not None:
                row['outflow'] = outflow
            
            df_data.append(row)
        
        if not df_data:
            fig = go.Figure()
            fig.add_annotation(
                text="有効なデータがありません",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig
        
        df = pd.DataFrame(df_data)
        
        # 二軸グラフを作成
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # 河川水位（左軸）
        if 'river_level' in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=df['river_level'],
                    mode='lines+markers',
                    name='河川水位（持世寺）',
                    line=dict(color='#1f77b4')
                ),
                secondary_y=False
            )
        
        # ダム全放流量（右軸）
        if 'outflow' in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=df['outflow'],
                    mode='lines+markers',
                    name='全放流量（厚東川ダム）',
                    line=dict(color='#d62728')
                ),
                secondary_y=True
            )
        
        # 軸の設定
        fig.update_yaxes(
            title_text="河川水位 (m)",
            range=[0, 6],
            dtick=1,
            secondary_y=False
        )
        fig.update_yaxes(
            title_text="全放流量 (m³/s)",
            range=[0, 900],
            dtick=150,
            secondary_y=True
        )
        
        fig.update_xaxes(title_text="時刻")
        
        fig.update_layout(
            height=400,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            margin=dict(t=30)
        )
        
        return fig
    
    def create_dam_water_level_graph(self, history_data: List[Dict[str, Any]]) -> go.Figure:
        """ダム水位グラフを作成（ダム水位 + 時間雨量の二軸表示）"""
        if not history_data:
            fig = go.Figure()
            fig.add_annotation(
                text="表示するデータがありません",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig
        
        # データをDataFrameに変換
        df_data = []
        for item in history_data:
            # 観測時刻（data_time）を使用、なければtimestampを使用
            data_time = item.get('data_time') or item.get('timestamp', '')
            try:
                dt = datetime.fromisoformat(data_time.replace('Z', '+00:00'))
                # タイムゾーンがない場合はJSTとして扱う
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=ZoneInfo('Asia/Tokyo'))
                else:
                    dt = dt.astimezone(ZoneInfo('Asia/Tokyo'))
            except:
                continue
                
            row = {'timestamp': dt}
            
            # ダム水位
            dam_level = item.get('dam', {}).get('water_level')
            if dam_level is not None:
                row['dam_level'] = dam_level
            
            # 雨量
            rainfall = item.get('rainfall', {}).get('hourly')
            if rainfall is not None:
                row['rainfall'] = rainfall
            
            df_data.append(row)
        
        if not df_data:
            fig = go.Figure()
            fig.add_annotation(
                text="有効なデータがありません",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig
        
        df = pd.DataFrame(df_data)
        
        # 二軸グラフを作成
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # ダム水位（左軸）
        if 'dam_level' in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=df['dam_level'],
                    mode='lines+markers',
                    name='ダム貯水位（厚東川ダム）',
                    line=dict(color='#ff7f0e')
                ),
                secondary_y=False
            )
        
        # 時間雨量（右軸）
        if 'rainfall' in df.columns:
            fig.add_trace(
                go.Bar(
                    x=df['timestamp'],
                    y=df['rainfall'],
                    name='時間雨量（宇部市）',
                    marker_color='#87CEEB',
                    opacity=0.7
                ),
                secondary_y=True
            )
        
        # 軸の設定
        fig.update_yaxes(
            title_text="ダム貯水位 (m)",
            range=[0, 50],
            dtick=5,
            secondary_y=False
        )
        fig.update_yaxes(
            title_text="時間雨量 (mm/h)",
            range=[0, 50],
            dtick=5,
            secondary_y=True
        )
        
        fig.update_xaxes(title_text="時刻")
        
        fig.update_layout(
            height=400,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            margin=dict(t=30)
        )
        
        return fig
    
    def create_dam_flow_graph(self, history_data: List[Dict[str, Any]]) -> go.Figure:
        """ダム流入出量グラフを作成（流入量・全放流量 + 累加雨量の二軸表示）"""
        if not history_data:
            fig = go.Figure()
            fig.add_annotation(
                text="表示するデータがありません",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig
        
        # データをDataFrameに変換
        df_data = []
        for item in history_data:
            # 観測時刻（data_time）を使用、なければtimestampを使用
            data_time = item.get('data_time') or item.get('timestamp', '')
            try:
                dt = datetime.fromisoformat(data_time.replace('Z', '+00:00'))
                # タイムゾーンがない場合はJSTとして扱う
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=ZoneInfo('Asia/Tokyo'))
                else:
                    dt = dt.astimezone(ZoneInfo('Asia/Tokyo'))
            except:
                continue
                
            row = {'timestamp': dt}
            
            # ダム流入量
            inflow = item.get('dam', {}).get('inflow')
            if inflow is not None:
                row['inflow'] = inflow
            
            # ダム全放流量
            outflow = item.get('dam', {}).get('outflow')
            if outflow is not None:
                row['outflow'] = outflow
            
            # 累加雨量
            cumulative_rainfall = item.get('rainfall', {}).get('cumulative')
            if cumulative_rainfall is not None:
                row['cumulative_rainfall'] = cumulative_rainfall
            
            df_data.append(row)
        
        if not df_data:
            fig = go.Figure()
            fig.add_annotation(
                text="有効なデータがありません",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig
        
        df = pd.DataFrame(df_data)
        
        # 二軸グラフを作成
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # ダム流入量（左軸）
        if 'inflow' in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=df['inflow'],
                    mode='lines+markers',
                    name='流入量（厚東川ダム）',
                    line=dict(color='#2ca02c')
                ),
                secondary_y=False
            )
        
        # ダム全放流量（左軸）
        if 'outflow' in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=df['outflow'],
                    mode='lines+markers',
                    name='全放流量（厚東川ダム）',
                    line=dict(color='#d62728')
                ),
                secondary_y=False
            )
        
        # 累加雨量（右軸）
        if 'cumulative_rainfall' in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=df['cumulative_rainfall'],
                    mode='lines+markers',
                    name='累加雨量（宇部市）',
                    line=dict(color='#87CEEB'),
                    fill='tonexty'
                ),
                secondary_y=True
            )
        
        # 軸の設定
        fig.update_yaxes(
            title_text="流量 (m³/s)",
            range=[0, 900],
            dtick=100,
            secondary_y=False
        )
        fig.update_yaxes(
            title_text="累加雨量 (mm)",
            range=[0, 180],
            dtick=20,
            secondary_y=True
        )
        
        fig.update_xaxes(title_text="時刻")
        
        fig.update_layout(
            height=400,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            margin=dict(t=30)
        )
        
        return fig
    
    def create_data_table(self, history_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """データテーブルを作成"""
        if not history_data:
            return pd.DataFrame()
        
        table_data = []
        for item in history_data[-20:]:  # 最新20件
            # 観測時刻（data_time）を使用、なければtimestampを使用
            data_time = item.get('data_time') or item.get('timestamp', '')
            try:
                dt = datetime.fromisoformat(data_time.replace('Z', '+00:00'))
                # タイムゾーンがない場合はJSTとして扱う
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=ZoneInfo('Asia/Tokyo'))
                else:
                    dt = dt.astimezone(ZoneInfo('Asia/Tokyo'))
                formatted_time = dt.strftime('%Y-%m-%d %H:%M')
            except:
                formatted_time = data_time
            
            table_data.append({
                'ダム貯水位(m)': item.get('dam', {}).get('water_level', '--'),
                'ダム貯水率(%)': item.get('dam', {}).get('storage_rate', '--'),
                'ダム流入量(m³/s)': item.get('dam', {}).get('inflow', '--'),
                'ダム全放流量(m³/s)': item.get('dam', {}).get('outflow', '--'),
                '水位(m)（持世寺）': item.get('river', {}).get('water_level', '--'),
                '観測日時': formatted_time
            })
        
        return pd.DataFrame(table_data).iloc[::-1]  # 新しい順に並び替え

def main():
    """メイン関数"""
    monitor = KotogawaMonitor()
    
    # ヘッダー
    st.title("🌊 厚東川リアルタイム監視システム")
    
    # サイドバー設定
    st.sidebar.header("設定")
    
    # 自動更新設定（一時的に無効化）
    # auto_refresh = st.sidebar.checkbox("自動更新 (30秒)", value=False)
    # if auto_refresh:
    #     st.rerun()
    
    # 表示期間設定
    display_hours = st.sidebar.selectbox(
        "表示期間",
        [6, 12, 24, 48, 72],
        index=2,
        format_func=lambda x: f"{x}時間"
    )
    
    # アラート閾値設定
    st.sidebar.subheader("アラート設定")
    river_warning = st.sidebar.number_input("河川警戒水位 (m)", value=3.0, step=0.1)
    river_danger = st.sidebar.number_input("河川危険水位 (m)", value=5.0, step=0.1)
    dam_warning = st.sidebar.number_input("ダム警戒水位 (m)", value=39.2, step=0.1, help="洪水時最高水位")
    dam_danger = st.sidebar.number_input("ダム危険水位 (m)", value=40.0, step=0.1, help="設計最高水位")
    
    thresholds = {
        'river_warning': river_warning,
        'river_danger': river_danger,
        'dam_warning': dam_warning,
        'dam_danger': dam_danger
    }
    
    # データ読み込み
    latest_data = monitor.load_latest_data()
    
    # キャッシュキー取得
    cache_key = monitor.get_cache_key()
    
    # 履歴データの読み込み
    try:
        with st.spinner("履歴データを読み込み中..."):
            history_data = monitor.load_history_data(display_hours, cache_key)
    except Exception as e:
        st.warning(f"履歴データの読み込みに失敗しました: {e}")
        history_data = []
    
    # 最終更新時刻と観測時刻表示
    col1, col2 = st.columns([3, 1])
    with col1:
        if latest_data and latest_data.get('timestamp'):
            try:
                # データ取得時刻（timestamp）
                timestamp = datetime.fromisoformat(latest_data['timestamp'].replace('Z', '+00:00'))
                # タイムゾーンがない場合は日本時間として扱う（変換なし）
                if timestamp.tzinfo is None:
                    timestamp = timestamp.replace(tzinfo=ZoneInfo('Asia/Tokyo'))
                
                # 観測時刻（data_time）
                data_time_str = latest_data.get('data_time', '')
                if data_time_str:
                    data_time = datetime.fromisoformat(data_time_str.replace('Z', '+00:00'))
                    if data_time.tzinfo is None:
                        data_time = data_time.replace(tzinfo=ZoneInfo('Asia/Tokyo'))
                    st.info(f"観測時刻: {data_time.strftime('%Y年%m月%d日 %H:%M')} | 取得時刻: {timestamp.strftime('%Y年%m月%d日 %H:%M:%S')}")
                else:
                    st.info(f"最終更新: {timestamp.strftime('%Y年%m月%d日 %H:%M:%S')}")
            except Exception as e:
                st.info(f"最終更新: {latest_data.get('timestamp', '不明')} (時刻解析エラー)")
        else:
            st.warning("データが取得できていません")
    
    with col2:
        if st.button("🔄 更新", type="primary"):
            # 特定のキャッシュ関数をクリア
            monitor.load_history_data.clear()
            st.cache_data.clear()
            st.rerun()
    
    # アラート表示
    if latest_data:
        alerts = monitor.check_alert_status(latest_data, thresholds)
        
        # アラート詳細情報
        alert_details = []
        if alerts['river'] != '正常':
            river_status = latest_data.get('river', {}).get('status', '不明')
            alert_details.append(f"河川: {river_status}")
        if alerts['dam'] != '正常':
            dam_level = latest_data.get('dam', {}).get('water_level')
            if dam_level is not None:
                alert_details.append(f"ダム: {alerts['dam']} ({dam_level:.2f}m)")
            else:
                alert_details.append(f"ダム: {alerts['dam']}")
        if alerts['rainfall'] != '正常':
            hourly_rain = latest_data.get('rainfall', {}).get('hourly', 0)
            alert_details.append(f"雨量: {hourly_rain}mm/h")
        
        # 総合アラート表示
        if alerts['overall'] == '危険':
            detail_text = " | ".join(alert_details) if alert_details else ""
            st.error(f"🚨 **危険レベル**: 緊急対応が必要です {detail_text}")
        elif alerts['overall'] == '警戒':
            detail_text = " | ".join(alert_details) if alert_details else ""
            st.warning(f"⚠️ **警戒レベル**: 注意が必要です {detail_text}")
        elif alerts['overall'] == '注意':
            detail_text = " | ".join(alert_details) if alert_details else ""
            st.info(f"ℹ️ **注意レベル**: 状況を監視中 {detail_text}")
        elif alerts['overall'] == '正常':
            st.success("✅ **正常レベル**: 安全な状態です")
        else:
            st.info("ℹ️ データ確認中...")
    
    # 現在の状況表示
    monitor.create_metrics_display(latest_data)
    
    # 天気予報表示
    monitor.create_weather_forecast_display(latest_data)
    
    # タブによる表示切り替え
    tab1, tab2 = st.tabs(["📊 グラフ", "📋 データテーブル"])
    
    with tab1:
        st.subheader("河川水位・全放流量")
        fig1 = monitor.create_river_water_level_graph(history_data)
        st.plotly_chart(fig1, use_container_width=True)
        
        st.subheader("ダム流入出量・累加雨量")
        fig2 = monitor.create_dam_flow_graph(history_data)
        st.plotly_chart(fig2, use_container_width=True)
        
        st.subheader("ダム貯水位・時間雨量")
        fig3 = monitor.create_dam_water_level_graph(history_data)
        st.plotly_chart(fig3, use_container_width=True)
    
    with tab2:
        st.subheader("データテーブル")
        df_table = monitor.create_data_table(history_data)
        if not df_table.empty:
            st.dataframe(df_table, use_container_width=True)
            
            # CSVダウンロード
            csv = df_table.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 CSVダウンロード",
                data=csv,
                file_name=f"kotogawa_data_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )
        else:
            st.info("表示するデータがありません")
    
    # システム情報（サイドバー）
    st.sidebar.subheader("システム情報")
    
    # データ統計
    st.sidebar.info(
        f"📊 データ件数: {len(history_data)}件\n"
        f"⏱️ 表示期間: {display_hours}時間"
    )
    
    # 警戒レベル説明
    with st.sidebar.expander("🚨 警戒レベル説明"):
        st.write(f"""
        **河川水位基準**
        - 正常: 3.80m未満
        - 水防団待機: 3.80m以上
        - 氾濫注意: 5.00m以上
        - 避難判断: 5.10m以上
        - 氾濫危険: 5.50m以上
        
        **ダム水位基準**
        - 警戒: {dam_warning}m以上（洪水時最高水位）
        - 危険: {dam_danger}m以上（設計最高水位）
        
        **雨量基準**
        - 注意: 10mm/h以上
        - 警戒: 30mm/h以上
        - 危険: 50mm/h以上
        """)
    
    # データソース情報
    with st.sidebar.expander("📡 データソース"):
        st.write("""
        **厚東川ダム**
        - 観測地点: 宇部市
        - 更新間隔: 10分
        
        **厚東川(持世寺)**
        - 観測地点: 宇部市持世寺
        - 更新間隔: 10分
        
        データ提供: 山口県土木防災情報システム
        """)
    
    # 最終更新からの経過時間
    if latest_data and latest_data.get('timestamp'):
        try:
            last_update = datetime.fromisoformat(latest_data['timestamp'].replace('Z', '+00:00'))
            # タイムゾーンがない場合は日本時間として扱う（変換なし）
            if last_update.tzinfo is None:
                last_update = last_update.replace(tzinfo=ZoneInfo('Asia/Tokyo'))
            
            # 現在時刻（日本時間）
            now_jst = datetime.now(ZoneInfo('Asia/Tokyo'))
            time_diff = now_jst - last_update
            minutes_ago = int(time_diff.total_seconds() / 60)
            
            if minutes_ago < 60:
                st.sidebar.success(f"🟢 最新 ({minutes_ago}分前)")
            elif minutes_ago < 120:
                st.sidebar.warning(f"🟡 やや古い ({minutes_ago}分前)")
            else:
                st.sidebar.error(f"🔴 古いデータ ({minutes_ago}分前)")
        except:
            st.sidebar.info("🔵 更新時刻確認中")
    
    # アプリ情報
    st.sidebar.markdown("---")
    st.sidebar.caption("厚東川リアルタイム監視システム v1.0")
    st.sidebar.caption("Powered by Streamlit")

if __name__ == "__main__":
    main()