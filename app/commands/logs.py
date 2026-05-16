import json


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
