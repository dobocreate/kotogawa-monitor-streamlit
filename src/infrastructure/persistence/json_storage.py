"""JSONストレージ実装"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional


logger = logging.getLogger(__name__)


class JsonStorage:
    """JSON形式でのデータストレージ"""
    
    def __init__(self, file_path: Path):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
    
    def save(self, data: Dict[str, Any]) -> bool:
        """データをJSON形式で保存"""
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.debug(f"Data saved to {self.file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save data to {self.file_path}: {e}")
            return False
    
    def load(self) -> Optional[Dict[str, Any]]:
        """JSONファイルからデータを読み込み"""
        if not self.file_path.exists():
            logger.debug(f"File not found: {self.file_path}")
            return None
        
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.debug(f"Data loaded from {self.file_path}")
            return data
        except Exception as e:
            logger.error(f"Failed to load data from {self.file_path}: {e}")
            return None
    
    def exists(self) -> bool:
        """ファイルが存在するか確認"""
        return self.file_path.exists()
    
    def delete(self) -> bool:
        """ファイルを削除"""
        try:
            if self.file_path.exists():
                self.file_path.unlink()
                logger.debug(f"File deleted: {self.file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete file {self.file_path}: {e}")
            return False