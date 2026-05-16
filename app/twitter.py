from datetime import datetime
from .template import render_template
from .logger import write_log


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
