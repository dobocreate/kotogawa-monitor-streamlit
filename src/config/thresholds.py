"""閾値設定"""
from dataclasses import dataclass
from typing import Dict


@dataclass
class ThresholdConfig:
    """アラート閾値の設定"""
    
    # 河川水位の閾値（メートル）
    river_preparedness: float = 3.80  # 水防団待機水位
    river_caution: float = 5.00      # 氾濫注意水位
    river_evacuation: float = 5.10   # 避難判断水位
    river_danger: float = 5.50       # 氾濫危険水位
    
    # ダム貯水率の閾値（パーセント）
    dam_warning: float = 90.0
    dam_danger: float = 95.0
    dam_critical: float = 98.0
    
    # 降水量の閾値（mm/h）
    rainfall_caution: float = 20.0
    rainfall_warning: float = 30.0
    rainfall_danger: float = 50.0
    
    # 水位変化率の閾値（m/h）
    level_change_warning: float = 0.5
    level_change_danger: float = 1.0
    
    def get_river_thresholds(self) -> Dict[str, float]:
        """河川水位の閾値を辞書形式で返す"""
        return {
            'preparedness': self.river_preparedness,
            'caution': self.river_caution,
            'evacuation': self.river_evacuation,
            'danger': self.river_danger
        }
    
    def get_dam_thresholds(self) -> Dict[str, float]:
        """ダムの閾値を辞書形式で返す"""
        return {
            'warning': self.dam_warning,
            'danger': self.dam_danger,
            'critical': self.dam_critical
        }
    
    def get_rainfall_thresholds(self) -> Dict[str, float]:
        """降水量の閾値を辞書形式で返す"""
        return {
            'caution': self.rainfall_caution,
            'warning': self.rainfall_warning,
            'danger': self.rainfall_danger
        }