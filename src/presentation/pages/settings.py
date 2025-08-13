"""設定ページ"""
import streamlit as st
from typing import Dict, Any, Optional
import json
from pathlib import Path


class SettingsPage:
    """設定管理ページ"""
    
    def __init__(self, config_service=None):
        """
        Args:
            config_service: 設定サービス
        """
        self.config_service = config_service
        self.config_file = Path("config/app_config.json")
    
    def render(self):
        """ページを描画"""
        st.header("⚙️ 設定")
        
        # タブ作成
        tab1, tab2, tab3, tab4 = st.tabs(
            ["表示設定", "アラート設定", "データ取得設定", "システム設定"]
        )
        
        with tab1:
            self._render_display_settings()
        
        with tab2:
            self._render_alert_settings()
        
        with tab3:
            self._render_data_settings()
        
        with tab4:
            self._render_system_settings()
    
    def _render_display_settings(self):
        """表示設定"""
        st.subheader("📊 表示設定")
        
        # 現在の設定を取得
        current_config = self._load_config()
        display_config = current_config.get('display', {})
        
        # 自動更新設定
        st.markdown("#### 自動更新")
        auto_refresh = st.checkbox(
            "自動更新を有効にする",
            value=display_config.get('auto_refresh', True)
        )
        
        if auto_refresh:
            refresh_interval = st.slider(
                "更新間隔（秒）",
                min_value=10,
                max_value=600,
                value=display_config.get('refresh_interval', 60),
                step=10
            )
        else:
            refresh_interval = display_config.get('refresh_interval', 60)
        
        # グラフ設定
        st.markdown("#### グラフ表示")
        show_markers = st.checkbox(
            "データポイントにマーカーを表示",
            value=display_config.get('show_markers', True)
        )
        
        chart_height = st.slider(
            "グラフの高さ（ピクセル）",
            min_value=300,
            max_value=800,
            value=display_config.get('chart_height', 400),
            step=50
        )
        
        # データ表示期間
        st.markdown("#### データ表示期間")
        default_period = st.selectbox(
            "デフォルトの表示期間",
            options=["6時間", "12時間", "24時間", "48時間", "7日間"],
            index=["6時間", "12時間", "24時間", "48時間", "7日間"].index(
                display_config.get('default_period', '24時間')
            )
        )
        
        # 保存ボタン
        if st.button("表示設定を保存", type="primary"):
            new_config = current_config.copy()
            new_config['display'] = {
                'auto_refresh': auto_refresh,
                'refresh_interval': refresh_interval,
                'show_markers': show_markers,
                'chart_height': chart_height,
                'default_period': default_period
            }
            self._save_config(new_config)
            st.success("表示設定を保存しました")
    
    def _render_alert_settings(self):
        """アラート設定"""
        st.subheader("🚨 アラート設定")
        
        # 現在の設定を取得
        current_config = self._load_config()
        alert_config = current_config.get('alerts', {})
        
        # 河川水位アラート
        st.markdown("#### 河川水位アラート閾値")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            warning_level = st.number_input(
                "注意水位 (m)",
                min_value=0.0,
                max_value=10.0,
                value=alert_config.get('water_level', {}).get('warning', 3.0),
                step=0.1,
                format="%.1f"
            )
        
        with col2:
            danger_level = st.number_input(
                "警戒水位 (m)",
                min_value=0.0,
                max_value=10.0,
                value=alert_config.get('water_level', {}).get('danger', 4.0),
                step=0.1,
                format="%.1f"
            )
        
        with col3:
            critical_level = st.number_input(
                "危険水位 (m)",
                min_value=0.0,
                max_value=10.0,
                value=alert_config.get('water_level', {}).get('critical', 5.0),
                step=0.1,
                format="%.1f"
            )
        
        # ダム貯水率アラート
        st.markdown("#### ダム貯水率アラート閾値")
        
        col1, col2 = st.columns(2)
        
        with col1:
            low_storage = st.number_input(
                "低貯水率警告 (%)",
                min_value=0,
                max_value=100,
                value=alert_config.get('dam_storage', {}).get('low', 30),
                step=5
            )
        
        with col2:
            high_storage = st.number_input(
                "高貯水率警告 (%)",
                min_value=0,
                max_value=100,
                value=alert_config.get('dam_storage', {}).get('high', 90),
                step=5
            )
        
        # 通知設定
        st.markdown("#### 通知設定")
        
        enable_notifications = st.checkbox(
            "アラート通知を有効にする",
            value=alert_config.get('enable_notifications', True)
        )
        
        if enable_notifications:
            notification_methods = st.multiselect(
                "通知方法",
                options=["画面表示", "音声", "メール", "LINE"],
                default=alert_config.get('notification_methods', ["画面表示"])
            )
        else:
            notification_methods = []
        
        # 保存ボタン
        if st.button("アラート設定を保存", type="primary"):
            new_config = current_config.copy()
            new_config['alerts'] = {
                'water_level': {
                    'warning': warning_level,
                    'danger': danger_level,
                    'critical': critical_level
                },
                'dam_storage': {
                    'low': low_storage,
                    'high': high_storage
                },
                'enable_notifications': enable_notifications,
                'notification_methods': notification_methods
            }
            self._save_config(new_config)
            st.success("アラート設定を保存しました")
    
    def _render_data_settings(self):
        """データ取得設定"""
        st.subheader("📡 データ取得設定")
        
        # 現在の設定を取得
        current_config = self._load_config()
        data_config = current_config.get('data', {})
        
        # データソース設定
        st.markdown("#### データソース")
        
        data_source = st.selectbox(
            "データ取得元",
            options=["山口県河川防災情報", "デモデータ", "カスタムAPI"],
            index=["山口県河川防災情報", "デモデータ", "カスタムAPI"].index(
                data_config.get('source', '山口県河川防災情報')
            )
        )
        
        if data_source == "カスタムAPI":
            api_url = st.text_input(
                "API URL",
                value=data_config.get('api_url', '')
            )
            api_key = st.text_input(
                "API キー",
                value=data_config.get('api_key', ''),
                type="password"
            )
        else:
            api_url = ""
            api_key = ""
        
        # データ取得間隔
        st.markdown("#### データ取得間隔")
        
        fetch_interval = st.slider(
            "取得間隔（分）",
            min_value=1,
            max_value=60,
            value=data_config.get('fetch_interval', 10),
            step=1
        )
        
        # データ保持期間
        st.markdown("#### データ保持期間")
        
        retention_days = st.number_input(
            "データ保持日数",
            min_value=1,
            max_value=365,
            value=data_config.get('retention_days', 30),
            step=1
        )
        
        # 保存ボタン
        if st.button("データ取得設定を保存", type="primary"):
            new_config = current_config.copy()
            new_config['data'] = {
                'source': data_source,
                'api_url': api_url,
                'api_key': api_key,
                'fetch_interval': fetch_interval,
                'retention_days': retention_days
            }
            self._save_config(new_config)
            st.success("データ取得設定を保存しました")
    
    def _render_system_settings(self):
        """システム設定"""
        st.subheader("🖥️ システム設定")
        
        # 現在の設定を取得
        current_config = self._load_config()
        system_config = current_config.get('system', {})
        
        # ログ設定
        st.markdown("#### ログ設定")
        
        log_level = st.selectbox(
            "ログレベル",
            options=["DEBUG", "INFO", "WARNING", "ERROR"],
            index=["DEBUG", "INFO", "WARNING", "ERROR"].index(
                system_config.get('log_level', 'INFO')
            )
        )
        
        enable_file_logging = st.checkbox(
            "ファイルへのログ出力を有効にする",
            value=system_config.get('enable_file_logging', True)
        )
        
        if enable_file_logging:
            log_retention_days = st.number_input(
                "ログ保持日数",
                min_value=1,
                max_value=90,
                value=system_config.get('log_retention_days', 7),
                step=1
            )
        else:
            log_retention_days = 7
        
        # キャッシュ設定
        st.markdown("#### キャッシュ設定")
        
        enable_cache = st.checkbox(
            "データキャッシュを有効にする",
            value=system_config.get('enable_cache', True)
        )
        
        if enable_cache:
            cache_ttl = st.slider(
                "キャッシュ有効期限（秒）",
                min_value=10,
                max_value=3600,
                value=system_config.get('cache_ttl', 300),
                step=10
            )
        else:
            cache_ttl = 300
        
        # デバッグモード
        st.markdown("#### デバッグ")
        
        debug_mode = st.checkbox(
            "デバッグモードを有効にする",
            value=system_config.get('debug_mode', False)
        )
        
        # 保存ボタン
        if st.button("システム設定を保存", type="primary"):
            new_config = current_config.copy()
            new_config['system'] = {
                'log_level': log_level,
                'enable_file_logging': enable_file_logging,
                'log_retention_days': log_retention_days,
                'enable_cache': enable_cache,
                'cache_ttl': cache_ttl,
                'debug_mode': debug_mode
            }
            self._save_config(new_config)
            st.success("システム設定を保存しました")
        
        # 設定のエクスポート/インポート
        st.markdown("---")
        st.markdown("#### 設定のバックアップ")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("設定をエクスポート"):
                config_json = json.dumps(current_config, indent=2, ensure_ascii=False)
                st.download_button(
                    label="設定ファイルをダウンロード",
                    data=config_json,
                    file_name="kotogawa_config.json",
                    mime="application/json"
                )
        
        with col2:
            uploaded_file = st.file_uploader(
                "設定ファイルをインポート",
                type=['json']
            )
            if uploaded_file is not None:
                try:
                    imported_config = json.loads(uploaded_file.read())
                    self._save_config(imported_config)
                    st.success("設定をインポートしました")
                    st.rerun()
                except Exception as e:
                    st.error(f"設定のインポートに失敗しました: {e}")
    
    def _load_config(self) -> Dict[str, Any]:
        """設定を読み込み"""
        if self.config_service:
            return self.config_service.get_all()
        
        # ファイルから読み込み
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        
        # デフォルト設定
        return {
            'display': {
                'auto_refresh': True,
                'refresh_interval': 60,
                'show_markers': True,
                'chart_height': 400,
                'default_period': '24時間'
            },
            'alerts': {
                'water_level': {
                    'warning': 3.0,
                    'danger': 4.0,
                    'critical': 5.0
                },
                'dam_storage': {
                    'low': 30,
                    'high': 90
                },
                'enable_notifications': True,
                'notification_methods': ['画面表示']
            },
            'data': {
                'source': '山口県河川防災情報',
                'fetch_interval': 10,
                'retention_days': 30
            },
            'system': {
                'log_level': 'INFO',
                'enable_file_logging': True,
                'log_retention_days': 7,
                'enable_cache': True,
                'cache_ttl': 300,
                'debug_mode': False
            }
        }
    
    def _save_config(self, config: Dict[str, Any]):
        """設定を保存"""
        if self.config_service:
            self.config_service.save_all(config)
        else:
            # ファイルに保存
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)