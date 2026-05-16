import asyncio
from twikit import Client

client = Client('ja')

async def main():
    # クッキーが存在する場合は読み込み、なければログイン
    try:
        client.load_cookies('cookies.json')
    except FileNotFoundError:
        await client.login(
            auth_info_1='email@example.com',
            auth_info_2='example_user',
            password='password0000'
        )
        client.save_cookies('cookies.json')

    # ツイートする
    tweet_text = 'ツイート本文'
    media_ids = [
        await client.upload_media('./media1.png'),
        await client.upload_media('./media2.png'),
        await client.upload_media('./media3.png')
    ]
    await client.create_tweet(tweet_text, media_ids=media_ids)

    # ツイートの検索
    # 第二引数にはTop, Latest, Mediaを指定できる
    await client.search_tweet('検索クエリ', 'Top')

    # ユーザーの検索
    await client.search_user('検索クエリ')

    # ニュースカテゴリーのトレンドを取得
    await client.get_trends('news')

asyncio.run(main())
