#!/usr/bin/env python3
"""
厚東川監視システム データ収集スクリプト（Selenium版）
Seleniumを使用してJavaScriptレンダリング後のデータを正確に取得
"""

import json
import os
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Any, Union
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class KotogawaDataCollectorSelenium:
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.data_dir = self.base_dir / "data"
        self.history_dir = self.data_dir / "history"
        
        # Create directories if they don't exist
        self.data_dir.mkdir(exist_ok=True)
        self.history_dir.mkdir(exist_ok=True)
        
        # URLs for data sources
        self.dam_url = "https://y-bousai.pref.yamaguchi.lg.jp/citizen/dam/kdm_graph.aspx?stncd=015"
        self.river_url = "https://y-bousai.pref.yamaguchi.lg.jp/citizen/water/kwl_graph.aspx?stncd=067"
        
        # Setup Chrome options
        self.chrome_options = Options()
        self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_argument('--window-size=1920,1080')
        
    def create_driver(self):
        """WebDriverインスタンスを作成"""
        return webdriver.Chrome(options=self.chrome_options)
    
    def wait_for_data_load(self, driver, timeout=20):
        """データが読み込まれるまで待機"""
        try:
            # グラフまたはテーブルが表示されるまで待機
            WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "table"))
            )
            # 追加で少し待機（JavaScriptの実行完了を待つ）
            time.sleep(2)
            return True
        except TimeoutException:
            print("Timeout waiting for page to load")
            return False
    
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
        """ダムデータを収集する（Selenium版）"""
        driver = self.create_driver()
        dam_data = {
            'water_level': None,
            'storage_rate': None,
            'inflow': None,
            'outflow': None,
            'storage_change': None
        }
        
        try:
            driver.get(self.dam_url)
            
            if not self.wait_for_data_load(driver):
                return dam_data
            
            # テーブルを探す
            tables = driver.find_elements(By.TAG_NAME, "table")
            
            for table in tables:
                rows = table.find_elements(By.TAG_NAME, "tr")
                
                # 最後の行（最新データ）から探す
                for row in reversed(rows):
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if not cells:
                        cells = row.find_elements(By.TAG_NAME, "th")
                    
                    for i, cell in enumerate(cells):
                        cell_text = cell.text.strip()
                        
                        # 前のセルのテキストも確認（ラベルの可能性）
                        if i > 0:
                            prev_text = cells[i-1].text.strip()
                            
                            # 貯水位を探す
                            if '貯水位' in prev_text and cell_text:
                                level = self.extract_number(cell_text)
                                if level and 30 <= level <= 40:
                                    dam_data['water_level'] = level
                            
                            # 流入量を探す
                            elif '流入' in prev_text and cell_text:
                                inflow = self.extract_number(cell_text)
                                if inflow is not None:
                                    dam_data['inflow'] = inflow
                            
                            # 放流量を探す
                            elif ('放流' in prev_text or '流出' in prev_text) and cell_text:
                                outflow = self.extract_number(cell_text)
                                if outflow is not None:
                                    dam_data['outflow'] = outflow
            
            # JavaScriptで動的に表示されている値を取得
            try:
                # 現在貯水位を含む要素を探す
                water_level_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '貯水位')]")
                for elem in water_level_elements:
                    parent = elem.find_element(By.XPATH, "..")
                    text = parent.text
                    match = re.search(r'(\d+\.\d+)\s*m', text)
                    if match:
                        level = float(match.group(1))
                        if 30 <= level <= 40:
                            dam_data['water_level'] = level
                            break
            except:
                pass
            
            # より具体的なセレクタで値を取得
            if dam_data['water_level'] is None:
                try:
                    # グラフの最新値を取得する試み
                    script = driver.execute_script("""
                        var charts = document.querySelectorAll('[id*="Chart"]');
                        for (var chart of charts) {
                            var data = $(chart).c1compositechart('option', 'data');
                            if (data && data.length > 0) {
                                var series = data[0];
                                if (series.y && series.y.length > 0) {
                                    return series.y[series.y.length - 1];
                                }
                            }
                        }
                        return null;
                    """)
                    if script and 30 <= script <= 40:
                        dam_data['water_level'] = script
                except:
                    pass
            
            print(f"Dam data collected: {dam_data}")
            
        except Exception as e:
            print(f"Error collecting dam data: {e}")
        finally:
            driver.quit()
        
        return dam_data
    
    def collect_river_data(self) -> Dict[str, Any]:
        """河川データを収集する（Selenium版）"""
        driver = self.create_driver()
        river_data = {
            'water_level': None,
            'level_change': None,
            'status': '正常'
        }
        
        # 警戒レベル閾値
        thresholds = {
            'preparedness': 3.80,    # 水防団待機水位
            'caution': 5.00,        # 氾濫注意水位
            'evacuation': 5.10,     # 避難判断水位
            'danger': 5.50          # 氾濫危険水位
        }
        
        try:
            driver.get(self.river_url)
            
            if not self.wait_for_data_load(driver):
                return river_data
            
            water_levels = []
            
            # テーブルからデータを取得
            tables = driver.find_elements(By.TAG_NAME, "table")
            
            for table in tables:
                rows = table.find_elements(By.TAG_NAME, "tr")
                
                for row in rows:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if not cells:
                        cells = row.find_elements(By.TAG_NAME, "th")
                    
                    for cell in cells:
                        cell_text = cell.text.strip()
                        # 水位の数値を探す
                        if re.match(r'^\d+\.\d+$', cell_text):
                            level = float(cell_text)
                            # 警戒水位の値でないことを確認
                            if 0 <= level <= 10 and level not in thresholds.values():
                                water_levels.append(level)
            
            # JavaScriptで動的に表示されている値を取得
            try:
                script = driver.execute_script("""
                    var charts = document.querySelectorAll('[id*="riverC1WebChart"]');
                    if (charts.length > 0) {
                        var chart = charts[0];
                        var data = $(chart).c1compositechart('option', 'data');
                        if (data && data.length > 0) {
                            var series = data[0];
                            if (series.y && series.y.length > 0) {
                                return series.y[series.y.length - 1];
                            }
                        }
                    }
                    return null;
                """)
                if script and 0 <= script <= 10:
                    water_levels.append(script)
            except:
                pass
            
            # 最新の水位を使用
            if water_levels:
                river_data['water_level'] = water_levels[-1]
                
                # 水位変化を計算
                if len(water_levels) >= 2:
                    river_data['level_change'] = round(water_levels[-1] - water_levels[-2], 2)
                else:
                    river_data['level_change'] = 0.0
                
                # 警戒レベルの判定
                current_level = river_data['water_level']
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
            
            print(f"River data collected: {river_data}")
            
        except Exception as e:
            print(f"Error collecting river data: {e}")
        finally:
            driver.quit()
        
        return river_data
    
    def collect_rainfall_data(self) -> Dict[str, Any]:
        """雨量データを収集する"""
        # 簡易版として固定値を返す（実際のサイトから取得する場合は上記と同様の実装が必要）
        return {
            'hourly': 0,
            'cumulative': 0,
            'change': 0
        }
    
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
        print("Starting data collection with Selenium...")
        
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
    collector = KotogawaDataCollectorSelenium()
    
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