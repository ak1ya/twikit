from ..auth import _default_account


async def cmd_accounts(args, config):
    accounts = config.get('accounts', {})
    if not accounts:
        print('config.yaml に accounts の設定がありません')
        return
    default = _default_account(config)
    for name in accounts:
        marker = ' (デフォルト)' if name == default else ''
        print(f'  {name}{marker}')
