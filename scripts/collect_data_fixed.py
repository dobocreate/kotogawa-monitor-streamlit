#!/usr/bin/env python3
"""
厚東川監視システム データ収集スクリプト（修正版）
より正確なデータ取得のための改良版
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any, Union
import requests
from bs4 import BeautifulSoup

class KotogawaDataCollectorFixed:
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
        """ダムデータを収集する - 修正版"""
        params = {'stncd': '015'}
        soup = self.fetch_page(self.dam_url, params)
        
        if not soup:
            return {'water_level': None, 'storage_rate': None, 'inflow': None, 'outflow': None}
        
        dam_data = {'water_level': None, 'storage_rate': None, 'inflow': None, 'outflow': None}
        
        try:
            # JavaScriptコードからデータを抽出
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string and 'c1compositechart' in script.string:
                    script_text = script.string
                    
                    # 貯水位データの配列を検索
                    water_level_match = re.search(r'貯水位.*?\[([\d.,\s]+)\]', script_text, re.DOTALL)
                    if water_level_match:
                        values = [float(v.strip()) for v in water_level_match.group(1).split(',') if v.strip()]
                        if values:
                            dam_data['water_level'] = values[-1]  # 最新値
                    
                    # 貯水率データの配列を検索  
                    storage_match = re.search(r'貯水率.*?\[([\d.,\s]+)\]', script_text, re.DOTALL)
                    if storage_match:
                        values = [float(v.strip()) for v in storage_match.group(1).split(',') if v.strip()]
                        if values:
                            dam_data['storage_rate'] = values[-1]
                    
                    # 流入量データ
                    inflow_match = re.search(r'流入量.*?\[([\d.,\s]+)\]', script_text, re.DOTALL)
                    if inflow_match:
                        values = [float(v.strip()) for v in inflow_match.group(1).split(',') if v.strip()]
                        if values:
                            dam_data['inflow'] = values[-1]
                    
                    # 流出量データ
                    outflow_match = re.search(r'放流量.*?\[([\d.,\s]+)\]', script_text, re.DOTALL)
                    if outflow_match:
                        values = [float(v.strip()) for v in outflow_match.group(1).split(',') if v.strip()]
                        if values:
                            dam_data['outflow'] = values[-1]
            
            # HTMLのテーブルからも確認
            if dam_data['water_level'] is None:
                tables = soup.find_all('table')
                for table in tables:
                    # ヘッダーを確認
                    headers = []
                    header_row = table.find('tr')
                    if header_row:
                        headers = [th.get_text().strip() for th in header_row.find_all(['th', 'td'])]
                    
                    # 貯水位の列を特定
                    water_level_col = -1
                    for i, header in enumerate(headers):
                        if '貯水位' in header:
                            water_level_col = i
                            break
                    
                    if water_level_col >= 0:
                        # データ行を確認
                        rows = table.find_all('tr')[1:]  # ヘッダーをスキップ
                        for row in reversed(rows):  # 最新のデータから確認
                            cells = row.find_all(['td'])
                            if len(cells) > water_level_col:
                                try:
                                    value = float(cells[water_level_col].get_text().strip())
                                    if 30 <= value <= 40:  # ダム水位の妥当性チェック
                                        dam_data['water_level'] = value
                                        break
                                except:
                                    continue
                        
        except Exception as e:
            print(f"Error extracting dam data: {e}")
        
        return dam_data
    
    def collect_river_data(self) -> Dict[str, Any]:
        """河川データを収集する - 修正版"""
        params = {'stncd': '067'}
        soup = self.fetch_page(self.river_url, params)
        
        if not soup:
            return {'water_level': None, 'level_change': None, 'status': 'データなし'}
        
        river_data = {'water_level': None, 'level_change': None, 'status': '正常'}
        
        # 警戒レベル閾値
        thresholds = {
            'preparedness': 3.80,
            'caution': 5.00,
            'evacuation': 5.10,
            'danger': 5.50
        }
        
        try:
            # JavaScriptコードからデータを抽出
            scripts = soup.find_all('script')
            water_levels = []
            
            for script in scripts:
                if script.string and 'c1compositechart' in script.string:
                    script_text = script.string
                    
                    # 水位データの配列を検索
                    water_match = re.search(r'水位.*?\[([\d.,\s]+)\]', script_text, re.DOTALL)
                    if water_match:
                        values = water_match.group(1).split(',')
                        for v in values:
                            try:
                                level = float(v.strip())
                                # 警戒水位値を除外し、妥当な範囲の値のみ
                                if (level not in thresholds.values() and 
                                    0.5 <= level <= 10):
                                    water_levels.append(level)
                            except:
                                continue
            
            # HTMLテーブルからも確認
            if not water_levels:
                tables = soup.find_all('table')
                for table in tables:
                    # ヘッダーを確認
                    headers = []
                    header_row = table.find('tr')
                    if header_row:
                        headers = [th.get_text().strip() for th in header_row.find_all(['th', 'td'])]
                    
                    # 水位列を特定
                    water_col = -1
                    for i, header in enumerate(headers):
                        if '水位' in header and '警戒' not in header:
                            water_col = i
                            break
                    
                    if water_col >= 0:
                        rows = table.find_all('tr')[1:]
                        for row in rows:
                            cells = row.find_all(['td'])
                            if len(cells) > water_col:
                                try:
                                    # 時刻列があることを確認（データ行の識別）
                                    time_text = cells[0].get_text().strip()
                                    if re.match(r'\d{1,2}:\d{2}', time_text):
                                        value = float(cells[water_col].get_text().strip())
                                        if (value not in thresholds.values() and 
                                            0.5 <= value <= 10):
                                            water_levels.append(value)
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
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string:
                    script_text = script.string
                    
                    # 60分雨量の配列を検索
                    hourly_match = re.search(r'60分雨量.*?\[([\d.,\s]+)\]', script_text, re.DOTALL)
                    if hourly_match:
                        values = [float(v.strip()) for v in hourly_match.group(1).split(',') if v.strip()]
                        if values:
                            rainfall_data['hourly'] = int(values[-1])
                    
                    # 累積雨量の配列を検索
                    cumulative_match = re.search(r'累積雨量.*?\[([\d.,\s]+)\]', script_text, re.DOTALL)
                    if cumulative_match:
                        values = [float(v.strip()) for v in cumulative_match.group(1).split(',') if v.strip()]
                        if values:
                            rainfall_data['cumulative'] = int(values[-1])
                            
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
        
        print("Data collection completed successfully")
        return data

def main():
    """メイン関数"""
    collector = KotogawaDataCollectorFixed()
    
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