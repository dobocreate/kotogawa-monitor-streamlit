"""
コアスタイル定義 - 基本的なレイアウトとリセット
"""


def get_core_styles() -> str:
    """
    アプリケーション全体のコアスタイルを返す
    
    Returns:
        str: コアCSSスタイル
    """
    return """
        /* === メインコンテナのレイアウト === */
        .main .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
            padding-top: 0rem !important;
            margin-top: 0rem !important;
            max-width: 100%;
        }
        
        /* === Streamlitデフォルトマージンのリセット === */
        .main .block-container > div:first-child {
            margin-top: 0 !important;
            padding-top: 0 !important;
        }
        
        /* デフォルトヘッダーの非表示 */
        .stApp > header {
            display: none !important;
        }
        
        /* メインコンテナの上部スペース除去 */
        .main {
            padding-top: 0 !important;
        }
        
        /* 垂直ブロックの上部マージン除去 */
        [data-testid="stVerticalBlock"] > div:first-child {
            margin-top: 0 !important;
            padding-top: 0 !important;
        }
        
        /* アプリ全体の上部スペース除去 */
        .stApp {
            padding-top: 0 !important;
            margin-top: 0 !important;
        }
        
        /* 最初の要素の上部マージン完全除去 */
        .main .block-container > div > div:first-child {
            margin-top: 0 !important;
            padding-top: 0 !important;
        }
        
        /* === 自動更新コンポーネントの非表示 === */
        iframe[title="st_autorefresh.autorefresh"] {
            display: none !important;
            height: 0 !important;
            width: 0 !important;
        }
        
        /* 自動更新コンテナの非表示 */
        [data-testid="stIFrame"]:has(iframe[title*="autorefresh"]) {
            display: none !important;
            height: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
        }
        
        /* === タイトル・ヘッダーのスタイル === */
        .main .block-container h1,
        .main h1,
        h1[data-testid="stMarkdown"] {
            text-align: center !important;
            color: #1f77b4;
            margin-bottom: 1rem;
        }
        
        /* === アラートのスタイル === */
        .stAlert {
            margin-bottom: 1rem;
        }
    """