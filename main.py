import argparse
import asyncio
from dotenv import load_dotenv
from app.config import load_config
from app.commands.tweet import cmd_tweet
from app.commands.search import cmd_search_tweet, cmd_search_user
from app.commands.trends import cmd_trends
from app.commands.scheduler import cmd_schedule
from app.commands.logs import cmd_logs
from app.commands.accounts import cmd_accounts

load_dotenv()


async def main():
    config = load_config()

    parser = argparse.ArgumentParser(prog='twikit', description='Twitter CLIツール')
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
