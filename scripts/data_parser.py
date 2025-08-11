#!/usr/bin/env python3
"""
データ解析専用モジュール
HTMLからデータを抽出し、検証を行う
"""

import re
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from bs4 import BeautifulSoup

from config_manager import config

logger = logging.getLogger(__name__)

try:
    from zoneinfo import ZoneInfo
except ImportError:
    import pytz
    ZoneInfo = lambda x: pytz.timezone(x)


class DataParser:
    """データ解析クラス"""
    
    def __init__(self):
        """初期化"""
        self.jst = ZoneInfo('Asia/Tokyo')
        
        # 検証範囲を設定から読み込み
        self.validation_rules = {
            'dam': {
                'water_level': config.get_validation_range('dam', 'water_level'),
                'storage_rate': config.get_validation_range('dam', 'storage_rate'),
                'flow': config.get_validation_range('dam', 'flow')
            },
            'river': {
                'water_level': config.get_validation_range('river', 'water_level'),
                'thresholds': config.get_section('validation')['river']['thresholds']
            },
            'rainfall': {
                'hourly': config.get_validation_range('rainfall', 'hourly'),
                'cumulative': config.get_validation_range('rainfall', 'cumulative')
            }
        }
        
    def extract_number(self, text: str) -> Optional[float]:
        """
        テキストから数値を抽出
        
        Args:
            text: 抽出対象テキスト
            
        Returns:
            float: 抽出された数値
            None: 抽出失敗時
        """
        if not text:
            return None
        
        try:
            # 数値パターンを検索（負の数も含む）
            match = re.search(r'-?\d+\.?\d*', text.strip())
            if match:
                return float(match.group())
        except (ValueError, AttributeError) as e:
            logger.debug(f"Failed to extract number from '{text}': {e}")
            
        return None
    
    def validate_value(self, value: Optional[float], data_type: str, field: str) -> Optional[float]:
        """
        値の妥当性を検証
        
        Args:
            value: 検証対象の値
            data_type: データタイプ（dam, river, rainfall）
            field: フィールド名（water_level, storage_rate等）
            
        Returns:
            float: 検証済みの値
            None: 検証失敗時
        """
        if value is None:
            return None
        
        # 検証ルールを取得
        if data_type in self.validation_rules and field in self.validation_rules[data_type]:
            min_val, max_val = self.validation_rules[data_type][field]
            
            if min_val is not None and value < min_val:
                logger.debug(f"Value {value} below minimum {min_val} for {data_type}.{field}")
                return None
                
            if max_val is not None and value > max_val:
                logger.debug(f"Value {value} above maximum {max_val} for {data_type}.{field}")
                return None
        
        return value
    
    def parse_dam_data(self, soup: BeautifulSoup, target_time: datetime) -> Dict[str, Any]:
        """
        ダムデータを解析
        
        Args:
            soup: BeautifulSoupオブジェクト
            target_time: 対象時刻
            
        Returns:
            Dict: ダムデータと降雨データ
        """
        dam_data = {
            'water_level': None,
            'storage_rate': None,
            'inflow': None,
            'outflow': None,
            'storage_change': None,
            'actual_observation_time': None
        }
        
        rainfall_data = {
            'hourly': None,
            'cumulative': None,
            'change': None
        }
        
        if not soup:
            return {'dam': dam_data, 'rainfall': rainfall_data}
        
        target_date = target_time.strftime('%Y/%m/%d')
        target_time_str = target_time.strftime('%H:%M')
        
        try:
            # テーブルから目標時刻のデータを検索
            found = self._extract_from_table(
                soup, target_date, target_time_str,
                dam_data, rainfall_data
            )
            
            # 目標データが見つからない場合、最新データを取得
            if not found:
                logger.info(f"Target data not found for {target_date} {target_time_str}. Looking for latest...")
                self._extract_latest_from_table(soup, dam_data, rainfall_data)
            
            # 変化量の計算
            rainfall_data['change'] = 0 if rainfall_data['hourly'] is not None else None
            
        except Exception as e:
            logger.error(f"Error parsing dam data: {e}")
        
        return {'dam': dam_data, 'rainfall': rainfall_data}
    
    def _extract_from_table(
        self, soup: BeautifulSoup, target_date: str, target_time: str,
        dam_data: Dict, rainfall_data: Dict
    ) -> bool:
        """
        テーブルから特定時刻のデータを抽出
        
        Returns:
            bool: データが見つかった場合True
        """
        for table in soup.find_all('table'):
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                
                # ダムデータテーブル（9列以上）
                if len(cells) >= 9:
                    try:
                        date_text = cells[0].get_text().strip()
                        time_text = cells[1].get_text().strip()
                        
                        if date_text == target_date and time_text == target_time:
                            # ダムデータ抽出
                            self._extract_dam_values(cells, dam_data)
                            
                            # 降雨データ抽出
                            self._extract_rainfall_values(cells, rainfall_data)
                            
                            dam_data['actual_observation_time'] = f"{date_text} {time_text}"
                            return True
                            
                    except (IndexError, AttributeError) as e:
                        logger.debug(f"Error processing row: {e}")
                        continue
        
        return False
    
    def _extract_latest_from_table(
        self, soup: BeautifulSoup, dam_data: Dict, rainfall_data: Dict
    ) -> bool:
        """
        テーブルから最新データを抽出
        
        Returns:
            bool: データが見つかった場合True
        """
        for table in soup.find_all('table'):
            rows = table.find_all('tr')
            
            # 最後から順に有効なデータ行を探す
            for row in reversed(rows[-10:] if len(rows) > 10 else rows):
                cells = row.find_all('td')
                
                if len(cells) >= 9:
                    try:
                        date_text = cells[0].get_text().strip()
                        time_text = cells[1].get_text().strip()
                        
                        # 日付形式のチェック
                        if re.match(r'\d{4}/\d{2}/\d{2}', date_text) and re.match(r'\d{2}:\d{2}', time_text):
                            # データ抽出
                            if self._extract_dam_values(cells, dam_data):
                                self._extract_rainfall_values(cells, rainfall_data)
                                dam_data['actual_observation_time'] = f"{date_text} {time_text}"
                                logger.info(f"Found latest data: {date_text} {time_text}")
                                return True
                                
                    except (IndexError, AttributeError) as e:
                        logger.debug(f"Error processing row: {e}")
                        continue
        
        return False
    
    def _extract_dam_values(self, cells: list, dam_data: Dict) -> bool:
        """
        セルからダムデータを抽出
        
        Returns:
            bool: 有効なデータが抽出された場合True
        """
        extracted_any = False
        
        # 貯水位（列2）
        try:
            value = self.extract_number(cells[2].get_text())
            validated = self.validate_value(value, 'dam', 'water_level')
            if validated is not None:
                dam_data['water_level'] = validated
                extracted_any = True
        except (IndexError, AttributeError):
            pass
        
        # 貯水率（列3）
        try:
            value = self.extract_number(cells[3].get_text())
            validated = self.validate_value(value, 'dam', 'storage_rate')
            if validated is not None:
                dam_data['storage_rate'] = validated
                extracted_any = True
        except (IndexError, AttributeError):
            pass
        
        # 流入量（列4）
        try:
            value = self.extract_number(cells[4].get_text())
            validated = self.validate_value(value, 'dam', 'flow')
            if validated is not None:
                dam_data['inflow'] = validated
                extracted_any = True
        except (IndexError, AttributeError):
            pass
        
        # 全放流量（列5）
        try:
            value = self.extract_number(cells[5].get_text())
            validated = self.validate_value(value, 'dam', 'flow')
            if validated is not None:
                dam_data['outflow'] = validated
                extracted_any = True
        except (IndexError, AttributeError):
            pass
        
        return extracted_any
    
    def _extract_rainfall_values(self, cells: list, rainfall_data: Dict):
        """セルから降雨データを抽出"""
        # 60分雨量（列7）
        if len(cells) > 7:
            try:
                value = self.extract_number(cells[7].get_text())
                if value is not None:
                    validated = self.validate_value(int(value), 'rainfall', 'hourly')
                    if validated is not None:
                        rainfall_data['hourly'] = int(validated)
            except (IndexError, AttributeError, ValueError):
                pass
        
        # 累加雨量（列8）
        if len(cells) > 8:
            try:
                value = self.extract_number(cells[8].get_text())
                if value is not None:
                    validated = self.validate_value(int(value), 'rainfall', 'cumulative')
                    if validated is not None:
                        rainfall_data['cumulative'] = int(validated)
            except (IndexError, AttributeError, ValueError):
                pass
    
    def parse_river_data(self, soup: BeautifulSoup, target_time: datetime) -> Dict[str, Any]:
        """
        河川データを解析
        
        Args:
            soup: BeautifulSoupオブジェクト
            target_time: 対象時刻
            
        Returns:
            Dict: 河川データ
        """
        river_data = {
            'water_level': None,
            'level_change': None,
            'status': None,
            'actual_observation_time': None
        }
        
        if not soup:
            return river_data
        
        target_date = target_time.strftime('%Y/%m/%d')
        target_time_str = target_time.strftime('%H:%M')
        
        try:
            # Table 2（インデックス2）から検索
            tables = soup.find_all('table')
            if len(tables) > 2:
                table = tables[2]
                found = self._extract_river_from_table(
                    table, target_date, target_time_str, river_data
                )
                
                # 目標データが見つからない場合、最新データを取得
                if not found:
                    logger.info(f"Target river data not found for {target_date} {target_time_str}. Looking for latest...")
                    self._extract_latest_river_from_table(table, river_data)
            
            # 警戒レベルの判定
            if river_data['water_level'] is not None:
                river_data['status'] = self._determine_river_status(river_data['water_level'])
            
        except Exception as e:
            logger.error(f"Error parsing river data: {e}")
        
        return river_data
    
    def _extract_river_from_table(
        self, table, target_date: str, target_time: str, river_data: Dict
    ) -> bool:
        """
        テーブルから特定時刻の河川データを抽出
        
        Returns:
            bool: データが見つかった場合True
        """
        rows = table.find_all('tr')
        
        for row in rows:
            cells = row.find_all('td')
            
            if len(cells) >= 4:
                try:
                    date_text = cells[0].get_text().strip()
                    time_text = cells[1].get_text().strip()
                    
                    if date_text == target_date and time_text == target_time:
                        # 水位抽出
                        water_level_text = cells[2].get_text().strip()
                        
                        # データ妥当性チェック
                        if water_level_text and not water_level_text.startswith(('*', '-')):
                            value = self.extract_number(water_level_text)
                            validated = self.validate_value(value, 'river', 'water_level')
                            
                            if validated is not None:
                                river_data['water_level'] = validated
                                
                                # 水位変化抽出
                                if len(cells) > 3:
                                    self._extract_river_change(cells[3], river_data)
                                
                                river_data['actual_observation_time'] = f"{date_text} {time_text}"
                                return True
                                
                except (IndexError, AttributeError) as e:
                    logger.debug(f"Error processing river row: {e}")
                    continue
        
        return False
    
    def _extract_latest_river_from_table(self, table, river_data: Dict) -> bool:
        """
        テーブルから最新の河川データを抽出
        
        Returns:
            bool: データが見つかった場合True
        """
        rows = table.find_all('tr')
        
        # 最大10行前までチェック
        rows_to_check = rows[-10:] if len(rows) > 10 else rows
        
        for row in reversed(rows_to_check):
            cells = row.find_all('td')
            
            if len(cells) >= 4:
                try:
                    date_text = cells[0].get_text().strip()
                    time_text = cells[1].get_text().strip()
                    water_level_text = cells[2].get_text().strip()
                    
                    # 妥当性チェック
                    if (re.match(r'\d{4}/\d{2}/\d{2}', date_text) and 
                        re.match(r'\d{2}:\d{2}', time_text) and
                        water_level_text and 
                        not water_level_text.startswith(('*', '-'))):
                        
                        value = self.extract_number(water_level_text)
                        validated = self.validate_value(value, 'river', 'water_level')
                        
                        if validated is not None:
                            river_data['water_level'] = validated
                            
                            # 水位変化抽出
                            if len(cells) > 3:
                                self._extract_river_change(cells[3], river_data)
                            
                            river_data['actual_observation_time'] = f"{date_text} {time_text}"
                            logger.info(f"Found latest river data: {date_text} {time_text}")
                            return True
                            
                except (IndexError, AttributeError) as e:
                    logger.debug(f"Error processing river row: {e}")
                    continue
        
        return False
    
    def _extract_river_change(self, cell, river_data: Dict):
        """河川水位変化を抽出"""
        try:
            change_text = cell.get_text().strip()
            change_match = re.search(r'([+-]?\d+\.\d+)', change_text)
            
            if change_match:
                change = float(change_match.group(1))
                river_data['level_change'] = round(change, 2)
            else:
                river_data['level_change'] = 0.0
                
        except (ValueError, AttributeError):
            river_data['level_change'] = 0.0
    
    def _determine_river_status(self, water_level: float) -> str:
        """
        河川の警戒レベルを判定
        
        Args:
            water_level: 水位（m）
            
        Returns:
            str: 警戒レベル
        """
        thresholds = self.validation_rules['river']['thresholds']
        
        if water_level >= thresholds['danger']:
            return '氾濫危険'
        elif water_level >= thresholds['evacuation']:
            return '避難判断'
        elif water_level >= thresholds['caution']:
            return '氾濫注意'
        elif water_level >= thresholds['preparedness']:
            return '水防団待機'
        else:
            return '正常'


if __name__ == "__main__":
    # テスト実行
    import logging
    logging.basicConfig(level=logging.DEBUG)
    
    parser = DataParser()
    
    # 数値抽出テスト
    test_values = ['35.5', '-1.2', 'abc', '', '100.0', '1500.1']
    print("=== Number Extraction Test ===")
    for val in test_values:
        result = parser.extract_number(val)
        print(f"'{val}' -> {result}")
    
    # 検証テスト
    print("\n=== Validation Test ===")
    test_cases = [
        (35.5, 'dam', 'water_level'),  # 正常値
        (29.9, 'dam', 'water_level'),  # 範囲外
        (100.0, 'dam', 'storage_rate'),  # 境界値
        (5.5, 'river', 'water_level'),  # 正常値
    ]
    
    for value, data_type, field in test_cases:
        result = parser.validate_value(value, data_type, field)
        print(f"{data_type}.{field} = {value} -> {result}")
    
    # 警戒レベル判定テスト
    print("\n=== River Status Test ===")
    water_levels = [2.0, 3.8, 5.0, 5.1, 5.5, 6.0]
    for level in water_levels:
        status = parser._determine_river_status(level)
        print(f"Water level {level}m -> {status}")