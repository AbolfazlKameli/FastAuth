from fastapi import FastAPI

from .configs.logging_config import setup_logging
from .core.exceptions import register_exceptions
from .core.lifecycle import lifespan
from .core.middlewares import register_middlewares
from .core.router import include_routers

setup_logging()

app = FastAPI(
    title='FastAuth',
    summary='A simple authentication application written in FastAPI',
    version='0.1.0',
    lifespan=lifespan,
)

register_middlewares(app)
register_exceptions(app)
include_routers(app)
