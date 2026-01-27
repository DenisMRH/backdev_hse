from fastapi import APIRouter, Depends, HTTPException, status
from models.items import Item, PredictionResponse
from services.items import ItemsService
from services.ml_model import ModelNotLoadedError
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/predict", response_model=PredictionResponse)
async def predict(
    item: Item, 
    service: ItemsService = Depends()
) -> PredictionResponse:
    try:
        is_violation, probability = await service.predict(item)
        return PredictionResponse(
            is_violation=is_violation, 
            probability=probability
        )
    except ModelNotLoadedError:
        logger.error("Model not loaded")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model is not loaded"
        )
    except Exception as e:
        logger.error(f"Prediction error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error"
        )
