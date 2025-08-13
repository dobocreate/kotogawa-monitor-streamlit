"""山口県防災情報システムAPIクライアント"""
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import aiohttp
from bs4 import BeautifulSoup

from .base import APIBase


logger = logging.getLogger(__name__)


class YamaguchiPrefectureAPI(APIBase):
    """山口県防災情報システムのAPIクライアント"""
    
    def __init__(self, timeout: int = 30):
        super().__init__("https://y-bousai.pref.yamaguchi.lg.jp", timeout)
        self.station_codes = {
            'dam': '015',  # 厚東川ダムの観測所コード
            'river': '05067',  # 厚東川（持世寺）の観測所コード
        }
    
    async def get_water_level(self, location: str = "持世寺") -> Optional[Dict[str, Any]]:
        """河川水位データを取得"""
        try:
            url = f"{self.base_url}/citizen/water/kwl_table.aspx"
            params = {'cd': self.station_codes['river']}
            
            if not self._session:
                self._session = aiohttp.ClientSession(timeout=self.timeout)
            
            async with self._session.get(url, params=params) as response:
                response.raise_for_status()
                html = await response.text()
                
                # HTMLをパース
                soup = BeautifulSoup(html, 'html.parser')
                data = self._parse_water_level_html(soup)
                
                if data:
                    data['location'] = location
                    data['station_code'] = self.station_codes['river']
                
                return data
                
        except Exception as e:
            logger.error(f"Failed to get water level: {e}")
            return None
    
    async def get_dam_data(self, dam_name: str = "厚東川ダム") -> Optional[Dict[str, Any]]:
        """ダムデータを取得"""
        try:
            url = f"{self.base_url}/citizen/dam/kdm_table.aspx"
            params = {'cd': self.station_codes['dam']}
            
            if not self._session:
                self._session = aiohttp.ClientSession(timeout=self.timeout)
            
            async with self._session.get(url, params=params) as response:
                response.raise_for_status()
                html = await response.text()
                
                # HTMLをパース
                soup = BeautifulSoup(html, 'html.parser')
                data = self._parse_dam_html(soup)
                
                if data:
                    data['name'] = dam_name
                    data['station_code'] = self.station_codes['dam']
                
                return data
                
        except Exception as e:
            logger.error(f"Failed to get dam data: {e}")
            return None
    
    def _parse_water_level_html(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """河川水位HTMLをパース"""
        try:
            # テーブルから最新データを取得
            table = soup.find('table', {'class': 'tb_style01'})
            if not table:
                return None
            
            rows = table.find_all('tr')
            if len(rows) < 2:
                return None
            
            # 最新行を取得（ヘッダーの次の行）
            latest_row = rows[1]
            cells = latest_row.find_all('td')
            
            if len(cells) < 3:
                return None
            
            # データを抽出
            observation_time_str = cells[0].text.strip()
            level_str = cells[1].text.strip()
            change_str = cells[2].text.strip() if len(cells) > 2 else "0"
            
            # 観測時刻をパース
            observation_time = self._parse_time(observation_time_str)
            
            # 水位をパース
            level = self._parse_float(level_str)
            if level is None:
                return None
            
            # 変化量をパース
            change = self._parse_float(change_str)
            
            return {
                'observation_time': observation_time.isoformat() if observation_time else None,
                'level': level,
                'change_rate': change,
                'status': self._determine_water_level_status(level)
            }
            
        except Exception as e:
            logger.error(f"Failed to parse water level HTML: {e}")
            return None
    
    def _parse_dam_html(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """ダムHTMLをパース"""
        try:
            # テーブルから最新データを取得
            table = soup.find('table', {'class': 'tb_style01'})
            if not table:
                return None
            
            rows = table.find_all('tr')
            if len(rows) < 2:
                return None
            
            # 最新行を取得
            latest_row = rows[1]
            cells = latest_row.find_all('td')
            
            if len(cells) < 5:
                return None
            
            # データを抽出
            observation_time_str = cells[0].text.strip()
            water_level_str = cells[1].text.strip()
            storage_rate_str = cells[2].text.strip()
            inflow_str = cells[3].text.strip()
            outflow_str = cells[4].text.strip()
            
            # 観測時刻をパース
            observation_time = self._parse_time(observation_time_str)
            
            # 数値をパース
            water_level = self._parse_float(water_level_str)
            storage_rate = self._parse_float(storage_rate_str)
            inflow = self._parse_float(inflow_str)
            outflow = self._parse_float(outflow_str)
            
            if water_level is None or storage_rate is None:
                return None
            
            return {
                'observation_time': observation_time.isoformat() if observation_time else None,
                'water_level': water_level,
                'storage_rate': storage_rate,
                'inflow': inflow or 0,
                'outflow': outflow or 0,
                'status': self._determine_dam_status(storage_rate)
            }
            
        except Exception as e:
            logger.error(f"Failed to parse dam HTML: {e}")
            return None
    
    def _parse_time(self, time_str: str) -> Optional[datetime]:
        """時刻文字列をパース"""
        try:
            # 例: "2024/01/15 10:00"
            return datetime.strptime(time_str, "%Y/%m/%d %H:%M")
        except:
            try:
                # 例: "01/15 10:00"
                current_year = datetime.now().year
                return datetime.strptime(f"{current_year}/{time_str}", "%Y/%m/%d %H:%M")
            except:
                return None
    
    def _parse_float(self, value_str: str) -> Optional[float]:
        """文字列を浮動小数点数にパース"""
        try:
            # 不要な文字を除去
            value_str = value_str.replace(',', '').replace('m', '').replace('%', '').strip()
            if value_str == '-' or value_str == '':
                return None
            return float(value_str)
        except:
            return None
    
    def _determine_water_level_status(self, level: float) -> str:
        """水位のステータスを判定"""
        if level >= 5.5:
            return "danger"
        elif level >= 5.0:
            return "caution"
        elif level >= 3.8:
            return "preparedness"
        return "normal"
    
    def _determine_dam_status(self, storage_rate: float) -> str:
        """ダムのステータスを判定"""
        if storage_rate >= 95.0:
            return "danger"
        elif storage_rate >= 90.0:
            return "warning"
        return "normal"