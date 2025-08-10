#!/usr/bin/env python3
"""
厚東川監視システム 欠損データ収集スクリプト
12:00以降の欠損したダムデータを遡って取得する
"""

import json
import os
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Any
import requests
from bs4 import BeautifulSoup

try:
    from zoneinfo import ZoneInfo
except ImportError:
    import pytz
    ZoneInfo = lambda x: pytz.timezone(x)

class MissingDataCollector:
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.data_dir = self.base_dir / "data"
        self.history_dir = self.data_dir / "history"
        
        # URLs for data sources
        self.dam_url = "https://y-bousai.pref.yamaguchi.lg.jp/citizen/dam/kdm_table.aspx"
        
        # Request settings
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.timeout = 30
        self.max_retries = 3
        self.retry_delay = 2
        
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
                
                if len(response.content) < 100:
                    raise requests.RequestException(f"Response too small: {len(response.content)} bytes")
                
                return BeautifulSoup(response.content, 'html.parser')
                
            except requests.RequestException as e:
                print(f"Attempt {attempt + 1}/{self.max_retries} failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    return None
    
    def collect_historical_data(self, target_time: datetime) -> Dict[str, Any]:
        """特定時刻のダムデータを収集する"""
        jst = ZoneInfo('Asia/Tokyo')
        
        # 10分単位に丸める
        minutes = (target_time.minute // 10) * 10
        observation_time = target_time.replace(minute=minutes, second=0, microsecond=0)
        obsdt = observation_time.strftime('%Y%m%d%H%M')
        
        print(f"Fetching data for: {observation_time.strftime('%Y/%m/%d %H:%M')}")
        
        params = {
            'check': '015',     # 厚東川ダムの観測所コード
            'obsdt': obsdt,     # 観測時刻
            'pop': '1'
        }
        
        soup = self.fetch_page(self.dam_url, params)
        
        if not soup:
            print(f"Failed to fetch page for {observation_time}")
            return None
        
        dam_data = {
            'water_level': None,
            'storage_rate': None,
            'inflow': None,
            'outflow': None,
            'storage_change': None
        }
        
        rainfall_data = {
            'hourly': None,
            'cumulative': None,
            'change': None
        }
        
        try:
            tables = soup.find_all('table')
            target_date = observation_time.strftime('%Y/%m/%d')
            target_time = observation_time.strftime('%H:%M')
            
            print(f"Looking for: {target_date} {target_time}")
            
            # テーブルから該当時刻のデータを探す
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 9:
                        try:
                            date_text = cells[0].get_text().strip()
                            time_text = cells[1].get_text().strip()
                            
                            # 目標時刻のデータを探す
                            if date_text == target_date and time_text == target_time:
                                print(f"Found data for {date_text} {time_text}")
                                
                                # データ抽出
                                water_level_text = cells[2].get_text().strip()
                                storage_rate_text = cells[3].get_text().strip()
                                inflow_text = cells[4].get_text().strip()
                                outflow_text = cells[5].get_text().strip()
                                
                                # 貯水位
                                try:
                                    level = float(water_level_text)
                                    if 30 <= level <= 40:
                                        dam_data['water_level'] = level
                                except ValueError:
                                    pass
                                
                                # 貯水率
                                try:
                                    rate = float(storage_rate_text)
                                    if 0 <= rate <= 100:
                                        dam_data['storage_rate'] = rate
                                except ValueError:
                                    pass
                                
                                # 流入量
                                try:
                                    inflow = float(inflow_text)
                                    if 0 <= inflow <= 100:
                                        dam_data['inflow'] = inflow
                                except ValueError:
                                    pass
                                
                                # 放流量
                                try:
                                    outflow = float(outflow_text)
                                    if 0 <= outflow <= 100:
                                        dam_data['outflow'] = outflow
                                except ValueError:
                                    pass
                                
                                # 降雨データ
                                if len(cells) > 7:
                                    try:
                                        hourly = int(cells[7].get_text().strip())
                                        if 0 <= hourly <= 200:
                                            rainfall_data['hourly'] = hourly
                                    except ValueError:
                                        pass
                                
                                if len(cells) > 8:
                                    try:
                                        cumulative = int(cells[8].get_text().strip())
                                        if 0 <= cumulative <= 1000:
                                            rainfall_data['cumulative'] = cumulative
                                    except ValueError:
                                        pass
                                
                                return {
                                    'dam': dam_data,
                                    'rainfall': rainfall_data,
                                    'observation_time': observation_time.isoformat()
                                }
                        except (IndexError, ValueError):
                            continue
            
            print(f"No data found for {target_date} {target_time}")
            return None
            
        except Exception as e:
            print(f"Error processing data: {e}")
            return None
    
    def save_data(self, data: Dict[str, Any], observation_time: datetime):
        """データを保存する"""
        jst = ZoneInfo('Asia/Tokyo')
        
        # 保存先ディレクトリ作成
        date_dir = self.history_dir / observation_time.strftime("%Y") / observation_time.strftime("%m") / observation_time.strftime("%d")
        date_dir.mkdir(parents=True, exist_ok=True)
        
        # ファイル名
        history_file = date_dir / f"{observation_time.strftime('%H%M')}.json"
        
        # 既存データの読み込み（あれば）
        if history_file.exists():
            with open(history_file, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        else:
            existing_data = {}
        
        # データ統合
        full_data = {
            'timestamp': datetime.now(jst).isoformat(),
            'data_time': observation_time.isoformat(),
            'dam': data['dam'],
            'rainfall': data['rainfall']
        }
        
        # 既存データに追加
        if existing_data:
            # 既存のriver, weatherデータは保持
            if 'river' in existing_data:
                full_data['river'] = existing_data['river']
            if 'weather' in existing_data:
                full_data['weather'] = existing_data['weather']
            if 'precipitation_intensity' in existing_data:
                full_data['precipitation_intensity'] = existing_data['precipitation_intensity']
        
        # 保存
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(full_data, f, ensure_ascii=False, indent=2)
        
        print(f"Saved: {history_file}")
        return history_file
    
    def collect_missing_data(self):
        """12:00から現在までの欠損データを収集"""
        jst = ZoneInfo('Asia/Tokyo')
        current_time = datetime.now(jst)
        
        # 12:00から開始
        start_time = current_time.replace(hour=12, minute=0, second=0, microsecond=0)
        
        # 10分ごとに遡って収集
        time_cursor = start_time
        collected_count = 0
        failed_count = 0
        
        while time_cursor <= current_time:
            # ファイルの存在確認
            date_dir = self.history_dir / time_cursor.strftime("%Y") / time_cursor.strftime("%m") / time_cursor.strftime("%d")
            history_file = date_dir / f"{time_cursor.strftime('%H%M')}.json"
            
            # ファイルが存在し、ダムデータがある場合はスキップ
            if history_file.exists():
                with open(history_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    if 'dam' in existing_data and existing_data['dam'].get('water_level') is not None:
                        print(f"Data already exists for {time_cursor.strftime('%H:%M')}, skipping...")
                        time_cursor += timedelta(minutes=10)
                        continue
            
            # データ収集
            data = self.collect_historical_data(time_cursor)
            
            if data and data['dam']['water_level'] is not None:
                self.save_data(data, time_cursor)
                collected_count += 1
                print(f"Collected data for {time_cursor.strftime('%H:%M')}")
            else:
                failed_count += 1
                print(f"No data available for {time_cursor.strftime('%H:%M')}")
            
            # 次の時刻へ
            time_cursor += timedelta(minutes=10)
            
            # サーバー負荷軽減のため少し待つ
            time.sleep(1)
        
        print(f"\nCollection complete!")
        print(f"Collected: {collected_count} records")
        print(f"Failed: {failed_count} records")

if __name__ == "__main__":
    collector = MissingDataCollector()
    collector.collect_missing_data()