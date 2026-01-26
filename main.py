from fastapi import FastAPI
from models.items import Item

app = FastAPI()

@app.post("/predict")
async def predict(item: Item) -> bool:
    if item.is_verified_seller:
        return True
    
    if item.images_qty > 0:
        return True
        
    return False
