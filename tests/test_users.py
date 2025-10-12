from datetime import datetime, timedelta

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from src.apps.auth.models import Otp
from src.apps.auth.services import create_jwt_token
from src.apps.users.models import User
from tests.conftest import overrides_get_db, anon_client


@pytest.mark.asyncio
async def test_list_users_success(admin_auth_client):
    response = await admin_auth_client.get("/users")

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_list_users_empty_pagination(admin_auth_client):
    response = await admin_auth_client.get("/users", params={"page": 12})

    assert response.status_code == 200
    assert len(response.json()["data"]["items"]) == 0


@pytest.mark.asyncio
async def test_list_users_pagination(admin_auth_client, generate_test_user):
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


@pytest.mark.asyncio
async def test_user_profile_success(user_auth_client):
    response = await user_auth_client.get("/users/profile")

    assert response.status_code == 200
    assert response.json()["data"]["username"] == "testuser"


@pytest.mark.asyncio
async def test_user_profile_inactive_user(anon_client, generate_inactive_user):
    auth_token = create_jwt_token(generate_inactive_user.id, generate_inactive_user.email, "access")

    anon_client.headers["Authorization"] = f"Bearer {auth_token}"

    response = await anon_client.get("/users/profile")

    assert response.status_code == 401
    assert response.json() == {'data': {'errors': 'Inactive account.'}}


@pytest.mark.asyncio
async def test_request_otp_to_reset_password_success(anon_client, mocker, generate_test_user):
    mock_generate_otp = mocker.patch("src.apps.auth.services.generate_otp")
    mock_generate_otp.return_value = (mocker.ANY, "123456", "hashed_code", True, datetime.now() + timedelta(minutes=2))

    mock_send_otp_task = mocker.patch("src.apps.auth.services.send_otp_code_email", return_value=None)
    mock_send_otp_task.delay = mocker.MagicMock()

    response = await anon_client.post("/users/profile/password/reset", json={"email": "testuser@gmail.com"})

    mock_generate_otp.assert_called_once_with(mocker.ANY, "testuser@gmail.com")
    mock_send_otp_task.delay.assert_called_once_with("testuser@gmail.com", "123456")

    assert response.status_code == 202


@pytest.mark.asyncio
async def test_request_otp_to_reset_password_too_many_requests(anon_client, mocker, generate_test_user):
    mock_generate_and_send_otp = mocker.patch("src.apps.users.router.generate_and_send_otp")
    mock_generate_and_send_otp.side_effect = HTTPException(
        status_code=429,
        detail="Too many requests. Your email has been added to the blacklist."
    )

    response = await anon_client.post("/users/profile/password/reset", json={"email": "testuser@gmail.com"})

    mock_generate_and_send_otp.assert_called_once_with(mocker.ANY, "testuser@gmail.com")

    assert response.status_code == 429


@pytest.mark.asyncio
async def test_request_otp_to_reset_password_blacklisted_with_time(anon_client, mocker):
    mock_blacklist_checker = mocker.patch("src.apps.users.router.check_blacklist_for_user")
    mock_blacklist_checker.return_value = f"You have benn blocked until f{datetime.now()}"

    response = await anon_client.post("/users/profile/password/reset", json={"email": "testuser@gmail.com"})

    mock_blacklist_checker.assert_called_once_with(mocker.ANY, "testuser@gmail.com")

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_request_otp_to_reset_password_blacklisted_permanently(anon_client, mocker):
    mock_blacklist_checker = mocker.patch("src.apps.users.router.check_blacklist_for_user")
    mock_blacklist_checker.return_value = ("You have been permanently blocked. if you believe this is a mistake,"
                                           " please contact support.")

    response = await anon_client.post("/users/profile/password/reset", json={"email": "testuser@gmail.com"})

    mock_blacklist_checker.assert_called_once_with(mocker.ANY, "testuser@gmail.com")

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_request_otp_to_reset_password_invalid_email(anon_client):
    response = await anon_client.post("/users/profile/password/reset", json={"email": "doesnotexist@gmail.com"})

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_set_password_success(overrides_get_db, anon_client, mocker, generate_test_otp, generate_test_user):
    mock_get_otp = mocker.patch("src.apps.users.router.get_otp_by_email", return_value=generate_test_otp)

    mock_otp_validator = mocker.patch("src.apps.users.router.is_otp_valid", return_value=True)

    request_data = {
        "email": "testuser@gmail.com",
        "otp_code": "123456",
        "new_password": "@userNewPassword1",
        "confirm_password": "@userNewPassword1"
    }

    response = await anon_client.post("/users/profile/password/set", json=request_data)

    await overrides_get_db.refresh(generate_test_user)

    mock_get_otp.assert_called_once_with(mocker.ANY, "testuser@gmail.com")
    mock_otp_validator.assert_called_once_with("123456", generate_test_otp)

    assert response.status_code == 200
    assert generate_test_user.verify_password("@userNewPassword1")
    assert (await overrides_get_db.scalars(select(Otp))).all() == []


