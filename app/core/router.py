from fastapi import FastAPI, status

from app.api.users.routers import router as user_router
from app.schemas import DataSchema, HealthCheckResponse


def include_routers(app: FastAPI):
    @app.get('/health-check', status_code=status.HTTP_200_OK, response_model=DataSchema[HealthCheckResponse])
    async def health_check():
        return DataSchema(data={'status': 'OK'})

    app.include_router(user_router)
