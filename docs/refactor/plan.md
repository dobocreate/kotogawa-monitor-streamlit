# リファクタリング計画：実データ対応

## 目的
app.pyを実データ（data/history内のJSONファイル）に対応させ、デモモードと実データモードの切り替えを可能にする

## 現状分析
- **app.py**：デモモード固定（line 161: `st.session_state.demo_mode = True`）
- **DashboardPage**：monitoring_service未設定のため、常に`_get_demo_history_data()`を使用
- **streamlit_app.py**：`load_history_data()`で実データを読み込む既存実装あり
- **data/history/**：YYYY/MM/DD/*.json形式で実データが保存されている

## 影響範囲
- app.py（サービス注入箇所）
- src/presentation/pages/dashboard.py（データ取得ロジック）
- 新規作成：src/infrastructure/repositories/history_repository.py
- 新規作成：src/application/services/history_service.py

## リスク評価
- **低リスク**：新規ファイル追加のため既存機能への影響なし
- **中リスク**：DashboardPageの変更（ただしデモモードは維持）
- **注意点**：JSONファイル読み込み時のエラーハンドリング

## ロールバック計画
1. 各コミットは独立してrevert可能
2. デモモード動作は常に保証される
3. 実データ読み込みエラー時はデモモードへフォールバック

## 実装ステップ
1. **Step 1**：履歴データリポジトリの作成（behavior-preserving）
2. **Step 2**：履歴サービスの作成（behavior-preserving）
3. **Step 3**：DashboardPageへのサービス統合（behavior-preserving）
4. **Step 4**：app.pyでのサービス注入（behavior-preserving）
5. **Step 5**：動作検証とテスト

## 完了条件
- [ ] デモモードが従来通り動作する
- [ ] 実データモードでdata/historyからデータを読み込める
- [ ] モード切り替えがサイドバーから可能
- [ ] エラー時の適切なフォールバック
- [ ] 既存のグラフ表示機能が維持される