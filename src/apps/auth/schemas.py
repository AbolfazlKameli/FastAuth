from pydantic import BaseModel, EmailStr


class UserRegisterRequest(BaseModel):
    email: EmailStr


class UserRegisterResponse(BaseModel):
    message: str
    otp_valid_time: str
