"""ダムリポジトリインターフェース"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from ..entities.dam import Dam


class DamRepository(ABC):
    """ダムデータのリポジトリインターフェース"""
    
    @abstractmethod
    async def get_latest(self, dam_name: str) -> Optional[Dam]:
        """最新のダムデータを取得"""
        pass
    
    @abstractmethod
    async def get_history(
        self,
        dam_name: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[Dam]:
        """指定期間のダム履歴を取得"""
        pass
    
    @abstractmethod
    async def save(self, dam: Dam) -> None:
        """ダムデータを保存"""
        pass
    
    @abstractmethod
    async def get_dam_names(self) -> List[str]:
        """利用可能なダムのリストを取得"""
        pass