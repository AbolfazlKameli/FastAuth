from typing import Annotated

from fastapi import APIRouter, status, Query, HTTPException, Request, Response
from fastapi_cache.decorator import cache

from src.apps.auth.repository import get_otp_by_email
from src.apps.auth.services import check_blacklist_for_user, is_otp_valid, delete_otp, generate_and_send_otp
from src.apps.dependencies import user_dependency, admin_dependency, auth_responses
from src.core.limiter import user_limiter, admin_limiter, limiter
from src.core.schemas import PaginatedResponse, DataSchema, ErrorResponse, SuccessResponse
from src.dependencies import db_dependency
from .repository import get_user_by_email, user_exists_with_email_or_username
from .schemas import (
    UserOut,
    ResetPasswordRequest,
    OTPSetPasswordRequest,
    ChangePasswordRequest,
    UserUpdateRequest,
    UserActivationRequest
)
from .services import get_all_users_paginated

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
@admin_limiter()
async def list_users(
        db: db_dependency,
        _: admin_dependency,
        request: Request,
        response: Response,
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
@user_limiter()
async def get_user(
        user: user_dependency,
        request: Request,
        response: Response
):
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
@limiter.limit("5/minute")
async def request_otp_to_reset_password(
        db: db_dependency,
        reset_data: ResetPasswordRequest,
        request: Request,
        response: Response
):
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

    await generate_and_send_otp(db, email)

    return {"data": {"message": "Otp code sent for reset password."}}


@router.post(
    "/profile/password/set",
    status_code=status.HTTP_200_OK,
    response_model=DataSchema[SuccessResponse],
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": DataSchema[ErrorResponse],
            "description": "Invalid email address."
        },
        status.HTTP_403_FORBIDDEN: {
            "model": DataSchema[ErrorResponse],
            "description": "Invalid OTP code."
        }
    }
)
@limiter.limit("5/minute")
async def set_password(
        db: db_dependency,
        validated_data: OTPSetPasswordRequest,
        request: Request,
        response: Response
):
    otp_code = validated_data.otp_code
    email = str(validated_data.email)

    otp_obj = await get_otp_by_email(db, email)

    if not is_otp_valid(otp_code, otp_obj):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid or expired OTP code.")

    user = await get_user_by_email(db, email)

    user.set_password(validated_data.new_password.get_secret_value())
    db.add(user)
    await db.commit()

    await delete_otp(db, otp_obj)

    return {"data": {"message": "Your password has been changed successfully."}}


@router.post(
    "/profile/password/change",
    status_code=status.HTTP_200_OK,
    response_model=DataSchema[SuccessResponse],
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": DataSchema[ErrorResponse],
            "description": "Incorrect password."
        },
        **auth_responses
    }
)
@limiter.limit("10/5minute")
async def change_user_password(
        db: db_dependency,
        change_request: ChangePasswordRequest,
        user: user_dependency,
        request: Request,
        response: Response
):
    password = change_request.old_password.get_secret_value()
    new_password = change_request.new_password.get_secret_value()

    if not user.verify_password(password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect password.")

    user.set_password(new_password)
    db.add(user)
    await db.commit()

    return {"data": {"message": "Your password has been changed successfully."}}


@router.put(
    "/profile/update",
    status_code=status.HTTP_200_OK,
    response_model=DataSchema[SuccessResponse],
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": DataSchema[ErrorResponse],
            "description": "Invalid email or username"
        },
        **auth_responses
    }
)
@limiter.limit("10/5minute")
async def update_user_profile(
        db: db_dependency,
        update_request: UserUpdateRequest,
        user: user_dependency,
        request: Request,
        response: Response
):
    update_request_dict = update_request.model_dump(exclude_unset=True)
    email = update_request_dict.get("email")

    response_message = "User profile updated successfully."

    if await user_exists_with_email_or_username(db, email, update_request.username):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username or email already taken.")

    for key, value in update_request_dict.items():
        setattr(user, key, value)

    if "email" in update_request_dict:
        user.is_active = False
        response_message += " Otp Code sent to your new email address."
        await generate_and_send_otp(db, email)

    db.add(user)
    await db.commit()

    return {"data": {"message": response_message}}


@router.post(
    "/profile/activate",
    status_code=status.HTTP_200_OK,
    response_model=DataSchema[SuccessResponse],
    responses={
        status.HTTP_403_FORBIDDEN: {
            "model": DataSchema[ErrorResponse],
            "description": "Invalid or expired OTP code."
        }
    }
)
@limiter.limit("10/5minute")
async def activate_user_account(
        db: db_dependency,
        activation_request: UserActivationRequest,
        request: Request,
        response: Response
):
    otp_code = activation_request.otp_code
    email = str(activation_request.email)

    otp_obj = await get_otp_by_email(db, email)

    if not is_otp_valid(otp_code, otp_obj):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid or expired OTP code.")

    user = await get_user_by_email(db, email)
    user.is_active = True
    db.add(user)
    await db.commit()

    await delete_otp(db, otp_obj)

    return {"data": {"message": "Your account has been activated successfully."}}


@router.delete(
    "/profile/delete",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        **auth_responses
    }
)
@limiter.limit("10/5minute")
async def delete_user_profile(
        db: db_dependency,
        user: user_dependency,
        request: Request,
        response: Response
):
    await db.delete(user)
    await db.commit()
