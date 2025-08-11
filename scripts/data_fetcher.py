#!/usr/bin/env python3
"""
データ取得専用モジュール
HTTPリクエスト処理とエラーハンドリングを担当
"""

import time
import logging
from typing import Optional, Dict, Any
import requests
from bs4 import BeautifulSoup

from config_manager import config

logger = logging.getLogger(__name__)


class DataFetcher:
    """データ取得クラス"""
    
    def __init__(self):
        """初期化"""
        self.timeout = config.get('http.timeout', 30)
        self.max_retries = config.get('http.max_retries', 5)
        self.retry_delay = config.get('http.retry_delay', 3)
        self.headers = {
            'User-Agent': config.get('http.user_agent')
        }
        
        # リトライ戦略の設定
        self.retry_strategy = self._get_retry_strategy()
        
    def _get_retry_strategy(self) -> Dict[str, Any]:
        """リトライ戦略を取得"""
        return {
            'max_retries': self.max_retries,
            'backoff_factor': 1.5,  # 指数バックオフの係数
            'max_delay': 30,  # 最大待機時間（秒）
            'jitter': True,  # ジッター（ランダム性）を追加
        }
    
    def fetch_page(self, url: str, params: Dict[str, str]) -> Optional[BeautifulSoup]:
        """
        指定されたURLからHTMLを取得し、BeautifulSoupオブジェクトを返す
        
        Args:
            url: 取得先URL
            params: クエリパラメータ
            
        Returns:
            BeautifulSoup: パース済みHTML
            None: エラー時
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                # デバッグモードの場合、詳細ログを出力
                if config.is_feature_enabled('debug_mode'):
                    logger.debug(f"Fetching URL: {url} with params: {params}")
                
                # リクエスト実行
                response = requests.get(
                    url,
                    params=params,
                    headers=self.headers,
                    timeout=self.timeout
                )
                
                # HTTPステータスチェック
                response.raise_for_status()
                
                # レスポンスサイズチェック
                content_length = len(response.content)
                if content_length < 100:
                    raise requests.RequestException(
                        f"Response too small: {content_length} bytes"
                    )
                
                # 成功時のログ
                logger.info(f"Successfully fetched {url} (attempt {attempt + 1}/{self.max_retries})")
                
                return BeautifulSoup(response.content, 'html.parser')
                
            except requests.Timeout as e:
                last_error = e
                logger.warning(f"Timeout on attempt {attempt + 1}/{self.max_retries}: {e}")
                wait_time = self._calculate_wait_time(attempt)
                
            except requests.ConnectionError as e:
                last_error = e
                logger.warning(f"Connection error on attempt {attempt + 1}/{self.max_retries}: {e}")
                wait_time = self._calculate_wait_time(attempt)
                
            except requests.HTTPError as e:
                last_error = e
                logger.warning(f"HTTP error on attempt {attempt + 1}/{self.max_retries}: {e}")
                
                # 特定のHTTPエラーはリトライしない
                if response.status_code in [400, 401, 403, 404]:
                    logger.error(f"Non-retryable HTTP error {response.status_code}")
                    return None
                    
                wait_time = self._calculate_wait_time(attempt)
                
            except requests.RequestException as e:
                last_error = e
                logger.warning(f"Request error on attempt {attempt + 1}/{self.max_retries}: {e}")
                wait_time = self._calculate_wait_time(attempt)
                
            except Exception as e:
                last_error = e
                logger.error(f"Unexpected error on attempt {attempt + 1}: {type(e).__name__}: {e}")
                wait_time = self._calculate_wait_time(attempt)
            
            # リトライ前の待機
            if attempt < self.max_retries - 1:
                logger.info(f"Waiting {wait_time:.1f} seconds before retry...")
                time.sleep(wait_time)
            else:
                logger.error(f"Failed to fetch {url} after {self.max_retries} attempts. Last error: {last_error}")
                
        return None
    
    def _calculate_wait_time(self, attempt: int) -> float:
        """
        リトライ待機時間を計算（指数バックオフ + ジッター）
        
        Args:
            attempt: 試行回数（0から開始）
            
        Returns:
            float: 待機時間（秒）
        """
        strategy = self.retry_strategy
        
        # 基本的な指数バックオフ
        base_delay = self.retry_delay * (strategy['backoff_factor'] ** attempt)
        
        # 最大遅延時間でキャップ
        base_delay = min(base_delay, strategy['max_delay'])
        
        # ジッターを追加（±20%のランダム性）
        if strategy['jitter']:
            import random
            jitter = base_delay * 0.2 * (2 * random.random() - 1)
            base_delay += jitter
        
        return max(base_delay, 1.0)  # 最小1秒
    
    def fetch_with_circuit_breaker(self, url: str, params: Dict[str, str]) -> Optional[BeautifulSoup]:
        """
        サーキットブレーカーパターンでフェッチ
        （将来の機能拡張用）
        
        Args:
            url: 取得先URL
            params: クエリパラメータ
            
        Returns:
            BeautifulSoup: パース済みHTML
            None: エラー時
        """
        if not config.is_feature_enabled('use_circuit_breaker'):
            return self.fetch_page(url, params)
        
        # サーキットブレーカーの実装（将来的に追加）
        # 現在は通常のフェッチにフォールバック
        return self.fetch_page(url, params)
    
    def check_connectivity(self, url: str) -> bool:
        """
        接続性をチェック（HEADリクエストを使用）
        
        Args:
            url: チェック対象URL
            
        Returns:
            bool: 接続可能な場合True
        """
        try:
            response = requests.head(url, headers=self.headers, timeout=5)
            return response.status_code < 500
        except requests.RequestException as e:
            logger.warning(f"Connectivity check failed for {url}: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        フェッチ統計を取得
        
        Returns:
            Dict: 統計情報
        """
        # 将来的に統計情報を追跡する場合に使用
        return {
            'timeout': self.timeout,
            'max_retries': self.max_retries,
            'retry_delay': self.retry_delay,
            'retry_strategy': self.retry_strategy
        }


if __name__ == "__main__":
    # テスト実行
    import logging
    logging.basicConfig(level=logging.DEBUG)
    
    fetcher = DataFetcher()
    
    # 接続性チェック
    dam_url = config.get('data_sources.dam.url')
    print(f"Checking connectivity to {dam_url}...")
    is_connected = fetcher.check_connectivity(dam_url)
    print(f"Connected: {is_connected}")
    
    # テストフェッチ
    if is_connected:
        from datetime import datetime
        try:
            from zoneinfo import ZoneInfo
        except ImportError:
            import pytz
            ZoneInfo = lambda x: pytz.timezone(x)
        
        jst = ZoneInfo('Asia/Tokyo')
        current_time = datetime.now(jst)
        obsdt = current_time.strftime('%Y%m%d%H%M')
        
        params = {
            'check': config.get('data_sources.dam.station_code'),
            'obsdt': obsdt,
            'pop': '1'
        }
        
        print(f"\nFetching dam data for {obsdt}...")
        soup = fetcher.fetch_page(dam_url, params)
        
        if soup:
            print(f"Success! HTML length: {len(str(soup))} characters")
            tables = soup.find_all('table')
            print(f"Found {len(tables)} tables")
        else:
            print("Failed to fetch data")
    
    # 統計情報
    print(f"\nFetcher stats:")
    import json
    print(json.dumps(fetcher.get_stats(), indent=2))