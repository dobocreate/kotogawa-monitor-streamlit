"""
コンポーネント別スタイル定義 - UI要素ごとのスタイル
"""


def get_component_styles() -> str:
    """
    コンポーネント固有のスタイルを返す
    
    Returns:
        str: コンポーネントCSSスタイル
    """
    return """
        /* === メトリクスコンポーネント === */
        [data-testid="metric-container"] {
            width: 100%;
            min-width: 0;
            background-color: #f0f2f6;
            padding: 1rem;
            border-radius: 0.5rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.12);
        }
        
        /* === サイドバー === */
        section[data-testid="stSidebar"] > div {
            padding-top: 0rem;
        }
        
        /* === Plotlyグラフ === */
        .js-plotly-plot .plotly {
            width: 100% !important;
            height: auto !important;
        }
        
        /* Streamlitグラフコンテナ */
        .stPlotlyChart {
            width: 100% !important;
        }
        
        /* === データフレーム === */
        .dataframe {
            width: 100% !important;
            overflow-x: auto;
        }
        
        /* === ボタン === */
        .stButton > button {
            width: 100%;
            transition: all 0.3s ease;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }
        
        /* === エキスパンダー === */
        .streamlit-expanderHeader {
            font-weight: 600;
            background-color: rgba(240, 242, 246, 0.5);
            border-radius: 0.25rem;
        }
        
        /* === セレクトボックス === */
        .stSelectbox > div > div {
            background-color: #f0f2f6;
        }
        
        /* === 入力フィールド === */
        .stNumberInput > div > div > input,
        .stTextInput > div > div > input {
            background-color: #ffffff;
            border: 1px solid #ddd;
        }
        
        /* === チェックボックス === */
        .stCheckbox {
            padding: 0.5rem 0;
        }
        
        /* === マークダウン === */
        .stMarkdown {
            line-height: 1.6;
        }
        
        /* === キャプション === */
        .stCaption {
            color: #666;
            font-size: 0.85rem;
        }
    """