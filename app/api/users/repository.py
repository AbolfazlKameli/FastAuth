from sqlalchemy import select

from .models import User


def get_all_users():
    return select(User)
