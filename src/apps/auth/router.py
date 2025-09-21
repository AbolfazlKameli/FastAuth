from fastapi import APIRouter, status, Response, HTTPException

from src.apps.tasks import send_otp_code_email
from src.core.configs.settings import configs
from src.dependencies import db_dependency
from .schemas import UserRegister
from .services import (
    check_blacklist_for_user,
    check_email_exists,
    generate_otp,
    handle_user_blacklist,
    refresh_otp_code
)

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)


@router.post(
    "/register",
    status_code=status.HTTP_202_ACCEPTED
)
async def request_otp_to_register(register_data: UserRegister, db: db_dependency, response: Response):
    email = str(register_data.email)

    if (message := await check_blacklist_for_user(db, email)) is not None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=message)

    if await check_email_exists(db, email):
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"data": {"message": "Email already registered"}}

    otp_obj, otp_code, hashed_code, is_new, expires_at = await generate_otp(db, email)

    if not is_new and otp_obj.attempts >= configs.OTP_SETTINGS.MAX_ATTEMPTS:
        message = await handle_user_blacklist(db, email)
        response.status_code = status.HTTP_429_TOO_MANY_REQUESTS
        return {"data": {"message": message}}

    if not is_new:
        await refresh_otp_code(db, otp_obj, hashed_code, expires_at)

    send_otp_code_email.delay(email, otp_code)

    return {
        "data": {
            "message": "Verification email sent.",
            "otp_valid_time": "120s"
        }
    }
