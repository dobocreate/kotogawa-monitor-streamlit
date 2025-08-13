"""河川水位リポジトリインターフェース"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from ..entities.water_level import WaterLevel


class WaterLevelRepository(ABC):
    """河川水位データのリポジトリインターフェース"""
    
    @abstractmethod
    async def get_latest(self, location: str) -> Optional[WaterLevel]:
        """最新の水位データを取得"""
        pass
    
    @abstractmethod
    async def get_history(
        self, 
        location: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[WaterLevel]:
        """指定期間の水位履歴を取得"""
        pass
    
    @abstractmethod
    async def save(self, water_level: WaterLevel) -> None:
        """水位データを保存"""
        pass
    
    @abstractmethod
    async def get_locations(self) -> List[str]:
        """利用可能な観測地点のリストを取得"""
        pass