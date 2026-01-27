import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from model import train_model, save_model
from routers.items import router as items_router
from services.ml_model import load_ml_model

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    model_path = "model.pkl"
    if not Path(model_path).exists():
        logger.info("Model not found. Training new model...")
        model = train_model()
        save_model(model, model_path)
        logger.info("Model trained and saved.")
    logger.info("Loading model...")
    load_ml_model(model_path)
    logger.info("Model loaded.")
    yield

app = FastAPI(lifespan=lifespan)

app.include_router(items_router)
