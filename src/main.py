from fastapi import FastAPI, status

from src.apps.users.models import User  # noqa
from src.apps.users.router import router as user_router
from src.core.configs.logging_config import setup_logging
from src.core.exceptions import register_exceptions
from src.core.lifecycle import lifespan
from src.core.schemas import DataSchema, HealthCheckResponse

setup_logging()

app = FastAPI(
    title='FastAuth',
    summary='A simple authentication application written in FastAPI',
    version='0.1.0',
    lifespan=lifespan,
)

register_exceptions(app)


@app.get('/health-check', status_code=status.HTTP_200_OK, response_model=DataSchema[HealthCheckResponse])
async def health_check():
    return DataSchema(data={'status': 'OK'})


app.include_router(user_router)
