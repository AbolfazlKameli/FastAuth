from typing import Annotated

from fastapi import APIRouter, status, Query

from app.dependencies import db_dependency
from app.schemas import PaginatedResponse
from .repository import get_all_users
from .schemas import UserBase
from ...core.pagination import paginate

router = APIRouter(
    prefix='/users',
    tags=['users']
)


@router.get("", response_model=PaginatedResponse[UserBase], status_code=status.HTTP_200_OK)
async def list_users(
        db: db_dependency,
        page: Annotated[int, Query(ge=1)] = 1,
        per_page: Annotated[int, Query(ge=1, le=100)] = 1,
):
    return await paginate(get_all_users(), db, page, per_page)
