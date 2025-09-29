from typing import Annotated

from fastapi import APIRouter, status, Query, HTTPException
from fastapi_cache.decorator import cache

from src.apps.auth.services import check_blacklist_for_user, generate_otp, refresh_otp_code, handle_user_blacklist
from src.apps.dependencies import user_dependency, admin_dependency, auth_responses
from src.apps.tasks import send_otp_code_email
from src.core.configs.settings import configs
from src.core.schemas import PaginatedResponse, DataSchema, ErrorResponse, SuccessResponse
from src.dependencies import db_dependency
from .repository import get_user_by_email
from .schemas import UserOut, ResetPasswordRequest
from .services import get_all_users_paginated, get_user_or_404

router = APIRouter(
    prefix='/users',
    tags=['users']
)


@router.get(
    "",
    response_model=DataSchema[PaginatedResponse[UserOut]],
    status_code=status.HTTP_200_OK,
    responses=auth_responses
)
@cache(expire=60)
async def list_users(
        db: db_dependency,
        _: admin_dependency,
        page: Annotated[int, Query(ge=1)] = 1,
        per_page: Annotated[int, Query(ge=1, le=100)] = 10,
):
    return {"data": await get_all_users_paginated(db, page, per_page)}


@router.get(
    "/profile",
    response_model=DataSchema[UserOut],
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": DataSchema[ErrorResponse],
        },
        **auth_responses
    }
)
@cache(expire=60)
async def get_user(
        db: db_dependency,
        user: user_dependency
):
    user = await get_user_or_404(db, user.id)
    return {"data": user}


@router.post(
    "/profile/password/reset",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=DataSchema[SuccessResponse],
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": DataSchema[ErrorResponse],
            "description": "Invalid email address."
        },
        status.HTTP_403_FORBIDDEN: {
            "model": DataSchema[ErrorResponse],
            "description": "Blacklisted email."
        },
        status.HTTP_429_TOO_MANY_REQUESTS: {
            "model": DataSchema[ErrorResponse],
            "description": "Too many requests."
        },
    }
)
async def request_otp_to_reset_password(db: db_dependency, reset_data: ResetPasswordRequest):
    email = str(reset_data.email)

    if (message := await check_blacklist_for_user(db, email)) is not None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=message)

    user = await get_user_by_email(db, email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="That address is either invalid,"
                   " not a verified primary email or is not associated with a personal user account."
        )

    otp_obj, otp_code, hashed_code, is_new, expires_at = await generate_otp(db, email)

    if not is_new and otp_obj.attempts >= configs.OTP_SETTINGS.MAX_ATTEMPTS:
        message = await handle_user_blacklist(db, email)
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=message)

    if not is_new:
        await refresh_otp_code(db, otp_obj, hashed_code, expires_at)

    send_otp_code_email.delay(email, otp_code)

    return {"data": {"message": "Otp code sent for reset password."}}
