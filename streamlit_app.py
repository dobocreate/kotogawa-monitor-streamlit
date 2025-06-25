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
from streamlit_autorefresh import st_autorefresh

# ページ設定
st.set_page_config(
    page_title="厚東川監視システム",
    page_icon="■",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# サイドバー表示時のレスポンシブ対応CSS
st.markdown("""
<style>
    /* サイドバーが開いている時のメインコンテンツ幅調整 */
    .main .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
        max-width: 100%;
    }
    
    /* サイドバーが開いている時のグラフコンテナ */
    [data-testid="stSidebar"][aria-expanded="true"] ~ .main .block-container {
        max-width: calc(100vw - 21rem);
    }
    
    /* Plotlyグラフのレスポンシブ対応 */
    .js-plotly-plot .plotly {
        width: 100% !important;
        height: auto !important;
    }
    
    /* Streamlitのグラフコンテナ */
    .stPlotlyChart {
        width: 100% !important;
    }
    
    /* メトリクス表示の調整 */
    [data-testid="metric-container"] {
        width: 100%;
        min-width: 0;
    }
    
    /* 固定ヘッダーのスタイル */
    .fixed-header {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        background-color: white;
        z-index: 999;
        padding: 1rem 1rem 0.5rem 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* サイドバーが開いている時の固定ヘッダー調整 */
    [data-testid="stSidebar"][aria-expanded="true"] ~ .main .fixed-header {
        left: 21rem;
        right: 0;
    }
    
    /* 固定ヘッダー分のメインコンテンツ上部マージン */
    .main-content {
        margin-top: 140px;
    }
    
    /* サイドバーの上部余白調整 */
    section[data-testid="stSidebar"] > div {
        padding-top: 0rem;
    }
</style>
""", unsafe_allow_html=True)

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
            st.warning("■ データファイルが見つかりません。データ収集スクリプトを実行してください。")
            return None
        
        try:
            # ファイル更新時刻をキャッシュキーとして使用
            file_mtime = latest_file.stat().st_mtime
            return _self._load_latest_data_cached(str(latest_file), file_mtime)
        except Exception as e:
            st.error(f"× データ読み込みエラー: {e}")
            return None
    
    @st.cache_data(ttl=300)  # ファイル更新時刻が変わるまでキャッシュ
    def _load_latest_data_cached(_self, file_path: str, file_mtime: float) -> Optional[Dict[str, Any]]:
        """ファイル更新時刻をキーとするキャッシュされたデータ読み込み"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # データの整合性チェック
                if not data or 'timestamp' not in data:
                    st.error("× データファイルの形式が正しくありません")
                    return None
                
                return data
        except json.JSONDecodeError as e:
            st.error(f"× JSONファイルの形式エラー: {e}")
            return None
        except FileNotFoundError:
            st.warning("■ データファイルが見つかりません")
            return None
        except Exception as e:
            st.error(f"× データ読み込みエラー: {e}")
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
            st.info("■ 履歴データディレクトリがありません。データが蓄積されるまでお待ちください。")
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
                            st.warning(f"■ 破損した履歴ファイル: {file_path.name}")
                    except Exception as e:
                        error_count += 1
                        if error_count <= 3:
                            st.warning(f"■ 履歴データエラー: {file_path.name}")
            
            current_time -= timedelta(days=1)
        
        # エラーサマリー表示
        if error_count > 3:
            st.warning(f"■ 履歴データの読み込みで {error_count} 件のエラーがありました")
        
        # 時系列順にソート
        try:
            history_data.sort(key=lambda x: x.get('timestamp', ''))
        except Exception as e:
            st.error(f"× 履歴データソートエラー: {e}")
            
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
    
    def create_weather_forecast_display(self, data: Dict[str, Any], show_weekly: bool = True) -> None:
        """天気予報情報を表示する"""
        st.markdown("## 天気予報（宇部市）")
        
        weather_data = data.get('weather', {})
        
        if not weather_data or not weather_data.get('today', {}).get('weather_text'):
            st.info("天気予報データが利用できません")
            return
        
        # 更新時刻の表示
        if weather_data.get('update_time'):
            try:
                update_time = datetime.fromisoformat(weather_data['update_time'])
                st.caption(f"予報更新時刻 : {update_time.strftime('%Y-%m-%d %H:%M')} JST")
            except:
                pass
        
        # 今日・明日の天気予報を横並びで表示
        col1, col2 = st.columns(2)
        
        # 今日の天気
        with col1:
            st.markdown("### 今日")
            today = weather_data.get('today', {})
            
            # 天気
            weather_text = today.get('weather_text', 'データなし')
            # スペースを削除して2行分確保
            weather_text_cleaned = weather_text.replace('　', '').replace(' ', '')
            st.markdown(f"**天気:**<br>{weather_text_cleaned}", unsafe_allow_html=True)
            # 2行分の高さを確保するための空白行
            st.markdown("<br>", unsafe_allow_html=True)
            
            # 気温
            temp_max = today.get('temp_max')
            temp_min = today.get('temp_min')
            if temp_max is not None and temp_min is not None:
                st.markdown(f"**気温:** {temp_max}°C / {temp_min}°C")
            elif temp_max is not None:
                st.markdown(f"**最高気温:** {temp_max}°C")
            elif temp_min is not None:
                st.markdown(f"**最低気温:** {temp_min}°C")
            
            # 時間別降水確率をグラフで表示
            precip_prob = today.get('precipitation_probability', [])
            precip_times = today.get('precipitation_times', [])
            if precip_prob and precip_times:
                st.markdown(f"**降水確率:**")
                # Plotlyでグラフ作成
                import plotly.graph_objects as go
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=precip_times,
                    y=precip_prob,
                    mode='lines+markers+text',
                    text=[f'{p}%' if p is not None else '--' for p in precip_prob],
                    textposition='top center',
                    textfont=dict(size=12, color='black'),
                    line=dict(color='#4488ff', width=3),
                    marker=dict(
                        size=12,
                        color='white',
                        line=dict(width=2, color='#4488ff')
                    )
                ))
                fig.update_layout(
                    height=200,
                    margin=dict(l=20, r=20, t=30, b=30),
                    xaxis_title="",
                    yaxis_title="降水確率 (%)",
                    yaxis=dict(range=[0, 100], fixedrange=True),
                    xaxis=dict(fixedrange=True),
                    showlegend=False,
                    autosize=True,
                    font=dict(size=9)
                )
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        # 明日の天気
        with col2:
            st.markdown("### 明日")
            tomorrow = weather_data.get('tomorrow', {})
            
            # 天気
            weather_text = tomorrow.get('weather_text', 'データなし')
            # スペースを削除して2行分確保
            weather_text_cleaned = weather_text.replace('　', '').replace(' ', '')
            st.markdown(f"**天気:**<br>{weather_text_cleaned}", unsafe_allow_html=True)
            # 2行分の高さを確保するための空白行
            st.markdown("<br>", unsafe_allow_html=True)
            
            # 気温
            temp_max = tomorrow.get('temp_max')
            temp_min = tomorrow.get('temp_min')
            if temp_max is not None and temp_min is not None:
                st.markdown(f"**気温:** {temp_max}°C / {temp_min}°C")
            elif temp_max is not None:
                st.markdown(f"**最高気温:** {temp_max}°C")
            elif temp_min is not None:
                st.markdown(f"**最低気温:** {temp_min}°C")
            
            # 時間別降水確率をグラフで表示
            precip_prob = tomorrow.get('precipitation_probability', [])
            precip_times = tomorrow.get('precipitation_times', [])
            if precip_prob and precip_times:
                st.markdown(f"**降水確率:**")
                # Plotlyでグラフ作成
                import plotly.graph_objects as go
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=precip_times,
                    y=precip_prob,
                    mode='lines+markers+text',
                    text=[f'{p}%' if p is not None else '--' for p in precip_prob],
                    textposition='top center',
                    textfont=dict(size=12, color='black'),
                    line=dict(color='#4488ff', width=3),
                    marker=dict(
                        size=12,
                        color='white',
                        line=dict(width=2, color='#4488ff')
                    )
                ))
                fig.update_layout(
                    height=200,
                    margin=dict(l=20, r=20, t=30, b=30),
                    xaxis_title="",
                    yaxis_title="降水確率 (%)",
                    yaxis=dict(range=[0, 100], fixedrange=True),
                    xaxis=dict(fixedrange=True),
                    showlegend=False,
                    autosize=True,
                    font=dict(size=9)
                )
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        
        # 警戒メッセージ
        today_precip = weather_data.get('today', {}).get('precipitation_probability', [])
        tomorrow_precip = weather_data.get('tomorrow', {}).get('precipitation_probability', [])
        
        # 2日間の最大降水確率を取得
        max_today = max([p for p in today_precip if p is not None], default=0)
        max_tomorrow = max([p for p in tomorrow_precip if p is not None], default=0)
        
        if max_today >= 70 or max_tomorrow >= 70:
            st.warning("■ 降水確率が高くなっています。水位の変化にご注意ください。")
        elif max_today >= 50 or max_tomorrow >= 50:
            st.info("● 降水の可能性があります。河川・ダムの状況を定期的にご確認ください。")
        
        st.markdown("---")
        
        # 週間予報の表示（条件付き）
        if show_weekly:
            self.create_weekly_forecast_display(data)
    
    def get_weather_icon(self, weather_code: str, weather_text: str = "") -> str:
        """天気コードまたは天気テキストから適切な絵文字を返す"""
        if not weather_code and not weather_text:
            return "❓"
        
        # 天気コードベースの判定
        if weather_code:
            code = str(weather_code)
            # 晴れ系
            if code.startswith('1'):
                if code in ['100']:
                    return "☀️"  # 晴れ
                elif code in ['101', '110', '111']:
                    return "🌤️"  # 晴れ時々くもり
                elif code in ['102', '112', '113']:
                    return "🌦️"  # 晴れ一時雨
                else:
                    return "☀️"
            # くもり系
            elif code.startswith('2'):
                if code in ['200']:
                    return "☁️"  # くもり
                elif code in ['201', '210', '211']:
                    return "⛅"  # くもり時々晴れ
                elif code in ['202', '212', '213']:
                    return "🌦️"  # くもり一時雨
                elif code in ['203']:
                    return "🌧️"  # くもり時々雨
                elif code in ['204']:
                    return "🌨️"  # くもり一時雪
                else:
                    return "☁️"
            # 雨系
            elif code.startswith('3'):
                if code in ['300', '313']:
                    return "🌧️"  # 雨
                elif code in ['301']:
                    return "🌦️"  # 雨時々晴れ
                elif code in ['302']:
                    return "🌧️"  # 雨時々くもり
                elif code in ['303', '314']:
                    return "🌨️"  # 雨時々雪、雨のち雪
                elif code in ['308']:
                    return "⛈️"  # 大雨
                elif code in ['311']:
                    return "🌦️"  # 雨のち晴れ
                else:
                    return "🌧️"
            # 雪系
            elif code.startswith('4'):
                if code in ['400', '413']:
                    return "❄️"  # 雪
                elif code in ['401', '411']:
                    return "🌨️"  # 雪時々晴れ、雪のち晴れ
                elif code in ['402']:
                    return "🌨️"  # 雪時々くもり
                elif code in ['403', '414']:
                    return "🌨️"  # 雪時々雨、雪のち雨
                elif code in ['406']:
                    return "❄️"  # 大雪
                else:
                    return "❄️"
        
        # 天気テキストベースの判定（フォールバック）
        if weather_text:
            text = weather_text.lower()
            if "晴" in text:
                if "雨" in text:
                    return "🌦️"
                elif "くもり" in text or "曇" in text:
                    return "🌤️"
                else:
                    return "☀️"
            elif "くもり" in text or "曇" in text:
                if "雨" in text:
                    return "🌧️"
                elif "晴" in text:
                    return "⛅"
                else:
                    return "☁️"
            elif "雨" in text:
                if "大雨" in text or "雷" in text:
                    return "⛈️"
                else:
                    return "🌧️"
            elif "雪" in text:
                return "❄️"
        
        return "❓"
    
    def create_weekly_forecast_display(self, data: Dict[str, Any]) -> None:
        """週間予報情報を表示する"""
        weather_data = data.get('weather', {})
        weekly_forecast = weather_data.get('weekly_forecast', [])
        
        if not weekly_forecast:
            return
        
        st.markdown("## 週間天気予報（山口県）")
        
        # レスポンシブ用のCSS
        st.markdown("""
        <style>
            /* デフォルト（デスクトップ）: 7列表示 */
            .weekly-forecast-container {
                display: grid;
                grid-template-columns: repeat(7, 1fr);
                gap: 10px;
            }
            
            /* タブレット: 4列表示 */
            @media (max-width: 768px) {
                .weekly-forecast-container {
                    grid-template-columns: repeat(4, 1fr);
                }
            }
            
            /* スマートフォン: 2列表示 */
            @media (max-width: 480px) {
                .weekly-forecast-container {
                    grid-template-columns: repeat(2, 1fr);
                }
            }
            
            .weather-day-item {
                text-align: center;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 8px;
                background-color: #f9f9f9;
            }
            
            .weather-date {
                font-weight: bold;
                margin-bottom: 5px;
            }
            
            .weather-label {
                font-weight: bold;
                margin-bottom: 10px;
            }
            
            .weather-icon {
                font-size: 24px;
                margin: 10px 0 5px 0;
            }
            
            .weather-text {
                font-size: 10px;
                color: #666;
                margin-bottom: 10px;
            }
            
            .weather-precip {
                margin-bottom: 0;
            }
        </style>
        """, unsafe_allow_html=True)
        
        # 週間予報を表形式で表示
        if len(weekly_forecast) >= 7:
            # HTMLコンテナで週間予報を表示
            html_content = '<div class="weekly-forecast-container">'
            
            # 曜日の日本語マッピング
            weekday_jp = {
                'Mon': '月', 'Tue': '火', 'Wed': '水', 'Thu': '木', 
                'Fri': '金', 'Sat': '土', 'Sun': '日'
            }
            
            for day_data in weekly_forecast[:7]:
                html_content += '<div class="weather-day-item">'
                
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
                        # 英語の曜日を日本語に変換
                        day_label = weekday_jp.get(day_of_week, day_of_week)
                    
                    html_content += f'<div class="weather-date">{month_day}</div>'
                    html_content += f'<div class="weather-label">{day_label}</div>'
                except:
                    html_content += f'<div class="weather-date">{day_data.get("date", "")}</div>'
                    html_content += '<div class="weather-label">--</div>'
                
                # 天気アイコン
                weather_code = day_data.get('weather_code', '')
                weather_text = day_data.get('weather_text', 'データなし')
                weather_icon = self.get_weather_icon(weather_code, weather_text)
                
                html_content += f'<div class="weather-icon">{weather_icon}</div>'
                
                # 短縮版のテキスト
                if len(weather_text) > 6:
                    weather_short = weather_text[:6] + "..."
                else:
                    weather_short = weather_text
                html_content += f'<div class="weather-text">{weather_short}</div>'
                
                # 降水確率
                precip_prob = day_data.get('precipitation_probability')
                if precip_prob is not None:
                    if precip_prob >= 70:
                        precip_text = f'雨 <strong>{precip_prob}%</strong>'
                    elif precip_prob >= 50:
                        precip_text = f'雨 <strong>{precip_prob}%</strong>'
                    elif precip_prob >= 30:
                        precip_text = f'曇 {precip_prob}%'
                    else:
                        precip_text = f'晴 {precip_prob}%'
                else:
                    precip_text = '--'
                
                html_content += f'<div class="weather-precip">{precip_text}</div>'
                html_content += '</div>'
            
            html_content += '</div>'
            st.markdown(html_content, unsafe_allow_html=True)
        
        st.markdown("---")
    
    def create_data_analysis_display(self, history_data: List[Dict[str, Any]], enable_graph_interaction: bool) -> None:
        """データ分析セクションを表示する"""
        # データ分析セクション
        st.markdown("## データ分析")
        
        # タブによる表示切り替え
        tab1, tab2 = st.tabs(["グラフ", "データテーブル"])
        
        with tab1:
            # Plotlyの設定（小画面対応を強化）
            plotly_config = {
                'scrollZoom': enable_graph_interaction,
                'doubleClick': 'reset' if enable_graph_interaction else False,
                'displayModeBar': True,
                'displaylogo': False,
                'responsive': True,
                'modeBarButtonsToRemove': ['lasso2d', 'select2d'] if enable_graph_interaction else ['pan2d', 'zoom2d', 'lasso2d', 'select2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d']
            }
            
            st.subheader("河川水位・全放流量")
            fig1 = self.create_river_water_level_graph(history_data, enable_graph_interaction)
            st.plotly_chart(fig1, use_container_width=True, config=plotly_config)
            
            st.subheader("ダム流入出量・累加雨量")
            fig2 = self.create_dam_flow_graph(history_data, enable_graph_interaction)
            st.plotly_chart(fig2, use_container_width=True, config=plotly_config)
            
            st.subheader("ダム貯水位・時間雨量")
            fig3 = self.create_dam_water_level_graph(history_data, enable_graph_interaction)
            st.plotly_chart(fig3, use_container_width=True, config=plotly_config)
            
            # 降水強度グラフの表示（最新データから取得）
            if history_data:
                latest_data = history_data[-1] if history_data else {}
                precipitation_intensity_data = latest_data.get('precipitation_intensity', {})
                
                if precipitation_intensity_data and (
                    precipitation_intensity_data.get('observation') or 
                    precipitation_intensity_data.get('forecast')
                ):
                    st.subheader("Yahoo! Weather API")
                    # 更新時刻を表示
                    if precipitation_intensity_data.get('update_time'):
                        try:
                            update_dt = datetime.fromisoformat(precipitation_intensity_data['update_time'])
                            if update_dt.tzinfo is None:
                                update_dt = update_dt.replace(tzinfo=ZoneInfo('Asia/Tokyo'))
                            update_str = update_dt.strftime('%H:%M:%S')
                            st.caption(f"更新日時 : {update_str}")
                        except:
                            pass
                    
                    fig4 = self.create_precipitation_intensity_graph(precipitation_intensity_data, enable_graph_interaction, history_data)
                    st.plotly_chart(fig4, use_container_width=True, config=plotly_config)
        
        with tab2:
            st.subheader("データテーブル")
            df_table = self.create_data_table(history_data)
            if not df_table.empty:
                st.dataframe(df_table, use_container_width=True)
                
                # CSVダウンロード
                csv = df_table.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="CSVダウンロード",
                    data=csv,
                    file_name=f"kotogawa_data_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv"
                )
            else:
                st.info("表示するデータがありません")
    
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
        st.markdown("## 現在の観測状況")
        
        # 河川情報と降雨情報を横並びで表示
        river_rain_col1, river_rain_col2 = st.columns(2)
        
        # 河川情報（左側）
        with river_rain_col1:
            st.markdown("### 河川情報")
            st.caption(f"更新時刻 : {obs_time_str}")
            river_subcol1, river_subcol2 = st.columns(2)
            
            with river_subcol1:
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
                            st.error(f"危険 {river_status}")
                        elif river_status in ['氾濫注意', '水防団待機']:
                            st.warning(f"注意 {river_status}")
                    else:
                        st.success(f"{river_status}")
                else:
                    st.metric(label="水位 (m)", value="--")
            
            with river_subcol2:
                st.metric(
                    label="観測地点",
                    value="持世寺"
                )
        
        # 降雨情報（右側）
        with river_rain_col2:
            st.markdown("### 降雨情報")
            st.caption(f"更新時刻 : {obs_time_str}")
            rain_subcol1, rain_subcol2 = st.columns(2)
            
            with rain_subcol1:
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
                        st.error("雨 大雨注意")
                    elif hourly_rain > 10:
                        st.warning("雨 雨量多め")
                else:
                    st.metric(label="60分雨量 (mm)", value="--")
            
            with rain_subcol2:
                cumulative_rain = data.get('rainfall', {}).get('cumulative')
                if cumulative_rain is not None:
                    st.metric(
                        label="累加雨量 (mm)",
                        value=f"{cumulative_rain}"
                    )
                else:
                    st.metric(label="累加雨量 (mm)", value="--")
        
        # ダム情報（小画面対応：列数を動的調整）
        st.markdown("### ダム情報")
        st.caption(f"更新時刻 : {obs_time_str}")
        dam_col1, dam_col2, dam_col3, dam_col4, dam_col5, dam_col6 = st.columns([1, 1, 1, 1, 1, 0.2])
        
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
                label="ダム名",
                value="厚東川ダム"
            )
        
        with dam_col6:
            # 空のカラム
            pass
    
    def get_common_time_range(self, history_data: List[Dict[str, Any]]) -> tuple:
        """履歴データから共通の時間範囲を取得（将来予測値を考慮）"""
        if not history_data:
            return None, None
        
        # 現在時刻（日本時間）
        now_jst = datetime.now(ZoneInfo('Asia/Tokyo'))
        
        # 履歴データの時間範囲を取得
        timestamps = []
        for item in history_data:
            data_time = item.get('data_time') or item.get('timestamp', '')
            try:
                dt = datetime.fromisoformat(data_time.replace('Z', '+00:00'))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=ZoneInfo('Asia/Tokyo'))
                else:
                    dt = dt.astimezone(ZoneInfo('Asia/Tokyo'))
                timestamps.append(dt)
            except:
                continue
        
        if not timestamps:
            return None, None
        
        # 履歴データの最古時刻を開始時刻とし、現在時刻+2時間を終了時刻とする
        time_min = min(timestamps)
        time_max = now_jst + timedelta(hours=2)
        
        return time_min, time_max
    
    def create_river_water_level_graph(self, history_data: List[Dict[str, Any]], enable_interaction: bool = False) -> go.Figure:
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
                    line=dict(color='#1f77b4', width=3),
                    marker=dict(size=8, color='white', line=dict(width=2, color='#1f77b4'))
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
                    line=dict(color='#d62728', width=3),
                    marker=dict(size=8, color='white', line=dict(width=2, color='#d62728'))
                ),
                secondary_y=True
            )
        
        # 軸の設定（小画面対応）
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
        
        # 共通の時間範囲を取得して設定
        time_min, time_max = self.get_common_time_range(history_data)
        xaxis_config = dict(
            title_text="時刻",
            title_font_size=12,
            tickfont_size=12
        )
        if time_min and time_max:
            xaxis_config['range'] = [time_min, time_max]
        
        fig.update_xaxes(**xaxis_config)
        
        fig.update_layout(
            height=400,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.25,
                xanchor="left",
                x=0.0,
                bgcolor="rgba(255, 255, 255, 0.8)",
                bordercolor="rgba(0, 0, 0, 0.2)",
                borderwidth=1
            ),
            margin=dict(t=30, l=40, r=40, b=100),
            autosize=True,
            font=dict(size=9)
        )
        
        # インタラクションが無効の場合は軸を固定
        if not enable_interaction:
            fig.update_xaxes(fixedrange=True)
            fig.update_yaxes(fixedrange=True, secondary_y=False)
            fig.update_yaxes(fixedrange=True, secondary_y=True)
        
        return fig
    
    def create_dam_water_level_graph(self, history_data: List[Dict[str, Any]], enable_interaction: bool = False) -> go.Figure:
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
            
            # Yahoo! Weather API降水強度データ
            precipitation_intensity = item.get('precipitation_intensity', {})
            if precipitation_intensity.get('observation'):
                # 最新の観測値を取得
                latest_obs = precipitation_intensity['observation'][-1] if precipitation_intensity['observation'] else None
                if latest_obs:
                    row['precipitation_intensity_obs'] = latest_obs.get('intensity', 0)
            
            if precipitation_intensity.get('forecast'):
                # 最新の予測値を取得
                latest_forecast = precipitation_intensity['forecast'][-1] if precipitation_intensity['forecast'] else None
                if latest_forecast:
                    row['precipitation_intensity_forecast'] = latest_forecast.get('intensity', 0)
            
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
                    line=dict(color='#ff7f0e', width=3),
                    marker=dict(size=8, color='white', line=dict(width=2, color='#ff7f0e'))
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
                    opacity=0.7,
                    width=600000
                ),
                secondary_y=True
            )
        
        # Yahoo! Weather API降水強度観測値（右軸）
        if 'precipitation_intensity_obs' in df.columns:
            fig.add_trace(
                go.Bar(
                    x=df['timestamp'],
                    y=df['precipitation_intensity_obs'],
                    name='降水強度・観測値（厚東川ダム）',
                    marker_color='#66CDAA',
                    opacity=0.8,
                    width=600000
                ),
                secondary_y=True
            )
        
        # Yahoo! Weather API降水強度予測値（右軸）
        if 'precipitation_intensity_forecast' in df.columns:
            fig.add_trace(
                go.Bar(
                    x=df['timestamp'],
                    y=df['precipitation_intensity_forecast'],
                    name='降水強度・予測値（厚東川ダム）',
                    marker_color='#98FB98',
                    opacity=0.6,
                    width=600000
                ),
                secondary_y=True
            )
        
        # 軸の設定（小画面対応）
        fig.update_yaxes(
            title_text="ダム貯水位 (m)",
            range=[0, 50],
            dtick=5,
            secondary_y=False,
            title_font_size=12,
            tickfont_size=12
        )
        fig.update_yaxes(
            title_text="時間雨量 (mm/h)",
            range=[0, 50],
            dtick=5,
            secondary_y=True,
            title_font_size=12,
            tickfont_size=12
        )
        
        # 共通の時間範囲を取得して設定
        time_min, time_max = self.get_common_time_range(history_data)
        xaxis_config = dict(
            title_text="時刻",
            title_font_size=12,
            tickfont_size=12
        )
        if time_min and time_max:
            xaxis_config['range'] = [time_min, time_max]
        
        fig.update_xaxes(**xaxis_config)
        
        fig.update_layout(
            height=400,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.25,
                xanchor="left",
                x=0.0,
                bgcolor="rgba(255, 255, 255, 0.8)",
                bordercolor="rgba(0, 0, 0, 0.2)",
                borderwidth=1
            ),
            margin=dict(t=30, l=40, r=40, b=100),
            autosize=True,
            font=dict(size=9)
        )
        
        # インタラクションが無効の場合は軸を固定
        if not enable_interaction:
            fig.update_xaxes(fixedrange=True)
            fig.update_yaxes(fixedrange=True, secondary_y=False)
            fig.update_yaxes(fixedrange=True, secondary_y=True)
        
        return fig
    
    def create_dam_flow_graph(self, history_data: List[Dict[str, Any]], enable_interaction: bool = False) -> go.Figure:
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
        
        # 累加雨量（右軸）- 最背面に配置するため最初に追加
        if 'cumulative_rainfall' in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=df['cumulative_rainfall'],
                    mode='lines+markers',
                    name='累加雨量（宇部市）',
                    line=dict(color='#87CEEB', width=3),
                    marker=dict(size=8, color='white', line=dict(width=2, color='#87CEEB')),
                    fill='tonexty'
                ),
                secondary_y=True
            )
        
        # ダム流入量（左軸）
        if 'inflow' in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=df['inflow'],
                    mode='lines+markers',
                    name='流入量（厚東川ダム）',
                    line=dict(color='#2ca02c', width=3),
                    marker=dict(size=8, color='white', line=dict(width=2, color='#2ca02c'))
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
                    line=dict(color='#d62728', width=3),
                    marker=dict(size=8, color='white', line=dict(width=2, color='#d62728'))
                ),
                secondary_y=False
            )
        
        # 軸の設定（小画面対応）
        fig.update_yaxes(
            title_text="流量 (m³/s)",
            range=[0, 900],
            dtick=100,
            secondary_y=False,
            title_font_size=12,
            tickfont_size=12
        )
        fig.update_yaxes(
            title_text="累加雨量 (mm)",
            range=[0, 180],
            dtick=20,
            secondary_y=True,
            title_font_size=12,
            tickfont_size=12
        )
        
        # 共通の時間範囲を取得して設定
        time_min, time_max = self.get_common_time_range(history_data)
        xaxis_config = dict(
            title_text="時刻",
            title_font_size=12,
            tickfont_size=12
        )
        if time_min and time_max:
            xaxis_config['range'] = [time_min, time_max]
        
        fig.update_xaxes(**xaxis_config)
        
        fig.update_layout(
            height=400,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.25,
                xanchor="left",
                x=0.0,
                bgcolor="rgba(255, 255, 255, 0.8)",
                bordercolor="rgba(0, 0, 0, 0.2)",
                borderwidth=1
            ),
            margin=dict(t=30, l=40, r=40, b=100),
            autosize=True,
            font=dict(size=9)
        )
        
        # インタラクションが無効の場合は軸を固定
        if not enable_interaction:
            fig.update_xaxes(fixedrange=True)
            fig.update_yaxes(fixedrange=True, secondary_y=False)
            fig.update_yaxes(fixedrange=True, secondary_y=True)
        
        return fig
    
    def create_precipitation_intensity_graph(self, precipitation_data: Dict[str, Any], enable_interaction: bool = True, history_data: List[Dict[str, Any]] = None) -> go.Figure:
        """降水強度グラフを作成"""
        from plotly.subplots import make_subplots
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # 観測データの処理
        obs_times = []
        obs_intensities = []
        
        if precipitation_data.get('observation'):
            for item in precipitation_data['observation']:
                try:
                    dt = datetime.fromisoformat(item['datetime'])
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=ZoneInfo('Asia/Tokyo'))
                    else:
                        dt = dt.astimezone(ZoneInfo('Asia/Tokyo'))
                    obs_times.append(dt)
                    obs_intensities.append(item['intensity'])
                except (ValueError, KeyError):
                    continue
        
        # 予測データの処理
        forecast_times = []
        forecast_intensities = []
        
        if precipitation_data.get('forecast'):
            for item in precipitation_data['forecast']:
                try:
                    dt = datetime.fromisoformat(item['datetime'])
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=ZoneInfo('Asia/Tokyo'))
                    else:
                        dt = dt.astimezone(ZoneInfo('Asia/Tokyo'))
                    forecast_times.append(dt)
                    forecast_intensities.append(item['intensity'])
                except (ValueError, KeyError):
                    continue
        
        # 観測データのプロット（棒グラフ、左軸）
        if obs_times and obs_intensities:
            fig.add_trace(go.Bar(
                x=obs_times,
                y=obs_intensities,
                name='降水強度・観測値（厚東川ダム）',
                marker=dict(color='#66CDAA'),
                hovertemplate='<b>観測値</b><br>%{x|%H:%M}<br>降水強度: %{y:.1f} mm/h<extra></extra>',
                width=600000
            ), secondary_y=False)
        
        # 予測データのプロット（棒グラフ、左軸）
        if forecast_times and forecast_intensities:
            fig.add_trace(go.Bar(
                x=forecast_times,
                y=forecast_intensities,
                name='降水強度・予測値（厚東川ダム）',
                marker=dict(color='#98FB98', opacity=0.7),
                hovertemplate='<b>予測値</b><br>%{x|%H:%M}<br>降水強度: %{y:.1f} mm/h<extra></extra>',
                width=600000
            ), secondary_y=False)
        
        # 時間雨量データの追加（右軸）
        if history_data:
            rainfall_times = []
            rainfall_values = []
            
            for item in history_data:
                # 観測時刻（data_time）を使用、なければtimestampを使用
                data_time = item.get('data_time') or item.get('timestamp', '')
                try:
                    dt = datetime.fromisoformat(data_time.replace('Z', '+00:00'))
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=ZoneInfo('Asia/Tokyo'))
                    else:
                        dt = dt.astimezone(ZoneInfo('Asia/Tokyo'))
                    
                    rainfall = item.get('rainfall', {}).get('hourly')
                    if rainfall is not None:
                        rainfall_times.append(dt)
                        rainfall_values.append(rainfall)
                except:
                    continue
            
            if rainfall_times and rainfall_values:
                fig.add_trace(go.Bar(
                    x=rainfall_times,
                    y=rainfall_values,
                    name='時間雨量（宇部市）',
                    marker=dict(color='#87CEEB', opacity=0.7),
                    hovertemplate='<b>時間雨量</b><br>%{x|%H:%M}<br>雨量: %{y:.1f} mm/h<extra></extra>',
                    width=600000
                ), secondary_y=True)
        
        # レイアウト設定
        fig.update_layout(
            height=400,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.25,
                xanchor="left",
                x=0.0,
                bgcolor="rgba(255, 255, 255, 0.8)",
                bordercolor="rgba(0, 0, 0, 0.2)",
                borderwidth=1
            ),
            margin=dict(t=30, l=40, r=40, b=100),
            autosize=True,
            font=dict(size=9)
        )
        
        # 軸設定 - 履歴データから共通の時間範囲を取得
        time_min, time_max = None, None
        if history_data:
            time_min, time_max = self.get_common_time_range(history_data)
        
        xaxis_config = dict(
            title_text="時刻",
            title_font_size=12,
            tickfont_size=12
        )
        if time_min and time_max:
            xaxis_config['range'] = [time_min, time_max]
        
        fig.update_xaxes(**xaxis_config)
        
        # 左軸（降水強度）の設定
        fig.update_yaxes(
            title_text="降水強度 (mm/h)",
            range=[0, 50],
            dtick=5,
            secondary_y=False,
            title_font_size=12,
            tickfont_size=12
        )
        
        # 右軸（時間雨量）の設定
        fig.update_yaxes(
            title_text="時間雨量 (mm/h)",
            range=[0, 50],
            dtick=5,
            secondary_y=True,
            title_font_size=12,
            tickfont_size=12
        )
        
        # インタラクションが無効の場合は軸を固定
        if not enable_interaction:
            fig.update_xaxes(fixedrange=True)
            fig.update_yaxes(fixedrange=True, secondary_y=False)
            fig.update_yaxes(fixedrange=True, secondary_y=True)
        
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
    
    # 固定ヘッダー用のプレースホルダー
    header_placeholder = st.empty()
    
    # メインコンテンツ用のコンテナ
    main_content = st.container()
    
    # サイドバー設定
    st.sidebar.header("設定")
    
    # 手動更新ボタン
    if st.sidebar.button("手動更新", type="primary", key="sidebar_refresh"):
        monitor.load_history_data.clear()
        st.cache_data.clear()
        st.rerun()
    
    # 自動更新設定
    refresh_interval = st.sidebar.selectbox(
        "自動更新間隔",
        options=[
            ("自動更新なし", 0),
            ("10分", 10 * 60 * 1000),
            ("30分", 30 * 60 * 1000),
            ("60分", 60 * 60 * 1000)
        ],
        index=1,  # デフォルトは10分
        format_func=lambda x: x[0]
    )
    
    # 自動更新の実行
    if refresh_interval[1] > 0:
        count = st_autorefresh(
            interval=refresh_interval[1],
            limit=None,
            key="autorefresh"
        )
    
    # 表示期間設定
    display_hours = st.sidebar.selectbox(
        "表示期間",
        [6, 12, 24, 48, 72],
        index=2,
        format_func=lambda x: f"{x}時間"
    )
    
    # グラフ操作設定
    enable_graph_interaction = st.sidebar.checkbox(
        "グラフの編集の有効化",
        value=False,
        help="チェックを入れるとグラフの拡大・縮小・移動が可能になります"
    )
    
    # 週間天気表示設定
    show_weekly_weather = st.sidebar.checkbox(
        "週間天気を表示",
        value=True,
        help="チェックを外すと週間天気予報を非表示にします"
    )
    
    # アラート閾値設定
    st.sidebar.subheader("アラート設定")
    river_warning = st.sidebar.number_input("河川警戒水位 (m)", value=3.8, step=0.1)
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
    with st.spinner('データを更新中...'):
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
    
    # アラート表示とステータス情報の準備
    alert_status = ""
    update_info = ""
    
    if latest_data:
        alerts = monitor.check_alert_status(latest_data, thresholds)
        
        # アラート詳細情報
        alert_details = []
        if alerts['river'] != '正常':
            alert_details.append(f"河川: {alerts['river']}")
        if alerts['dam'] != '正常':
            alert_details.append(f"ダム: {alerts['dam']}")
        
        # ステータス表示文の作成
        if alerts['overall'] == '危険':
            alert_status = f"危険 **危険レベル** : 緊急対応が必要です"
            if alert_details:
                alert_status += f" ({' ｜ '.join(alert_details)})"
        elif alerts['overall'] == '警戒':
            alert_status = f"注意 **警戒レベル** : 注意が必要です"
            if alert_details:
                alert_status += f" ({' ｜ '.join(alert_details)})"
        elif alerts['overall'] == '注意':
            alert_status = f"情報 **注意レベル** : 状況を監視中"
            if alert_details:
                alert_status += f" ({' ｜ '.join(alert_details)})"
        elif alerts['overall'] == '正常':
            alert_status = "**監視状況** : 正常 - 安全な状態です"
        else:
            alert_status = "情報 データ確認中..."
        
        # 更新時刻情報の作成
        if latest_data.get('timestamp'):
            try:
                timestamp = datetime.fromisoformat(latest_data['timestamp'].replace('Z', '+00:00'))
                if timestamp.tzinfo is None:
                    timestamp = timestamp.replace(tzinfo=ZoneInfo('Asia/Tokyo'))
                
                data_time_str = latest_data.get('data_time', '')
                if data_time_str:
                    data_time = datetime.fromisoformat(data_time_str.replace('Z', '+00:00'))
                    if data_time.tzinfo is None:
                        data_time = data_time.replace(tzinfo=ZoneInfo('Asia/Tokyo'))
                    now = datetime.now(ZoneInfo('Asia/Tokyo'))
                    update_info = f"観測時刻 : {data_time.strftime('%Y年%m月%d日 %H:%M')} ｜ 取得時刻 : {timestamp.strftime('%Y年%m月%d日 %H:%M:%S')}"
                    if refresh_interval[1] > 0:
                        update_info += f" ｜ 最終確認 : {now.strftime('%H:%M:%S')}"
                else:
                    update_info = f"最終更新 : {timestamp.strftime('%Y年%m月%d日 %H:%M:%S')}"
            except Exception as e:
                update_info = f"最終更新 : {latest_data.get('timestamp', '不明')} (時刻解析エラー)"
    else:
        alert_status = "注意 データが取得できていません"
        update_info = "データ取得中..."
    
    # 固定ヘッダーの内容を設定
    with header_placeholder.container():
        st.markdown('<div class="fixed-header">', unsafe_allow_html=True)
        st.markdown("<h1 style='text-align: center; margin: 0;'>厚東川氾濫監視システムv2.0</h1>", unsafe_allow_html=True)
        
        # アラート状態表示
        if "危険" in alert_status:
            st.error(alert_status)
        elif "警戒" in alert_status:
            st.warning(alert_status)
        elif "注意" in alert_status:
            st.info(alert_status)
        elif "正常" in alert_status:
            st.success(alert_status)
        else:
            st.info(alert_status)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # メインコンテンツ
    st.markdown('<div class="main-content">', unsafe_allow_html=True)
    
    # 現在の状況表示
    monitor.create_metrics_display(latest_data)
    
    # 天気予報表示
    monitor.create_weather_forecast_display(latest_data, show_weekly_weather)
    
    # データ分析表示
    monitor.create_data_analysis_display(history_data, enable_graph_interaction)
    
    # システム情報（サイドバー）
    st.sidebar.subheader("システム情報")
    
    # 観測時刻の表示
    if latest_data and latest_data.get('data_time'):
        try:
            # data_timeを使用（観測時刻）
            obs_time = datetime.fromisoformat(latest_data['data_time'].replace('Z', '+00:00'))
            if obs_time.tzinfo is None:
                obs_time = obs_time.replace(tzinfo=ZoneInfo('Asia/Tokyo'))
            
            # 現在時刻（日本時間）
            now_jst = datetime.now(ZoneInfo('Asia/Tokyo'))
            time_diff = now_jst - obs_time
            minutes_ago = int(time_diff.total_seconds() / 60)
            
            if minutes_ago < 60:
                st.sidebar.success(f"● 観測時刻 ({minutes_ago}分前)")
            elif minutes_ago < 120:
                st.sidebar.warning(f"● 観測時刻 ({minutes_ago}分前)")
            else:
                st.sidebar.error(f"● 観測時刻 ({minutes_ago}分前)")
        except:
            st.sidebar.info("● 観測時刻確認中")
    
    # データ統計
    st.sidebar.info(f"■ データ件数: {len(history_data)}件")
    
    # 警戒レベル説明
    with st.sidebar.expander("■ 警戒レベル説明"):
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
    with st.sidebar.expander("■ データソース"):
        st.write("""
        **厚東川ダム**
        - 観測地点: 宇部市
        - 更新間隔: 10分
        
        **厚東川(持世寺)**
        - 観測地点: 宇部市持世寺
        - 更新間隔: 10分
        
        データ提供: 山口県土木防災情報システム
        """)
    
    # アプリ情報
    st.sidebar.markdown("---")
    st.sidebar.caption("厚東川リアルタイム監視システム v2.0")
    st.sidebar.caption("Powered by Streamlit")
    
    # メインコンテンツのdivを閉じる
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()