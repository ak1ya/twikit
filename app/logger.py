import json
from datetime import datetime


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
