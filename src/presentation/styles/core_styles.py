"""
厚東川監視システム - コアスタイル
基本的なCSS設定、リセット、レイアウト基盤
"""

def get_core_styles() -> str:
    """コアスタイルを取得"""
    return """
        /* リセットCSS */
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        /* Streamlitデフォルトマージン削除 */
        .main .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
            max-width: 100%;
        }
        
        /* コンテナ基本設定 */
        .stApp {
            background-color: #f8f9fa;
        }
        
        /* ヘッダー部分 */
        .header-container {
            background: linear-gradient(135deg, #1e3d59 0%, #2e5266 100%);
            color: white;
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        .header-title {
            font-size: 1.8rem;
            font-weight: bold;
            text-align: center;
            margin: 0;
        }
        
        /* サイドバー */
        .css-1d391kg {
            background-color: #f8f9fa;
        }
        
        /* メトリクス表示の基本スタイル */
        .metric-container {
            background: white;
            border-radius: 8px;
            padding: 1rem;
            margin: 0.5rem 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 4px solid #007bff;
        }
        
        /* テキスト基本設定 */
        .stMarkdown {
            line-height: 1.5;
        }
        
        /* ボタン基本設定 */
        .stButton > button {
            width: 100%;
            border-radius: 6px;
            border: 1px solid #ddd;
            transition: all 0.2s ease;
        }
        
        .stButton > button:hover {
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
    """