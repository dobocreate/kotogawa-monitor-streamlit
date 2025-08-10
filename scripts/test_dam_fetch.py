#!/usr/bin/env python3
"""
ダムデータ取得テストスクリプト
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

try:
    from zoneinfo import ZoneInfo
except ImportError:
    import pytz
    ZoneInfo = lambda x: pytz.timezone(x)

def test_fetch():
    url = "https://y-bousai.pref.yamaguchi.lg.jp/citizen/dam/kdm_table.aspx"
    
    jst = ZoneInfo('Asia/Tokyo')
    current_time = datetime.now(jst)
    
    # 現在時刻から10分単位に丸める
    minutes = (current_time.minute // 10) * 10
    observation_time = current_time.replace(minute=minutes, second=0, microsecond=0)
    
    print(f"Current time: {current_time.strftime('%Y/%m/%d %H:%M')}")
    print(f"Target time: {observation_time.strftime('%Y/%m/%d %H:%M')}")
    
    # パラメータ設定
    obsdt = observation_time.strftime('%Y%m%d%H%M')
    params = {
        'check': '015',
        'obsdt': obsdt,
        'pop': '1'
    }
    
    print(f"Fetching with params: {params}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        print(f"Response status: {response.status_code}")
        print(f"Response size: {len(response.content)} bytes")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # テーブル探索
        tables = soup.find_all('table')
        print(f"Found {len(tables)} tables")
        
        target_date = observation_time.strftime('%Y/%m/%d')
        target_time = observation_time.strftime('%H:%M')
        
        found_data = False
        for i, table in enumerate(tables):
            rows = table.find_all('tr')
            print(f"\nTable {i+1}: {len(rows)} rows")
            
            # 最初の数行を表示
            for j, row in enumerate(rows[:5]):
                cells = row.find_all('td')
                if cells:
                    cell_texts = [cell.get_text().strip() for cell in cells[:3]]
                    print(f"  Row {j+1}: {cell_texts}")
                    
                    # 目標時刻のデータを探す
                    if len(cells) >= 9:
                        date_text = cells[0].get_text().strip()
                        time_text = cells[1].get_text().strip()
                        if date_text == target_date and time_text == target_time:
                            print(f"\n*** Found target data! ***")
                            print(f"Date: {date_text}, Time: {time_text}")
                            print(f"Water level: {cells[2].get_text().strip()}")
                            print(f"Storage rate: {cells[3].get_text().strip()}")
                            found_data = True
        
        if not found_data:
            print(f"\nTarget data not found for {target_date} {target_time}")
            print("Looking for most recent data...")
            
            # 最新データを探す
            for table in tables:
                rows = table.find_all('tr')
                for row in reversed(rows):
                    cells = row.find_all('td')
                    if len(cells) >= 9:
                        date_text = cells[0].get_text().strip()
                        time_text = cells[1].get_text().strip()
                        if '/' in date_text and ':' in time_text:
                            print(f"Most recent: {date_text} {time_text}")
                            print(f"Water level: {cells[2].get_text().strip()}")
                            print(f"Storage rate: {cells[3].get_text().strip()}")
                            break
                if '/' in date_text:
                    break
                    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_fetch()