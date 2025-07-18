from fastapi import FastAPI

from .core.exceptions import register_exceptions
from .core.lifecycle import lifespan
from .core.router import include_routers

app = FastAPI(
    title='FastAuth',
    summary='A simple authentication application written in FastAPI',
    version='0.1.0',
    lifespan=lifespan,
)

register_exceptions(app)
include_routers(app)
