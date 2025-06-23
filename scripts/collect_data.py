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

try:
    from zoneinfo import ZoneInfo
except ImportError:
    # Python 3.8以前の場合
    import pytz
    ZoneInfo = lambda x: pytz.timezone(x)

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
        self.max_retries = 5  # リトライ回数を増加
        self.retry_delay = 3  # リトライ間隔（秒）
        
    def fetch_page(self, url: str, params: Dict[str, str]) -> Optional[BeautifulSoup]:
        """指定されたURLからHTMLを取得し、BeautifulSoupオブジェクトを返す"""
        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = requests.get(
                    url, 
                    params=params, 
                    headers=self.headers, 
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                # レスポンスサイズをチェック
                if len(response.content) < 100:
                    raise requests.RequestException(f"Response too small: {len(response.content)} bytes")
                
                return BeautifulSoup(response.content, 'html.parser')
                
            except requests.RequestException as e:
                last_error = e
                
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (attempt + 1)  # 指数バックオフ
                    time.sleep(wait_time)
                else:
                    return None
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
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
        # 日本時間で現在時刻を取得し、10分単位に丸める
        jst = ZoneInfo('Asia/Tokyo')
        current_time = datetime.now(jst)
        # 分を15で割って切り捨て、15を掛けることで15分単位に
        minutes = (current_time.minute // 15) * 15
        # 最新の15分単位時刻のデータを取得
        observation_time = current_time.replace(minute=minutes, second=0, microsecond=0)
        # 山口県システムにはJST時間で送信する
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
            
            # テーブルから正確な日時マッチングで目標データを取得
            tables = soup.find_all('table')
            target_date = observation_time.strftime('%Y/%m/%d')
            target_time = observation_time.strftime('%H:%M')
            
            
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 9:  # ダムテーブルの最小列数（日付、時刻、貯水位、貯水率、流入量、全放流量、調整流量、60分雨量、累加雨量）
                        try:
                            date_text = cells[0].get_text().strip()
                            time_text = cells[1].get_text().strip()
                            
                            # 日時が完全一致する行を探す
                            if date_text == target_date and time_text == target_time:
                                
                                # 列位置に基づいてデータを抽出
                                # 列2: 貯水位, 列3: 貯水率, 列4: 流入量, 列5: 全放流量
                                water_level_text = cells[2].get_text().strip()
                                storage_rate_text = cells[3].get_text().strip()
                                inflow_text = cells[4].get_text().strip()
                                outflow_text = cells[5].get_text().strip()
                                
                                # 貯水位
                                try:
                                    level = float(water_level_text)
                                    if 30 <= level <= 40:  # 妥当性チェック
                                        dam_data['water_level'] = level
                                except ValueError:
                                    pass
                                
                                # 貯水率
                                try:
                                    rate = float(storage_rate_text)
                                    if 0 <= rate <= 100:  # 妥当性チェック
                                        dam_data['storage_rate'] = rate
                                except ValueError:
                                    pass
                                
                                # 流入量
                                try:
                                    inflow = float(inflow_text)
                                    if 0 <= inflow <= 100:  # 範囲を拡張
                                        dam_data['inflow'] = inflow
                                except ValueError:
                                    pass
                                
                                # 全放流量
                                try:
                                    outflow = float(outflow_text)
                                    if 0 <= outflow <= 100:  # 範囲を拡張
                                        dam_data['outflow'] = outflow
                                except ValueError:
                                    pass
                                
                                break  # 目標行が見つかったら終了
                        except (IndexError, ValueError) as e:
                            continue
                
                if dam_data['water_level'] is not None:
                    break  # データが見つかったらテーブル検索終了
            
            # 貯水率の計算（水位から）
            if dam_data['water_level'] and not dam_data['storage_rate']:
                # 最低水位20m、最高水位40mと仮定
                level = dam_data['water_level']
                dam_data['storage_rate'] = ((level - 20) / (40 - 20)) * 100
            
            # 変化量の計算
            if len(water_levels) >= 2:
                dam_data['storage_change'] = round(water_levels[-1] - water_levels[-2], 2)
                
        except Exception as e:
            pass
        
        return dam_data
    
    def collect_river_data(self) -> Dict[str, Any]:
        """河川データを収集する"""
        # 日本時間で現在時刻を取得し、10分単位に丸める
        jst = ZoneInfo('Asia/Tokyo')
        current_time = datetime.now(jst)
        # 分を15で割って切り捨て、15を掛けることで15分単位に
        minutes = (current_time.minute // 15) * 15
        # 最新の15分単位時刻のデータを取得
        observation_time = current_time.replace(minute=minutes, second=0, microsecond=0)
        # 山口県システムにはJST時間で送信する
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
            # テーブルから正確な日時マッチングで目標データを取得
            tables = soup.find_all('table')
            target_date = observation_time.strftime('%Y/%m/%d')
            target_time = observation_time.strftime('%H:%M')
            
            
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 4:  # 河川テーブルの最小列数（日付、時刻、水位、変化量など）
                        try:
                            date_text = cells[0].get_text().strip()
                            time_text = cells[1].get_text().strip()
                            
                            # 日時が完全一致する行を探す
                            if date_text == target_date and time_text == target_time:
                                
                                # 列位置に基づいてデータを抽出
                                # 列2: 水位, 列3: 水位変化（推定）
                                water_level_text = cells[2].get_text().strip()
                                
                                # 水位
                                try:
                                    level = float(water_level_text)
                                    if 0.5 <= level <= 10:  # 合理的な水位範囲
                                        river_data['water_level'] = level
                                        
                                        # 水位変化（列3があれば）
                                        if len(cells) > 3:
                                            try:
                                                change_text = cells[3].get_text().strip()
                                                # +0.01 や -0.02 のような形式から数値を抽出
                                                change_match = re.search(r'([+-]?\d+\.\d+)', change_text)
                                                if change_match:
                                                    change = float(change_match.group(1))
                                                    river_data['level_change'] = round(change, 2)
                                                else:
                                                    river_data['level_change'] = 0.0
                                            except (ValueError, IndexError):
                                                river_data['level_change'] = 0.0
                                        else:
                                            river_data['level_change'] = 0.0
                                        
                                        # 警戒レベルの判定
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
                                        
                                        break  # 目標行が見つかったら終了
                                except ValueError:
                                    pass
                        except (IndexError, ValueError) as e:
                            continue
                
                if river_data['water_level'] is not None:
                    break  # データが見つかったらテーブル検索終了
            
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
            pass
        
        return river_data
    
    def validate_rainfall_data(self, hourly: int, cumulative: int) -> bool:
        """雨量データの妥当性を検証する"""
        # 時間雨量の妥当性チェック（0-100mm/h）
        if not (0 <= hourly <= 100):
            return False
        
        # 累積雨量の妥当性チェック（0-500mm）
        if not (0 <= cumulative <= 500):
            return False
        
        # 論理的整合性チェック（時間雨量 > 0 なら累積雨量も > 0 であるべき）
        if hourly > 0 and cumulative == 0:
            pass
        
        return True
    
    def collect_rainfall_data(self) -> Dict[str, Any]:
        """雨量データを収集する"""
        # 日本時間で現在時刻を取得し、10分単位に丸める
        jst = ZoneInfo('Asia/Tokyo')
        current_time = datetime.now(jst)
        minutes = (current_time.minute // 10) * 10
        observation_time = current_time.replace(minute=minutes, second=0, microsecond=0)
        obsdt = observation_time.strftime('%Y%m%d%H%M')
        
        params = {
            'check': '015',     # 厚東川ダムの観測所コード
            'obsdt': obsdt,     # 10分単位に丸めた観測時刻  
            'pop': '1'
        }
        soup = self.fetch_page(self.dam_url, params)
        
        rainfall_data = {
            'hourly': 0,
            'cumulative': 0,
            'change': 0
        }
        
        if not soup:
            return rainfall_data
        
        try:
            # 雨量データは同じダムテーブルから取得（列7: 60分雨量、列8: 累積雨量）
            tables = soup.find_all('table')
            target_date = observation_time.strftime('%Y/%m/%d')
            target_time = observation_time.strftime('%H:%M')
            
            
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 9:  # ダムテーブルの全列数
                        try:
                            date_text = cells[0].get_text().strip()
                            time_text = cells[1].get_text().strip()
                            
                            # 日時が完全一致する行を探す
                            if date_text == target_date and time_text == target_time:
                                
                                # 列位置に基づいて雨量データを抽出
                                # 列7: 60分雨量, 列8: 累積雨量
                                hourly_text = cells[7].get_text().strip()
                                cumulative_text = cells[8].get_text().strip()
                                
                                # 60分雨量
                                try:
                                    hourly = int(hourly_text)
                                    if self.validate_rainfall_data(hourly, 0):
                                        rainfall_data['hourly'] = hourly
                                except ValueError:
                                    pass
                                
                                # 累積雨量
                                try:
                                    cumulative = int(cumulative_text)
                                    if self.validate_rainfall_data(0, cumulative):
                                        rainfall_data['cumulative'] = cumulative
                                except ValueError:
                                    pass
                                
                                break  # 目標行が見つかったら終了
                        except (IndexError, ValueError) as e:
                            continue
                
                if rainfall_data['hourly'] != 0 or rainfall_data['cumulative'] != 0:
                    break  # データが見つかったらテーブル検索終了
            
            # 変化量の計算（前回データとの比較は省略し、0を設定）
            rainfall_data['change'] = 0
            
            # 最終的な検証
            if not self.validate_rainfall_data(rainfall_data['hourly'], rainfall_data['cumulative']):
                pass
            
        except Exception as e:
            pass
        
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
                    continue
                    
                for month_dir in year_dir.iterdir():
                    if not month_dir.is_dir():
                        continue
                    
                    try:
                        month = int(month_dir.name)
                        if year == cutoff_date.year and month < cutoff_date.month:
                            import shutil
                            shutil.rmtree(month_dir)
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
                            except (ValueError, OSError) as e:
                                pass
                                
                    except (ValueError, OSError) as e:
                        pass
                        
            except (ValueError, OSError) as e:
                pass
    
    def collect_all_data(self) -> Dict[str, Any]:
        """全てのデータを収集する"""
        
        # データ収集
        dam_data = self.collect_dam_data()
        river_data = self.collect_river_data()
        rainfall_data = self.collect_rainfall_data()
        
        # 観測時刻を計算（15分単位で最新の観測時刻）- 日本時間で統一
        jst = ZoneInfo('Asia/Tokyo')
        current_time = datetime.now(jst)
        minutes = (current_time.minute // 15) * 15
        observation_time = current_time.replace(minute=minutes, second=0, microsecond=0)
        
        # データを統合（日本時間で保存）
        timestamp_jst = datetime.now(jst)
        observation_time_jst = observation_time  # 既にJST
        
        data = {
            'timestamp': timestamp_jst.isoformat(),
            'data_time': observation_time_jst.isoformat(),  # 観測時刻を追加
            'dam': dam_data,
            'river': river_data,
            'rainfall': rainfall_data
        }
        
        # データ保存
        self.save_data(data)
        
        # 古いデータのクリーンアップ
        self.cleanup_old_data()
        
        return data

def main():
    """メイン関数"""
    collector = KotogawaDataCollector()
    
    try:
        data = collector.collect_all_data()
    except Exception as e:
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())