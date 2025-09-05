from fastapi import FastAPI

from app.apps.users.models import User  # noqa
from app.core.configs.logging_config import setup_logging
from app.core.exceptions import register_exceptions
from app.core.lifecycle import lifespan
from app.core.router import include_routers

setup_logging()

app = FastAPI(
    title='FastAuth',
    summary='A simple authentication application written in FastAPI',
    version='0.1.0',
    lifespan=lifespan,
)

register_exceptions(app)
include_routers(app)
