from typing import Self

from pydantic import BaseModel, EmailStr, Field, model_validator

from src.apps.users.schemas import UserOut
from .validators import PasswordValidator


class UserRegisterRequest(BaseModel):
    email: EmailStr


class UserOTPResponse(BaseModel):
    message: str
    otp_valid_time: str


class UserRegisterResponse(BaseModel):
    message: str
    user: UserOut


class OtpVerifyUserRegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=4)
    password: PasswordValidator
    confirm_password: PasswordValidator
    otp_code: str = Field(min_length=6, max_length=6)

    @model_validator(mode="after")
    def check_passwords_match(self) -> Self:
        if self.password != self.confirm_password:
            raise ValueError("Passwords don't match")
        return self
