from ..auth import get_client, _default_account
from ..twitter import post_tweet


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
