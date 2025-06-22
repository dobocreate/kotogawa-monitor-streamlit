#!/usr/bin/env python3
"""
厚東川監視システム データ処理スクリプト
収集データの処理、分析、統計計算を行う
"""

import json
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

class KotogawaDataProcessor:
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.data_dir = self.base_dir / "data"
        self.history_dir = self.data_dir / "history"
    
    def load_historical_data(self, hours: int = 24) -> List[Dict[str, Any]]:
        """指定時間の履歴データを読み込む"""
        history_data = []
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        current_time = start_time
        while current_time <= end_time:
            date_dir = (self.history_dir / 
                       current_time.strftime("%Y") / 
                       current_time.strftime("%m") / 
                       current_time.strftime("%d"))
            
            if date_dir.exists():
                for file_path in sorted(date_dir.glob("*.json")):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            history_data.append(data)
                    except Exception as e:
                        print(f"Error loading {file_path}: {e}")
            
            current_time += timedelta(days=1)
        
        # 時系列順にソート
        history_data.sort(key=lambda x: x.get('timestamp', ''))
        return history_data
    
    def create_dataframe(self, history_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """履歴データをDataFrameに変換"""
        df_data = []
        
        for item in history_data:
            timestamp = item.get('timestamp', '')
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except:
                continue
            
            row = {
                'timestamp': dt,
                'river_level': item.get('river', {}).get('water_level'),
                'river_status': item.get('river', {}).get('status'),
                'river_change': item.get('river', {}).get('level_change'),
                'dam_level': item.get('dam', {}).get('water_level'),
                'dam_storage': item.get('dam', {}).get('storage_rate'),
                'dam_inflow': item.get('dam', {}).get('inflow'),
                'dam_outflow': item.get('dam', {}).get('outflow'),
                'rainfall_hourly': item.get('rainfall', {}).get('hourly'),
                'rainfall_cumulative': item.get('rainfall', {}).get('cumulative')
            }
            df_data.append(row)
        
        df = pd.DataFrame(df_data)
        if not df.empty:
            df.set_index('timestamp', inplace=True)
        
        return df
    
    def calculate_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """統計情報を計算"""
        if df.empty:
            return {}
        
        stats = {}
        
        # 河川水位統計
        if 'river_level' in df.columns and not df['river_level'].isna().all():
            river_data = df['river_level'].dropna()
            stats['river'] = {
                'current': river_data.iloc[-1] if not river_data.empty else None,
                'max': river_data.max(),
                'min': river_data.min(),
                'mean': river_data.mean(),
                'trend': self._calculate_trend(river_data)
            }
        
        # ダム統計
        if 'dam_level' in df.columns and not df['dam_level'].isna().all():
            dam_data = df['dam_level'].dropna()
            stats['dam'] = {
                'current': dam_data.iloc[-1] if not dam_data.empty else None,
                'max': dam_data.max(),
                'min': dam_data.min(),
                'mean': dam_data.mean(),
                'trend': self._calculate_trend(dam_data)
            }
        
        # 雨量統計
        if 'rainfall_hourly' in df.columns and not df['rainfall_hourly'].isna().all():
            rain_data = df['rainfall_hourly'].dropna()
            stats['rainfall'] = {
                'current': rain_data.iloc[-1] if not rain_data.empty else None,
                'max': rain_data.max(),
                'total_24h': rain_data.sum(),
                'mean': rain_data.mean()
            }
        
        return stats
    
    def _calculate_trend(self, data: pd.Series) -> str:
        """データのトレンドを計算"""
        if len(data) < 2:
            return "不明"
        
        # 最新の値と平均を比較
        recent_mean = data.tail(3).mean()
        overall_mean = data.mean()
        
        if recent_mean > overall_mean * 1.1:
            return "上昇"
        elif recent_mean < overall_mean * 0.9:
            return "下降"
        else:
            return "安定"
    
    def detect_anomalies(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """異常値を検出"""
        anomalies = []
        
        if df.empty:
            return anomalies
        
        # 河川水位の急激な変化を検出
        if 'river_level' in df.columns:
            river_data = df['river_level'].dropna()
            if len(river_data) > 1:
                changes = river_data.diff().abs()
                threshold = river_data.std() * 2  # 2σを閾値とする
                
                for idx, change in changes.items():
                    if change > threshold and change > 0.5:  # 0.5m以上の急変
                        anomalies.append({
                            'type': 'river_sudden_change',
                            'timestamp': idx,
                            'value': change,
                            'description': f'河川水位の急激な変化: {change:.2f}m'
                        })
        
        # 雨量の異常値検出
        if 'rainfall_hourly' in df.columns:
            rain_data = df['rainfall_hourly'].dropna()
            if len(rain_data) > 0:
                # 50mm/h以上は異常値として検出
                high_rain = rain_data[rain_data >= 50]
                for idx, value in high_rain.items():
                    anomalies.append({
                        'type': 'heavy_rainfall',
                        'timestamp': idx,
                        'value': value,
                        'description': f'大雨警報レベル: {value}mm/h'
                    })
        
        return anomalies
    
    def generate_summary_report(self, hours: int = 24) -> Dict[str, Any]:
        """サマリーレポートを生成"""
        history_data = self.load_historical_data(hours)
        df = self.create_dataframe(history_data)
        stats = self.calculate_statistics(df)
        anomalies = self.detect_anomalies(df)
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'period_hours': hours,
            'data_points': len(history_data),
            'statistics': stats,
            'anomalies': anomalies,
            'status_summary': self._generate_status_summary(stats, anomalies)
        }
        
        return report
    
    def _generate_status_summary(self, stats: Dict[str, Any], anomalies: List[Dict[str, Any]]) -> Dict[str, str]:
        """状況サマリーを生成"""
        summary = {
            'overall': '正常',
            'river': '正常',
            'dam': '正常',
            'rainfall': '正常'
        }
        
        # 異常値の有無をチェック
        for anomaly in anomalies:
            if anomaly['type'] == 'river_sudden_change':
                summary['river'] = '注意'
                summary['overall'] = '注意'
            elif anomaly['type'] == 'heavy_rainfall':
                summary['rainfall'] = '警戒'
                summary['overall'] = '警戒'
        
        # 統計値による判定
        if 'river' in stats and stats['river'].get('current'):
            current_level = stats['river']['current']
            if current_level >= 5.0:
                summary['river'] = '危険'
                summary['overall'] = '危険'
            elif current_level >= 3.8:
                summary['river'] = '警戒'
                if summary['overall'] == '正常':
                    summary['overall'] = '警戒'
        
        return summary
    
    def export_to_csv(self, hours: int = 24, output_path: Optional[str] = None) -> str:
        """データをCSVファイルにエクスポート"""
        history_data = self.load_historical_data(hours)
        df = self.create_dataframe(history_data)
        
        if output_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = self.data_dir / f"kotogawa_export_{timestamp}.csv"
        
        df.to_csv(output_path, encoding='utf-8-sig')
        return str(output_path)

def main():
    """メイン関数"""
    processor = KotogawaDataProcessor()
    
    # 24時間のサマリーレポートを生成
    report = processor.generate_summary_report(24)
    
    print("=== 厚東川監視システム サマリーレポート ===")
    print(f"生成時刻: {report['generated_at']}")
    print(f"対象期間: {report['period_hours']}時間")
    print(f"データ件数: {report['data_points']}件")
    print()
    
    print("--- 状況サマリー ---")
    for key, value in report['status_summary'].items():
        print(f"{key}: {value}")
    print()
    
    if report['statistics']:
        print("--- 統計情報 ---")
        for category, stats in report['statistics'].items():
            print(f"{category}:")
            for key, value in stats.items():
                if isinstance(value, float):
                    print(f"  {key}: {value:.2f}")
                else:
                    print(f"  {key}: {value}")
        print()
    
    if report['anomalies']:
        print("--- 異常検出 ---")
        for anomaly in report['anomalies']:
            print(f"- {anomaly['description']}")
            print(f"  時刻: {anomaly['timestamp']}")
            print(f"  値: {anomaly['value']}")
        print()
    
    # CSVエクスポート
    csv_path = processor.export_to_csv(24)
    print(f"CSVエクスポート完了: {csv_path}")

if __name__ == "__main__":
    main()