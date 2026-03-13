import hashlib
from typing import Optional

from database import Database


def _hash_password(password: str) -> str:
    return hashlib.md5(password.encode("utf-8")).hexdigest()


class AccountStorage:
    def __init__(self):
        self.db = Database()

    async def create(self, login: str, password: str) -> dict:
        hashed = _hash_password(password)
        async with self.db.get_connection() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO account (login, password, is_blocked)
                VALUES ($1, $2, FALSE)
                RETURNING id, login, password, is_blocked
                """,
                login,
                hashed,
            )
            return dict(row)

    async def get_by_id(self, account_id: int) -> Optional[dict]:
        async with self.db.get_connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, login, password, is_blocked
                FROM account
                WHERE id = $1
                """,
                account_id,
            )
            return dict(row) if row else None

    async def delete(self, account_id: int) -> bool:
        async with self.db.get_connection() as conn:
            result = await conn.execute(
                """
                DELETE FROM account
                WHERE id = $1
                """,
                account_id,
            )
            return result.split()[-1] == "1"

    async def block(self, account_id: int) -> bool:
        async with self.db.get_connection() as conn:
            result = await conn.execute(
                """
                UPDATE account
                SET is_blocked = TRUE
                WHERE id = $1
                """,
                account_id,
            )
            return result.split()[-1] == "1"

    async def get_by_login_password(self, login: str, password: str) -> Optional[dict]:
        hashed = _hash_password(password)
        async with self.db.get_connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, login, password, is_blocked
                FROM account
                WHERE login = $1 AND password = $2
                """,
                login,
                hashed,
            )
            return dict(row) if row else None
