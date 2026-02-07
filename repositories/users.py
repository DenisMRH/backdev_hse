from typing import Optional
import logging
from database import Database
from models.domain import User, UserCreate

logger = logging.getLogger(__name__)


class UserRepository:
    
    def __init__(self):
        self.db = Database()
    
    async def create(self, user_data: UserCreate) -> User:
        async with self.db.get_connection() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO users (is_verified)
                VALUES ($1)
                RETURNING id, is_verified
                """,
                user_data.is_verified
            )
            logger.info(f"User created: id={row['id']}")
            return User(id=row['id'], is_verified=row['is_verified'])
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        async with self.db.get_connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, is_verified
                FROM users
                WHERE id = $1
                """,
                user_id
            )
            if row is None:
                return None
            return User(id=row['id'], is_verified=row['is_verified'])
    
    async def delete(self, user_id: int) -> bool:
        async with self.db.get_connection() as conn:
            result = await conn.execute(
                """
                DELETE FROM users
                WHERE id = $1
                """,
                user_id
            )
            deleted = result.split()[-1] == "1"
            if deleted:
                logger.info(f"User deleted: id={user_id}")
            return deleted
