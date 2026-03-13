import pytest
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient
from main import app
from app.dependencies.auth import get_current_account, AUTH_COOKIE_NAME
from models.domain import Account
from repositories.accounts import AccountRepository
from services.auth import AuthService


@pytest.fixture
def client_no_auth_override():
    with TestClient(app) as c:
        yield c


def test_login_success(client_no_auth_override, monkeypatch):
    account = Account(id=10, login="user1", password="hashed", is_blocked=False)

    async def mock_get_by_login_password(self, login, password):
        return account if login == "user1" and password == "secret" else None

    monkeypatch.setattr(AccountRepository, "get_by_login_password", mock_get_by_login_password)

    response = client_no_auth_override.post(
        "/login",
        json={"login": "user1", "password": "secret"},
    )
    assert response.status_code == 200
    assert "message" in response.json()
    assert AUTH_COOKIE_NAME in response.cookies
    token = response.cookies[AUTH_COOKIE_NAME]
    assert token
    auth = AuthService()
    assert auth.verify_token(token) == 10


def test_login_invalid_credentials(client_no_auth_override, monkeypatch):
    async def mock_get_by_login_password(self, login, password):
        return None

    monkeypatch.setattr(AccountRepository, "get_by_login_password", mock_get_by_login_password)

    response = client_no_auth_override.post(
        "/login",
        json={"login": "user1", "password": "wrong"},
    )
    assert response.status_code == 401
    assert "Invalid" in response.json()["detail"] or "invalid" in response.json()["detail"].lower()


def test_login_blocked_account(client_no_auth_override, monkeypatch):
    account = Account(id=5, login="blocked", password="x", is_blocked=True)

    async def mock_get_by_login_password(self, login, password):
        return account if login == "blocked" else None

    monkeypatch.setattr(AccountRepository, "get_by_login_password", mock_get_by_login_password)

    response = client_no_auth_override.post(
        "/login",
        json={"login": "blocked", "password": "p"},
    )
    assert response.status_code == 403
    assert "blocked" in response.json()["detail"].lower()


def test_me_requires_auth(client_no_auth_override):
    response = client_no_auth_override.get("/me")
    assert response.status_code == 401


def test_me_invalid_token_returns_401(client_no_auth_override):
    client_no_auth_override.cookies.set(AUTH_COOKIE_NAME, "invalid.jwt.token")
    response = client_no_auth_override.get("/me")
    assert response.status_code == 401


def test_me_returns_account_with_valid_token(client_no_auth_override, monkeypatch):
    account = Account(id=7, login="me_user", password="hash", is_blocked=False)

    async def mock_get_by_id(self, account_id):
        return account if account_id == 7 else None

    monkeypatch.setattr(AccountRepository, "get_by_id", mock_get_by_id)

    token = AuthService().create_token(7)
    client_no_auth_override.cookies.set(AUTH_COOKIE_NAME, token)
    response = client_no_auth_override.get("/me")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 7
    assert data["login"] == "me_user"
    assert data["is_blocked"] is False
