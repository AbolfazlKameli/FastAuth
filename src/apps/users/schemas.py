from datetime import datetime

from pydantic import BaseModel, EmailStr

from .models import UserRoles


class UserBase(BaseModel):
    username: str
    email: EmailStr
    created_at: datetime


class UserOut(UserBase):
    id: int
    role: UserRoles


class ResetPasswordRequest(BaseModel):
    email: EmailStr
