# 🌊 厚東川リアルタイム監視システム

山口県宇部市の厚東川ダムおよび厚東川（持世寺）の水位・雨量データをリアルタイムで監視・表示するWebアプリケーションです。

## 📋 概要

- **データソース**: 山口県土木防災情報システム
- **更新頻度**: 10分間隔
- **データ保持**: 過去7日間
- **警戒レベル**: 4段階のアラート機能

## 🚀 デプロイ方法

### Streamlit Cloud でのデプロイ

1. **GitHubリポジトリの準備**
   ```bash
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **Streamlit Cloud でアプリを作成**
   - [Streamlit Cloud](https://streamlit.io/cloud) にアクセス
   - GitHubアカウントでサインイン
   - "New app" をクリック
   - リポジトリを選択: `kotogawa-monitor-streamlit`
   - Branch: `main`
   - Main file path: `streamlit_app.py`
   - "Deploy!" をクリック

3. **GitHub Actions の有効化**
   - リポジトリの Settings → Actions → General
   - "Allow all actions and reusable workflows" を選択
   - 初回データ収集を手動実行:
     ```bash
     python scripts/collect_data.py
     git add data/
     git commit -m "Initial data collection"
     git push
     ```

## 💻 ローカル実行

### 必要要件

- Python 3.9以上
- pip

### インストール

```bash
# リポジトリのクローン
git clone <repository-url>
cd kotogawa-monitor-streamlit

# 仮想環境の作成（推奨）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# または
venv\Scripts\activate  # Windows

# 依存関係のインストール
pip install -r requirements.txt
```

### 実行

```bash
# データ収集（初回）
python scripts/collect_data.py

# Streamlitアプリの起動
streamlit run streamlit_app.py
```

ブラウザで `http://localhost:8501` にアクセス

## 📊 機能

### データ表示
- **河川水位**: 現在値・変化量・警戒ステータス
- **ダム水位**: 水位・貯水率・流入出量
- **雨量**: 時間雨量・累積雨量
- **時系列グラフ**: 過去24時間のトレンド表示

### アラート機能
- **4段階の警戒レベル**:
  - 🟢 正常: 3.80m未満
  - 🟡 水防団待機: 3.80m以上
  - 🟠 氾濫注意: 5.00m以上
  - 🔴 氾濫危険: 5.50m以上

### データ管理
- **自動収集**: GitHub Actions による10分間隔
- **履歴保存**: 7日間のデータ保持
- **CSVエクスポート**: データのダウンロード機能
- **自動クリーンアップ**: 古いデータの削除

## 🔧 設定

### 警戒水位の変更

サイドバーで以下の値を調整可能:
- 河川警戒水位
- 河川危険水位  
- ダム警戒貯水率
- ダム危険貯水率

### 表示期間の変更

サイドバーで6時間〜72時間の範囲で表示期間を選択可能

## 📁 プロジェクト構造

```
kotogawa-monitor-streamlit/
├── streamlit_app.py          # メインアプリケーション
├── requirements.txt          # 依存パッケージ
├── README.md                 # このファイル
├── .streamlit/
│   └── config.toml          # Streamlit設定
├── data/
│   ├── latest.json          # 最新データ
│   └── history/             # 履歴データ（YYYY/MM/DD/）
├── scripts/
│   ├── collect_data.py      # データ収集スクリプト
│   ├── process_data.py      # データ処理・分析
│   └── cleanup_data.py      # 古いデータ削除
├── .github/
│   └── workflows/
│       ├── data_collection.yml  # 定期データ収集
│       └── cleanup.yml          # 定期クリーンアップ
└── doc/
    └── 厚東川監視システム開発仕様書.txt
```

## 🔄 GitHub Actions

### データ収集ワークフロー
- **実行間隔**: 10分ごと
- **タイムアウト**: 5分
- **処理**: データ取得 → 保存 → Git push

### クリーンアップワークフロー  
- **実行間隔**: 毎日0時（UTC）
- **処理**: 7日以前のデータ削除 → Git push

## 🐛 トラブルシューティング

### データが表示されない場合

1. **データファイルの確認**:
   ```bash
   ls -la data/
   cat data/latest.json
   ```

2. **手動データ収集**:
   ```bash
   python scripts/collect_data.py
   ```

3. **GitHub Actions の確認**:
   - リポジトリの "Actions" タブで実行状況を確認
   - 失敗している場合はログを確認

### アプリがエラーで起動しない場合

1. **依存関係の確認**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Python バージョンの確認**:
   ```bash
   python --version  # 3.9以上
   ```

3. **ファイルパスの確認**:
   - 絶対パスでの実行を推奨
   ```bash
   cd /path/to/kotogawa-monitor-streamlit
   streamlit run streamlit_app.py
   ```

## 📈 今後の拡張

### Phase 2 実装予定
- 予測機能の追加
- メール通知機能
- 複数地点対応

### Phase 3 実装予定  
- モバイルアプリ開発
- API提供
- 外部システム連携

## 📄 ライセンス

このプロジェクトはMITライセンスのもとで公開されています。

## 🤝 貢献

プルリクエストやイシューの報告を歓迎します。

---

## 📞 お問い合わせ

システムに関するご質問やご要望は、GitHubのIssuesからお願いします。

**データ提供**: 山口県土木防災情報システム  
**開発**: Claude Code を使用して開発