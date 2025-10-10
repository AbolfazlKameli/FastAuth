from datetime import datetime, timedelta

import pytest
from fastapi import HTTPException


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
