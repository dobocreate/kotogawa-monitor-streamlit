"""河川水位エンティティ"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class WaterLevel:
    """河川水位を表すエンティティ"""
    
    observation_time: datetime
    level: float  # 水位（メートル）
    location: str
    change_rate: Optional[float] = None  # 変化率（メートル/時）
    
    @property
    def is_warning_level(self) -> bool:
        """警戒水位を超えているか"""
        return self.level >= 3.0
    
    @property
    def is_danger_level(self) -> bool:
        """危険水位を超えているか"""
        return self.level >= 5.0
    
    @property
    def status(self) -> str:
        """水位の状態を返す"""
        if self.is_danger_level:
            return "danger"
        elif self.is_warning_level:
            return "warning"
        return "normal"
    
    def format_level(self) -> str:
        """水位を文字列形式で返す"""
        return f"{self.level:.2f}m"