# 厚東川監視システム プロジェクト詳細

## プロジェクト概要
山口県宇部市の厚東川ダムおよび厚東川（持世寺）の水位・雨量データをリアルタイムで監視するWebアプリケーション。

## デプロイ情報
- **本番URL**: https://kotogawa-monitor-app-fjprveyn8fzb3mbffkwq6i.streamlit.app/
- **GitHubリポジトリ**: https://github.com/dobocreate/kotogawa-monitor-streamlit
- **ホスティング**: Streamlit Cloud
- **自動更新**: GitHub Actions（60分間隔）

## 技術スタック
- **フロントエンド**: Streamlit
- **バックエンド**: Python 3.9+
- **データ収集**: BeautifulSoup4 (Web scraping)
- **可視化**: Plotly
- **データ処理**: pandas
- **CI/CD**: GitHub Actions

## プロジェクト構造
```
kotogawa-monitor-streamlit/
├── streamlit_app.py          # メインアプリケーション
├── scripts/
│   ├── collect_data.py       # データ収集スクリプト
│   └── save_current_webfetch_data.py  # 手動データ取得
├── data/
│   ├── latest.json          # 最新データ
│   ├── history/             # 履歴データ (年/月/日/時刻.json)
│   └── logs/                # 実行ログ
├── .github/workflows/
│   ├── data_collection.yml  # 自動データ収集（60分間隔）
│   └── cleanup.yml          # 古いデータクリーンアップ（毎日）
├── requirements.txt         # Python依存関係
└── README.md               # プロジェクト説明

```

## データソース

### 山口県土木防災情報システム
1. **厚東川ダム（観測所コード: 015）**
   - URL: https://y-bousai.pref.yamaguchi.lg.jp/citizen/dam/kdm_table.aspx
   - パラメータ: `check=015&obsdt=YYYYMMDDHHmm&pop=1`
   - 取得データ: 貯水位、貯水率、流入量、全放流量

2. **厚東川・持世寺（観測所コード: 05067）**
   - URL: https://y-bousai.pref.yamaguchi.lg.jp/citizen/water/kwl_table.aspx
   - パラメータ: `check=05067&obsdt=YYYYMMDDHHmm&pop=1`
   - 取得データ: 河川水位、水位変化、警戒レベル

3. **雨量データ**
   - ダムページから同時取得
   - 取得データ: 60分雨量、累積雨量

## 主要機能

### 1. リアルタイム監視
- 現在の水位・雨量をメトリクスで表示
- 3セクション構成：降雨情報、河川情報、ダム情報
- 観測時刻の表示

### 2. アラート機能
- 河川警戒レベル（水防団待機: 3.80m、氾濫注意: 5.00m、避難判断: 5.10m、氾濫危険: 5.50m）
- ダム貯水率警戒（警戒: 90%、危険: 95%）
- 雨量警戒（注意: 10mm/h、警戒: 30mm/h、危険: 50mm/h）

### 3. データ可視化
- 時系列グラフ（Plotly）
- データテーブル表示
- CSVダウンロード機能

### 4. 自動データ収集
- GitHub Actionsで60分ごとに実行（毎時0分）
- 10分単位でデータを丸めて取得（データ公開遅延対応）
- 自動的にGitHubリポジトリにコミット

## 重要な実装詳細

### 時刻処理
```python
# 10分単位に丸めて、さらに10分前のデータを取得
current_time = datetime.now()
minutes = (current_time.minute // 10) * 10
observation_time = current_time.replace(minute=minutes, second=0, microsecond=0) - timedelta(minutes=10)
obsdt = observation_time.strftime('%Y%m%d%H%M')
```

### データ形式（latest.json）
```json
{
  "timestamp": "2025-06-23T04:09:31.717981",
  "data_time": "2025-06-22T14:00:00",
  "dam": {
    "water_level": 36.74,
    "storage_rate": 97.0,
    "inflow": 7.31,
    "outflow": 9.41,
    "storage_change": -0.02
  },
  "river": {
    "water_level": 2.85,
    "level_change": -0.03,
    "status": "正常"
  },
  "rainfall": {
    "hourly": 1,
    "cumulative": 2,
    "change": 1
  }
}
```

## 最近の主要変更

### 2025年6月23日
1. **河川データ取得URL修正**
   - `kwl_graph.aspx` → `kwl_table.aspx`
   - テーブル形式での確実なデータ取得
   - パラメータ: `check=05067&obsdt=YYYYMMDDHHmm&pop=1`

2. **ダムデータ取得URL修正**
   - `kdm_graph.aspx` → `kdm_table.aspx`
   - テーブル形式での確実なデータ取得
   - パラメータ: `check=015&obsdt=YYYYMMDDHHmm&pop=1`

3. **時刻処理の改善**
   - 10分単位での丸め処理
   - データ公開遅延への対応（10分前のデータを取得）
   - 全ての時刻表示を日本時間（JST）に統一

4. **GitHub Actions間隔変更**
   - 10分間隔 → 60分間隔（毎時0分）
   - cron設定: `0 * * * *`

5. **Streamlit読み込み問題の修正**
   - 履歴データ処理の最適化（最大100ファイル）
   - 自動更新の一時無効化
   - 新しいファイルから優先的に処理

6. **UI改善**
   - 河川情報セクションに観測日時を追加
   - 3列レイアウト（水位、観測地点、観測日時）

7. **手動データ更新スクリプト追加**
   - `scripts/update_latest_data.py`
   - GitHub Actions停止時の緊急対応用

## トラブルシューティング

### よくある問題

1. **データが更新されない**
   - GitHub Actionsの実行状況を確認
   - データソースのWebサイトアクセス状況を確認

2. **Streamlitが読み込み中のまま**
   - 履歴データが多すぎる場合がある
   - ブラウザキャッシュをクリア（Ctrl+F5）

3. **データ値が正しくない**
   - BeautifulSoupの解析パターンを確認
   - Webサイトの構造変更を確認

### デバッグ用スクリプト
```bash
# 手動でデータ取得
python scripts/save_current_webfetch_data.py

# データ収集テスト
python scripts/collect_data.py

# 最小版アプリテスト
streamlit run streamlit_app_minimal.py
```

## 連絡先・管理
- **Streamlit Cloud管理**: https://share.streamlit.io/
- **GitHub Actions管理**: https://github.com/dobocreate/kotogawa-monitor-streamlit/actions

## 現在の状態（2025年6月23日 5:15 JST）

### システム稼働状況
- **Streamlit App**: ✅ 稼働中
- **最新データ**: 2025-06-23 04:50 JST
- **GitHub Actions**: ⚠️ 次回実行は 06:00 JST予定

### 最新観測データ
- **ダム貯水位**: 36.82m (97.9%)
- **河川水位**: 2.91m (正常)
- **流入量**: 17.22 m³/s
- **全放流量**: 9.25 m³/s

### 未解決の課題
1. GitHub Actionsの自動実行が一時的に停止（設定変更後の初回実行待ち）
2. 雨量データの取得が不安定
3. Git rebaseの残骸が残っている可能性

## 今後の改善案
1. データ取得エラー時の通知機能
2. 過去データの統計分析機能
3. 予測機能の追加
4. モバイル対応の改善
5. 雨量データ専用URLの調査と実装
6. エラーログの可視化機能