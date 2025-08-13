"""時間範囲の値オブジェクト"""
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class TimeRange:
    """時間範囲を表す値オブジェクト"""
    
    start: datetime
    end: datetime
    
    def __post_init__(self):
        """バリデーション"""
        if self.start >= self.end:
            raise ValueError("Start time must be before end time")
    
    def contains(self, time: datetime) -> bool:
        """指定時刻が範囲内にあるか"""
        return self.start <= time <= self.end
    
    def duration_hours(self) -> float:
        """期間を時間単位で返す"""
        return (self.end - self.start).total_seconds() / 3600
    
    def duration_days(self) -> float:
        """期間を日単位で返す"""
        return self.duration_hours() / 24