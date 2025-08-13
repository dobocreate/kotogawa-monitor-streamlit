"""アラートリポジトリインターフェース"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from ..entities.alert import Alert


class AlertRepository(ABC):
    """アラートのリポジトリインターフェース"""
    
    @abstractmethod
    async def get_active_alerts(self) -> List[Alert]:
        """アクティブなアラートのリストを取得"""
        pass
    
    @abstractmethod
    async def save(self, alert: Alert) -> None:
        """アラートを保存"""
        pass
    
    @abstractmethod
    async def dismiss(self, alert_id: str) -> None:
        """アラートを消去"""
        pass
    
    @abstractmethod
    async def get_history(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> List[Alert]:
        """指定期間のアラート履歴を取得"""
        pass