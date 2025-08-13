"""APIベースクラス"""
import asyncio
from typing import Optional, Dict, Any
import aiohttp
import json
from datetime import datetime
import logging


logger = logging.getLogger(__name__)


class APIBase:
    """外部API通信の基底クラス"""
    
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """非同期コンテキストマネージャーのエントリー"""
        self._session = aiohttp.ClientSession(timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """非同期コンテキストマネージャーのイグジット"""
        if self._session:
            await self._session.close()
    
    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """GET リクエストを送信"""
        if not self._session:
            self._session = aiohttp.ClientSession(timeout=self.timeout)
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with self._session.get(url, params=params) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as e:
            logger.error(f"API request failed: {url}, error: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {url}, error: {e}")
            raise
    
    async def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """POST リクエストを送信"""
        if not self._session:
            self._session = aiohttp.ClientSession(timeout=self.timeout)
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with self._session.post(url, json=data) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as e:
            logger.error(f"API request failed: {url}, error: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {url}, error: {e}")
            raise
    
    def close(self):
        """セッションをクローズ"""
        if self._session:
            asyncio.create_task(self._session.close())