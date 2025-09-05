from typing import Annotated

from fastapi import APIRouter, status, Query, Path

from app.core.pagination import paginate
from app.dependencies import db_dependency
from app.schemas import PaginatedResponse, DataSchema
from .repository import get_all_users, get_user_by_id
from .schemas import UserBase

router = APIRouter(
    prefix='/users',
    tags=['users']
)


@router.get("", response_model=DataSchema[PaginatedResponse[UserBase]], status_code=status.HTTP_200_OK)
async def list_users(
        db: db_dependency,
        page: Annotated[int, Query(ge=1)] = 1,
        per_page: Annotated[int, Query(ge=1, le=100)] = 10,
):
    return DataSchema(data=await paginate(get_all_users(), db, page, per_page))


@router.get("/{user_id}", response_model=DataSchema[UserBase], status_code=status.HTTP_200_OK)
async def get_user(db: db_dependency, user_id: Annotated[int, Path(ge=1)]):
    user = await get_user_by_id(db, user_id)
    return DataSchema(data=user)
