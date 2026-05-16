import asyncio
import time
import schedule
from ..auth import get_client, _default_account
from ..twitter import post_tweet


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
