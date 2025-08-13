"""リポジトリ実装"""

# 注意: 以下のファイルは存在しません
# - dam_repository_impl.py
# 
# 存在するファイル:
# - history_repository.py
# - water_level_repository_impl.py

from .history_repository import HistoryRepository

__all__ = [
    "HistoryRepository"
]

# 以下は依存関係（aiohttp）が必要なため、必要時のみインポート
# from .water_level_repository_impl import WaterLevelRepositoryImpl

