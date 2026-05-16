import re
from datetime import datetime

_WEEKDAYS = ['月曜日', '火曜日', '水曜日', '木曜日', '金曜日', '土曜日', '日曜日']

_TEMPLATE_VARS = {
    'date':    lambda now: now.strftime('%Y-%m-%d'),
    'time':    lambda now: now.strftime('%H:%M'),
    'year':    lambda now: now.strftime('%Y'),
    'month':   lambda now: now.strftime('%m'),
    'day':     lambda now: now.strftime('%d'),
    'weekday': lambda now: _WEEKDAYS[now.weekday()],
}


def render_template(text):
    now = datetime.now()
    def replace(match):
        key = match.group(1).strip()
        if key in _TEMPLATE_VARS:
            return _TEMPLATE_VARS[key](now)
        return match.group(0)
    return re.sub(r'\{\{(.+?)\}\}', replace, text)
