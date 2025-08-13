"""アプリケーション設定（クリーンアーキテクチャ版）"""
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import json


@dataclass
class AppSettings:
    """アプリケーション設定"""
    
    # パス設定
    base_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent)
    data_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent / "data")
    history_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent / "data" / "history")
    
    # API設定
    api_endpoints: Dict[str, str] = field(default_factory=lambda: {
        'dam': "https://y-bousai.pref.yamaguchi.lg.jp/citizen/dam/kdm_table.aspx",
        'river': "https://y-bousai.pref.yamaguchi.lg.jp/citizen/water/kwl_table.aspx",
        'weather': "https://www.jma.go.jp/bosai/forecast/data/forecast/350000.json",
        'yahoo_weather': "https://map.yahooapis.jp/weather/V1/place"
    })
    
    # 観測所コード
    station_codes: Dict[str, str] = field(default_factory=lambda: {
        'dam': '015',  # 厚東川ダムの観測所コード
        'river': '05067',  # 厚東川（持世寺）の観測所コード
        'weather_area': '350010',  # 山口県西部
        'weather_prefecture': '350000'  # 山口県
    })
    
    # リクエスト設定
    request_timeout: int = 30
    max_retries: int = 5
    retry_delay: int = 3
    
    # Yahoo Weather API
    yahoo_app_id: str = "dj00aiZpPW5YTFVqSXc0S2dCcSZzPWNvbnN1bWVyc2VjcmV0Jng9MDA-"
    yahoo_coordinates: str = "131.289496,34.079891"  # 経度,緯度
    
    # 更新間隔（秒）
    refresh_interval: int = 60
    data_collection_interval: int = 600  # 10分
    
    # アラート閾値
    river_thresholds: Dict[str, float] = field(default_factory=lambda: {
        'preparedness': 3.80,  # 水防団待機水位
        'caution': 5.00,      # 氾濫注意水位
        'evacuation': 5.10,   # 避難判断水位
        'danger': 5.50        # 氾濫危険水位
    })
    
    dam_warning_threshold: float = 90.0
    dam_danger_threshold: float = 95.0
    
    # データ保持期間（日）
    data_retention_days: int = 7
    
    # ログ設定
    log_level: str = "INFO"
    log_format: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    @classmethod
    def from_env(cls) -> 'AppSettings':
        """環境変数から設定を読み込む"""
        settings = cls()
        
        # 環境変数からの上書き
        if api_timeout := os.getenv('KOTOGAWA_API_TIMEOUT'):
            settings.request_timeout = int(api_timeout)
        
        if refresh := os.getenv('KOTOGAWA_REFRESH_INTERVAL'):
            settings.refresh_interval = int(refresh)
        
        if retention := os.getenv('KOTOGAWA_DATA_RETENTION_DAYS'):
            settings.data_retention_days = int(retention)
        
        if log_level := os.getenv('KOTOGAWA_LOG_LEVEL'):
            settings.log_level = log_level
        
        return settings
    
    @classmethod
    def from_file(cls, file_path: Path) -> 'AppSettings':
        """ファイルから設定を読み込む"""
        if not file_path.exists():
            return cls()
        
        with open(file_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        return cls(**config)
    
    @classmethod
    def load(cls) -> 'AppSettings':
        """設定を読み込む（環境変数優先）"""
        # デフォルト設定
        settings = cls()
        
        # 設定ファイルがあれば読み込む
        config_file = Path(__file__).parent.parent.parent / "config" / "app_config.json"
        if config_file.exists():
            settings = cls.from_file(config_file)
        
        # 環境変数で上書き
        env_settings = cls.from_env()
        for key, value in env_settings.__dict__.items():
            if value != getattr(cls(), key, None):  # デフォルトと違う場合のみ上書き
                setattr(settings, key, value)
        
        return settings
    
    def to_dict(self) -> Dict[str, Any]:
        """設定を辞書形式で返す"""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, Path):
                result[key] = str(value)
            else:
                result[key] = value
        return result
    
    def save(self, file_path: Path):
        """設定をファイルに保存"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)