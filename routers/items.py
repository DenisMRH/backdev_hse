from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from models.items import Item, PredictionResponse
from models.domain import ModerationResult
from services.items import ItemsService
from services.ml_model import ModelNotLoadedError
from repositories.moderation_results import ModerationResultRepository
from app.clients.kafka import KafkaProducerClient
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


class SimplePredictRequest(BaseModel):
    advertisement_id: int = Field(..., gt=0)


class AsyncPredictRequest(BaseModel):
    item_id: int = Field(..., gt=0)


def get_kafka(request: Request) -> KafkaProducerClient | None:
    return getattr(request.app.state, "kafka", None)


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


@router.post("/async_predict")
async def async_predict(
    request: AsyncPredictRequest,
    kafka: KafkaProducerClient | None = Depends(get_kafka),
) -> dict:
    if kafka is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Kafka is not available",
        )
    mod_repo = ModerationResultRepository()
    result = await mod_repo.create_pending(request.item_id)
    await kafka.send_moderation_request(request.item_id, result.id)
    return {
        "task_id": result.id,
        "status": "pending",
        "message": "Moderation request accepted",
    }


@router.get("/moderation_result/{task_id}")
async def get_moderation_result(task_id: int) -> dict:
    mod_repo = ModerationResultRepository()
    result = await mod_repo.get_by_id(task_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found",
        )
    response: dict = {
        "task_id": result.id,
        "status": result.status,
        "is_violation": result.is_violation,
        "probability": result.probability,
    }
    if result.status == "failed" and result.error_message:
        response["error_message"] = result.error_message
    return response
