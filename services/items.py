import logging
from models.items import Item
from services.ml_model import get_prediction

logger = logging.getLogger(__name__)

class ItemsService:
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
