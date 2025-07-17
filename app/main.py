from fastapi import FastAPI, status

app = FastAPI(
    title='FastAuth',
    summary='A simple authentication application written in FastAPI',
    version='0.1.0',
)


@app.get('/health-check', status_code=status.HTTP_200_OK)
async def health_check():
    return {'status': 'OK'}
