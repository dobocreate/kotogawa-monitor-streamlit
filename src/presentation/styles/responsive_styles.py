"""
厚東川監視システム - レスポンシブスタイル
異なる画面サイズに対応するメディアクエリとレスポンシブデザイン
"""

def get_responsive_styles() -> str:
    """レスポンシブスタイルを取得"""
    return """
        /* モバイル対応（768px以下） */
        @media screen and (max-width: 768px) {
            .main .block-container {
                padding: 0.5rem;
            }
            
            .header-title {
                font-size: 1.4rem;
            }
            
            .metric-container {
                padding: 0.75rem;
                margin: 0.25rem 0;
            }
            
            .metric-value {
                font-size: 1.5rem;
            }
            
            .graph-container {
                padding: 0.75rem;
                margin: 0.5rem 0;
            }
            
            /* サイドバーを自動で閉じる */
            .css-1d391kg {
                width: 0 !important;
            }
            
            /* モバイルでのグラフサイズ調整 */
            .js-plotly-plot {
                width: 100% !important;
                height: 300px !important;
            }
        }
        
        /* タブレット対応（769px-1024px） */
        @media screen and (min-width: 769px) and (max-width: 1024px) {
            .main .block-container {
                padding: 0.75rem;
            }
            
            .metric-container {
                padding: 0.875rem;
            }
            
            .graph-container {
                padding: 0.875rem;
            }
        }
        
        /* デスクトップ対応（1025px以上） */
        @media screen and (min-width: 1025px) {
            .main .block-container {
                max-width: 1200px;
                margin: 0 auto;
            }
            
            .metric-container {
                padding: 1rem;
            }
            
            .graph-container {
                padding: 1rem;
            }
        }
        
        /* 大画面対応（1440px以上） */
        @media screen and (min-width: 1440px) {
            .main .block-container {
                max-width: 1400px;
            }
            
            .header-title {
                font-size: 2rem;
            }
            
            .metric-value {
                font-size: 2.25rem;
            }
        }
        
        /* 印刷対応 */
        @media print {
            .stSidebar,
            .stButton,
            .stSelectbox,
            .stNumberInput {
                display: none !important;
            }
            
            .main .block-container {
                max-width: 100%;
                padding: 0;
            }
            
            .graph-container,
            .metric-container {
                break-inside: avoid;
                page-break-inside: avoid;
            }
            
            .header-container {
                background: #1e3d59 !important;
                color: white !important;
            }
        }
        
        /* ダークモード対応 */
        @media (prefers-color-scheme: dark) {
            .stApp {
                background-color: #1a1a1a;
            }
            
            .metric-container,
            .graph-container,
            .data-table {
                background: #2d2d2d;
                color: #ffffff;
            }
            
            .sidebar-section {
                background: #2d2d2d;
                color: #ffffff;
            }
        }
        
        /* 高コントラストモード */
        @media (prefers-contrast: high) {
            .metric-container,
            .graph-container {
                border: 2px solid #000;
            }
            
            .stButton > button {
                border: 2px solid #000;
                background-color: #fff;
                color: #000;
            }
            
            .status-normal {
                border: 2px solid #000;
            }
            
            .status-warning {
                border: 2px solid #000;
            }
            
            .status-danger {
                border: 2px solid #000;
            }
        }
        
        /* 縮小モーション設定（アクセシビリティ対応） */
        @media (prefers-reduced-motion: reduce) {
            * {
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
            }
        }
    """