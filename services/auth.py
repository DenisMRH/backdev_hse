import os
from typing import Optional

import jwt

JWT_ALGORITHM = "HS256"
JWT_SUB_CLAIM = "sub"


class AuthService:
    def __init__(self, secret: Optional[str] = None):
        self._secret = secret or os.getenv("JWT_SECRET_KEY", "dev-secret-change-in-production")

    def create_token(self, account_id: int) -> str:
        payload = {JWT_SUB_CLAIM: str(account_id)}
        return jwt.encode(
            payload,
            self._secret,
            algorithm=JWT_ALGORITHM,
        )

    def verify_token(self, token: str) -> Optional[int]:
        try:
            payload = jwt.decode(
                token,
                self._secret,
                algorithms=[JWT_ALGORITHM],
            )
            sub = payload.get(JWT_SUB_CLAIM)
            if sub is None:
                return None
            return int(sub)
        except (jwt.InvalidTokenError, ValueError, TypeError):
            return None
