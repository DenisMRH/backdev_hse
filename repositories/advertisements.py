from typing import Optional
import logging
from database import Database
from models.domain import Advertisement, AdvertisementCreate, AdvertisementWithUser

logger = logging.getLogger(__name__)


class AdvertisementRepository:
    
    def __init__(self):
        self.db = Database()
    
    async def create(self, ad_data: AdvertisementCreate) -> Advertisement:
        async with self.db.get_connection() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO advertisements (user_id, name, description, category, images_qty)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id, user_id, name, description, category, images_qty
                """,
                ad_data.user_id,
                ad_data.name,
                ad_data.description,
                ad_data.category,
                ad_data.images_qty
            )
            logger.info(f"Advertisement created: id={row['id']}, user_id={row['user_id']}")
            return Advertisement(
                id=row['id'],
                user_id=row['user_id'],
                name=row['name'],
                description=row['description'],
                category=row['category'],
                images_qty=row['images_qty']
            )
    
    async def get_by_id(self, ad_id: int) -> Optional[Advertisement]:
        async with self.db.get_connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, user_id, name, description, category, images_qty
                FROM advertisements
                WHERE id = $1
                """,
                ad_id
            )
            if row is None:
                return None
            return Advertisement(
                id=row['id'],
                user_id=row['user_id'],
                name=row['name'],
                description=row['description'],
                category=row['category'],
                images_qty=row['images_qty']
            )
    
    async def get_with_user(self, ad_id: int) -> Optional[AdvertisementWithUser]:
        async with self.db.get_connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT 
                    a.id, a.user_id, a.name, a.description, a.category, a.images_qty,
                    u.is_verified as is_verified_seller
                FROM advertisements a
                JOIN users u ON a.user_id = u.id
                WHERE a.id = $1
                """,
                ad_id
            )
            if row is None:
                return None
            return AdvertisementWithUser(
                id=row['id'],
                user_id=row['user_id'],
                name=row['name'],
                description=row['description'],
                category=row['category'],
                images_qty=row['images_qty'],
                is_verified_seller=row['is_verified_seller']
            )
    
    async def delete(self, ad_id: int) -> bool:
        async with self.db.get_connection() as conn:
            result = await conn.execute(
                """
                DELETE FROM advertisements
                WHERE id = $1
                """,
                ad_id
            )
            deleted = result.split()[-1] == "1"
            if deleted:
                logger.info(f"Advertisement deleted: id={ad_id}")
            return deleted
