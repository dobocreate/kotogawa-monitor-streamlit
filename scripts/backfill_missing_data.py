#\!/usr/bin/env python3
"""
欠損データ補完スクリプト
GitHub Actions実行時に過去1時間分の欠損データを取得
"""

import json
import os
import sys
import time
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional

# 既存のcollect_dataモジュールをインポート
try:
    from collect_data import KotogawaDataCollector
except ImportError:
    print("Error: collect_data module not found")
    sys.exit(1)

try:
    from zoneinfo import ZoneInfo
except ImportError:
    import pytz
    ZoneInfo = lambda x: pytz.timezone(x)

class DataBackfiller:
    def __init__(self, dry_run: bool = False):
        self.collector = KotogawaDataCollector()
        self.base_dir = Path(__file__).parent.parent
        self.history_dir = self.base_dir / "data" / "history"
        self.dry_run = dry_run
        self.jst = ZoneInfo('Asia/Tokyo')
        
    def find_missing_timepoints(self, hours_back: int = 1) -> List[datetime]:
        """過去N時間の欠損時刻を検出"""
        now = datetime.now(self.jst)
        missing = []
        
        # 過去N時間分のチェック（10分刻み）
        for minutes_ago in range(10, hours_back * 60 + 10, 10):
            check_time = now - timedelta(minutes=minutes_ago)
            # 10分単位に丸める
            check_time = check_time.replace(
                minute=(check_time.minute // 10) * 10,
                second=0,
                microsecond=0
            )
            
            # ファイルの存在確認
            date_dir = self.history_dir / check_time.strftime("%Y") / check_time.strftime("%m") / check_time.strftime("%d")
            file_path = date_dir / f"{check_time.strftime('%H%M')}.json"
            
            if not file_path.exists():
                missing.append(check_time)
                
        return sorted(missing)
    
    def fetch_historical_data(self, target_time: datetime) -> Optional[Dict[str, Any]]:
        """特定時刻のデータを取得"""
        obsdt = target_time.strftime('%Y%m%d%H%M')
        
        print(f"  Fetching data for {target_time.strftime('%Y-%m-%d %H:%M')}...")
        
        # ダムデータ取得
        dam_params = {
            'check': '015',
            'obsdt': obsdt,
            'pop': '1'
        }
        dam_soup = self.collector.fetch_page(self.collector.dam_url, dam_params)
        
        if not dam_soup:
            print(f"    Failed to fetch dam data")
            return None
        
        # 河川データ取得
        river_params = {
            'check': '05067',
            'obsdt': obsdt,
            'pop': '1'
        }
        river_soup = self.collector.fetch_page(self.collector.river_url, river_params)
        
        # データ解析（既存のロジックを再利用）
        dam_data = self._parse_dam_data(dam_soup, target_time)
        river_data = self._parse_river_data(river_soup, target_time) if river_soup else None
        
        if dam_data['dam']['water_level'] is None and (river_data is None or river_data['water_level'] is None):
            print(f"    No valid data found for {target_time.strftime('%H:%M')}")
            return None
        
        # データ構造の構築
        data = {
            'timestamp': datetime.now(self.jst).isoformat(),
            'data_time': target_time.isoformat(),
            'dam': dam_data['dam'],
            'river': river_data if river_data else {
                'water_level': None,
                'level_change': None,
                'status': None
            },
            'rainfall': dam_data.get('rainfall', {
                'hourly': None,
                'cumulative': None,
                'change': None
            })
        }
        
        return data
    
    def _parse_dam_data(self, soup, target_time) -> Dict[str, Any]:
        """ダムデータの解析"""
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
        
        target_date = target_time.strftime('%Y/%m/%d')
        target_time_str = target_time.strftime('%H:%M')
        
        try:
            for table in soup.find_all('table'):
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 9:
                        date_text = cells[0].get_text().strip()
                        time_text = cells[1].get_text().strip()
                        
                        if date_text == target_date and time_text == target_time_str:
                            # ダムデータ抽出
                            try:
                                level = float(cells[2].get_text().strip())
                                if 30 <= level <= 40:
                                    dam_data['water_level'] = level
                            except ValueError:
                                pass
                            
                            try:
                                rate = float(cells[3].get_text().strip())
                                if 0 <= rate <= 100:
                                    dam_data['storage_rate'] = rate
                            except ValueError:
                                pass
                            
                            try:
                                inflow = float(cells[4].get_text().strip())
                                if 0 <= inflow <= 1500:
                                    dam_data['inflow'] = inflow
                            except ValueError:
                                pass
                            
                            try:
                                outflow = float(cells[5].get_text().strip())
                                if 0 <= outflow <= 1500:
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
                            
                            break
        except Exception as e:
            print(f"    Error parsing dam data: {e}")
        
        return {
            'dam': dam_data,
            'rainfall': rainfall_data
        }
    
    def _parse_river_data(self, soup, target_time) -> Optional[Dict[str, Any]]:
        """河川データの解析"""
        river_data = {
            'water_level': None,
            'level_change': None,
            'status': None
        }
        
        target_date = target_time.strftime('%Y/%m/%d')
        target_time_str = target_time.strftime('%H:%M')
        
        thresholds = {
            'preparedness': 3.80,
            'caution': 5.00,
            'evacuation': 5.10,
            'danger': 5.50
        }
        
        try:
            for table in soup.find_all('table'):
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 4:
                        date_text = cells[0].get_text().strip()
                        time_text = cells[1].get_text().strip()
                        
                        if date_text == target_date and time_text == target_time_str:
                            try:
                                level = float(cells[2].get_text().strip())
                                if 0.5 <= level <= 10:
                                    river_data['water_level'] = level
                                    
                                    # 警戒レベル判定
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
                                    
                                    # 水位変化
                                    if len(cells) > 3:
                                        try:
                                            import re
                                            change_text = cells[3].get_text().strip()
                                            change_match = re.search(r'([+-]?\d+\.\d+)', change_text)
                                            if change_match:
                                                river_data['level_change'] = float(change_match.group(1))
                                        except:
                                            river_data['level_change'] = 0.0
                            except ValueError:
                                pass
                            
                            break
        except Exception as e:
            print(f"    Error parsing river data: {e}")
        
        return river_data
    
    def save_historical_data(self, data: Dict[str, Any], observation_time: datetime) -> bool:
        """履歴データを保存"""
        if self.dry_run:
            print(f"    [DRY RUN] Would save data for {observation_time.strftime('%Y-%m-%d %H:%M')}")
            return True
        
        try:
            # 保存先ディレクトリ作成
            date_dir = self.history_dir / observation_time.strftime("%Y") / observation_time.strftime("%m") / observation_time.strftime("%d")
            date_dir.mkdir(parents=True, exist_ok=True)
            
            # ファイル保存
            file_path = date_dir / f"{observation_time.strftime('%H%M')}.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            
            print(f"    Saved: {file_path.name}")
            return True
            
        except Exception as e:
            print(f"    Error saving data: {e}")
            return False
    
    def backfill(self, hours_back: int = 1, max_items: int = 6) -> int:
        """欠損データを補完"""
        print(f"Checking for missing data in the last {hours_back} hour(s)...")
        missing = self.find_missing_timepoints(hours_back)
        
        if not missing:
            print("No missing data found")
            return 0
        
        print(f"Found {len(missing)} missing timepoints")
        
        # 最大取得数を制限
        to_fetch = missing[:max_items]
        if len(missing) > max_items:
            print(f"Limiting to {max_items} items (API rate limit)")
        
        success_count = 0
        for i, target_time in enumerate(to_fetch, 1):
            print(f"\n[{i}/{len(to_fetch)}] Processing {target_time.strftime('%Y-%m-%d %H:%M')}...")
            
            if not self.dry_run:
                try:
                    data = self.fetch_historical_data(target_time)
                    
                    if data:
                        # 観測時刻を使用して保存
                        obs_time = datetime.fromisoformat(data['data_time'])
                        if self.save_historical_data(data, obs_time):
                            success_count += 1
                    else:
                        print(f"    No data available")
                    
                    # API負荷軽減のため待機
                    if i < len(to_fetch):
                        time.sleep(2)
                    
                except Exception as e:
                    print(f"    Error: {e}")
            else:
                print(f"    [DRY RUN] Would fetch and save data")
                success_count += 1
        
        print(f"\nSummary: Successfully backfilled {success_count}/{len(to_fetch)} timepoints")
        return success_count

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='Backfill missing monitoring data')
    parser.add_argument('--hours', type=int, default=6, help='Hours to look back (default: 6)')
    parser.add_argument('--max', type=int, default=6, help='Maximum items to fetch (default: 6)')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode (no actual fetching)')
    
    args = parser.parse_args()
    
    backfiller = DataBackfiller(dry_run=args.dry_run)
    result = backfiller.backfill(hours_back=args.hours, max_items=args.max)
    
    # Exit code: 0 if any data was backfilled, 1 if none
    sys.exit(0 if result > 0 or args.dry_run else 1)

if __name__ == "__main__":
    main()
