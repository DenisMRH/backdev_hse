from typing import Optional

from models.domain import Account, AccountCreate
from storages.account_storage import AccountStorage


class AccountRepository:
    def __init__(self):
        self._storage = AccountStorage()

    async def create(self, data: AccountCreate) -> Account:
        row = await self._storage.create(data.login, data.password)
        return Account(
            id=row["id"],
            login=row["login"],
            password=row["password"],
            is_blocked=row["is_blocked"],
        )

    async def get_by_id(self, account_id: int) -> Optional[Account]:
        row = await self._storage.get_by_id(account_id)
        if row is None:
            return None
        return Account(
            id=row["id"],
            login=row["login"],
            password=row["password"],
            is_blocked=row["is_blocked"],
        )

    async def delete(self, account_id: int) -> bool:
        return await self._storage.delete(account_id)

    async def block(self, account_id: int) -> bool:
        return await self._storage.block(account_id)

    async def get_by_login_password(self, login: str, password: str) -> Optional[Account]:
        row = await self._storage.get_by_login_password(login, password)
        if row is None:
            return None
        return Account(
            id=row["id"],
            login=row["login"],
            password=row["password"],
            is_blocked=row["is_blocked"],
        )
