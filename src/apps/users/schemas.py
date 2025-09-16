from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    username: str
    email: EmailStr
    created_at: datetime


class UserOut(UserBase):
    id: int


class UsersList(BaseModel):
    users: list[UserBase]
