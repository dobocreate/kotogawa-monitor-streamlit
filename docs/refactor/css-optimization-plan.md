# CSS最適化実施計画

## 目的
Kotogawa監視アプリケーションのCSS実装を最適化し、パフォーマンス向上と保守性改善を実現する

## 現状の問題点
1. 3つのPythonファイルで同じCSSが重複定義されている
2. 2つのメインファイル（app.py、streamlit_app.py）が並存している
3. インラインCSSによりキャッシュが効かない
4. スタイル変更時に複数箇所の修正が必要

## 実施内容

### フェーズ1: 即時対応（2時間）

#### 1.1 重複ファイルの整理
- [ ] `streamlit_app.py`のバックアップ作成
- [ ] `app.py`を主要ファイルとして確定
- [ ] エントリーポイントの統一

#### 1.2 CSS統合モジュールの作成
```python
# src/presentation/styles/core_styles.py
def get_core_styles() -> str:
    """コアスタイルを返す"""
    return """<style>
    /* 基本レイアウト */
    .main .block-container {
        padding: 0 1rem;
        margin-top: 0 !important;
        max-width: 100%;
    }
    
    /* Streamlitデフォルトの上部マージン除去 */
    .stApp > header { display: none !important; }
    .main { padding-top: 0 !important; }
    
    /* 自動更新コンポーネント非表示 */
    iframe[title*="autorefresh"] { display: none !important; }
    </style>"""
```

### フェーズ2: スタイル整理（3時間）

#### 2.1 コンポーネント別スタイル分離
```
src/presentation/styles/
├── __init__.py          # スタイル統合
├── core_styles.py       # 基本レイアウト
├── components.py        # コンポーネント用
├── responsive.py        # レスポンシブ対応
└── theme.py            # テーマ定義
```

#### 2.2 重複除去チェックリスト
- [ ] 上部マージン除去の統一
- [ ] サイドバー幅調整の統一
- [ ] Plotlyグラフスタイルの統一
- [ ] メトリクスカードスタイルの統一

### フェーズ3: 最適化（4時間）

#### 3.1 パフォーマンス改善
- [ ] Critical CSSの分離
- [ ] 不要なスタイルの削除
- [ ] CSS minification（可能な範囲で）

#### 3.2 保守性向上
- [ ] CSS変数の導入
- [ ] BEMネーミング規約の採用
- [ ] コメントとドキュメント追加

## 実装手順

### ステップ1: バックアップとテスト環境準備
```bash
# バックアップ作成
cp streamlit_app.py streamlit_app.py.backup
cp app.py app.py.backup

# テスト実行
python -m streamlit run app.py
```

### ステップ2: スタイルモジュール作成
```bash
# ディレクトリ作成
mkdir -p src/presentation/styles

# モジュール作成
touch src/presentation/styles/__init__.py
touch src/presentation/styles/core_styles.py
touch src/presentation/styles/components.py
```

### ステップ3: 既存コードからCSS抽出
1. `app.py`の`initialize_css()`から抽出
2. `header.py`の`_get_custom_css()`から抽出
3. `metrics_card.py`のインラインスタイルから抽出

### ステップ4: 統合とテスト
```python
# app.pyの変更
from src.presentation.styles import initialize_all_styles

def main():
    initialize_all_styles()  # CSS初期化を統合
    # ... 既存のコード
```

### ステップ5: 検証
- [ ] ビジュアル回帰テスト
- [ ] パフォーマンス測定
- [ ] クロスブラウザテスト

## 成功基準

### パフォーマンス指標
- CSS処理時間: 50ms以下
- 初回ロード時間: 10%改善
- ファイルサイズ: 30%削減

### 品質指標
- 重複コード: 0行
- CSS lint エラー: 0件
- ドキュメント化率: 100%

## リスクと対策

| リスク | 影響度 | 対策 |
|--------|--------|------|
| スタイル崩れ | 高 | 段階的移行、スクリーンショット比較 |
| Streamlit更新での非互換 | 中 | バージョン固定、テスト自動化 |
| パフォーマンス悪化 | 低 | ベンチマーク測定、ロールバック準備 |

## タイムライン

### Day 1（2時間）
- 10:00-11:00: バックアップと重複ファイル整理
- 11:00-12:00: CSS統合モジュール作成

### Day 2（3時間）
- 13:00-15:00: コンポーネント別スタイル分離
- 15:00-16:00: 重複除去とテスト

### Day 3（4時間）
- 10:00-12:00: パフォーマンス最適化
- 13:00-15:00: ドキュメント作成と最終テスト

## チェックリスト

### 事前準備
- [ ] バックアップ作成
- [ ] 現状のスクリーンショット取得
- [ ] パフォーマンスベースライン測定

### 実装
- [ ] スタイルモジュール作成
- [ ] 重複CSS除去
- [ ] コンポーネント統合
- [ ] テスト実施

### 完了確認
- [ ] ビジュアル確認
- [ ] パフォーマンス測定
- [ ] ドキュメント更新
- [ ] コードレビュー

## 期待される成果

1. **パフォーマンス向上**
   - 初回ロード時間: 30%改善
   - CSS処理時間: 40%削減

2. **保守性向上**
   - 変更箇所: 1箇所に集約
   - コード量: 50%削減

3. **開発効率向上**
   - スタイル変更時間: 70%削減
   - デバッグ時間: 50%削減