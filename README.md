# twikit
- Twitter APIを利用せずにツイートが可能

## 導入
1. インストール
  - `$ pip install twikit`
2. Twitter(X)アカウントの作成
  - [こちら](https://twitter.com/i/flow/signup)にアクセスして、Twitterアカウントを作成しましょう

## ログイン
- ツイートのたびにログインするため以下で回避

- save_cookiesを使用することで、ログインした際のクッキー情報をファイルに保存
```
# クッキーの保存
client.save_cookies('cookies.json')
```

- load_cookiesメソッドを使用することで、保存されたクッキー情報を読み込み
  - ログイン情報を再利用し、再度ログインの手続きを省略することが可
```
# クッキーの読み込み
client.load_cookies('cookies.json')
```
