import pytest
from database import Database
from repositories.users import UserRepository
from repositories.advertisements import AdvertisementRepository
from repositories.moderation_results import ModerationResultRepository
from models.domain import UserCreate, AdvertisementCreate


@pytest.fixture
async def db():
    database = Database()
    await database.initialize()
    yield database
    await database.close()


@pytest.fixture
async def user_repo(db):
    return UserRepository()


@pytest.fixture
async def ad_repo(db):
    return AdvertisementRepository()


@pytest.fixture
async def mod_repo(db):
    return ModerationResultRepository()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_user_repository_create_and_get(db, user_repo):
    user_data = UserCreate(is_verified=True)
    created = await user_repo.create(user_data)
    assert created.id is not None
    assert created.is_verified is True

    fetched = await user_repo.get_by_id(created.id)
    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.is_verified == created.is_verified

    await user_repo.delete(created.id)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_advertisement_repository_create_get_delete(db, user_repo, ad_repo):
    user = await user_repo.create(UserCreate(is_verified=False))
    ad_data = AdvertisementCreate(
        user_id=user.id,
        name="Test Ad",
        description="Test description",
        category=1,
        images_qty=3,
    )
    created = await ad_repo.create(ad_data)
    assert created.id is not None
    assert created.name == "Test Ad"

    fetched = await ad_repo.get_by_id(created.id)
    assert fetched is not None
    assert fetched.name == created.name

    deleted = await ad_repo.delete(created.id)
    assert deleted is True

    after_delete = await ad_repo.get_by_id(created.id)
    assert after_delete is None

    await user_repo.delete(user.id)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_moderation_result_repository_workflow(db, ad_repo, mod_repo, user_repo):
    user = await user_repo.create(UserCreate(is_verified=True))
    ad = await ad_repo.create(AdvertisementCreate(
        user_id=user.id,
        name="Ad",
        description="Desc",
        category=1,
        images_qty=5,
    ))

    result = await mod_repo.create_pending(ad.id)
    assert result.id is not None
    assert result.status == "pending"
    assert result.item_id == ad.id

    await mod_repo.set_completed(result.id, True, 0.95)
    updated = await mod_repo.get_by_id(result.id)
    assert updated.status == "completed"
    assert updated.is_violation is True
    assert updated.probability == 0.95

    task_ids = await mod_repo.get_task_ids_by_item_id(ad.id)
    assert result.id in task_ids

    await mod_repo.delete_by_item_id(ad.id)
    await ad_repo.delete(ad.id)
    await user_repo.delete(user.id)
