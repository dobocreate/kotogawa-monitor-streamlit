"""閾値の値オブジェクト"""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Threshold:
    """閾値を表す値オブジェクト"""
    
    warning: float
    danger: float
    critical: Optional[float] = None
    
    def __post_init__(self):
        """バリデーション"""
        if self.warning >= self.danger:
            raise ValueError("Warning threshold must be less than danger threshold")
        if self.critical is not None and self.danger >= self.critical:
            raise ValueError("Danger threshold must be less than critical threshold")
    
    def get_level(self, value: float) -> str:
        """値に対応するレベルを返す"""
        if self.critical is not None and value >= self.critical:
            return "critical"
        elif value >= self.danger:
            return "danger"
        elif value >= self.warning:
            return "warning"
        return "normal"


class WaterLevelThreshold(Threshold):
    """河川水位の閾値"""
    
    @classmethod
    def default(cls) -> 'WaterLevelThreshold':
        """デフォルトの閾値を返す"""
        return cls(warning=3.0, danger=5.0, critical=7.0)


class DamStorageThreshold(Threshold):
    """ダム貯水率の閾値"""
    
    @classmethod
    def default(cls) -> 'DamStorageThreshold':
        """デフォルトの閾値を返す"""
        return cls(warning=90.0, danger=95.0, critical=98.0)