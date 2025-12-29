from social_core.backends.telegram import TelegramAuth as BaseTelegramAuth

class SafeTelegramAuth(BaseTelegramAuth):
    def __init__(self, *args, **kwargs):
        # Для Django Admin strategy может быть None
        if 'strategy' not in kwargs:
            kwargs['strategy'] = None
        super().__init__(*args, **kwargs)