from typing import Annotated

from fastapi import Depends, status

from src.core.schemas import DataSchema, ErrorResponse
from .auth.services import get_authenticated_user, get_admin_user
from .users.models import User

user_dependency = Annotated[User, Depends(get_authenticated_user)]
admin_dependency = Annotated[User, Depends(get_admin_user)]

auth_responses = {
    status.HTTP_401_UNAUTHORIZED: {
        "model": DataSchema[ErrorResponse],
        "description": "Authentication failed."
    },
    status.HTTP_403_FORBIDDEN: {
        "model": DataSchema[ErrorResponse],
        "description": "Not Permitted."
    }
}
