import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.clients.kafka import KafkaProducerClient
from routers.items import router as items_router
from services.ml_model import ModelClient
from database import Database

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

    logger.info("Initializing Database...")
    try:
        db = Database()
        await db.initialize()
        logger.info("Database ready")
    except Exception as e:
        logger.error(f"Failed to initialize Database: {e}")

    logger.info("Initializing Kafka producer...")
    kafka = KafkaProducerClient()
    try:
        await kafka.start()
        app.state.kafka = kafka
        logger.info("Kafka producer ready")
    except Exception as e:
        logger.error(f"Failed to start Kafka producer: {e}")
        app.state.kafka = None

    yield

    try:
        if getattr(app.state, "kafka", None) is not None:
            logger.info("Stopping Kafka producer...")
            await kafka.stop()
        logger.info("Disconnecting from database...")
        await db.close()
        logger.info("Database disconnected")
    except (RuntimeError, AttributeError, ValueError) as e:
        err_msg = str(e).lower()
        cause_msg = str(e.__cause__).lower() if e.__cause__ else ""
        is_teardown_artifact = (
            "event loop is closed" in err_msg
            or "event loop is closed" in cause_msg
            or ("nonetype" in err_msg and "send" in err_msg)
            or ("future" in err_msg and "different loop" in err_msg)
        )
        if is_teardown_artifact:
            logger.debug("Shutdown skipped: event loop already closed or mixed loops (e.g. in test teardown)")
        else:
            raise


app = FastAPI(lifespan=lifespan)

app.include_router(items_router)