@pytest.mark.asyncio
async def test_set_password_passwords_does_not_match(overrides_get_db, generate_test_otp, anon_client):
    request_data = {
        "email": "testuser@gmail.com",
        "otp_code": "123456",
        "new_password": "@userNewPassword1",
        "confirm_password": "@userNewPassword2"
    }

    response = await anon_client.post("/users/profile/password/set", json=request_data)

    assert response.status_code == 422
    assert (await overrides_get_db.scalars(select(Otp))).all() == [generate_test_otp]


@pytest.mark.asyncio
async def test_set_password_otp_expired(overrides_get_db, anon_client, generate_test_otp, mocker):
    mocker.patch("src.apps.users.router.get_otp_by_email", return_value=generate_test_otp)

    fake_now = datetime.now() + timedelta(hours=1)
    mocker.patch("src.apps.auth.services.datetime", wraps=datetime)
    mocker.patch("src.apps.auth.services.datetime.now", return_value=fake_now)

    request_data = {
        "email": "testuser@gmail.com",
        "otp_code": "123456",
        "new_password": "@userNewPassword1",
        "confirm_password": "@userNewPassword1"
    }
    response = await anon_client.post("/users/profile/password/set", json=request_data)

    assert response.status_code == 403
    assert (await overrides_get_db.scalars(select(Otp))).all() == [generate_test_otp]


@pytest.mark.asyncio
async def test_set_password_otp_code_invalid(overrides_get_db, anon_client, generate_test_otp, mocker):
    mocker.patch("src.apps.users.router.get_otp_by_email", return_value=generate_test_otp)

    fake_now = datetime.now()
    mocker.patch("src.apps.auth.services.datetime", wraps=datetime)
    mocker.patch("src.apps.auth.services.datetime.now", return_value=fake_now)

    request_data = {
        "email": "testuser@gmail.com",
        "otp_code": "123457",
        "new_password": "@userNewPassword1",
        "confirm_password": "@userNewPassword1"
    }
    response = await anon_client.post("/users/profile/password/set", json=request_data)

    assert response.status_code == 403
    assert (await overrides_get_db.scalars(select(Otp))).all() == [generate_test_otp]


@pytest.mark.asyncio
async def test_change_password_success(overrides_get_db, user_auth_client, generate_test_user):
    request_data = {
        "old_password": "new@userPassword1",
        "new_password": "@userNewPassword1",
        "confirm_password": "@userNewPassword1"
    }
    response = await user_auth_client.post("/users/profile/password/change", json=request_data)

    await overrides_get_db.refresh(generate_test_user)

    assert response.status_code == 200
    assert generate_test_user.verify_password("@userNewPassword1")


@pytest.mark.asyncio
async def test_change_password_incorrect_password(overrides_get_db, user_auth_client, generate_test_user):
    request_data = {
        "old_password": "incor@userPassword1",
        "new_password": "@userNewPassword1",
        "confirm_password": "@userNewPassword1"
    }
    response = await user_auth_client.post("/users/profile/password/change", json=request_data)

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_change_password_missing_authentication_token(anon_client):
    request_data = {
        "old_password": "new@userpassword1",
        "new_password": "@userNewPassword1",
        "confirm_password": "@userNewPassword1"
    }
    response = await anon_client.post("/users/profile/password/change", json=request_data)

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_change_password_inactive_user(anon_client, inactive_user_client):
    request_data = {
        "old_password": "new@userPassword1",
        "new_password": "@userNewPassword1",
        "confirm_password": "@userNewPassword1"
    }
    response = await inactive_user_client.post("/users/profile/password/change", json=request_data)

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_change_password_passwords_does_not_match(overrides_get_db, user_auth_client):
    request_data = {
        "old_password": "new@userPassword1",
        "new_password": "@userNewPassword1",
        "confirm_password": "@userNewPassword2"
    }

    response = await user_auth_client.post("/users/profile/password/change", json=request_data)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_user_update_profile_without_email_success(overrides_get_db, generate_test_user, user_auth_client):
    response = await user_auth_client.put("/users/profile/update", json={"username": "updatedusername"})
    await overrides_get_db.refresh(generate_test_user)

    assert response.status_code == 200
    assert generate_test_user.username == "updatedusername"


