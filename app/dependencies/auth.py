from fastapi import Cookie, Depends, HTTPException, status

from models.domain import Account
from repositories.accounts import AccountRepository
from services.auth import AuthService


AUTH_COOKIE_NAME = "token"


async def get_current_account(
    token: str | None = Cookie(default=None, alias=AUTH_COOKIE_NAME),
) -> Account:
    if token is None or token == "":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    auth_service = AuthService()
    account_id = auth_service.verify_token(token)
    if account_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    repo = AccountRepository()
    account = await repo.get_by_id(account_id)
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account not found",
        )
    if account.is_blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is blocked",
        )
    return account
