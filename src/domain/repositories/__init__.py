"""リポジトリインターフェース"""

from .water_level_repository import WaterLevelRepository
from .dam_repository import DamRepository
from .weather_repository import WeatherRepository
from .alert_repository import AlertRepository

__all__ = [
    'WaterLevelRepository',
    'DamRepository', 
    'WeatherRepository',
    'AlertRepository'
]