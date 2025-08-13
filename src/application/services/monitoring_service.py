"""監視サービス"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import logging

from ...domain.entities import WaterLevel, Dam, Weather, Alert
from ...domain.repositories import (
    WaterLevelRepository,
    DamRepository,
    WeatherRepository,
    AlertRepository
)
from ...domain.value_objects import TimeRange, WaterLevelThreshold, DamStorageThreshold


logger = logging.getLogger(__name__)


class MonitoringService:
    """河川・ダム監視サービス"""
    
    def __init__(
        self,
        water_level_repo: WaterLevelRepository,
        dam_repo: DamRepository,
        weather_repo: WeatherRepository,
        alert_repo: AlertRepository
    ):
        self.water_level_repo = water_level_repo
        self.dam_repo = dam_repo
        self.weather_repo = weather_repo
        self.alert_repo = alert_repo
        self.water_level_threshold = WaterLevelThreshold.default()
        self.dam_storage_threshold = DamStorageThreshold.default()
    
    async def get_current_status(self) -> Dict[str, Any]:
        """現在の監視状況を取得"""
        try:
            # 各データソースから最新データを取得
            water_level = await self.water_level_repo.get_latest("持世寺")
            dam = await self.dam_repo.get_latest("厚東川ダム")
            weather = await self.weather_repo.get_latest()
            
            # アラートをチェック
            alerts = await self._check_alerts(water_level, dam, weather)
            
            return {
                "timestamp": datetime.now(),
                "water_level": water_level,
                "dam": dam,
                "weather": weather,
                "alerts": alerts,
                "status": self._determine_overall_status(alerts)
            }
        except Exception as e:
            logger.error(f"Failed to get current status: {e}")
            raise
    
    async def get_historical_data(
        self,
        hours: int = 72
    ) -> Dict[str, Any]:
        """過去データを取得"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        time_range = TimeRange(start_time, end_time)
        
        try:
            water_levels = await self.water_level_repo.get_history(
                "持世寺", time_range.start, time_range.end
            )
            dam_data = await self.dam_repo.get_history(
                "厚東川ダム", time_range.start, time_range.end
            )
            
            return {
                "time_range": time_range,
                "water_levels": water_levels,
                "dam_data": dam_data
            }
        except Exception as e:
            logger.error(f"Failed to get historical data: {e}")
            raise
    
    async def _check_alerts(
        self,
        water_level: Optional[WaterLevel],
        dam: Optional[Dam],
        weather: Optional[Weather]
    ) -> List[Alert]:
        """アラート条件をチェック"""
        alerts = []
        
        # 河川水位チェック
        if water_level:
            level_status = self.water_level_threshold.get_level(water_level.level)
            if level_status != "normal":
                alerts.append(self._create_water_level_alert(water_level, level_status))
        
        # ダム貯水率チェック
        if dam:
            storage_status = self.dam_storage_threshold.get_level(dam.storage_rate)
            if storage_status != "normal":
                alerts.append(self._create_dam_alert(dam, storage_status))
        
        # 天気チェック
        if weather and weather.is_heavy_rain:
            alerts.append(self._create_weather_alert(weather))
        
        return alerts
    
    def _create_water_level_alert(self, water_level: WaterLevel, status: str) -> Alert:
        """河川水位アラートを作成"""
        from ...domain.entities.alert import Alert, AlertLevel, AlertType
        import uuid
        
        level_map = {
            "warning": AlertLevel.WARNING,
            "danger": AlertLevel.DANGER,
            "critical": AlertLevel.CRITICAL
        }
        
        return Alert(
            id=str(uuid.uuid4()),
            type=AlertType.WATER_LEVEL,
            level=level_map[status],
            title=f"河川水位{status.upper()}",
            message=f"持世寺の水位が{water_level.format_level()}に達しました",
            created_at=datetime.now(),
            location="持世寺",
            value=water_level.level,
            threshold=self.water_level_threshold.warning if status == "warning" else self.water_level_threshold.danger
        )
    
    def _create_dam_alert(self, dam: Dam, status: str) -> Alert:
        """ダムアラートを作成"""
        from ...domain.entities.alert import Alert, AlertLevel, AlertType
        import uuid
        
        level_map = {
            "warning": AlertLevel.WARNING,
            "danger": AlertLevel.DANGER,
            "critical": AlertLevel.CRITICAL
        }
        
        return Alert(
            id=str(uuid.uuid4()),
            type=AlertType.DAM_STORAGE,
            level=level_map[status],
            title=f"ダム貯水率{status.upper()}",
            message=f"厚東川ダムの貯水率が{dam.format_storage_rate()}に達しました",
            created_at=datetime.now(),
            location="厚東川ダム",
            value=dam.storage_rate,
            threshold=self.dam_storage_threshold.warning if status == "warning" else self.dam_storage_threshold.danger
        )
    
    def _create_weather_alert(self, weather: Weather) -> Alert:
        """天気アラートを作成"""
        from ...domain.entities.alert import Alert, AlertLevel, AlertType
        import uuid
        
        return Alert(
            id=str(uuid.uuid4()),
            type=AlertType.HEAVY_RAIN,
            level=AlertLevel.WARNING,
            title="大雨警報",
            message=f"現在の降水量: {weather.current_rainfall.amount}mm/h",
            created_at=datetime.now()
        )
    
    def _determine_overall_status(self, alerts: List[Alert]) -> str:
        """全体のステータスを決定"""
        if not alerts:
            return "normal"
        
        has_critical = any(alert.is_critical for alert in alerts)
        if has_critical:
            return "critical"
        
        return "warning"