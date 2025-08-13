"""
厚東川監視システム - コンポーネントスタイル
UI コンポーネント固有のスタイル設定
"""

def get_component_styles() -> str:
    """コンポーネントスタイルを取得"""
    return """
        /* メトリクス表示 */
        .metric-value {
            font-size: 2rem;
            font-weight: bold;
            color: #1e3d59;
        }
        
        .metric-label {
            font-size: 0.9rem;
            color: #666;
            margin-bottom: 0.25rem;
        }
        
        .metric-delta {
            font-size: 0.8rem;
            margin-top: 0.25rem;
        }
        
        /* ステータス表示 */
        .status-normal {
            color: #28a745;
            background-color: #d4edda;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-weight: bold;
        }
        
        .status-warning {
            color: #ffc107;
            background-color: #fff3cd;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-weight: bold;
        }
        
        .status-danger {
            color: #dc3545;
            background-color: #f8d7da;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-weight: bold;
        }
        
        /* アラートバナー */
        .alert-banner {
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 6px;
            padding: 1rem;
            margin: 1rem 0;
            color: #856404;
        }
        
        .alert-warning {
            background-color: #fff3cd;
            border-color: #ffeaa7;
            color: #856404;
        }
        
        .alert-danger {
            background-color: #f8d7da;
            border-color: #f5c6cb;
            color: #721c24;
        }
        
        /* グラフコンテナ */
        .graph-container {
            background: white;
            border-radius: 8px;
            padding: 1rem;
            margin: 1rem 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .graph-title {
            font-size: 1.1rem;
            font-weight: bold;
            margin-bottom: 0.5rem;
            color: #1e3d59;
        }
        
        /* Plotlyグラフの調整 */
        .js-plotly-plot {
            border-radius: 6px;
        }
        
        /* サイドバーコンテンツ */
        .sidebar-section {
            background: white;
            border-radius: 6px;
            padding: 1rem;
            margin: 0.5rem 0;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        
        .sidebar-title {
            font-weight: bold;
            color: #1e3d59;
            margin-bottom: 0.5rem;
        }
        
        /* データ表示テーブル */
        .data-table {
            background: white;
            border-radius: 6px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .stDataFrame {
            border: none;
        }
    """