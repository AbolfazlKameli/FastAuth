from typing import Generic, TypeVar

from pydantic import BaseModel

DataT = TypeVar("DataT")


class DataSchema(BaseModel, Generic[DataT]):
    data: DataT
