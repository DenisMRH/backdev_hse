import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.clients.kafka import KafkaProducerClient
from app.clients.redis_client import RedisClient
from app.observability import PrometheusMiddleware, PrometheusMetricsRecorder, metrics_router
from routers.auth import router as auth_router
from routers.items import router as items_router
from services.ml_model import ModelClient
from services.ports.metrics import set_metrics_recorder
from database import Database

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    set_metrics_recorder(PrometheusMetricsRecorder())

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

    logger.info("Initializing Redis...")
    redis_client = RedisClient()
    try:
        await redis_client.connect()
        app.state.redis = redis_client
        logger.info("Redis ready")
    except Exception as e:
        logger.error(f"Failed to connect Redis: {e}")
        app.state.redis = None

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
        if getattr(app.state, "redis", None) is not None:
            logger.info("Closing Redis...")
            await app.state.redis.close()
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

app.add_middleware(PrometheusMiddleware, exclude_paths={"/metrics"})

app.include_router(auth_router)
app.include_router(items_router)
app.include_router(metrics_router)