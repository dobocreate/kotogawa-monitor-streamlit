"""
厚東川監視システム 設定ファイル
Configuration settings for Kotogawa Monitoring System
"""

from pathlib import Path
from typing import Dict, Any

# Base configuration
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
HISTORY_DIR = DATA_DIR / "history"

# API Endpoints
API_ENDPOINTS = {
    'dam': "https://y-bousai.pref.yamaguchi.lg.jp/citizen/dam/kdm_table.aspx",
    'river': "https://y-bousai.pref.yamaguchi.lg.jp/citizen/water/kwl_table.aspx",
    'weather': "https://www.jma.go.jp/bosai/forecast/data/forecast/350000.json",
    'yahoo_weather': "https://map.yahooapis.jp/weather/V1/place"
}

# Station codes
STATION_CODES = {
    'dam': '015',  # 厚東川ダムの観測所コード
    'river': '05067',  # 厚東川（持世寺）の観測所コード
    'weather_area': '350010',  # 山口県西部
    'weather_prefecture': '350000'  # 山口県
}

# Request settings
REQUEST_CONFIG = {
    'timeout': 30,
    'max_retries': 5,
    'retry_delay': 3,
    'headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
}

# Yahoo Weather API
YAHOO_WEATHER_CONFIG = {
    'app_id': "dj00aiZpPW5YTFVqSXc0S2dCcSZzPWNvbnN1bWVyc2VjcmV0Jng9MDA-",
    'coordinates': "131.289496,34.079891",  # 経度,緯度
    'interval': '10'
}

# Data validation ranges
VALIDATION_RANGES = {
    'dam': {
        'water_level': (30, 40),  # meters
        'storage_rate': (0, 100),  # percentage
        'inflow': (0, 1500),  # m³/s
        'outflow': (0, 1500)  # m³/s
    },
    'river': {
        'water_level': (0.5, 10),  # meters
        'level_change': (-5, 5)  # meters
    },
    'rainfall': {
        'hourly': (0, 200),  # mm
        'cumulative': (0, 1000)  # mm
    },
    'temperature': {
        'min': (-10, 45),  # celsius
        'max': (-10, 45)  # celsius
    }
}

# River warning thresholds
RIVER_THRESHOLDS = {
    'preparedness': 3.80,  # 水防団待機水位
    'caution': 5.00,      # 氾濫注意水位
    'evacuation': 5.10,   # 避難判断水位
    'danger': 5.50        # 氾濫危険水位
}

# Data retention settings
DATA_RETENTION = {
    'days_to_keep': 7
}

# Backfill settings
BACKFILL_CONFIG = {
    'default_hours': 24,
    'default_max_items': 20
}

# Weather code mapping
WEATHER_CODE_MAP = {
    '100': '晴れ', '101': '晴れ時々くもり', '102': '晴れ一時雨',
    '110': '晴れ時々くもり一時雨', '111': '晴れ時々くもり一時雪',
    '112': '晴れ一時雨', '113': '晴れ時々雨', '114': '晴れ一時雪',
    '200': 'くもり', '201': 'くもり時々晴れ', '202': 'くもり一時雨',
    '203': 'くもり時々雨', '204': 'くもり一時雪', '210': 'くもり時々晴れ一時雨',
    '211': 'くもり時々晴れ一時雪', '212': 'くもり一時雨か雪', '213': 'くもり一時雨か雷雨',
    '300': '雨', '301': '雨時々晴れ', '302': '雨時々くもり',
    '303': '雨時々雪', '308': '大雨', '311': '雨のち晴れ',
    '313': '雨のちくもり', '314': '雨のち雪',
    '400': '雪', '401': '雪時々晴れ', '402': '雪時々くもり',
    '403': '雪時々雨', '406': '大雪', '411': '雪のち晴れ',
    '413': '雪のちくもり', '414': '雪のち雨'
}

# Logging configuration
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'date_format': '%Y-%m-%d %H:%M:%S'
}

def get_config() -> Dict[str, Any]:
    """Get all configuration as dictionary"""
    return {
        'base_dir': str(BASE_DIR),
        'data_dir': str(DATA_DIR),
        'history_dir': str(HISTORY_DIR),
        'api_endpoints': API_ENDPOINTS,
        'station_codes': STATION_CODES,
        'request_config': REQUEST_CONFIG,
        'yahoo_weather_config': YAHOO_WEATHER_CONFIG,
        'validation_ranges': VALIDATION_RANGES,
        'river_thresholds': RIVER_THRESHOLDS,
        'data_retention': DATA_RETENTION,
        'backfill_config': BACKFILL_CONFIG,
        'weather_code_map': WEATHER_CODE_MAP,
        'logging_config': LOGGING_CONFIG
    }