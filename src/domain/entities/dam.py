"""ダムエンティティ"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class Dam:
    """ダムの状態を表すエンティティ"""
    
    observation_time: datetime
    water_level: float  # 貯水位（メートル）
    storage_rate: float  # 貯水率（パーセント）
    inflow: float  # 流入量（m³/s）
    outflow: float  # 放流量（m³/s）
    name: str
    
    @property
    def is_warning_level(self) -> bool:
        """警戒貯水率を超えているか"""
        return self.storage_rate >= 90.0
    
    @property
    def is_danger_level(self) -> bool:
        """危険貯水率を超えているか"""
        return self.storage_rate >= 95.0
    
    @property
    def status(self) -> str:
        """ダムの状態を返す"""
        if self.is_danger_level:
            return "danger"
        elif self.is_warning_level:
            return "warning"
        return "normal"
    
    @property
    def net_flow(self) -> float:
        """純流量（流入 - 放流）を計算"""
        return self.inflow - self.outflow
    
    def format_storage_rate(self) -> str:
        """貯水率を文字列形式で返す"""
        return f"{self.storage_rate:.1f}%"