from typing import Generic, TypeVar

from pydantic import BaseModel, Field

DataT = TypeVar("DataT")


class DataSchema(BaseModel, Generic[DataT]):
    data: DataT


class PaginatedResponse(BaseModel, Generic[DataT]):
    count: int = Field(description='Number of total items')
    previous_page: int | None = Field(None, description='Previous page if it exists', ge=1)
    next_page: int | None = Field(None, description='Next page if it exists', ge=1)
    last_page: int | None = Field(None, description='Last page', ge=1)
    items: list[DataT] = Field(description='List of items returned in a paginated response')


class HealthCheckResponse(BaseModel):
    status: str


class NotFoundResponse(BaseModel):
    errors: str
