import logging
from models.items import Item
from services.ml_model import get_prediction
from repositories.advertisements import AdvertisementRepository

logger = logging.getLogger(__name__)

class ItemsService:
    def __init__(self):
        self.ad_repository = AdvertisementRepository()
    
    async def predict(self, item: Item) -> tuple[bool, float]:
        logger.info(f"Predicting for seller_id={item.seller_id}, item_id={item.item_id}")
        
        feat_verified = 1.0 if item.is_verified_seller else 0.0
        feat_images = min(item.images_qty, 10) / 10.0 
        feat_desc_len = len(item.description) / 1000.0
        feat_category = item.category / 100.0
        
        features = [feat_verified, feat_images, feat_desc_len, feat_category]
        logger.info(f"Features: {features}")
        
        is_violation, probability = get_prediction(features)
        
        logger.info(f"Prediction result: is_violation={is_violation}, probability={probability}")
        
        return is_violation, probability
    
    async def predict_by_id(self, advertisement_id: int) -> tuple[bool, float]:
        logger.info(f"Predicting for advertisement_id={advertisement_id}")
        
        ad_with_user = await self.ad_repository.get_with_user(advertisement_id)
        
        if ad_with_user is None:
            raise ValueError(f"Advertisement with id {advertisement_id} not found")
        
        item = Item(
            seller_id=ad_with_user.user_id,
            is_verified_seller=ad_with_user.is_verified_seller,
            item_id=ad_with_user.id,
            name=ad_with_user.name,
            description=ad_with_user.description,
            category=ad_with_user.category,
            images_qty=ad_with_user.images_qty
        )
        
        return await self.predict(item)
