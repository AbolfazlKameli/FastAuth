from fastapi import FastAPI, status

from .schemas import DataSchema

app = FastAPI(
    title='FastAuth',
    summary='A simple authentication application written in FastAPI',
    version='0.1.0',
)


@app.get('/health-check', status_code=status.HTTP_200_OK, response_model=DataSchema)
async def health_check():
    return DataSchema(data={'status': 'OK'})
