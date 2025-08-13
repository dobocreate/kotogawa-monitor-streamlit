"""天気エンティティ"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List


@dataclass(frozen=True)
class RainfallData:
    """降水量データ"""
    time: datetime
    amount: float  # mm
    location: str


@dataclass(frozen=True)
class WeatherForecast:
    """天気予報"""
    date: datetime
    description: str
    precipitation_probability: int  # パーセント
    max_temperature: Optional[float] = None
    min_temperature: Optional[float] = None


@dataclass(frozen=True)
class Weather:
    """天気情報を表すエンティティ"""
    
    observation_time: datetime
    current_rainfall: Optional[RainfallData] = None
    hourly_rainfall: Optional[List[RainfallData]] = None
    cumulative_rainfall: Optional[float] = None  # 累積雨量（mm）
    forecast: Optional[List[WeatherForecast]] = None
    
    @property
    def is_heavy_rain(self) -> bool:
        """大雨かどうか"""
        if self.current_rainfall:
            return self.current_rainfall.amount >= 30.0  # 30mm/h以上を大雨とする
        return False
    
    @property
    def has_rain_forecast(self) -> bool:
        """雨の予報があるか"""
        if self.forecast:
            return any(f.precipitation_probability >= 50 for f in self.forecast[:3])  # 3日以内
        return False