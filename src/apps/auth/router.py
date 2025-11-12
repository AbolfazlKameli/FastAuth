import random
from datetime import timedelta, datetime, timezone

from fastapi import APIRouter, status, HTTPException, Response, Request
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.apps.users.repository import user_exists_with_email_or_username, get_user_by_email
from src.apps.utils import get_or_create, auth_responses
from src.core.limiter import limiter
from src.core.schemas import DataSchema, ErrorResponse
from src.core.settings import configs
from src.dependencies import db_dependency
from .models import RefreshTokenBlacklist
from .repository import get_otp_by_email
from .schemas import (
    UserRegisterRequest,
    UserOTPResponse,
    OtpVerifyUserRegisterRequest,
    UserRegisterResponse,
    UserLoginRequest,
    UserTokenResponse,
    RefreshTokenRequest
)
from .services import (
    check_blacklist_for_user,
    check_email_exists,
    is_otp_valid,
    register_user,
    delete_otp,
    create_jwt_token,
    authenticate_user,
    get_authenticated_user,
    decode_refresh_token,
    generate_and_send_otp,
    oauth
)

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)


@router.post(
    "/register",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=DataSchema[UserOTPResponse],
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": DataSchema[ErrorResponse],
            "description": "Error when email already exists."
        },
        status.HTTP_403_FORBIDDEN: {
            "model": DataSchema[ErrorResponse],
            "description": "Error when user is blacklisted."
        },
        status.HTTP_429_TOO_MANY_REQUESTS: {
            "model": DataSchema[ErrorResponse],
            "description": "Error when too many requests occurs."
        }
    }
)
@limiter.limit("5/minute")
async def request_otp_to_register(
        register_data: UserRegisterRequest,
        db: db_dependency,
        request: Request,
        response: Response
):
    email = str(register_data.email)

    if (message := await check_blacklist_for_user(db, email)) is not None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=message)

    if await check_email_exists(db, email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists. if you believe your account is deactivated, call support."
        )

    await generate_and_send_otp(db, email)

    return {
        "data": {
            "message": "Verification email sent.",
            "otp_valid_time": "120s"
        }
    }


@router.post(
    "/register/verify",
    status_code=status.HTTP_201_CREATED,
    response_model=DataSchema[UserRegisterResponse],
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": DataSchema[ErrorResponse],
            "description": "Error when email already exists."
        },
        status.HTTP_403_FORBIDDEN: {
            "model": DataSchema[ErrorResponse],
            "description": "Error when OTP verification failed."
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": DataSchema[ErrorResponse],
            "description": "Error when something unexpected happened."
        }
    }
)
@limiter.limit("5/minute")
async def verify_otp_code(
        request_data: OtpVerifyUserRegisterRequest,
        db: db_dependency,
        request: Request,
        response: Response
):
    otp_code = request_data.otp_code
    email = str(request_data.email)
    otp_obj = await get_otp_by_email(db, email)

    if not is_otp_valid(otp_code, otp_obj):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid or expired OTP code.")

    if await user_exists_with_email_or_username(db, email, request_data.username):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username or email already taken.")

    try:
        user = await register_user(
            db,
            password=request_data.password.get_secret_value(),
            email=email,
            username=request_data.username
        )
    except (IntegrityError, SQLAlchemyError):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.")

    await delete_otp(db, otp_obj)
    await db.refresh(user)

    return {
        "data": {
            "message": "User Registered successfully.",
            "user": user
        }
    }


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    response_model=DataSchema[UserTokenResponse],
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": DataSchema[ErrorResponse],
            "description": "Error when email or password is incorrect."
        }
    }
)
@limiter.limit("5/minute")
async def user_login(
        login_data: UserLoginRequest,
        db: db_dependency,
        response: Response,
        request: Request,
):
    email = str(login_data.email)
    user = await authenticate_user(db, email, login_data.password.get_secret_value())

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or password incorrect. if you believe your account is deactivated, call support."
        )

    refresh_token = create_jwt_token(user.id, email, "refresh", timedelta(hours=24))
    response.set_cookie(
        key="refresh_auth",
        value=refresh_token,
        httponly=True,
        secure=(not configs.DEBUG),
        path="/auth/refresh",
        expires=datetime.now(tz=timezone.utc) + timedelta(hours=24),
        samesite="lax"
    )

    access_token = create_jwt_token(user.id, email, "access")
    return {"data": {"message": "User logged in Successfully.", "access_token": access_token}}


@router.post(
    "/refresh",
    status_code=status.HTTP_200_OK,
    response_model=DataSchema[UserTokenResponse],
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": DataSchema[ErrorResponse],
            "description": "Invalid refresh token."
        },
        **auth_responses
    }
)
@limiter.limit("5/minute")
async def refresh_token(db: db_dependency, refresh_data: RefreshTokenRequest, response: Response, request: Request):
    user_id = decode_refresh_token(refresh_data.refresh_token)
    user = await get_authenticated_user(db, user_id)

    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid refresh token.")

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token."
        )

    user_id = user.id
    user_email = user.email

    _, is_new = await get_or_create(db, RefreshTokenBlacklist, refresh=refresh_data.refresh_token)
    if not is_new:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Blocked refresh token.")

    refresh_token = create_jwt_token(user_id, user_email, "refresh", timedelta(hours=24))
    response.set_cookie(
        key="refresh_auth",
        value=refresh_token,
        httponly=True,
        secure=(not configs.DEBUG),
        path="/auth/refresh",
        expires=datetime.now(tz=timezone.utc) + timedelta(hours=24),
        samesite="lax"
    )

    access_token = create_jwt_token(user_id, user_email, "access")
    return {"data": {"message": "Token Refreshed successfully.", "access_token": access_token}}


@router.post(
    "/login/google",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": DataSchema[ErrorResponse],
            "description": "Error when email already exists."
        },
    }
)
@limiter.limit("5/minute")
async def login_by_google(db: db_dependency, request: Request, request_data: UserRegisterRequest, response: Response):
    email = str(request_data.email)

    if (message := await check_blacklist_for_user(db, email)) is not None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=message)

    redirect_url = request.url_for("auth_by_google")
    return await oauth.google.authorize_redirect(request, redirect_url)


@router.get(
    "/login/google/auth"
)
@limiter.limit("5/minute")
async def auth_by_google(db: db_dependency, request: Request, response: Response):
    token = await oauth.google.authorize_access_token(request)
    userinfo = dict(token['userinfo'])

    email = userinfo.get("email")

    user = await get_user_by_email(db, email)

    if user is None:
        username = userinfo.get("given_name")
        if await user_exists_with_email_or_username(db, email, username):
            username += random.randint(1000, 9999)

        user = await register_user(
            db,
            email=email,
            username=username
        )

    refresh_token = create_jwt_token(user.id, email, "refresh", timedelta(hours=24))
    response.set_cookie(
        key="refresh_auth",
        value=refresh_token,
        httponly=True,
        secure=(not configs.DEBUG),
        path="/auth/refresh",
        expires=datetime.now(tz=timezone.utc) + timedelta(hours=24),
        samesite="lax"
    )

    access_token = create_jwt_token(user.id, email, "access")
    return {"data": {"message": "User logged in Successfully.", "access_token": access_token}}
