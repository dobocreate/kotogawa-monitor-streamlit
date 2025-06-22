#!/usr/bin/env python3
"""
厚東川監視システム データ収集スクリプト
山口県土木防災情報システムからデータを取得し、JSON形式で保存する
"""

import json
import os
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Any, Union
import requests
from bs4 import BeautifulSoup

class KotogawaDataCollector:
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.data_dir = self.base_dir / "data"
        self.history_dir = self.data_dir / "history"
        
        # Create directories if they don't exist
        self.data_dir.mkdir(exist_ok=True)
        self.history_dir.mkdir(exist_ok=True)
        
        # URLs for data sources
        self.dam_url = "https://y-bousai.pref.yamaguchi.lg.jp/citizen/dam/kdm_table.aspx"
        self.river_url = "https://y-bousai.pref.yamaguchi.lg.jp/citizen/water/kwl_table.aspx"
        
        # Request settings
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.timeout = 30
        self.max_retries = 3
        
    def fetch_page(self, url: str, params: Dict[str, str]) -> Optional[BeautifulSoup]:
        """指定されたURLからHTMLを取得し、BeautifulSoupオブジェクトを返す"""
        for attempt in range(self.max_retries):
            try:
                response = requests.get(
                    url, 
                    params=params, 
                    headers=self.headers, 
                    timeout=self.timeout
                )
                response.raise_for_status()
                return BeautifulSoup(response.content, 'html.parser')
            except requests.RequestException as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(5)  # Wait before retry
                else:
                    print(f"Failed to fetch {url} after {self.max_retries} attempts")
                    return None
    
    def extract_number(self, text: str) -> Optional[float]:
        """テキストから数値を抽出する"""
        if not text:
            return None
        
        # 数値パターンを検索（負の数も含む）
        match = re.search(r'-?\d+\.?\d*', text.strip())
        if match:
            try:
                return float(match.group())
            except ValueError:
                return None
        return None
    
    def collect_dam_data(self) -> Dict[str, Union[float, None]]:
        """ダムデータを収集する"""
        # 現在時刻を取得し、10分単位に丸める（過去方向）
        current_time = datetime.now()
        # 分を10で割って切り捨て、10を掛けることで10分単位に
        minutes = (current_time.minute // 10) * 10
        # 10分前のデータを取得（データ更新の遅延を考慮）
        observation_time = current_time.replace(minute=minutes, second=0, microsecond=0) - timedelta(minutes=10)
        obsdt = observation_time.strftime('%Y%m%d%H%M')
        
        params = {
            'check': '015',     # 厚東川ダムの観測所コード
            'obsdt': obsdt,     # 10分単位に丸めた観測時刻
            'pop': '1'
        }
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
            # 貯水位パターンで検索（より具体的に）
            full_text = soup.get_text()
            
            # 貯水位を明示的に検索（ダム水位の正確な値）
            water_level_patterns = [
                r'貯水位[:\s]*(\d+\.\d+)\s*m',
                r'現在[:\s]*(\d+\.\d+)\s*m',
                r'水位[:\s]*(\d+\.\d+)\s*m'
            ]
            
            for pattern in water_level_patterns:
                match = re.search(pattern, full_text)
                if match:
                    level = float(match.group(1))
                    # ダム水位の妥当性チェック（30-40mの範囲）
                    if 30 <= level <= 40:
                        dam_data['water_level'] = level
                        break
            
            # テーブルから時系列データを取得
            tables = soup.find_all('table')
            water_levels = []
            storage_rates = []
            inflows = []
            outflows = []
            
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 4:  # 時刻、貯水位、貯水率、流入量などの列がある場合
                        for i, cell in enumerate(cells):
                            text = cell.get_text().strip()
                            
                            # 数値のみを抽出
                            try:
                                value = float(text)
                                
                                # 値の妥当性で判定
                                if 30 <= value <= 40:  # ダム水位の範囲
                                    water_levels.append(value)
                                elif 90 <= value <= 100:  # 貯水率の範囲
                                    storage_rates.append(value)
                                elif 0 < value < 20:  # 流入・流出量の範囲
                                    # 前後のセルのテキストを確認
                                    if i > 0:
                                        prev_text = cells[i-1].get_text().strip()
                                        if '流入' in prev_text:
                                            inflows.append(value)
                                        elif '流出' in prev_text:
                                            outflows.append(value)
                            except ValueError:
                                continue
            
            # 最新値を使用（リストの最後の値）
            if water_levels and dam_data['water_level'] is None:
                dam_data['water_level'] = water_levels[-1]
            if storage_rates:
                dam_data['storage_rate'] = storage_rates[-1]
            if inflows:
                dam_data['inflow'] = inflows[-1]
            if outflows:
                dam_data['outflow'] = outflows[-1]
            
            # 貯水率の計算（水位から）
            if dam_data['water_level'] and not dam_data['storage_rate']:
                # 最低水位20m、最高水位40mと仮定
                level = dam_data['water_level']
                dam_data['storage_rate'] = ((level - 20) / (40 - 20)) * 100
            
            # 変化量の計算
            if len(water_levels) >= 2:
                dam_data['storage_change'] = round(water_levels[-1] - water_levels[-2], 2)
                
        except Exception as e:
            print(f"Error extracting dam data: {e}")
        
        return dam_data
    
    def collect_river_data(self) -> Dict[str, Any]:
        """河川データを収集する"""
        # 現在時刻を取得し、10分単位に丸める（過去方向）
        current_time = datetime.now()
        # 分を10で割って切り捨て、10を掛けることで10分単位に
        minutes = (current_time.minute // 10) * 10
        # 10分前のデータを取得（データ更新の遅延を考慮）
        observation_time = current_time.replace(minute=minutes, second=0, microsecond=0) - timedelta(minutes=10)
        obsdt = observation_time.strftime('%Y%m%d%H%M')
        
        params = {
            'check': '05067',  # 厚東川（持世寺）の観測所コード
            'obsdt': obsdt,     # 10分単位に丸めた観測時刻
            'pop': '1'
        }
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
        
        # 警戒レベル閾値（サイトから取得した実際の値）
        thresholds = {
            'preparedness': 3.80,    # 水防団待機水位
            'caution': 5.00,        # 氾濫注意水位
            'evacuation': 5.10,     # 避難判断水位
            'danger': 5.50          # 氾濫危険水位
        }
        
        try:
            # テーブルから最新の水位データを取得
            tables = soup.find_all('table')
            water_levels = []
            
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        # 各行のセルを順番に確認
                        row_text = ' '.join([cell.get_text().strip() for cell in cells])
                        
                        # 時刻パターンを含む行（データ行）かチェック
                        if re.search(r'\d{1,2}:\d{2}', row_text):
                            for cell in cells:
                                text = cell.get_text().strip()
                                # 水位の数値パターンを検索
                                if re.match(r'^\d+\.\d{2}$', text):
                                    try:
                                        level = float(text)
                                        # 合理的な水位範囲内かチェック (0.5-10m)
                                        # 0.02のような極小値は除外
                                        if 0.5 <= level <= 10:
                                            water_levels.append(level)
                                    except ValueError:
                                        continue
            
            # 最新の水位データを使用（ただし警戒水位値を除外）
            if water_levels:
                # 警戒水位の値を除外
                threshold_values = [3.80, 5.00, 5.10, 5.50]
                actual_levels = [level for level in water_levels if level not in threshold_values]
                
                if actual_levels:
                    current_level = actual_levels[-1]  # 最新値
                    river_data['water_level'] = current_level
                    
                    # 前の値と比較して変化量を計算
                    if len(actual_levels) > 1:
                        previous_level = actual_levels[-2]
                        river_data['level_change'] = round(current_level - previous_level, 2)
                    else:
                        river_data['level_change'] = 0.0
                    
                    # 警戒レベルの判定
                    if current_level >= thresholds['danger']:
                        river_data['status'] = '氾濫危険'
                    elif current_level >= thresholds['evacuation']:
                        river_data['status'] = '避難判断'
                    elif current_level >= thresholds['caution']:
                        river_data['status'] = '氾濫注意'
                    elif current_level >= thresholds['preparedness']:
                        river_data['status'] = '水防団待機'
                    else:
                        river_data['status'] = '正常'
            
            # JavaScriptから現在値を抽出
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string:
                    script_text = script.string
                    
                    # 現在水位の数値を検索
                    current_match = re.search(r'最新値.*?(\d+\.\d+)', script_text)
                    if current_match:
                        try:
                            level = float(current_match.group(1))
                            if 0 <= level <= 10:  # 合理的な範囲
                                river_data['water_level'] = level
                        except ValueError:
                            pass
            
            # HTMLテキスト全体から最新値を検索
            full_text = soup.get_text()
            latest_matches = re.findall(r'(\d+\.\d{2})', full_text)
            
            if latest_matches and not river_data['water_level']:
                # 最後に見つかった合理的な値を使用
                for match in reversed(latest_matches):
                    try:
                        level = float(match)
                        if 0 <= level <= 10:
                            river_data['water_level'] = level
                            break
                    except ValueError:
                        continue
                        
        except Exception as e:
            print(f"Error extracting river data: {e}")
        
        return river_data
    
    def collect_rainfall_data(self) -> Dict[str, Any]:
        """雨量データを収集する"""
        # ダムページから雨量データも取得できる場合がある
        params = {'stncd': '015'}
        soup = self.fetch_page(self.dam_url, params)
        
        rainfall_data = {
            'hourly': 0,
            'cumulative': 0,
            'change': 0
        }
        
        if not soup:
            return rainfall_data
        
        try:
            # テーブルから雨量データを検索
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    row_text = ' '.join([cell.get_text().strip() for cell in cells])
                    
                    # 60分雨量を検索
                    hourly_match = re.search(r'60分.*?(\d+)', row_text)
                    if hourly_match:
                        rainfall_data['hourly'] = int(hourly_match.group(1))
                    
                    # 累積雨量を検索
                    cumulative_match = re.search(r'累積.*?(\d+)', row_text)
                    if cumulative_match:
                        rainfall_data['cumulative'] = int(cumulative_match.group(1))
            
            # HTMLテキスト全体からも検索
            full_text = soup.get_text()
            
            # より柔軟なパターンマッチング
            if rainfall_data['hourly'] == 0:
                hourly_patterns = [
                    r'時間雨量.*?(\d+)',
                    r'60分.*?(\d+)',
                    r'1時間.*?(\d+)'
                ]
                for pattern in hourly_patterns:
                    match = re.search(pattern, full_text)
                    if match:
                        rainfall_data['hourly'] = int(match.group(1))
                        break
            
            if rainfall_data['cumulative'] == 0:
                cumulative_patterns = [
                    r'累積雨量.*?(\d+)',
                    r'総雨量.*?(\d+)',
                    r'積算.*?(\d+)'
                ]
                for pattern in cumulative_patterns:
                    match = re.search(pattern, full_text)
                    if match:
                        rainfall_data['cumulative'] = int(match.group(1))
                        break
                        
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
                    # Remove entire year directory
                    import shutil
                    shutil.rmtree(year_dir)
                    print(f"Removed old data directory: {year_dir}")
                    continue
                    
                for month_dir in year_dir.iterdir():
                    if not month_dir.is_dir():
                        continue
                    
                    try:
                        month = int(month_dir.name)
                        if year == cutoff_date.year and month < cutoff_date.month:
                            import shutil
                            shutil.rmtree(month_dir)
                            print(f"Removed old data directory: {month_dir}")
                            continue
                            
                        for day_dir in month_dir.iterdir():
                            if not day_dir.is_dir():
                                continue
                            
                            try:
                                day = int(day_dir.name)
                                dir_date = datetime(year, month, day)
                                if dir_date < cutoff_date:
                                    import shutil
                                    shutil.rmtree(day_dir)
                                    print(f"Removed old data directory: {day_dir}")
                            except (ValueError, OSError) as e:
                                print(f"Error processing day directory {day_dir}: {e}")
                                
                    except (ValueError, OSError) as e:
                        print(f"Error processing month directory {month_dir}: {e}")
                        
            except (ValueError, OSError) as e:
                print(f"Error processing year directory {year_dir}: {e}")
    
    def collect_all_data(self) -> Dict[str, Any]:
        """全てのデータを収集する"""
        print("Starting data collection...")
        
        # データ収集
        dam_data = self.collect_dam_data()
        river_data = self.collect_river_data()
        rainfall_data = self.collect_rainfall_data()
        
        # 観測時刻を計算（10分単位で最新の観測時刻）
        current_time = datetime.now()
        minutes = (current_time.minute // 10) * 10
        observation_time = current_time.replace(minute=minutes, second=0, microsecond=0)
        
        # データを統合
        data = {
            'timestamp': datetime.now().isoformat(),
            'data_time': observation_time.isoformat(),  # 観測時刻を追加
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
    collector = KotogawaDataCollector()
    
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