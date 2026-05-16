import os
from twikit import Client

_clients: dict[str, Client] = {}


def _default_account(config):
    return config.get('default_account', 'default')


def _account_cfg(account_name, config):
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
