from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field

from app.dependencies.auth import AUTH_COOKIE_NAME, get_current_account
from models.domain import Account
from repositories.accounts import AccountRepository
from services.auth import AuthService

router = APIRouter()


class LoginRequest(BaseModel):
    login: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


@router.post("/login")
async def login(
    request: LoginRequest,
    response: Response,
) -> dict:
    repo = AccountRepository()
    account = await repo.get_by_login_password(request.login, request.password)
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid login or password",
        )
    if account.is_blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is blocked",
        )
    token = AuthService().create_token(account.id)
    response.set_cookie(
        key=AUTH_COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
    )
    return {"message": "OK"}


@router.get("/me", response_model=Account)
async def me(account: Account = Depends(get_current_account)) -> Account:
    return account
