from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from models.items import Item, PredictionResponse
from services.items import ItemsService
from services.ml_model import ModelNotLoadedError
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


class SimplePredictRequest(BaseModel):
    advertisement_id: int = Field(..., gt=0, description="ID объявления")


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


@router.post("/simple_predict", response_model=PredictionResponse)
async def simple_predict(
    request: SimplePredictRequest,
    service: ItemsService = Depends()
) -> PredictionResponse:
    try:
        is_violation, probability = await service.predict_by_id(request.advertisement_id)
        return PredictionResponse(
            is_violation=is_violation, 
            probability=probability
        )
    except ValueError as e:
        logger.error(f"Advertisement not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
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
