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

# アカウント名 -> 認証済み Client のキャッシュ
_clients: dict[str, Client] = {}


def load_config(path='config.yaml'):
    try:
        with open(path) as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        return {}


def _account_cfg(account_name, config):
    """config.yaml の accounts セクションから指定アカウントの設定を返す。
    accounts セクションがない場合は環境変数にフォールバック。"""
    accounts = config.get('accounts', {})
    if accounts:
        cfg = accounts.get(account_name)
        if not cfg:
            raise KeyError(f'アカウント "{account_name}" が config.yaml の accounts に見つかりません')
        return cfg
    # 後方互換: accounts 未定義なら環境変数を使用
    return {
        'email':    os.environ['TWITTER_EMAIL'],
        'username': os.environ['TWITTER_USERNAME'],
        'password': os.environ['TWITTER_PASSWORD'],
        'cookies':  'cookies.json',
    }


async def get_client(account_name, config):
    """認証済み Client を返す。同一アカウントは再利用する。"""
    if account_name in _clients:
        return _clients[account_name]

    cfg = _account_cfg(account_name, config)
    client = Client('ja')
    cookies_path = cfg.get('cookies', f'cookies_{account_name}.json')

    try:
        client.load_cookies(cookies_path)
    except FileNotFoundError:
        await client.login(
            auth_info_1=cfg['email'],
            auth_info_2=cfg['username'],
            password=cfg['password'],
        )
        client.save_cookies(cookies_path)

    _clients[account_name] = client
    return client


def _default_account(config):
    """使用するデフォルトアカウント名を返す。"""
    return config.get('default_account', 'default')


async def post_tweet(client, text, media_paths=None):
    media_ids = []
    for path in (media_paths or []):
        media_id = await client.upload_media(path)
        media_ids.append(media_id)
    await client.create_tweet(text, media_ids=media_ids or None)
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    preview = text[:30] + '...' if len(text) > 30 else text
    print(f'[{ts}] ツイートしました: {preview}')


async def cmd_tweet(args, config):
    text = args.text or config.get('tweet', {}).get('text')
    media_paths = args.media or config.get('tweet', {}).get('media', [])

    if not text:
        print('エラー: ツイート本文を指定してください（引数 or config.yaml の tweet.text）')
        return

    account = args.account or _default_account(config)
    client = await get_client(account, config)
    await post_tweet(client, text, media_paths)


async def cmd_search_tweet(args, config):
    query = args.query or config.get('search', {}).get('tweet', {}).get('query')
    search_type = args.type or config.get('search', {}).get('tweet', {}).get('type', 'Top')

    if not query:
        print('エラー: 検索クエリを指定してください（引数 or config.yaml の search.tweet.query）')
        return

    account = args.account or _default_account(config)
    client = await get_client(account, config)
    results = await client.search_tweet(query, search_type)
    for tweet in results:
        print(f'@{tweet.user.screen_name}: {tweet.text}')


async def cmd_search_user(args, config):
    query = args.query or config.get('search', {}).get('user', {}).get('query')

    if not query:
        print('エラー: 検索クエリを指定してください（引数 or config.yaml の search.user.query）')
        return

    account = args.account or _default_account(config)
    client = await get_client(account, config)
    results = await client.search_user(query)
    for user in results:
        print(f'@{user.screen_name} ({user.name})')


async def cmd_trends(args, config):
    category = args.category or config.get('trends', {}).get('category', 'news')
    account = args.account or _default_account(config)
    client = await get_client(account, config)
    trends = await client.get_trends(category)
    for trend in trends:
        print(trend.name)


def register_schedules(schedules_config, config):
    DAYS = {
        'monday':    schedule.every().monday,
        'tuesday':   schedule.every().tuesday,
        'wednesday': schedule.every().wednesday,
        'thursday':  schedule.every().thursday,
        'friday':    schedule.every().friday,
        'saturday':  schedule.every().saturday,
        'sunday':    schedule.every().sunday,
    }

    for entry in schedules_config:
        text        = entry.get('text')
        media_paths = entry.get('media', [])
        at_time     = entry.get('at')
        every_day   = entry.get('every')
        account     = entry.get('account') or _default_account(config)

        if not text or not at_time:
            print(f'警告: text と at は必須です。スキップします: {entry}')
            continue

        def make_job(t, m, a):
            def job():
                async def _run():
                    c = await get_client(a, config)
                    await post_tweet(c, t, m)
                asyncio.run(_run())
            return job

        job_fn = make_job(text, media_paths, account)

        if every_day and every_day.lower() in DAYS:
            DAYS[every_day.lower()].at(at_time).do(job_fn)
            print(f'スケジュール登録 [{account}]: 毎週{every_day} {at_time} → "{text[:20]}"')
        else:
            schedule.every().day.at(at_time).do(job_fn)
            print(f'スケジュール登録 [{account}]: 毎日 {at_time} → "{text[:20]}"')


async def cmd_schedule(args, config):
    schedules_config = config.get('schedules', [])

    if not schedules_config:
        print('エラー: config.yaml に schedules の設定がありません')
        return

    register_schedules(schedules_config, config)
    print('スケジューラーを起動しました。Ctrl+C で停止します。')

    try:
        while True:
            schedule.run_pending()
            time.sleep(30)
    except KeyboardInterrupt:
        print('スケジューラーを停止しました')


async def cmd_accounts(args, config):
    accounts = config.get('accounts', {})
    if not accounts:
        print('config.yaml に accounts の設定がありません')
        return
    default = _default_account(config)
    for name in accounts:
        marker = ' (デフォルト)' if name == default else ''
        print(f'  {name}{marker}')


async def main():
    config = load_config()

    parser = argparse.ArgumentParser(prog='twikit', description='Twitter CLIツール')
    # グローバルオプション: 全サブコマンドで使用可能
    parser.add_argument('--account', default=None, metavar='NAME', help='使用するアカウント名（デフォルト: config.yaml の default_account）')
    subparsers = parser.add_subparsers(dest='command', required=True)

    # tweet
    p_tweet = subparsers.add_parser('tweet', help='ツイートする')
    p_tweet.add_argument('text', nargs='?', default=None, help='ツイート本文（省略時は config.yaml を使用）')
    p_tweet.add_argument('--media', nargs='*', default=[], metavar='FILE', help='添付メディアのパス')

    # search-tweet
    p_search_tweet = subparsers.add_parser('search-tweet', help='ツイートを検索する')
    p_search_tweet.add_argument('query', nargs='?', default=None, help='検索クエリ')
    p_search_tweet.add_argument('--type', choices=['Top', 'Latest', 'Media'], default=None)

    # search-user
    p_search_user = subparsers.add_parser('search-user', help='ユーザーを検索する')
    p_search_user.add_argument('query', nargs='?', default=None, help='検索クエリ')

    # trends
    p_trends = subparsers.add_parser('trends', help='トレンドを取得する')
    p_trends.add_argument('--category', default=None, choices=['trending', 'news', 'sports', 'entertainment'])

    # schedule
    subparsers.add_parser('schedule', help='config.yaml のスケジュールに従って自動ツイートする')

    # accounts
    subparsers.add_parser('accounts', help='登録済みアカウントの一覧を表示する')

    args = parser.parse_args()

    commands = {
        'tweet':        cmd_tweet,
        'search-tweet': cmd_search_tweet,
        'search-user':  cmd_search_user,
        'trends':       cmd_trends,
        'schedule':     cmd_schedule,
        'accounts':     cmd_accounts,
    }
    await commands[args.command](args, config)


asyncio.run(main())
