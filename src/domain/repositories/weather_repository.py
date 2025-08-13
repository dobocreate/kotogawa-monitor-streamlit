"""天気リポジトリインターフェース"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from ..entities.weather import Weather


class WeatherRepository(ABC):
    """天気データのリポジトリインターフェース"""
    
    @abstractmethod
    async def get_latest(self) -> Optional[Weather]:
        """最新の天気データを取得"""
        pass
    
    @abstractmethod
    async def save(self, weather: Weather) -> None:
        """天気データを保存"""
        pass