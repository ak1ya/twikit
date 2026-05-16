from ..auth import get_client, _default_account


async def cmd_trends(args, config):
    category = args.category or config.get('trends', {}).get('category', 'news')
    account  = args.account or _default_account(config)
    client   = await get_client(account, config)
    trends   = await client.get_trends(category)
    for trend in trends:
        print(trend.name)
