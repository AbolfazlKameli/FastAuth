from contextlib import asynccontextmanager

from fastapi import FastAPI, status, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .db.database import engine, Base
from .schemas import DataSchema, HealthCheckResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield


app = FastAPI(
    title='FastAuth',
    summary='A simple authentication application written in FastAPI',
    version='0.1.0',
    lifespan=lifespan,
)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        content={"data": {'errors': exc.detail}},
        status_code=exc.status_code,
        headers=exc.headers,
    )


@app.get('/health-check', status_code=status.HTTP_200_OK, response_model=DataSchema[HealthCheckResponse])
async def health_check():
    return DataSchema(data={'status': 'OK'})
