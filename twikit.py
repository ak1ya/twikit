import argparse
import asyncio
import json
import os
import re
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


_WEEKDAYS = ['月曜日', '火曜日', '水曜日', '木曜日', '金曜日', '土曜日', '日曜日']

_TEMPLATE_VARS = {
    'date':    lambda now: now.strftime('%Y-%m-%d'),
    'time':    lambda now: now.strftime('%H:%M'),
    'year':    lambda now: now.strftime('%Y'),
    'month':   lambda now: now.strftime('%m'),
    'day':     lambda now: now.strftime('%d'),
    'weekday': lambda now: _WEEKDAYS[now.weekday()],
}


def write_log(log_path, account, text, media_paths, status, error=None):
    entry = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'account':   account,
        'text':      text,
        'media':     media_paths or [],
        'status':    status,
    }
    if error:
        entry['error'] = error
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')


def render_template(text):
    """{{variable}} 形式のテンプレート変数を現在時刻で展開する。"""
    now = datetime.now()
    def replace(match):
        key = match.group(1).strip()
        if key in _TEMPLATE_VARS:
            return _TEMPLATE_VARS[key](now)
        return match.group(0)  # 未知の変数はそのまま残す
    return re.sub(r'\{\{(.+?)\}\}', replace, text)


async def post_tweet(client, text, account='unknown', media_paths=None, log_path='tweet.log'):
    text = render_template(text)
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    preview = text[:30] + '...' if len(text) > 30 else text
    try:
        media_ids = []
        for path in (media_paths or []):
            media_id = await client.upload_media(path)
            media_ids.append(media_id)
        await client.create_tweet(text, media_ids=media_ids or None)
        write_log(log_path, account, text, media_paths, 'success')
        print(f'[{ts}] ツイートしました [{account}]: {preview}')
    except Exception as e:
        write_log(log_path, account, text, media_paths, 'error', error=str(e))
        print(f'[{ts}] エラー [{account}]: {e}')
        raise


async def cmd_tweet(args, config):
    text = args.text or config.get('tweet', {}).get('text')
    media_paths = args.media or config.get('tweet', {}).get('media', [])

    if not text:
        print('エラー: ツイート本文を指定してください（引数 or config.yaml の tweet.text）')
        return

    account  = args.account or _default_account(config)
    log_path = config.get('log', {}).get('path', 'tweet.log')
    client   = await get_client(account, config)
    await post_tweet(client, text, account=account, media_paths=media_paths, log_path=log_path)


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
            log_path = config.get('log', {}).get('path', 'tweet.log')
            def job():
                async def _run():
                    c = await get_client(a, config)
                    await post_tweet(c, t, account=a, media_paths=m, log_path=log_path)
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


async def cmd_logs(args, config):
    log_path = config.get('log', {}).get('path', 'tweet.log')

    try:
        with open(log_path, encoding='utf-8') as f:
            entries = [json.loads(line) for line in f if line.strip()]
    except FileNotFoundError:
        print(f'ログファイルがまだ存在しません: {log_path}')
        return

    if args.account:
        entries = [e for e in entries if e.get('account') == args.account]

    entries = entries[-args.tail:]

    for e in entries:
        status  = '✓' if e['status'] == 'success' else '✗'
        preview = e['text'][:40] + '...' if len(e['text']) > 40 else e['text']
        line    = f"[{e['timestamp']}] {status} [{e['account']}] {preview}"
        if e['status'] == 'error':
            line += f" ERROR: {e.get('error', '')}"
        print(line)

    print(f'\n合計 {len(entries)} 件')


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

    # logs
    p_logs = subparsers.add_parser('logs', help='投稿ログを表示する')
    p_logs.add_argument('--tail', type=int, default=20, metavar='N', help='表示する最新件数（デフォルト: 20）')
    p_logs.add_argument('--account', default=None, metavar='NAME', help='アカウントでフィルタ')

    # accounts
    subparsers.add_parser('accounts', help='登録済みアカウントの一覧を表示する')

    args = parser.parse_args()

    commands = {
        'tweet':        cmd_tweet,
        'search-tweet': cmd_search_tweet,
        'search-user':  cmd_search_user,
        'trends':       cmd_trends,
        'schedule':     cmd_schedule,
        'logs':         cmd_logs,
        'accounts':     cmd_accounts,
    }
    await commands[args.command](args, config)


asyncio.run(main())
