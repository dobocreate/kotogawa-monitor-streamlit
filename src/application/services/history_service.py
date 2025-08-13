"""
履歴データサービス
リポジトリから取得したデータをプレゼンテーション層向けに変換
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
import streamlit as st

from src.infrastructure.repositories.history_repository import HistoryRepository


class HistoryService:
    """履歴データサービス"""
    
    def __init__(self, base_dir: Optional[Path] = None):
        """
        Args:
            base_dir: プロジェクトのベースディレクトリ
        """
        self.repository = HistoryRepository(base_dir)
    
    def get_current_data(self) -> Optional[Dict[str, Any]]:
        """現在の最新データを取得"""
        latest_data = self.repository.load_latest_data()
        
        if not latest_data:
            return None
        
        # プレゼンテーション層向けのデータ構造に変換
        return self._format_current_data(latest_data)
    
    @st.cache_data(ttl=300)  # 5分間キャッシュ
    def get_historical_data(_self, hours: int = 24) -> Dict[str, Any]:
        """履歴データを取得してグラフ用の形式に変換
        
        Args:
            hours: 取得する時間数
        
        Returns:
            グラフ描画用にフォーマットされたデータ
        """
        history_data = _self.repository.load_history_data(hours)
        
        if not history_data:
            return {}
        
        # グラフ用データの構造に変換
        return _self._format_historical_data(history_data, hours)
    
    def _format_current_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """現在のデータをフォーマット"""
        # タイムスタンプの解析
        timestamp = data.get('timestamp', '')
        if timestamp:
            try:
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except:
                timestamp = datetime.now()
        else:
            timestamp = datetime.now()
        
        # データ構造の変換（DashboardPageが期待する形式）
        return {
            'timestamp': timestamp,
            'river': {
                'water_level': data.get('river', {}).get('water_level', 0),
                'level_change': data.get('river', {}).get('level_change', 0),
                'status': data.get('river', {}).get('status', '正常'),
                'location': '持世寺',
            },
            'rainfall': {
                'hour_60': data.get('rainfall', {}).get('hourly', 0),
                'hourly': data.get('rainfall', {}).get('hourly', 0),
                'cumulative': data.get('rainfall', {}).get('cumulative', 0)
            },
            'dam': {
                'water_level': data.get('dam', {}).get('water_level', 0),
                'storage_rate': data.get('dam', {}).get('storage_rate', 0),
                'inflow': data.get('dam', {}).get('inflow', 0),
                'outflow': data.get('dam', {}).get('outflow', 0),
                'name': '厚東川ダム',
                'status': '正常'
            },
            'alerts': [],
            'status': 'normal'
        }
    
    def _format_historical_data(self, history_data: List[Dict[str, Any]], hours: int) -> Dict[str, Any]:
        """履歴データをグラフ用にフォーマット"""
        # 表示期間のフィルタリング
        now = datetime.now()
        start_time = now - timedelta(hours=hours)
        
        # データの抽出
        times = []
        river_levels = []
        dam_levels = []
        dam_discharge = []
        hourly_rain = []
        cumulative_rain = []
        inflow = []
        outflow = []
        discharge = []  # 全放流量
        intensity = []  # 降水強度（予測）
        
        for item in history_data:
            # タイムスタンプの解析
            try:
                # data_timeを優先、なければtimestamp
                time_str = item.get('data_time', item.get('timestamp', ''))
                if time_str:
                    data_time = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                    
                    # 時間範囲のフィルタリング
                    if data_time < start_time:
                        continue
                    
                    times.append(data_time)
                    
                    # 各データの抽出
                    river_data = item.get('river', {})
                    dam_data = item.get('dam', {})
                    rain_data = item.get('rainfall', {})
                    
                    river_levels.append(river_data.get('water_level', 0))
                    dam_levels.append(dam_data.get('water_level', 0))
                    dam_discharge.append(dam_data.get('outflow', 0))
                    hourly_rain.append(rain_data.get('hourly', 0))
                    cumulative_rain.append(rain_data.get('cumulative', 0))
                    inflow.append(dam_data.get('inflow', 0))
                    outflow.append(dam_data.get('outflow', 0))
                    discharge.append(dam_data.get('outflow', 0))  # 全放流量として使用
                    
                    # 降水強度（現時点では観測値と同じにする）
                    intensity.append(rain_data.get('hourly', 0))
                    
            except Exception:
                continue
        
        # グラフ描画用の辞書形式で返す
        return {
            'times': times,
            'river_levels': river_levels,
            'dam_levels': dam_levels,
            'dam_discharge': dam_discharge,
            'hourly_rain': hourly_rain,
            'cumulative_rain': cumulative_rain,
            'inflow': inflow,
            'outflow': outflow,
            'discharge': discharge,
            'intensity': intensity,
            # 元の履歴データも保持（テーブル表示用）
            'raw_data': history_data[-100:] if len(history_data) > 100 else history_data
        }