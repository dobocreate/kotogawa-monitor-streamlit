# CSS最適化リファクタリング実施チェックリスト

## 事前準備
- [ ] 現在の動作確認（スクリーンショット取得）
- [ ] gitブランチの確認（main/master）
- [ ] 依存パッケージの確認

## Step 1: CSS統合モジュールの作成
- [ ] src/presentation/styles/ディレクトリ作成
- [ ] __init__.py作成
- [ ] core_styles.py作成
- [ ] component_styles.py作成
- [ ] responsive_styles.py作成
- [ ] テスト実行・動作確認
- [ ] コミット: "feat: CSS統合モジュール構造の作成"

## Step 2: 重複スタイルの抽出と統合
- [ ] app.pyとstreamlit_app.pyのCSS比較
- [ ] 共通スタイルの抽出
- [ ] core_styles.pyへの実装
- [ ] テスト実行・動作確認
- [ ] コミット: "refactor: 重複CSSの統合"

## Step 3: コンポーネント別スタイルの整理
- [ ] メトリクス用スタイル分離
- [ ] グラフ用スタイル分離
- [ ] サイドバー用スタイル分離
- [ ] component_styles.pyへの実装
- [ ] テスト実行・動作確認
- [ ] コミット: "refactor: コンポーネント別CSS整理"

## Step 4: app.pyへの統合
- [ ] initialize_css関数の更新
- [ ] CSSモジュールのインポート
- [ ] インラインCSS削除
- [ ] テスト実行・動作確認
- [ ] コミット: "refactor: app.pyのCSS統合"

## Step 5: streamlit_app.pyへの統合
- [ ] CSSモジュールのインポート
- [ ] インラインCSS削除
- [ ] 統合スタイル適用
- [ ] テスト実行・動作確認
- [ ] コミット: "refactor: streamlit_app.pyのCSS統合"

## Step 6: 未使用スタイルの削除
- [ ] 使用状況の確認
- [ ] デッドコード削除
- [ ] 最適化
- [ ] テスト実行・動作確認
- [ ] コミット: "refactor: 未使用CSS削除"

## Step 7: パフォーマンス計測
- [ ] Before計測値記録
- [ ] After計測値記録
- [ ] 改善率の算出
- [ ] ドキュメント更新

## 最終確認
- [ ] デスクトップ表示確認
- [ ] モバイル表示確認
- [ ] 各ページ遷移確認
- [ ] エラーログ確認
- [ ] ドキュメント更新完了

## ロールバック手順
1. 問題発生時: `git status`で変更確認
2. 直前の状態に戻す: `git checkout -`
3. 特定コミットに戻す: `git revert <commit-hash>`
4. キャッシュクリア: `st.cache_data.clear()`