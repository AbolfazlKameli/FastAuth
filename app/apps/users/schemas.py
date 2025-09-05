from datetime import datetime

from pydantic import BaseModel


class UserBase(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime


class UsersList(BaseModel):
    users: list[UserBase]
