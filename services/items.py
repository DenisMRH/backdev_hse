import logging
import time

from models.items import Item
from services.ml_model import build_features, get_prediction
from repositories.advertisements import AdvertisementRepository
from storages.prediction_cache import PredictionCacheStorage
from services.ml_model import ModelNotLoadedError
from services.ports.metrics import get_metrics_recorder

logger = logging.getLogger(__name__)


class ItemsService:
    def __init__(self):
        self.ad_repository = AdvertisementRepository()
        self.cache = PredictionCacheStorage()
    
    async def predict(self, item: Item) -> tuple[bool, float]:
        logger.info(f"Predicting for seller_id={item.seller_id}, item_id={item.item_id}")

        features = build_features(item)
        logger.info(f"Features: {features}")
        
        recorder = get_metrics_recorder()
        start = time.perf_counter()
        try:
            is_violation, probability = get_prediction(features)
        except ModelNotLoadedError:
            recorder.record_prediction_error(error_type="model_unavailable")
            raise
        except Exception:
            recorder.record_prediction_error(error_type="prediction_error")
            raise
        elapsed = time.perf_counter() - start
        recorder.observe_prediction_inference(inference_seconds=elapsed)

        result_label = "violation" if is_violation else "no_violation"
        recorder.record_prediction_result(result=result_label)
        recorder.observe_prediction_probability(probability=probability)
        
        logger.info(f"Prediction result: is_violation={is_violation}, probability={probability}")
        
        return is_violation, probability
    
    async def predict_by_id(self, advertisement_id: int) -> tuple[bool, float]:
        cached = await self.cache.get_prediction_by_ad(advertisement_id)
        if cached is not None:
            is_violation, probability = cached
            recorder = get_metrics_recorder()
            result_label = "violation" if is_violation else "no_violation"
            recorder.record_prediction_result(result=result_label)
            recorder.observe_prediction_probability(probability=probability)
            return cached

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

        is_violation, probability = await self.predict(item)
        await self.cache.set_prediction_by_ad(advertisement_id, is_violation, probability)
        return is_violation, probability
