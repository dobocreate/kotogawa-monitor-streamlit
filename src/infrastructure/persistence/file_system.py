"""ファイルシステムベースの永続化実装"""
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
try:
    from zoneinfo import ZoneInfo
except ImportError:
    import pytz
    ZoneInfo = lambda x: pytz.timezone(x)


logger = logging.getLogger(__name__)


class FileSystemPersistence:
    """ファイルシステムを使用したデータ永続化"""
    
    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.history_dir = self.base_dir / "history"
        self.latest_file = self.base_dir / "latest.json"
        
        # ディレクトリ作成
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.history_dir.mkdir(parents=True, exist_ok=True)
    
    def save_data(self, data: Dict[str, Any]) -> bool:
        """データを保存"""
        try:
            # タイムスタンプを取得
            timestamp = data.get('timestamp')
            if not timestamp:
                timestamp = datetime.now(ZoneInfo('Asia/Tokyo')).isoformat()
                data['timestamp'] = timestamp
            
            # タイムスタンプをパース
            if isinstance(timestamp, str):
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=ZoneInfo('Asia/Tokyo'))
                else:
                    dt = dt.astimezone(ZoneInfo('Asia/Tokyo'))
            else:
                dt = timestamp
            
            # 履歴ファイルのパスを生成
            year_dir = self.history_dir / dt.strftime("%Y")
            month_dir = year_dir / dt.strftime("%m")
            day_dir = month_dir / dt.strftime("%d")
            day_dir.mkdir(parents=True, exist_ok=True)
            
            # ファイル名を生成（時分）
            filename = dt.strftime("%H%M.json")
            file_path = day_dir / filename
            
            # データを保存
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 最新データとしても保存
            with open(self.latest_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Data saved to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save data: {e}")
            return False
    
    def load_latest_data(self) -> Optional[Dict[str, Any]]:
        """最新データを読み込む"""
        try:
            # 最新ファイルから読み込み
            if self.latest_file.exists():
                with open(self.latest_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            
            # なければ履歴から最新を探す
            latest_file = self._find_latest_history_file()
            if latest_file:
                with open(latest_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to load latest data: {e}")
            return None
    
    def load_history_data(self, hours: int = 72) -> List[Dict[str, Any]]:
        """履歴データを読み込む"""
        history_data = []
        end_time = datetime.now(ZoneInfo('Asia/Tokyo'))
        start_time = end_time - timedelta(hours=hours)
        
        try:
            # 日付ごとにディレクトリを処理
            current_time = end_time
            while current_time >= start_time:
                date_dir = (self.history_dir / 
                           current_time.strftime("%Y") / 
                           current_time.strftime("%m") / 
                           current_time.strftime("%d"))
                
                if date_dir.exists():
                    # ファイルを読み込み
                    for file_path in sorted(date_dir.glob("*.json")):
                        # daily_summaryファイルはスキップ
                        if file_path.name == "daily_summary.json":
                            continue
                        
                        # エラーファイルはスキップ
                        if file_path.name.startswith("error_"):
                            continue
                        
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                                
                                # タイムスタンプチェック
                                if 'timestamp' in data:
                                    data_dt = datetime.fromisoformat(
                                        data['timestamp'].replace('Z', '+00:00')
                                    )
                                    if data_dt.tzinfo is None:
                                        data_dt = data_dt.replace(tzinfo=ZoneInfo('Asia/Tokyo'))
                                    else:
                                        data_dt = data_dt.astimezone(ZoneInfo('Asia/Tokyo'))
                                    
                                    # 期間内のデータのみ追加
                                    if start_time <= data_dt <= end_time:
                                        history_data.append(data)
                        except Exception as e:
                            logger.debug(f"Failed to read file {file_path}: {e}")
                            continue
                
                current_time -= timedelta(days=1)
            
            # 時系列順にソート
            history_data.sort(key=lambda x: x.get('timestamp', ''))
            
            return history_data
            
        except Exception as e:
            logger.error(f"Failed to load history data: {e}")
            return []
    
    def _find_latest_history_file(self) -> Optional[Path]:
        """最新の履歴ファイルを探す"""
        latest_file = None
        latest_time = None
        
        # 過去7日間を検索
        end_time = datetime.now(ZoneInfo('Asia/Tokyo'))
        for days_ago in range(7):
            check_date = end_time - timedelta(days=days_ago)
            date_dir = (self.history_dir / 
                       check_date.strftime("%Y") / 
                       check_date.strftime("%m") / 
                       check_date.strftime("%d"))
            
            if date_dir.exists():
                for file_path in sorted(date_dir.glob("*.json"), reverse=True):
                    if file_path.name == "daily_summary.json":
                        continue
                    if file_path.name.startswith("error_"):
                        continue
                    
                    try:
                        # ファイル名から時刻を取得
                        time_str = file_path.stem
                        file_dt = datetime.strptime(
                            f"{check_date.strftime('%Y%m%d')}{time_str}",
                            "%Y%m%d%H%M"
                        ).replace(tzinfo=ZoneInfo('Asia/Tokyo'))
                        
                        if latest_time is None or file_dt > latest_time:
                            latest_time = file_dt
                            latest_file = file_path
                    except:
                        continue
            
            if latest_file:
                break
        
        return latest_file
    
    def cleanup_old_data(self, days: int = 7):
        """古いデータを削除"""
        cutoff_date = datetime.now(ZoneInfo('Asia/Tokyo')) - timedelta(days=days)
        
        try:
            # 年ディレクトリを処理
            for year_dir in self.history_dir.iterdir():
                if not year_dir.is_dir():
                    continue
                
                # 月ディレクトリを処理
                for month_dir in year_dir.iterdir():
                    if not month_dir.is_dir():
                        continue
                    
                    # 日ディレクトリを処理
                    for day_dir in month_dir.iterdir():
                        if not day_dir.is_dir():
                            continue
                        
                        try:
                            # ディレクトリ名から日付を取得
                            dir_date = datetime.strptime(
                                f"{year_dir.name}{month_dir.name}{day_dir.name}",
                                "%Y%m%d"
                            ).replace(tzinfo=ZoneInfo('Asia/Tokyo'))
                            
                            # 古いディレクトリを削除
                            if dir_date < cutoff_date:
                                for file_path in day_dir.glob("*.json"):
                                    file_path.unlink()
                                day_dir.rmdir()
                                logger.info(f"Deleted old directory: {day_dir}")
                        except Exception as e:
                            logger.debug(f"Failed to process directory {day_dir}: {e}")
                    
                    # 空の月ディレクトリを削除
                    if not any(month_dir.iterdir()):
                        month_dir.rmdir()
                
                # 空の年ディレクトリを削除
                if not any(year_dir.iterdir()):
                    year_dir.rmdir()
                    
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")