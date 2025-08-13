"""
レスポンシブスタイル定義 - 画面サイズ対応
"""


def get_responsive_styles() -> str:
    """
    レスポンシブデザイン用のスタイルを返す
    
    Returns:
        str: レスポンシブCSSスタイル
    """
    return """
        /* === サイドバー開閉時のレイアウト調整 === */
        [data-testid="stSidebar"][aria-expanded="true"] ~ .main .block-container {
            max-width: calc(100vw - 21rem);
        }
        
        /* === モバイル対応（768px以下） === */
        @media (max-width: 768px) {
            /* メインコンテナのパディング調整 */
            .main .block-container {
                padding-left: 0.5rem;
                padding-right: 0.5rem;
            }
            
            /* メトリクスのレイアウト */
            [data-testid="metric-container"] {
                padding: 0.75rem;
                margin-bottom: 0.5rem;
            }
            
            /* グラフの高さ調整 */
            .js-plotly-plot {
                height: 300px !important;
            }
            
            /* ボタンサイズ調整 */
            .stButton > button {
                padding: 0.5rem 1rem;
                font-size: 0.9rem;
            }
            
            /* サイドバー幅調整 */
            [data-testid="stSidebar"][aria-expanded="true"] {
                width: 18rem !important;
            }
            
            /* タイトルのフォントサイズ */
            h1 {
                font-size: 1.5rem !important;
            }
            
            h2 {
                font-size: 1.25rem !important;
            }
            
            h3 {
                font-size: 1.1rem !important;
            }
        }
        
        /* === タブレット対応（768px-1024px） === */
        @media (min-width: 769px) and (max-width: 1024px) {
            /* メインコンテナの最大幅 */
            .main .block-container {
                max-width: 95%;
            }
            
            /* グラフの高さ調整 */
            .js-plotly-plot {
                height: 400px !important;
            }
        }
        
        /* === デスクトップ対応（1024px以上） === */
        @media (min-width: 1025px) {
            /* メインコンテナの最大幅 */
            .main .block-container {
                max-width: 1200px;
                margin: 0 auto;
            }
            
            /* グラフの最適高さ */
            .js-plotly-plot {
                height: 500px !important;
            }
        }
        
        /* === ワイドスクリーン対応（1440px以上） === */
        @media (min-width: 1441px) {
            .main .block-container {
                max-width: 1400px;
            }
        }
        
        /* === プリント対応 === */
        @media print {
            /* 不要な要素を非表示 */
            [data-testid="stSidebar"],
            .stButton,
            iframe[title*="autorefresh"] {
                display: none !important;
            }
            
            /* メインコンテンツの最大化 */
            .main .block-container {
                max-width: 100% !important;
                padding: 0 !important;
            }
            
            /* グラフのサイズ調整 */
            .js-plotly-plot {
                height: auto !important;
                page-break-inside: avoid;
            }
        }
    """