from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, headers_enabled=True)


def user_limiter():
    return limiter.limit("60/minute")


def admin_limiter():
    return limiter.limit("300/minute")