@pytest.mark.asyncio
async def test_user_update_profile_with_email(overrides_get_db, generate_test_user, user_auth_client, mocker):
    mock_generate_otp = mocker.patch("src.apps.auth.services.generate_otp")
    mock_generate_otp.return_value = (mocker.ANY, "123456", "hashed_code", True, datetime.now() + timedelta(minutes=2))

    mock_send_otp_task = mocker.patch("src.apps.auth.services.send_otp_code_email", return_value=None)
    mock_send_otp_task.delay = mocker.MagicMock()

    request_data = {
        "username": "updatedusername",
        "email": "updatedemail@gmail.com"
    }
    response = await user_auth_client.put("/users/profile/update", json=request_data)

    await overrides_get_db.refresh(generate_test_user)

    assert response.status_code == 200
    assert generate_test_user.email == "updatedemail@gmail.com"
    assert generate_test_user.username == "updatedusername"
    assert not generate_test_user.is_active


@pytest.mark.asyncio
async def test_user_update_profile_missing_authentication_token(anon_client):
    response = await anon_client.put("/users/profile/update", json={"username": "updatedusername"})

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_user_update_profile_inactive_user(generate_inactive_user, inactive_user_client):
    response = await inactive_user_client.put("/users/profile/update", json={"username": "updatedusername"})

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_user_update_profile_username_email_already_exists(
        generate_inactive_user,
        generate_test_user,
        user_auth_client
):
    response = await user_auth_client.put("/users/profile/update", json={"email": "inactiveuser@gmail.com"})

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_activate_user_success(
        overrides_get_db,
        generate_test_otp,
        anon_client,
        generate_inactive_user,
        mocker
):
    mock_get_otp = mocker.patch("src.apps.users.router.get_otp_by_email", return_value=generate_test_otp)

    mock_otp_validator = mocker.patch("src.apps.users.router.is_otp_valid", return_value=True)

    request_data = {
        "email": "inactiveuser@gmail.com",
        "otp_code": "123456"
    }
    response = await anon_client.post("/users/profile/activate", json=request_data)

    await overrides_get_db.refresh(generate_inactive_user)

    mock_get_otp.assert_called_once_with(mocker.ANY, "inactiveuser@gmail.com")
    mock_otp_validator.assert_called_once_with("123456", generate_test_otp)

    assert response.status_code == 200
    assert generate_inactive_user.is_active


@pytest.mark.asyncio
async def test_activate_user_otp_expired(
        overrides_get_db,
        generate_test_otp,
        anon_client,
        mocker
):
    mocker.patch("src.apps.auth.router.get_otp_by_email", return_value=generate_test_otp)

    fake_now = datetime.now() + timedelta(hours=1)
    mocker.patch("src.apps.auth.services.datetime", wraps=datetime)
    mocker.patch("src.apps.auth.services.datetime.now", return_value=fake_now)

    request_data = {
        "email": "testuser@gmail.com",
        "otp_code": "123456"
    }
    response = await anon_client.post("/users/profile/activate", json=request_data)

    assert response.status_code == 403
    assert (await overrides_get_db.scalars(select(Otp))).all() == [generate_test_otp]


@pytest.mark.asyncio
async def test_activate_user_otp_invalid(
        overrides_get_db,
        generate_test_otp,
        anon_client,
        mocker
):
    mocker.patch("src.apps.users.router.get_otp_by_email", return_value=generate_test_otp)

    fake_now = datetime.now()
    mocker.patch("src.apps.auth.services.datetime", wraps=datetime)
    mocker.patch("src.apps.auth.services.datetime.now", return_value=fake_now)

    request_data = {
        "email": "testuser@gmail.com",
        "otp_code": "123457"
    }
    response = await anon_client.post("/users/profile/activate", json=request_data)

    assert response.status_code == 403
    assert (await overrides_get_db.scalars(select(Otp))).all() == [generate_test_otp]


@pytest.mark.asyncio
async def test_delete_user_account_success(overrides_get_db, generate_test_user, user_auth_client):
    response = await user_auth_client.delete("/users/profile/delete")

    assert response.status_code == 204
    assert (
               await overrides_get_db.scalars(select(User).where(User.email == "testuser@gmail.com"))
           ).one_or_none() is None


@pytest.mark.asyncio
async def test_delete_user_account_missing_authentication_token(overrides_get_db, anon_client):
    response = await anon_client.delete("/users/profile/delete")

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_user_account_inactive_user(generate_inactive_user, inactive_user_client):
    response = await inactive_user_client.delete("/users/profile/delete")

    assert response.status_code == 401
