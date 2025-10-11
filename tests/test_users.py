import pytest


@pytest.mark.asyncio
async def test_list_users_success(admin_auth_client):
    response = await admin_auth_client.get("/users")

    assert response.status_code == 200
    assert len(response.json()["data"]["items"]) == 2
    assert response.json()["data"]["count"] == 2


@pytest.mark.asyncio
async def test_list_users_empty_pagination(admin_auth_client):
    response = await admin_auth_client.get("/users", params={"page": 12})

    assert response.status_code == 200
    assert len(response.json()["data"]["items"]) == 0


@pytest.mark.asyncio
async def test_list_users_pagination(admin_auth_client):
    response = await admin_auth_client.get("/users", params={"per_page": 1, "page": 2})

    assert response.status_code == 200
    assert len(response.json()["data"]["items"]) == 1


@pytest.mark.asyncio
async def test_list_users_not_admin_user(user_auth_client):
    response = await user_auth_client.get("/users")

    assert response.status_code == 403
    assert response.json() == {'data': {'errors': 'You do not have access to this resource'}}


@pytest.mark.asyncio
async def test_list_users_missing_authentication_token(anon_client):
    response = await anon_client.get("/users")

    assert response.status_code == 403
    assert response.json() == {'data': {'errors': 'Not authenticated'}}
