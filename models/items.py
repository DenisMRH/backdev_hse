from pydantic import BaseModel

class Item(BaseModel):
    seller_id: int
    is_verified_seller: bool
    item_id: int
    name: str
    description: str
    category: int
    images_qty: int

class PredictionResponse(BaseModel):
    is_violation: bool
    probability: float
