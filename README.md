# twikit
- Twitter APIを利用せずにツイートが可能

## 導入
1. インストール
  - `$ pip install twikit python-dotenv pyyaml schedule`
2. Twitter(X)アカウントの作成
  - [こちら](https://twitter.com/i/flow/signup)にアクセスして、Twitterアカウントを作成しましょう
3. 設定ファイルの作成
  - `config.example.yaml` をコピーして `config.yaml` を作成し、アカウント情報を記入
  ```
  cp config.example.yaml config.yaml
  ```

## 使い方

CLI引数と `config.yaml` の両方に対応しています。引数を省略した場合は `config.yaml` の値が使われます。

```bash
# ツイートする
python twikit.py tweet "ツイート本文"

# アカウントを指定してツイートする
python twikit.py --account sub tweet "サブアカウントのツイート"

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

# スケジューラーを起動する（Ctrl+C で停止）
python twikit.py schedule

# 登録済みアカウントの一覧を表示する
python twikit.py accounts
```

## マルチアカウント設定

`config.yaml` の `accounts` セクションで複数のアカウントを管理できます。

```yaml
default_account: main

accounts:
  main:
    email:    main@example.com
    username: main_user
    password: mainpassword
    cookies:  cookies_main.json

  sub:
    email:    sub@example.com
    username: sub_user
    password: subpassword
    cookies:  cookies_sub.json
```

- `--account NAME` で実行時にアカウントを切り替え可能
- `default_account` を省略した場合は `default` がデフォルト名になります
- `accounts` セクションがない場合は `.env` の環境変数にフォールバックします

## スケジュール設定

`config.yaml` の `schedules` セクションで自動ツイートのスケジュールを定義できます。

```yaml
schedules:
  - text: "おはようございます！"
    at: "09:00"
    account: main    # 省略時は default_account を使用

  - text: "週次レポートです。"
    every: monday
    at: "10:00"
    account: sub
    media:
      - ./report.png
```

| フィールド | 必須 | 説明 |
|---|---|---|
| `text` | ○ | ツイート本文 |
| `at` | ○ | 投稿時刻（HH:MM形式） |
| `every` | - | 曜日指定（monday〜sunday）。省略時は毎日 |
| `account` | - | 使用するアカウント名。省略時は `default_account` |
| `media` | - | 添付メディアのパス |

## ログイン
初回実行時にアカウント情報でログインし、`cookies` ファイルにクッキーを保存します。
2回目以降はクッキーを再利用するため、再ログインは不要です。
