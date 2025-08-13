"""観測地点の値オブジェクト"""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Location:
    """観測地点を表す値オブジェクト"""
    
    name: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    station_code: Optional[str] = None
    
    def __post_init__(self):
        """バリデーション"""
        if not self.name or not self.name.strip():
            raise ValueError("Location name cannot be empty")
        
        if self.latitude is not None:
            if not -90 <= self.latitude <= 90:
                raise ValueError("Latitude must be between -90 and 90")
        
        if self.longitude is not None:
            if not -180 <= self.longitude <= 180:
                raise ValueError("Longitude must be between -180 and 180")
    
    def has_coordinates(self) -> bool:
        """座標情報を持っているか"""
        return self.latitude is not None and self.longitude is not None
    
    def format_coordinates(self) -> str:
        """座標を文字列形式で返す"""
        if self.has_coordinates():
            return f"{self.latitude:.6f}, {self.longitude:.6f}"
        return "座標情報なし"