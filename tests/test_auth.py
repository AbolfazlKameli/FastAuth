from datetime import datetime, timedelta

import pytest
from fastapi import HTTPException

from src.apps.auth.services import create_jwt_token


@pytest.mark.asyncio
async def test_request_otp_to_register_success(anon_client, mocker):
    mock_generate_otp = mocker.patch("src.apps.auth.services.generate_otp")
    mock_generate_otp.return_value = (mocker.ANY, "123456", "hashed_code", True, datetime.now() + timedelta(minutes=2))

    mock_send_otp_task = mocker.patch("src.apps.auth.services.send_otp_code_email", return_value=None)
    mock_send_otp_task.delay = mocker.MagicMock()

    response = await anon_client.post("/auth/register", json={"email": "newuser@gmail.com"})

    mock_generate_otp.assert_called_once_with(mocker.ANY, "newuser@gmail.com")
    mock_send_otp_task.delay.assert_called_once_with("newuser@gmail.com", "123456")

    assert response.status_code == 202


@pytest.mark.asyncio
async def test_request_otp_to_register_too_many_requests(anon_client, mocker):
    mocker.patch("src.apps.auth.router.check_blacklist_for_user", return_value=None)

    mock_generate_and_send_otp = mocker.patch("src.apps.auth.router.generate_and_send_otp")
    mock_generate_and_send_otp.side_effect = HTTPException(
        status_code=429,
        detail="Too many requests. Your email has been added to the blacklist."
    )

    response = await anon_client.post("/auth/register", json={"email": "newuser@gmail.com"})

    mock_generate_and_send_otp.assert_called_once_with(mocker.ANY, "newuser@gmail.com")

    assert response.status_code == 429


@pytest.mark.asyncio
async def test_request_otp_to_register_blacklisted_with_time(anon_client, mocker):
    mock_blacklist_checker = mocker.patch("src.apps.auth.router.check_blacklist_for_user")
    mock_blacklist_checker.return_value = f"You have benn blocked until f{datetime.now()}"

    response = await anon_client.post("/auth/register", json={"email": "newuser@gmail.com"})

    mock_blacklist_checker.assert_called_once_with(mocker.ANY, "newuser@gmail.com")

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_request_otp_to_register_permanently_blacklisted(anon_client, mocker):
    mock_blacklist_checker = mocker.patch("src.apps.auth.router.check_blacklist_for_user")
    mock_blacklist_checker.return_value = ("You have been permanently blocked. if you believe this is a mistake,"
                                           " please contact support.")

    response = await anon_client.post("/auth/register", json={"email": "newuser@gmail.com"})

    mock_blacklist_checker.assert_called_once_with(mocker.ANY, "newuser@gmail.com")

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_request_otp_to_register_email_already_exists(anon_client, mocker):
    mock_email_checker = mocker.patch("src.apps.auth.router.check_email_exists", return_value=True)

    response = await anon_client.post("/auth/register", json={"email": "newuser@gmail.com"})

    mock_email_checker.assert_called_once_with(mocker.ANY, "newuser@gmail.com")

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_verify_otp_code_success(anon_client, generate_test_otp, mocker):
    mock_get_otp = mocker.patch("src.apps.auth.router.get_otp_by_email", return_value=generate_test_otp)

    mock_otp_validator = mocker.patch("src.apps.auth.router.is_otp_valid", return_value=True)

    request_data = {
        "email": "newuser@gmail.com",
        "username": "newuser",
        "password": "new@userPassword1",
        "confirm_password": "new@userPassword1",
        "otp_code": "123456",
    }
    response = await anon_client.post("/auth/register/verify", json=request_data)

    mock_get_otp.assert_called_once_with(mocker.ANY, "newuser@gmail.com")
    mock_otp_validator.assert_called_once_with("123456", generate_test_otp)

    assert response.status_code == 201
    assert response.json()["data"]["user"]["email"] == "newuser@gmail.com"


