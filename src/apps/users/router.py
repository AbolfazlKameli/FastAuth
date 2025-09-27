from typing import Annotated

from fastapi import APIRouter, status, Query
from fastapi_cache.decorator import cache

from src.apps.dependencies import user_dependency, admin_dependency, auth_responses
from src.core.schemas import ErrorResponse
from src.core.schemas import PaginatedResponse, DataSchema
from src.dependencies import db_dependency
from .schemas import UserOut
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
