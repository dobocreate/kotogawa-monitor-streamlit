#!/usr/bin/env python3
"""
厚東川監視システム データ収集スクリプト（簡素版）
HTMLテーブルから数値データのみを取得
"""

import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Any, Union
import requests
from bs4 import BeautifulSoup

class KotogawaDataCollectorSimple:
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.data_dir = self.base_dir / "data"
        self.history_dir = self.data_dir / "history"
        
        # Create directories if they don't exist
        self.data_dir.mkdir(exist_ok=True)
        self.history_dir.mkdir(exist_ok=True)
        
        # URLs for data sources
        self.dam_url = "https://y-bousai.pref.yamaguchi.lg.jp/citizen/dam/kdm_graph.aspx"
        self.river_url = "https://y-bousai.pref.yamaguchi.lg.jp/citizen/water/kwl_graph.aspx"
        
        # Request settings
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.timeout = 30
        
    def fetch_page(self, url: str, params: Dict[str, str]) -> Optional[BeautifulSoup]:
        """指定されたURLからHTMLを取得"""
        try:
            response = requests.get(url, params=params, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    def collect_dam_data(self) -> Dict[str, Union[float, None]]:
        """ダムデータを収集する - テーブル解析のみ"""
        params = {'stncd': '015'}
        soup = self.fetch_page(self.dam_url, params)
        
        if not soup:
            return {
                'water_level': None,
                'storage_rate': None,
                'inflow': None,
                'outflow': None,
                'storage_change': None
            }
        
        dam_data = {
            'water_level': None,
            'storage_rate': None,
            'inflow': None,
            'outflow': None,
            'storage_change': None
        }
        
        try:
            # HTMLテーブルから数値を直接取得
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                
                # 最新のデータ行を探す（最後から検索）
                for row in reversed(rows):
                    cells = row.find_all('td')
                    if len(cells) >= 4:  # 時刻を含む4列以上のテーブル
                        values = []
                        time_found = False
                        
                        for cell in cells:
                            text = cell.get_text().strip()
                            
                            # 時刻パターンがあるかチェック
                            if re.match(r'\d{1,2}:\d{2}', text):
                                time_found = True
                            
                            # 数値を抽出
                            try:
                                if '.' in text and re.match(r'^\d+\.\d+$', text):
                                    value = float(text)
                                    values.append(value)
                            except:
                                continue
                        
                        # 時刻を含む行で数値が取得できた場合
                        if time_found and values:
                            # 値の範囲で判定
                            for value in values:
                                if 30 <= value <= 40:  # ダム水位
                                    if dam_data['water_level'] is None:
                                        dam_data['water_level'] = value
                                elif 90 <= value <= 100:  # 貯水率
                                    if dam_data['storage_rate'] is None:
                                        dam_data['storage_rate'] = value
                                elif 0 < value < 50:  # 流入・流出量
                                    if dam_data['inflow'] is None:
                                        dam_data['inflow'] = value
                                    elif dam_data['outflow'] is None:
                                        dam_data['outflow'] = value
                            
                            # 最新行で必要なデータが取得できたら終了
                            if dam_data['water_level'] is not None:
                                break
            
            # 貯水率が取得できない場合は水位から計算
            if dam_data['water_level'] and not dam_data['storage_rate']:
                level = dam_data['water_level']
                # 水位20-40mを0-100%にマッピング
                dam_data['storage_rate'] = round(((level - 20) / (40 - 20)) * 100, 1)
                
        except Exception as e:
            print(f"Error extracting dam data: {e}")
        
        return dam_data
    
    def collect_river_data(self) -> Dict[str, Any]:
        """河川データを収集する - テーブル解析のみ"""
        params = {'stncd': '067'}
        soup = self.fetch_page(self.river_url, params)
        
        if not soup:
            return {
                'water_level': None,
                'level_change': None,
                'status': 'データなし'
            }
        
        river_data = {
            'water_level': None,
            'level_change': None,
            'status': '正常'
        }
        
        # 警戒レベル閾値
        thresholds = {
            'preparedness': 3.80,
            'caution': 5.00,
            'evacuation': 5.10,
            'danger': 5.50
        }
        
        try:
            # HTMLテーブルから数値を取得
            tables = soup.find_all('table')
            water_levels = []
            
            for table in tables:
                rows = table.find_all('tr')
                
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        row_text = ' '.join([cell.get_text().strip() for cell in cells])
                        
                        # 時刻パターンがある行
                        if re.search(r'\d{1,2}:\d{2}', row_text):
                            for cell in cells:
                                text = cell.get_text().strip()
                                
                                # 水位数値パターン
                                if re.match(r'^\d+\.\d{2}$', text):
                                    try:
                                        level = float(text)
                                        # 合理的な水位範囲（警戒水位値を除外）
                                        if (1.0 <= level <= 10.0 and 
                                            level not in thresholds.values()):
                                            water_levels.append(level)
                                    except:
                                        continue
            
            # 最新値を使用
            if water_levels:
                river_data['water_level'] = water_levels[-1]
                
                # 変化量計算
                if len(water_levels) > 1:
                    river_data['level_change'] = round(water_levels[-1] - water_levels[-2], 2)
                
                # 警戒レベル判定
                level = river_data['water_level']
                if level >= thresholds['danger']:
                    river_data['status'] = '氾濫危険'
                elif level >= thresholds['evacuation']:
                    river_data['status'] = '避難判断'
                elif level >= thresholds['caution']:
                    river_data['status'] = '氾濫注意'
                elif level >= thresholds['preparedness']:
                    river_data['status'] = '水防団待機'
                else:
                    river_data['status'] = '正常'
                    
        except Exception as e:
            print(f"Error extracting river data: {e}")
        
        return river_data
    
    def collect_rainfall_data(self) -> Dict[str, Any]:
        """雨量データを収集する"""
        # ダムページから雨量データも取得
        params = {'stncd': '015'}
        soup = self.fetch_page(self.dam_url, params)
        
        rainfall_data = {'hourly': 0, 'cumulative': 0, 'change': 0}
        
        if not soup:
            return rainfall_data
        
        try:
            # テーブルから雨量データを取得
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                
                # ヘッダー行を確認
                header_found = False
                rain_col = -1
                cumulative_col = -1
                
                for row in rows:
                    cells = row.find_all(['th', 'td'])
                    if not header_found:
                        # ヘッダー行をチェック
                        for i, cell in enumerate(cells):
                            text = cell.get_text().strip()
                            if '60分' in text or '時間雨量' in text:
                                rain_col = i
                            elif '累積' in text:
                                cumulative_col = i
                        header_found = True
                    else:
                        # データ行を処理
                        if len(cells) > max(rain_col, cumulative_col) and rain_col >= 0:
                            try:
                                # 時刻パターンがある行
                                time_text = cells[0].get_text().strip()
                                if re.match(r'\d{1,2}:\d{2}', time_text):
                                    if rain_col >= 0:
                                        rain_text = cells[rain_col].get_text().strip()
                                        if rain_text.isdigit():
                                            rainfall_data['hourly'] = int(rain_text)
                                    
                                    if cumulative_col >= 0:
                                        cum_text = cells[cumulative_col].get_text().strip()
                                        if cum_text.isdigit():
                                            rainfall_data['cumulative'] = int(cum_text)
                            except:
                                continue
                        
        except Exception as e:
            print(f"Error extracting rainfall data: {e}")
        
        return rainfall_data
    
    def save_data(self, data: Dict[str, Any]) -> None:
        """データを保存する"""
        timestamp = datetime.now()
        
        # 最新データを保存
        latest_file = self.data_dir / "latest.json"
        with open(latest_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        
        # 履歴データを保存
        date_dir = self.history_dir / timestamp.strftime("%Y") / timestamp.strftime("%m") / timestamp.strftime("%d")
        date_dir.mkdir(parents=True, exist_ok=True)
        
        history_file = date_dir / f"{timestamp.strftime('%H%M')}.json"
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"Data saved: {timestamp}")
    
    def cleanup_old_data(self, days_to_keep: int = 7) -> None:
        """古いデータを削除する"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        for year_dir in self.history_dir.iterdir():
            if not year_dir.is_dir():
                continue
                
            try:
                year = int(year_dir.name)
                if year < cutoff_date.year:
                    import shutil
                    shutil.rmtree(year_dir)
                    print(f"Removed old data directory: {year_dir}")
            except:
                continue
    
    def collect_all_data(self) -> Dict[str, Any]:
        """全てのデータを収集する"""
        print("Starting data collection...")
        
        # データ収集
        dam_data = self.collect_dam_data()
        river_data = self.collect_river_data()
        rainfall_data = self.collect_rainfall_data()
        
        # データを統合
        data = {
            'timestamp': datetime.now().isoformat(),
            'dam': dam_data,
            'river': river_data,
            'rainfall': rainfall_data
        }
        
        # データ保存
        self.save_data(data)
        
        # 古いデータのクリーンアップ
        self.cleanup_old_data()
        
        print("Data collection completed successfully")
        return data

def main():
    """メイン関数"""
    collector = KotogawaDataCollectorSimple()
    
    try:
        data = collector.collect_all_data()
        print("Collection successful!")
        print(f"Latest data: {json.dumps(data, ensure_ascii=False, indent=2, default=str)}")
    except Exception as e:
        print(f"Error during data collection: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())