@pytest.mark.asyncio
async def test_verify_otp_code_expired(anon_client, generate_test_otp, mocker):
    mocker.patch("src.apps.auth.router.get_otp_by_email", return_value=generate_test_otp)

    fake_now = datetime.now() + timedelta(hours=1)
    mocker.patch("src.apps.auth.services.datetime", wraps=datetime)
    mocker.patch("src.apps.auth.services.datetime.now", return_value=fake_now)

    request_data = {
        "email": "newuser@gmail.com",
        "username": "newuser",
        "password": "new@userPassword1",
        "confirm_password": "new@userPassword1",
        "otp_code": "123456",
    }
    response = await anon_client.post("/auth/register/verify", json=request_data)

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_verify_otp_code_invalid(anon_client, generate_test_otp, mocker):
    mocker.patch("src.apps.auth.router.get_otp_by_email", return_value=generate_test_otp)

    fake_now = datetime.now()
    mocker.patch("src.apps.auth.services.datetime", wraps=datetime)
    mocker.patch("src.apps.auth.services.datetime.now", return_value=fake_now)

    request_data = {
        "email": "newuser@gmail.com",
        "username": "newuser",
        "password": "new@userPassword1",
        "confirm_password": "new@userPassword1",
        "otp_code": "123457",
    }
    response = await anon_client.post("/auth/register/verify", json=request_data)

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_verify_otp_code_user_already_exists(anon_client, generate_test_otp, mocker):
    mocker.patch("src.apps.auth.router.get_otp_by_email", return_value=generate_test_otp)

    mock_otp_validator = mocker.patch("src.apps.auth.router.is_otp_valid", return_value=True)

    request_data = {
        "email": "newuser@gmail.com",
        "username": "testuser",  # This username is already taken.
        "password": "new@userPassword1",
        "confirm_password": "new@userPassword1",
        "otp_code": "123456",
    }
    response = await anon_client.post("/auth/register/verify", json=request_data)

    mock_otp_validator.assert_called_once_with("123456", generate_test_otp)

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_user_login_success(anon_client, generate_test_user):
    request_data = {
        "email": "testuser@gmail.com",
        "password": "new@userPassword1"
    }

    response = await anon_client.post("/auth/login", json=request_data)

    assert response.status_code == 200
    assert "access_token" in response.json()["data"]
    assert "refresh_auth" in response.cookies


@pytest.mark.asyncio
async def test_user_login_incorrect_email_or_password(anon_client):
    request_data = {
        "email": "incorrect@gmail.com",
        "password": "Incorrect@1"
    }

    response = await anon_client.post("/auth/login", json=request_data)

    assert response.status_code == 400
    assert "access_token" not in response.json()["data"]
    assert "refresh_auth" not in response.cookies


@pytest.mark.asyncio
async def test_refresh_token_success(anon_client, generate_test_user):
    refresh_token = create_jwt_token(
        generate_test_user.id,
        generate_test_user.email,
        "refresh",
        expires_at=timedelta(hours=24)
    )

    response = await anon_client.post("/auth/refresh", json={"refresh_token": refresh_token})

    assert response.status_code == 200
    assert "access_token" in response.json()["data"]
    assert "refresh_auth" in response.cookies


@pytest.mark.asyncio
async def test_refresh_token_invalid_user(anon_client):
    refresh_token = create_jwt_token(
        1873,
        "doesnotexists@gmail.com",
        "refresh",
        expires_at=timedelta(hours=24)
    )

    response = await anon_client.post("/auth/refresh", json={"refresh_token": refresh_token})

    assert response.status_code == 401
    assert response.json() == {'data': {'errors': 'Authentication failed, invalid user.'}}


@pytest.mark.asyncio
async def test_refresh_token_invalid_token_type(anon_client, generate_test_user):
    refresh_token = create_jwt_token(
        generate_test_user.id,
        generate_test_user.email,
        "access",
        expires_at=timedelta(hours=24)
    )

    response = await anon_client.post("/auth/refresh", json={"refresh_token": refresh_token})

    assert response.status_code == 401
    assert response.json() == {'data': {'errors': 'Authentication failed, invalid token type.'}}


@pytest.mark.asyncio
async def test_refresh_token_expired_token(anon_client, generate_test_user):
    refresh_token = create_jwt_token(
        generate_test_user.id,
        generate_test_user.email,
        "access",
        expires_at=timedelta(hours=-24)
    )

    response = await anon_client.post("/auth/refresh", json={"refresh_token": refresh_token})

    assert response.status_code == 401
    assert response.json() == {'data': {'errors': 'Authentication failed, invalid or expired token.'}}


@pytest.mark.asyncio
async def test_refresh_token_inactive_user(anon_client, generate_inactive_user):
    refresh_token = create_jwt_token(
        generate_inactive_user.id,
        generate_inactive_user.email,
        "refresh",
        expires_at=timedelta(hours=24)
    )

    response = await anon_client.post("/auth/refresh", json={"refresh_token": refresh_token})

    assert response.status_code == 401
    assert response.json() == {'data': {'errors': 'Invalid refresh token.'}}


@pytest.mark.asyncio
async def test_refresh_token_blocked_refresh(anon_client, generate_test_user, mocker):
    mock_get_or_create = mocker.patch("src.apps.auth.router.get_or_create")
    mock_get_or_create.return_value = (mocker.ANY, False)

    refresh_token = create_jwt_token(
        generate_test_user.id,
        generate_test_user.email,
        "refresh",
        expires_at=timedelta(hours=24)
    )

    response = await anon_client.post("/auth/refresh", json={"refresh_token": refresh_token})

    assert response.status_code == 403
    assert response.json() == {'data': {'errors': 'Blocked refresh token.'}}
