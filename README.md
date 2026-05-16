# twikit
- Twitter APIを利用せずにツイートが可能

## 導入
1. インストール
  - `$ pip install twikit python-dotenv pyyaml`
2. Twitter(X)アカウントの作成
  - [こちら](https://twitter.com/i/flow/signup)にアクセスして、Twitterアカウントを作成しましょう
3. 認証情報の設定
  - `.env.example` をコピーして `.env` を作成し、自分のアカウント情報を記入
  ```
  cp .env.example .env
  ```
4. 設定ファイルの作成（任意）
  - `config.example.yaml` をコピーして `config.yaml` を作成
  ```
  cp config.example.yaml config.yaml
  ```

## 使い方

CLI引数と `config.yaml` の両方に対応しています。引数を省略した場合は `config.yaml` の値が使われます。

```bash
# ツイートする（引数で指定）
python twikit.py tweet "ツイート本文"

# ツイートする（config.yaml の内容を使用）
python twikit.py tweet

# メディア付きツイート
python twikit.py tweet "ツイート本文" --media image1.png image2.png

# ツイートを検索する
python twikit.py search-tweet "検索クエリ"
python twikit.py search-tweet "検索クエリ" --type Latest

# ユーザーを検索する
python twikit.py search-user "検索クエリ"

# トレンドを取得する
python twikit.py trends
python twikit.py trends --category sports
```

## ログイン
初回実行時に `.env` の認証情報でログインし、`cookies.json` にクッキーを保存します。
2回目以降はクッキーを再利用するため、再ログインは不要です。
