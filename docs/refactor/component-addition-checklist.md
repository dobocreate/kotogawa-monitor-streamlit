# コンポーネント追加チェックリスト

## 実施日: 2025-08-12

## 問題の特定
- [x] エラー内容確認: `ModuleNotFoundError: No module named 'src.presentation.components.metrics_card'`
- [x] 不足ファイル特定完了
- [x] 影響範囲の確認完了

## 実装前準備
- [x] 既存構造の確認 (`src/presentation/components/__init__.py`)
- [x] 必要コンポーネントリスト作成
- [x] リファクタリング計画作成 (`docs/refactor/missing-components-plan.md`)

## コンポーネント作成
### MetricsCard
- [x] `src/presentation/components/metrics_card.py` 作成
- [x] 基本機能実装（値表示、変化量、ステータス）
- [x] 複数メトリクス表示対応
- [x] 比較カード機能

### TimeSeriesChart
- [x] `src/presentation/components/chart.py` 作成
- [x] 単一系列グラフ機能
- [x] 複数系列グラフ機能
- [x] 閾値線表示機能
- [x] サブプロット機能
- [x] デモデータ生成機能

### HistoryPage
- [x] `src/presentation/pages/history.py` 作成
- [x] 期間選択UI
- [x] 河川水位履歴表示
- [x] ダム情報履歴表示
- [x] 統計情報表示
- [x] デモデータ対応

### SettingsPage
- [x] `src/presentation/pages/settings.py` 作成
- [x] 表示設定タブ
- [x] アラート設定タブ
- [x] データ取得設定タブ
- [x] システム設定タブ
- [x] 設定エクスポート/インポート機能

## 依存関係
- [x] plotly インストール (6.3.0)
- [x] pandas 確認（既存）
- [x] python-dateutil 再インストール
- [x] streamlit-autorefresh 確認（既存）

## 検証
- [x] インポートテスト実施
- [x] 依存関係エラー解消
- [ ] Streamlitアプリ起動確認（環境依存のため保留）
- [x] 既存コードへの影響なし確認

## ドキュメント更新
- [x] `docs/refactor/missing-components-plan.md` 作成
- [x] `docs/refactor/change-log.md` 更新
- [x] 本チェックリスト作成

## リスク管理
- [x] 新規ファイルのみ（既存コード変更なし）
- [x] ロールバック手順明確（ファイル削除のみ）
- [x] 破壊的変更なし確認

## 完了条件
- [x] 全不足コンポーネント作成完了
- [x] インポートエラー解消
- [x] クリーンアーキテクチャ準拠
- [x] ドキュメント更新完了

## 備考
- デモデータ機能により、バックエンドサービスなしでも動作可能
- 設定はJSONファイルベースで永続化
- 全コンポーネントは既存のアーキテクチャパターンに準拠