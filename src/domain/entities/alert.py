"""アラートエンティティ"""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class AlertLevel(Enum):
    """アラートレベル"""
    INFO = "info"
    WARNING = "warning"
    DANGER = "danger"
    CRITICAL = "critical"


class AlertType(Enum):
    """アラートタイプ"""
    WATER_LEVEL = "water_level"
    DAM_STORAGE = "dam_storage"
    HEAVY_RAIN = "heavy_rain"
    RAPID_CHANGE = "rapid_change"


@dataclass(frozen=True)
class Alert:
    """アラートを表すエンティティ"""
    
    id: str
    type: AlertType
    level: AlertLevel
    title: str
    message: str
    created_at: datetime
    location: Optional[str] = None
    value: Optional[float] = None
    threshold: Optional[float] = None
    
    @property
    def is_critical(self) -> bool:
        """重大なアラートか"""
        return self.level in [AlertLevel.DANGER, AlertLevel.CRITICAL]
    
    def format_message(self) -> str:
        """アラートメッセージをフォーマット"""
        if self.location:
            return f"[{self.location}] {self.message}"
        return self.message