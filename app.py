#!/usr/bin/env python3
"""
厚東川監視システム - クリーンアーキテクチャ版
Streamlitアプリケーションのエントリーポイント
"""

import streamlit as st
from streamlit_autorefresh import st_autorefresh
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

from src.presentation.components import Header, AlertBanner, StatusBar
from src.presentation.pages import DashboardPage
from src.presentation.styles import get_all_styles
from src.config.app_settings import AppSettings
from src.application.services.history_service import HistoryService


# ページ設定
st.set_page_config(
    page_title="厚東川監視システム",
    page_icon="■",
    layout="wide",
    initial_sidebar_state="collapsed"
)


def initialize_css():
    """CSSスタイルを初期化（統合モジュールから読み込み）"""
    st.markdown(get_all_styles(), unsafe_allow_html=True)


def main():
    """メインアプリケーション"""
    
    # CSS初期化
    initialize_css()
    
    # 設定読み込み
    settings = AppSettings.load()
    
    # セッション状態から更新間隔を取得（サイドバーで設定される前のデフォルト値）
    # リソース制限対策：デフォルト間隔を60秒から300秒（5分）に変更
    refresh_interval = st.session_state.get('refresh_interval', 300)
    
    # 自動更新設定
    count = st_autorefresh(
        interval=refresh_interval * 1000 if refresh_interval > 0 else None,
        limit=None if refresh_interval > 0 else 0,
        key="kotogawa_refresh"
    )
    
    # セッション状態の初期化
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        st.session_state.demo_mode = False  # デフォルトは実データモード
    
    # ヘッダー表示
    header = Header(title="厚東川氾濫監視システムv2.0")
    header.render()
    
    # 状態表示バー
    status_bar = StatusBar()
    # デモ用の時刻データ
    from datetime import datetime
    current_time = datetime.now()
    # TODO: 実際のデータから状態を判定
    demo_status = '正常' if not st.session_state.get('show_demo_alert') else '警戒'
    status_bar.render(
        status=demo_status,
        last_update=current_time,
        api_fetch_time=current_time
    )
    
    # アラートバナー（アラートがある場合のみ表示）
    # TODO: 実際のアラートデータを取得して表示
    alert_banner = AlertBanner()
    demo_alerts = []  # デモ用：空のアラート
    if st.session_state.get('show_demo_alert'):
        demo_alerts = [
            {'level': 'warning', 'message': '河川水位が上昇傾向にあります（デモ）'}
        ]
    alert_banner.render(demo_alerts)
    
    # メインコンテンツ
    # デモモードの判定とサービスの注入
    if st.session_state.get('demo_mode', False):
        # デモモード：サービスなしで起動
        dashboard = DashboardPage()
    else:
        # 実データモード：履歴サービスを注入
        from pathlib import Path
        history_service = HistoryService(base_dir=Path.cwd())
        dashboard = DashboardPage(monitoring_service=history_service)
    
    dashboard.render()
    
    # サイドバー設定（元のstreamlit_app.pyから完全復元）
    # 更新設定
    with st.sidebar.expander("更新設定", expanded=True):
        # 自動更新設定
        refresh_interval = st.selectbox(
            "自動更新間隔",
            options=[
                ("自動更新なし", 0),
                ("30秒", 30),
                ("1分", 60),
                ("2分", 120),
                ("5分", 300)
            ],
            index=4,  # デフォルトは5分（リソース制限対策）
            format_func=lambda x: x[0]
        )
        # セッション状態に保存（次回の自動更新で使用）
        st.session_state.refresh_interval = refresh_interval[1]
        
        # 手動更新ボタン
        if st.button("手動更新", type="primary", key="sidebar_refresh"):
            st.cache_data.clear()
            st.rerun()
    
    # 表示設定
    with st.sidebar.expander("表示設定", expanded=False):
        # 表示期間設定
        st.session_state.display_hours = st.selectbox(
            "表示期間",
            [24, 48, 72, 168],
            index=0,
            format_func=lambda x: f"{x}時間" if x < 168 else "1週間"
        )
        
        # グラフ操作設定
        st.session_state.enable_graph_interaction = st.checkbox(
            "グラフ操作を有効化",
            value=False,
            help="チェックを入れるとグラフの拡大・縮小・移動が可能になります"
        )
        
        # デモモード設定
        demo_mode = st.checkbox(
            "デモモード",
            value=st.session_state.get('demo_mode', False),
            help="実際のデータではなくデモデータを使用"
        )
        
        # デモモードが変更された場合はページを再描画
        if demo_mode != st.session_state.get('demo_mode', False):
            st.session_state.demo_mode = demo_mode
            st.rerun()
    
    # アラート設定
    with st.sidebar.expander("アラート設定", expanded=False):
        st.session_state.river_warning = st.number_input(
            "河川警戒水位 (m)", 
            value=3.8, 
            step=0.1
        )
        st.session_state.river_danger = st.number_input(
            "河川危険水位 (m)", 
            value=5.0, 
            step=0.1
        )
        st.session_state.dam_warning = st.number_input(
            "ダム警戒水位 (m)", 
            value=39.2, 
            step=0.1, 
            help="洪水時最高水位"
        )
        st.session_state.dam_danger = st.number_input(
            "ダム危険水位 (m)", 
            value=40.0, 
            step=0.1, 
            help="設計最高水位"
        )
    
    # システム情報
    with st.sidebar.expander("システム情報", expanded=True):
        # 観測状況
        with st.expander("■ 観測状況", expanded=True):
            # 実データモードの場合は実際のデータから情報を取得
            if not st.session_state.get('demo_mode', False):
                try:
                    from pathlib import Path
                    history_service = HistoryService(base_dir=Path.cwd())
                    latest_data = history_service.get_current_data()
                    
                    if latest_data:
                        from datetime import datetime
                        obs_time = latest_data.get('timestamp', datetime.now())
                        if isinstance(obs_time, datetime):
                            time_diff = datetime.now() - obs_time
                            minutes_ago = int(time_diff.total_seconds() / 60)
                            st.success(f"観測時刻：{minutes_ago}分前")
                        else:
                            st.success("観測時刻：取得中")
                        
                        # データ件数（表示期間内のデータ数）
                        display_hours = st.session_state.get('display_hours', 24)
                        history_data = history_service.get_historical_data(display_hours)
                        if history_data and 'times' in history_data:
                            st.info(f"データ件数：{len(history_data['times'])} 件")
                        else:
                            st.info("データ件数：-- 件")
                    else:
                        st.warning("データ取得中...")
                        st.info("データ件数：-- 件")
                except:
                    st.success("観測時刻：--分前")
                    st.info("データ件数：-- 件")
            else:
                # デモモード
                st.success("観測時刻：10分前（デモ）")
                st.info("データ件数：24 件（デモ）")
            
            st.caption(f"自動更新回数: {count}")
        
        # 警戒レベル説明
        with st.expander("■ 警戒レベル説明", expanded=False):
            st.write("""
            **河川水位基準**
            - 正常: 3.80m未満
            - 水防団待機: 3.80m以上
            - 氾濫注意: 5.00m以上
            - 避難判断: 5.10m以上
            - 氾濫危険: 5.50m以上
            
            **ダム水位基準**
            - 警戒: 39.2m以上（洪水時最高水位）
            - 危険: 40.0m以上（設計最高水位）
            
            **雨量基準**
            - 注意: 10mm/h以上
            - 警戒: 30mm/h以上
            - 危険: 50mm/h以上
            """)
        
        # データソース情報
        with st.expander("■ データソース", expanded=False):
            st.write("""
            **厚東川ダム**
            
            ・ 更新間隔：10分
            
            **厚東川**
            
            ・ 更新間隔：10分
            
            データ提供: 山口県土木防災情報システム
            """)
    
    # フッター
    st.sidebar.markdown("---")
    st.sidebar.caption("厚東川氾濫監視システム v2.0")
    st.sidebar.caption("※ 本システムは山口県公開データを再加工した参考情報です。防災判断は必ず公式発表をご確認ください。")
    st.sidebar.caption("※ 本システムの利用または利用不能により生じた直接・間接の損害について、一切責任を負いません。")
    st.sidebar.caption("Powered by Streamlit")


if __name__ == "__main__":
    main()