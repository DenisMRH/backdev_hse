import pytest

from services.auth import AuthService


@pytest.mark.asyncio
async def test_create_token_returns_non_empty_string():
    service = AuthService(secret="test-secret")
    token = service.create_token(account_id=42)
    assert isinstance(token, str)
    assert len(token) > 0


@pytest.mark.asyncio
async def test_verify_token_returns_account_id():
    service = AuthService(secret="test-secret")
    token = service.create_token(account_id=100)
    account_id = service.verify_token(token)
    assert account_id == 100


@pytest.mark.asyncio
async def test_verify_token_invalid_returns_none():
    service = AuthService(secret="test-secret")
    assert service.verify_token("invalid.jwt.token") is None
    assert service.verify_token("") is None


@pytest.mark.asyncio
async def test_verify_token_wrong_secret_returns_none():
    service1 = AuthService(secret="secret-a")
    service2 = AuthService(secret="secret-b")
    token = service1.create_token(account_id=1)
    assert service2.verify_token(token) is None
