import pytest


@pytest.mark.asyncio
async def test_health_check(anon_client):
    response = await anon_client.get("/health-check")

    assert response.status_code == 200
