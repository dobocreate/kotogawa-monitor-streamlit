# リファクタリングチェックリスト：実データ対応

## 実施前チェック
- [x] 現状のコード分析完了
- [x] リファクタリング計画書作成
- [ ] テスト環境準備
- [ ] データサンプル確認

## Step 1: 履歴データリポジトリの作成
- [x] src/infrastructure/repositories/history_repository.py 作成
- [x] load_history_data()メソッド実装
- [x] load_latest_data()メソッド実装
- [x] エラーハンドリング実装
- [ ] 単体テスト作成

## Step 2: 履歴サービスの作成
- [x] src/application/services/history_service.py 作成
- [x] get_current_data()メソッド実装
- [x] get_historical_data()メソッド実装
- [x] データ変換ロジック実装
- [x] キャッシュ機能実装

## Step 3: DashboardPageへのサービス統合
- [x] dashboard.pyの修正
- [x] サービス注入のサポート追加
- [x] デモモードとの切り替えロジック実装
- [x] エラー時のフォールバック実装
- [ ] 動作確認

## Step 4: app.pyでのサービス注入
- [x] app.pyの修正
- [x] demo_mode判定ロジック実装
- [x] サービスインスタンス生成
- [x] DashboardPageへの注入
- [ ] 動作確認

## Step 5: 動作検証とテスト
- [ ] デモモード動作確認
- [ ] 実データモード動作確認
- [ ] モード切り替え動作確認
- [ ] エラーハンドリング確認
- [ ] パフォーマンス確認

## 完了確認
- [ ] 全テスト合格
- [ ] コードレビュー実施
- [ ] ドキュメント更新
- [ ] change-log.md更新