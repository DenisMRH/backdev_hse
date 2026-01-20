from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    seller_id: int
    is_verified_seller: bool
    item_id: int
    name: str
    description: str
    category: int
    images_qty: int 

@app.post("/predict")
async def predict(item: Item) -> bool:
    if item.is_verified_seller:
        return True
    
    if item.images_qty > 0:
        return True
        
    return False
