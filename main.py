import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from routers.items import router as items_router
from services.ml_model import ModelClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing ML Client...")
    try:
        ModelClient()
        logger.info("ML Client ready")
    except Exception as e:
        logger.error(f"Failed to initialize ML Client: {e}")

    yield

app = FastAPI(lifespan=lifespan)

app.include_router(items_router)