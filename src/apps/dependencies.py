from typing import Annotated

from fastapi import Depends

from .auth.services import get_admin_user, get_active_user
from .users.models import User

user_dependency = Annotated[User, Depends(get_active_user)]
admin_dependency = Annotated[User, Depends(get_admin_user)]
