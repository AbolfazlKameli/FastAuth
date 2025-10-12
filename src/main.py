from contextlib import asynccontextmanager

from fastapi import FastAPI, status, Request
from fastapi.responses import JSONResponse
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

from src.apps.auth.router import router as auth_router
from src.apps.users.router import router as user_router
from src.core.configs.logging_config import setup_logging
from src.core.configs.settings import configs
from src.core.limiter import limiter
from src.core.schemas import DataSchema, HealthCheckResponse
from src.infrastructure.redis_pool import redis_fastapi

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    backend = RedisBackend(redis_fastapi)
    FastAPICache().init(backend=backend, prefix="FastAuth_")

    yield

    await redis_fastapi.close()
    await redis_fastapi.connection_pool.disconnect()


app = FastAPI(
    title='FastAuth',
    summary='A simple authentication application written in FastAPI',
    version='0.5.0',
    lifespan=lifespan,
    contact={
        "name": "Denver",
        "url": "https://github.com/abolfazlkameli",
        "email": "abolfazlkameli0@gmail.com"
    },
    license_info={
        "name": "Beer License",
    },
)
app.state.limiter = limiter

app.include_router(user_router)
app.include_router(auth_router)

app.add_middleware(SessionMiddleware, secret_key=configs.SECRET_KEY)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        content={"data": {'errors': exc.detail}},
        status_code=exc.status_code,
        headers=exc.headers,
    )


app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.get('/health-check', status_code=status.HTTP_200_OK, response_model=DataSchema[HealthCheckResponse])
async def health_check():
    return DataSchema(data={'status': 'OK'})
