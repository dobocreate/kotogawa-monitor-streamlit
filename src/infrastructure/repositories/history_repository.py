"""
履歴データリポジトリ
data/historyディレクトリからJSONファイルを読み込む
"""
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
try:
    from zoneinfo import ZoneInfo
except ImportError:
    # Python 3.8以前の場合
    import pytz
    ZoneInfo = lambda x: pytz.timezone(x)


class HistoryRepository:
    """履歴データリポジトリ"""
    
    def __init__(self, base_dir: Optional[Path] = None):
        """
        Args:
            base_dir: プロジェクトのベースディレクトリ（デフォルトは現在のディレクトリ）
        """
        if base_dir is None:
            # app.pyから呼ばれることを想定し、プロジェクトルートを基準にする
            base_dir = Path.cwd()
        self.base_dir = base_dir
        self.history_dir = base_dir / "data" / "history"
    
    def load_latest_data(self) -> Optional[Dict[str, Any]]:
        """最新のデータを取得"""
        latest_file = self._get_latest_history_file()
        
        if not latest_file:
            return None
        
        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # データの整合性チェック
                if not data or 'timestamp' not in data:
                    return None
                return data
        except (json.JSONDecodeError, FileNotFoundError, Exception):
            return None
    
    def load_history_data(self, hours: int = 24) -> List[Dict[str, Any]]:
        """指定時間分の履歴データを取得
        
        Args:
            hours: 取得する時間数（デフォルト24時間）
        
        Returns:
            履歴データのリスト（時系列順）
        """
        history_data = []
        # JST（日本標準時）で現在時刻を取得
        end_time = datetime.now(ZoneInfo('Asia/Tokyo'))
        start_time = end_time - timedelta(hours=hours)
        
        if not self.history_dir.exists():
            return history_data
        
        processed_files = 0
        max_files = min(hours * 6 + 50, 500)  # 10分間隔データを想定
        
        # 時間に応じて日付ディレクトリを処理（新しいデータから逆順で処理）
        current_time = end_time
        while current_time >= start_time and processed_files < max_files:
            date_dir = (self.history_dir / 
                       current_time.strftime("%Y") / 
                       current_time.strftime("%m") / 
                       current_time.strftime("%d"))
            
            if date_dir.exists():
                # ファイルを降順でソートして新しいものから処理
                json_files = sorted(date_dir.glob("*.json"), reverse=True)
                for file_path in json_files:
                    if processed_files >= max_files:
                        break
                    
                    # daily_summaryファイルはスキップ
                    if file_path.name == "daily_summary.json":
                        continue
                    
                    # error_*.jsonファイルはスキップ
                    if file_path.name.startswith("error_"):
                        continue
                    
                    try:
                        # 直近で更新された可能性のあるファイル（書き込み中の一時的不整合を回避）をスキップ
                        try:
                            mtime = file_path.stat().st_mtime
                            age_sec = (datetime.now().timestamp() - mtime)
                            if age_sec < 10:
                                # 直近10秒以内に更新されたファイルは読み飛ばす
                                continue
                        except Exception:
                            pass
                        
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            
                            # データの基本検証
                            if data and 'timestamp' in data:
                                # タイムスタンプをJSTで解析して時間範囲チェック
                                try:
                                    data_timestamp = datetime.fromisoformat(
                                        data['timestamp'].replace('Z', '+00:00')
                                    )
                                    if data_timestamp.tzinfo is None:
                                        data_timestamp = data_timestamp.replace(
                                            tzinfo=ZoneInfo('Asia/Tokyo')
                                        )
                                    else:
                                        data_timestamp = data_timestamp.astimezone(
                                            ZoneInfo('Asia/Tokyo')
                                        )
                                    
                                    # 指定された時間範囲内のデータのみ追加
                                    if start_time <= data_timestamp <= end_time:
                                        history_data.append(data)
                                        processed_files += 1
                                    
                                except Exception:
                                    # タイムスタンプ解析エラーの場合も追加（後方互換性）
                                    history_data.append(data)
                                    processed_files += 1
                                    
                    except (json.JSONDecodeError, Exception):
                        # 個別のファイルエラーは無視して処理を継続
                        continue
            
            current_time -= timedelta(days=1)
        
        # 時系列順にソート（data_timeを優先、なければtimestamp）
        try:
            history_data.sort(key=lambda x: x.get('data_time', x.get('timestamp', '')))
        except Exception:
            pass
        
        return history_data
    
    def _get_latest_history_file(self) -> Optional[Path]:
        """最新の履歴ファイルを取得"""
        if not self.history_dir.exists():
            return None
        
        # 最新のファイルを検索（過去3日分を確認）
        end_time = datetime.now(ZoneInfo('Asia/Tokyo'))
        
        for days_ago in range(3):
            check_time = end_time - timedelta(days=days_ago)
            date_dir = (self.history_dir / 
                       check_time.strftime("%Y") / 
                       check_time.strftime("%m") / 
                       check_time.strftime("%d"))
            
            if date_dir.exists():
                # error_*.json以外のJSONファイルを取得
                json_files = [
                    f for f in sorted(date_dir.glob("*.json"), reverse=True)
                    if not f.name.startswith("error_") and f.name != "daily_summary.json"
                ]
                
                if json_files:
                    return json_files[0]  # 最新のファイルを返す
        
        return None