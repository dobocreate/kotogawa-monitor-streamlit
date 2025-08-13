# 不足コンポーネント追加計画

## 目的
Streamlitアプリケーション起動エラーを解消するため、不足しているUIコンポーネントを追加

## 現状分析

### エラー内容
```
ModuleNotFoundError: No module named 'src.presentation.components.metrics_card'
```

### 不足ファイル
1. `/src/presentation/components/metrics_card.py` - メトリクスカードコンポーネント
2. `/src/presentation/components/chart.py` - チャートコンポーネント  
3. `/src/presentation/pages/history.py` - 履歴ページ
4. `/src/presentation/pages/settings.py` - 設定ページ

### 既存ファイル（正常）
- `/src/presentation/components/header.py` ✅
- `/src/presentation/components/alert_banner.py` ✅
- `/src/presentation/pages/dashboard.py` ✅

## 影響範囲
- **直接影響**: app.py, components/__init__.py, pages/__init__.py
- **間接影響**: なし（新規追加のため）
- **破壊的変更**: なし

## リスク評価
- **リスクレベル**: 低
- **理由**: 新規ファイル追加のみで既存コードへの変更なし

## 実装方針
1. 最小限の実装で起動可能にする
2. 既存のコンポーネントパターンに従う
3. デモデータで動作確認可能にする

## ロールバック計画
- 追加したファイルを削除するのみ
- 既存ファイルへの変更はないため、影響なし

## 完了条件
- [ ] エラーなくStreamlitアプリが起動する
- [ ] コンポーネントがインポート可能
- [ ] 基本的な描画が可能