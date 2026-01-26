

from typing import Any, Mapping
from models.items import Item


class ItemsService:
    async def predict(self, item: Item) -> bool:
        if item.is_verified_seller:
            return True
        
        if item.images_qty > 0:
            return True
            
        return False