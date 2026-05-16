from ..auth import get_client, _default_account


async def cmd_search_tweet(args, config):
    query = args.query or config.get('search', {}).get('tweet', {}).get('query')
    search_type = args.type or config.get('search', {}).get('tweet', {}).get('type', 'Top')

    if not query:
        print('エラー: 検索クエリを指定してください（引数 or config.yaml の search.tweet.query）')
        return

    account = args.account or _default_account(config)
    client  = await get_client(account, config)
    results = await client.search_tweet(query, search_type)
    for tweet in results:
        print(f'@{tweet.user.screen_name}: {tweet.text}')


async def cmd_search_user(args, config):
    query = args.query or config.get('search', {}).get('user', {}).get('query')

    if not query:
        print('エラー: 検索クエリを指定してください（引数 or config.yaml の search.user.query）')
        return

    account = args.account or _default_account(config)
    client  = await get_client(account, config)
    results = await client.search_user(query)
    for user in results:
        print(f'@{user.screen_name} ({user.name})')
