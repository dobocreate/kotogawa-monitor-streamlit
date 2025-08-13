"""河川水位リポジトリの実装"""
import logging
from datetime import datetime
from typing import List, Optional

from ...domain.entities.water_level import WaterLevel
from ...domain.repositories.water_level_repository import WaterLevelRepository
from ..persistence.file_system import FileSystemPersistence
from ..api.yamaguchi_api import YamaguchiPrefectureAPI


logger = logging.getLogger(__name__)


class WaterLevelRepositoryImpl(WaterLevelRepository):
    """河川水位リポジトリの実装"""
    
    def __init__(self, persistence: FileSystemPersistence, api_client: YamaguchiPrefectureAPI):
        self.persistence = persistence
        self.api_client = api_client
    
    async def get_latest(self, location: str) -> Optional[WaterLevel]:
        """最新の水位データを取得"""
        try:
            # まずAPIから取得を試みる
            api_data = await self.api_client.get_water_level(location)
            if api_data:
                return self._convert_to_entity(api_data, location)
            
            # APIが失敗したら永続化層から取得
            persisted_data = self.persistence.load_latest_data()
            if persisted_data and 'river' in persisted_data:
                river_data = persisted_data['river']
                return self._convert_to_entity(river_data, location)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get latest water level: {e}")
            return None
    
    async def get_history(
        self,
        location: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[WaterLevel]:
        """指定期間の水位履歴を取得"""
        try:
            # 履歴データを読み込み
            hours = int((end_time - start_time).total_seconds() / 3600)
            history_data = self.persistence.load_history_data(hours)
            
            # 水位データを抽出してエンティティに変換
            water_levels = []
            for data in history_data:
                if 'river' in data:
                    entity = self._convert_to_entity(data['river'], location)
                    if entity and start_time <= entity.observation_time <= end_time:
                        water_levels.append(entity)
            
            return water_levels
            
        except Exception as e:
            logger.error(f"Failed to get water level history: {e}")
            return []
    
    async def save(self, water_level: WaterLevel) -> None:
        """水位データを保存"""
        try:
            data = {
                'timestamp': water_level.observation_time.isoformat(),
                'river': {
                    'location': water_level.location,
                    'level': water_level.level,
                    'change_rate': water_level.change_rate,
                    'observation_time': water_level.observation_time.isoformat()
                }
            }
            self.persistence.save_data(data)
            
        except Exception as e:
            logger.error(f"Failed to save water level: {e}")
            raise
    
    async def get_locations(self) -> List[str]:
        """利用可能な観測地点のリストを取得"""
        # 現在は固定値を返す
        return ["持世寺", "厚東川大橋", "広瀬"]
    
    def _convert_to_entity(self, data: dict, location: str) -> Optional[WaterLevel]:
        """データをエンティティに変換"""
        try:
            # 観測時刻を取得
            obs_time_str = data.get('observation_time') or data.get('timestamp')
            if not obs_time_str:
                return None
            
            obs_time = datetime.fromisoformat(obs_time_str.replace('Z', '+00:00'))
            
            # 水位を取得
            level = float(data.get('level', 0))
            
            # 変化率を計算（あれば）
            change_rate = None
            if 'change_rate' in data:
                change_rate = float(data['change_rate'])
            
            return WaterLevel(
                observation_time=obs_time,
                level=level,
                location=location,
                change_rate=change_rate
            )
            
        except Exception as e:
            logger.debug(f"Failed to convert data to WaterLevel entity: {e}")
            return None