from pydantic import BaseModel, EmailStr


class UserRegisterRequest(BaseModel):
    email: EmailStr


class UserOTPResponse(BaseModel):
    message: str
    otp_valid_time: str


class UserRegisterResponse(BaseModel):
    message: str
    otp_valid_time: str
