import argparse
import asyncio
import os
import time
import schedule
import yaml
from datetime import datetime
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


async def post_tweet(text, media_paths=None):
    media_ids = []
    for path in (media_paths or []):
        media_id = await client.upload_media(path)
        media_ids.append(media_id)
    await client.create_tweet(text, media_ids=media_ids or None)
    print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] ツイートしました: {text[:30]}...' if len(text) > 30 else f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] ツイートしました: {text}')


async def cmd_tweet(args, config):
    text = args.text or config.get('tweet', {}).get('text')
    media_paths = args.media or config.get('tweet', {}).get('media', [])

    if not text:
        print('エラー: ツイート本文を指定してください（引数 or config.yaml の tweet.text）')
        return

    await post_tweet(text, media_paths)


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


def register_schedules(schedules_config):
    DAYS = {
        'monday': schedule.every().monday,
        'tuesday': schedule.every().tuesday,
        'wednesday': schedule.every().wednesday,
        'thursday': schedule.every().thursday,
        'friday': schedule.every().friday,
        'saturday': schedule.every().saturday,
        'sunday': schedule.every().sunday,
    }

    for entry in schedules_config:
        text = entry.get('text')
        media_paths = entry.get('media', [])
        at_time = entry.get('at')
        every_day = entry.get('every')

        if not text or not at_time:
            print(f'警告: スケジュールに text と at は必須です。スキップします: {entry}')
            continue

        def make_job(t, m):
            def job():
                asyncio.run(post_tweet(t, m))
            return job

        job_fn = make_job(text, media_paths)

        if every_day and every_day.lower() in DAYS:
            DAYS[every_day.lower()].at(at_time).do(job_fn)
            print(f'スケジュール登録: 毎週{every_day} {at_time} → "{text[:20]}"')
        else:
            schedule.every().day.at(at_time).do(job_fn)
            print(f'スケジュール登録: 毎日 {at_time} → "{text[:20]}"')


async def cmd_schedule(args, config):
    schedules_config = config.get('schedules', [])

    if not schedules_config:
        print('エラー: config.yaml に schedules の設定がありません')
        return

    register_schedules(schedules_config)
    print('スケジューラーを起動しました。Ctrl+C で停止します。')

    try:
        while True:
            schedule.run_pending()
            time.sleep(30)
    except KeyboardInterrupt:
        print('スケジューラーを停止しました')


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

    # schedule サブコマンド
    subparsers.add_parser('schedule', help='config.yaml のスケジュールに従って自動ツイートする')

    args = parser.parse_args()

    await login()

    commands = {
        'tweet': cmd_tweet,
        'search-tweet': cmd_search_tweet,
        'search-user': cmd_search_user,
        'trends': cmd_trends,
        'schedule': cmd_schedule,
    }
    await commands[args.command](args, config)


asyncio.run(main())
