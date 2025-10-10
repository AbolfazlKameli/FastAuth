from slowapi import Limiter
from slowapi.util import get_remote_address

from src.core.configs.settings import configs

if configs.ENV_STATE == "test":
    limiter = Limiter(key_func=lambda: "", headers_enabled=True)
else:
    limiter = Limiter(key_func=get_remote_address, headers_enabled=True)


def user_limiter():
    return limiter.limit("60/minute")


def admin_limiter():
    return limiter.limit("300/minute")
