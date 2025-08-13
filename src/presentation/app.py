"""Streamlitアプリケーションのエントリーポイント"""
import streamlit as st
from streamlit_autorefresh import st_autorefresh
import asyncio
from pathlib import Path
import sys

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.presentation.pages import DashboardPage
from src.presentation.components import Header, AlertBanner
from src.infrastructure.persistence import FileSystemPersistence
from src.infrastructure.api import YamaguchiPrefectureAPI
from src.application.services import MonitoringService
from config.settings import Settings


# ページ設定
st.set_page_config(
    page_title="厚東川監視システム",
    page_icon="■",
    layout="wide",
    initial_sidebar_state="collapsed"
)


class KotogawaMonitorApp:
    """厚東川監視アプリケーション"""
    
    def __init__(self):
        self.settings = Settings()
        self.setup_dependencies()
    
    def setup_dependencies(self):
        """依存関係を設定"""
        # インフラストラクチャ層のセットアップ
        self.persistence = FileSystemPersistence(self.settings.data_dir)
        self.api_client = YamaguchiPrefectureAPI(self.settings.api_url)
        
        # リポジトリの実装をここで注入
        # TODO: 実際のリポジトリ実装を追加
        
        # サービス層のセットアップ
        # self.monitoring_service = MonitoringService(...)
    
    def run(self):
        """アプリケーションを実行"""
        # 自動更新設定
        count = st_autorefresh(
            interval=self.settings.refresh_interval * 1000,
            limit=None,
            key="kotogawa_refresh"
        )
        
        # ヘッダーコンポーネント
        header = Header()
        header.render()
        
        # アラートバナー
        alert_banner = AlertBanner()
        # TODO: 実際のアラートデータを渡す
        # alerts = asyncio.run(self.monitoring_service.get_alerts())
        # alert_banner.render(alerts)
        
        # メインダッシュボード
        dashboard = DashboardPage()
        dashboard.render()


def main():
    """メイン関数"""
    app = KotogawaMonitorApp()
    app.run()


if __name__ == "__main__":
    main()