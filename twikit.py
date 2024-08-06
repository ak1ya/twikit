import asyncio
from twikit import Client

# 第一引数に言語を指定
client = Client('ja')

async def main():
    # アカウントにログイン
    await client.login(
        auth_info_1='email@example.com',
        auth_info_2='example_user',
        password='password0000'
    )
asyncio.run(main())

# ツイートする
tweet_text = 'ツイート本文'
media_ids = [
    client.upload_media('./media1.png'),
    client.upload_media('./media2.png'),
    client.upload_media('./media3.png')
]
await client.create_tweet(tweet_text, media_idsS)

# ツイートの検索
# 第二引数にはTop, Latest, Mediaを指定できる
await client.search_tweet('検索クエリ', 'Top')

# ユーザーの検索
await client.search_user('検索クエリ')

# ニュースカテゴリーのトレンドを取得
await client.get_trends('news')
