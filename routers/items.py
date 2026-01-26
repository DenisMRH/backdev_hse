from fastapi import APIRouter, status
from starlette.status import HTTP_200_OK
from models.items import Item
from services.items import ItemsService


router = APIRouter()
item_service = ItemsService()

@router.post("/predict", status_code=status.HTTP_200_OK)
async def predict(item: Item) -> bool:        
    return await item_service.predict(item)