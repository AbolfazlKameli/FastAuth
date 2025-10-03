from datetime import datetime
from typing import Self

from pydantic import BaseModel, EmailStr, Field, model_validator

from src.apps.auth.validators import PasswordValidator
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


class ChangePasswordRequest(BaseModel):
    old_password: PasswordValidator
    new_password: PasswordValidator
    confirm_password: PasswordValidator

    @model_validator(mode="after")
    def check_passwords_match(self) -> Self:
        if self.new_password != self.confirm_password:
            raise ValueError("Passwords don't match")
        return self


class OTPSetPasswordRequest(BaseModel):
    email: EmailStr
    otp_code: str = Field(min_length=6, max_length=6)
    new_password: PasswordValidator
    confirm_password: PasswordValidator

    @model_validator(mode="after")
    def check_passwords_match(self) -> Self:
        if self.new_password != self.confirm_password:
            raise ValueError("Passwords don't match")
        return self


class UserUpdateRequest(BaseModel):
    username: str | None = Field(None, min_length=4)
    email: EmailStr | None = None
