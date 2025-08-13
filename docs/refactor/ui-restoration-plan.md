# UI復元リファクタリング計画

## 目的
元のstreamlit_app.pyのUIデザインを、新しいクリーンアーキテクチャ上で完全に復元する

## 範囲
- src/presentation/配下のUI層のみ
- ドメインロジック・データ取得層は変更しない
- behavior-preserving（既存の動作を変更しない）

## 影響範囲
- app.py（タイトル変更のみ）
- src/presentation/components/（新規コンポーネント追加）
- src/presentation/pages/dashboard.py（レイアウト修正）
- src/presentation/styles/（CSSファイル追加）

## リスク評価
- **低リスク**: 表示層のみの変更で、ビジネスロジックに影響なし
- **中リスク**: CSS競合の可能性（既存スタイルとの干渉）
- **対策**: 段階的実装と各ステップでの動作確認

## ロールバック計画
```bash
# 問題発生時の即時ロールバック
git checkout main app.py
git checkout main src/presentation/
```

## 完了条件
- [ ] タイトルが「厚東川氾濫監視システムv2.0」と表示
- [ ] 3列の状態表示バーが機能
- [ ] 6つのメトリクス（水位、変化量、流量、降雨量、貯水量、警戒レベル）が表示
- [ ] 元の131行のカスタムCSSが適用
- [ ] 5種類のグラフがすべて表示
- [ ] すべてのテストがグリーン
- [ ] デモモードで正常動作確認

## 実装フェーズ
1. **Phase 1**: 基本構造（タイトル、状態バー、メトリクス）
2. **Phase 2**: グラフとタブ機能
3. **Phase 3**: CSSとスタイル適用
4. **Phase 4**: 天気予報と追加機能

## タイムライン
- Phase 1: 30分
- Phase 2: 1時間
- Phase 3: 30分
- Phase 4: 1時間（オプション）