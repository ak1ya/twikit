import argparse
import asyncio
import os
import yaml
from dotenv import load_dotenv
from twikit import Client

load_dotenv()

client = Client('ja')


def load_config(path='config.yaml'):
    try:
        with open(path) as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        return {}


async def login():
    try:
        client.load_cookies('cookies.json')
    except FileNotFoundError:
        await client.login(
            auth_info_1=os.environ['TWITTER_EMAIL'],
            auth_info_2=os.environ['TWITTER_USERNAME'],
            password=os.environ['TWITTER_PASSWORD'],
        )
        client.save_cookies('cookies.json')


async def cmd_tweet(args, config):
    text = args.text or config.get('tweet', {}).get('text')
    media_paths = args.media or config.get('tweet', {}).get('media', [])

    if not text:
        print('エラー: ツイート本文を指定してください（引数 or config.yaml の tweet.text）')
        return

    media_ids = []
    for path in media_paths:
        media_id = await client.upload_media(path)
        media_ids.append(media_id)

    await client.create_tweet(text, media_ids=media_ids or None)
    print('ツイートしました')


async def cmd_search_tweet(args, config):
    query = args.query or config.get('search', {}).get('tweet', {}).get('query')
    search_type = args.type or config.get('search', {}).get('tweet', {}).get('type', 'Top')

    if not query:
        print('エラー: 検索クエリを指定してください（引数 or config.yaml の search.tweet.query）')
        return

    results = await client.search_tweet(query, search_type)
    for tweet in results:
        print(f'@{tweet.user.screen_name}: {tweet.text}')


async def cmd_search_user(args, config):
    query = args.query or config.get('search', {}).get('user', {}).get('query')

    if not query:
        print('エラー: 検索クエリを指定してください（引数 or config.yaml の search.user.query）')
        return

    results = await client.search_user(query)
    for user in results:
        print(f'@{user.screen_name} ({user.name})')


async def cmd_trends(args, config):
    category = args.category or config.get('trends', {}).get('category', 'news')
    trends = await client.get_trends(category)
    for trend in trends:
        print(trend.name)


async def main():
    config = load_config()

    parser = argparse.ArgumentParser(prog='twikit', description='Twitter CLIツール')
    subparsers = parser.add_subparsers(dest='command', required=True)

    # tweet サブコマンド
    p_tweet = subparsers.add_parser('tweet', help='ツイートする')
    p_tweet.add_argument('text', nargs='?', default=None, help='ツイート本文（省略時は config.yaml を使用）')
    p_tweet.add_argument('--media', nargs='*', default=[], metavar='FILE', help='添付メディアのパス（省略時は config.yaml を使用）')

    # search-tweet サブコマンド
    p_search_tweet = subparsers.add_parser('search-tweet', help='ツイートを検索する')
    p_search_tweet.add_argument('query', nargs='?', default=None, help='検索クエリ（省略時は config.yaml を使用）')
    p_search_tweet.add_argument('--type', choices=['Top', 'Latest', 'Media'], default=None, help='検索タイプ（デフォルト: Top）')

    # search-user サブコマンド
    p_search_user = subparsers.add_parser('search-user', help='ユーザーを検索する')
    p_search_user.add_argument('query', nargs='?', default=None, help='検索クエリ（省略時は config.yaml を使用）')

    # trends サブコマンド
    p_trends = subparsers.add_parser('trends', help='トレンドを取得する')
    p_trends.add_argument('--category', default=None, choices=['trending', 'news', 'sports', 'entertainment'], help='カテゴリ（デフォルト: news）')

    args = parser.parse_args()

    await login()

    commands = {
        'tweet': cmd_tweet,
        'search-tweet': cmd_search_tweet,
        'search-user': cmd_search_user,
        'trends': cmd_trends,
    }
    await commands[args.command](args, config)


asyncio.run(main())
