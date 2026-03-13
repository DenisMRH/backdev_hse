import pytest
from database import Database
from models.domain import AccountCreate
from repositories.accounts import AccountRepository


@pytest.fixture
async def db():
    database = Database()
    await database.initialize()
    async with database.get_connection() as conn:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS account (
                id SERIAL PRIMARY KEY,
                login TEXT NOT NULL,
                password TEXT NOT NULL,
                is_blocked BOOLEAN NOT NULL DEFAULT FALSE
            )
            """
        )
        await conn.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_account_login ON account(login)
            """
        )
    yield database
    await database.close()


@pytest.fixture
async def account_repo(db):
    return AccountRepository()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_account_repository_create_and_get_by_id(db, account_repo):
    data = AccountCreate(login="alice", password="pass1")
    created = await account_repo.create(data)
    assert created.id is not None
    assert created.login == "alice"
    assert created.is_blocked is False

    fetched = await account_repo.get_by_id(created.id)
    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.login == created.login

    await account_repo.delete(created.id)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_account_repository_get_by_login_password(db, account_repo):
    data = AccountCreate(login="bob", password="secret")
    created = await account_repo.create(data)
    found = await account_repo.get_by_login_password("bob", "secret")
    assert found is not None
    assert found.id == created.id
    assert found.login == "bob"

    wrong = await account_repo.get_by_login_password("bob", "wrong")
    assert wrong is None

    await account_repo.delete(created.id)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_account_repository_delete(db, account_repo):
    data = AccountCreate(login="del_user", password="p")
    created = await account_repo.create(data)
    deleted = await account_repo.delete(created.id)
    assert deleted is True
    assert await account_repo.get_by_id(created.id) is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_account_repository_block(db, account_repo):
    data = AccountCreate(login="block_user", password="p")
    created = await account_repo.create(data)
    assert created.is_blocked is False

    blocked = await account_repo.block(created.id)
    assert blocked is True
    updated = await account_repo.get_by_id(created.id)
    assert updated is not None
    assert updated.is_blocked is True

    await account_repo.delete(created.id)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_account_password_stored_hashed(db, account_repo):
    data = AccountCreate(login="hash_user", password="plaintext")
    created = await account_repo.create(data)
    assert created.password != "plaintext"
    assert len(created.password) == 32

    found = await account_repo.get_by_login_password("hash_user", "plaintext")
    assert found is not None
    assert found.id == created.id

    await account_repo.delete(created.id)
