#!/usr/bin/env python3
"""
設定管理モジュール
config.ymlから設定を読み込み、環境変数でオーバーライド可能
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging

class ConfigManager:
    """設定管理クラス"""
    
    _instance = None
    _config = None
    
    def __new__(cls):
        """シングルトンパターンの実装"""
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初期化"""
        if self._config is None:
            self.load_config()
    
    def load_config(self, config_path: Optional[str] = None):
        """設定ファイルを読み込む"""
        if config_path is None:
            # デフォルトパスを使用
            base_dir = Path(__file__).parent.parent
            config_path = base_dir / "config" / "config.yml"
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)
            
            # 環境変数でオーバーライド
            self._override_with_env()
            
            logging.info(f"Configuration loaded from {config_path}")
            
        except FileNotFoundError:
            logging.warning(f"Config file not found: {config_path}. Using defaults.")
            self._config = self._get_default_config()
        except yaml.YAMLError as e:
            logging.error(f"Error parsing config file: {e}. Using defaults.")
            self._config = self._get_default_config()
    
    def _override_with_env(self):
        """環境変数で設定をオーバーライド"""
        # HTTPタイムアウト
        if 'HTTP_TIMEOUT' in os.environ:
            self._config['http']['timeout'] = int(os.environ['HTTP_TIMEOUT'])
        
        # リトライ回数
        if 'MAX_RETRIES' in os.environ:
            self._config['http']['max_retries'] = int(os.environ['MAX_RETRIES'])
        
        # バックフィル設定
        if 'BACKFILL_HOURS' in os.environ:
            self._config['backfill']['default_hours'] = int(os.environ['BACKFILL_HOURS'])
        
        if 'BACKFILL_MAX_ITEMS' in os.environ:
            self._config['backfill']['max_items'] = int(os.environ['BACKFILL_MAX_ITEMS'])
        
        # 機能フラグ
        if 'USE_EXTENDED_BACKFILL' in os.environ:
            self._config['features']['use_extended_backfill'] = os.environ['USE_EXTENDED_BACKFILL'].lower() == 'true'
        
        if 'DEBUG_MODE' in os.environ:
            self._config['features']['debug_mode'] = os.environ['DEBUG_MODE'].lower() == 'true'
        
        # ログレベル
        if 'LOG_LEVEL' in os.environ:
            self._config['logging']['level'] = os.environ['LOG_LEVEL']
    
    def _get_default_config(self) -> Dict[str, Any]:
        """デフォルト設定を返す"""
        return {
            'data_sources': {
                'dam': {
                    'url': "https://y-bousai.pref.yamaguchi.lg.jp/citizen/dam/kdm_table.aspx",
                    'station_code': "015"
                },
                'river': {
                    'url': "https://y-bousai.pref.yamaguchi.lg.jp/citizen/water/kwl_table.aspx",
                    'station_code': "05067"
                },
                'weather': {
                    'jma_url': "https://www.jma.go.jp/bosai/forecast/data/forecast/350000.json",
                    'area_code': "350012",
                    'west_area_code': "350010"
                },
                'yahoo_weather': {
                    'api_url': "https://map.yahooapis.jp/weather/V1/place",
                    'app_id': "dj00aiZpPW5YTFVqSXc0S2dCcSZzPWNvbnN1bWVyc2VjcmV0Jng9MDA-",
                    'coordinates': "131.289496,34.079891"
                }
            },
            'http': {
                'timeout': 30,
                'max_retries': 5,
                'retry_delay': 3,
                'user_agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            },
            'validation': {
                'dam': {
                    'water_level': {'min': 30.0, 'max': 40.0},
                    'storage_rate': {'min': 0.0, 'max': 100.0},
                    'flow': {'min': 0.0, 'max': 1500.0}
                },
                'river': {
                    'water_level': {'min': 0.5, 'max': 10.0},
                    'thresholds': {
                        'preparedness': 3.80,
                        'caution': 5.00,
                        'evacuation': 5.10,
                        'danger': 5.50
                    }
                },
                'rainfall': {
                    'hourly': {'min': 0, 'max': 200},
                    'cumulative': {'min': 0, 'max': 1000}
                }
            },
            'backfill': {
                'default_hours': 12,
                'max_items': 6,
                'api_delay': 2,
                'extended': {
                    'hours': 24,
                    'max_items': 20,
                    'parallel': False
                }
            },
            'storage': {
                'data_dir': "data",
                'history_dir': "data/history",
                'retention_days': 7
            },
            'logging': {
                'level': "INFO",
                'format': "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                'file': "logs/collect_data.log",
                'max_bytes': 10485760,
                'backup_count': 5
            },
            'features': {
                'use_extended_backfill': False,
                'enable_parallel_processing': False,
                'use_circuit_breaker': False,
                'structured_logging': False,
                'debug_mode': False
            }
        }
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        ドット記法で設定値を取得
        例: config.get('http.timeout', 30)
        """
        keys = key_path.split('.')
        value = self._config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """設定セクション全体を取得"""
        return self._config.get(section, {})
    
    def is_feature_enabled(self, feature: str) -> bool:
        """機能フラグの状態を確認"""
        return self.get(f'features.{feature}', False)
    
    def get_validation_range(self, data_type: str, field: str) -> tuple:
        """検証範囲を取得"""
        min_val = self.get(f'validation.{data_type}.{field}.min')
        max_val = self.get(f'validation.{data_type}.{field}.max')
        return (min_val, max_val)
    
    def reload(self):
        """設定を再読み込み"""
        self._config = None
        self.load_config()
    
    @property
    def config(self) -> Dict[str, Any]:
        """設定全体を取得（読み取り専用）"""
        return self._config.copy() if self._config else {}


# グローバルインスタンス
config = ConfigManager()


if __name__ == "__main__":
    # テスト実行
    import json
    
    # 設定読み込み
    config_mgr = ConfigManager()
    
    # 設定値の取得例
    print("=== Configuration Test ===")
    print(f"HTTP Timeout: {config_mgr.get('http.timeout')}")
    print(f"Max Retries: {config_mgr.get('http.max_retries')}")
    print(f"Dam URL: {config_mgr.get('data_sources.dam.url')}")
    print(f"Debug Mode: {config_mgr.is_feature_enabled('debug_mode')}")
    
    # 検証範囲の取得
    dam_level_range = config_mgr.get_validation_range('dam', 'water_level')
    print(f"Dam Water Level Range: {dam_level_range}")
    
    # セクション取得
    http_config = config_mgr.get_section('http')
    print(f"\nHTTP Config:")
    print(json.dumps(http_config, indent=2))
    
    # 環境変数でオーバーライド
    os.environ['HTTP_TIMEOUT'] = '60'
    os.environ['DEBUG_MODE'] = 'true'
    config_mgr.reload()
    
    print(f"\n=== After Environment Override ===")
    print(f"HTTP Timeout: {config_mgr.get('http.timeout')}")
    print(f"Debug Mode: {config_mgr.is_feature_enabled('debug_mode')}")