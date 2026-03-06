import asyncio
import json
import logging
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from aiokafka import AIOKafkaConsumer
from services.ml_model import build_features, get_prediction, ModelNotLoadedError
from repositories.advertisements import AdvertisementRepository
from repositories.moderation_results import ModerationResultRepository
from app.clients.kafka import KafkaProducerClient, MODERATION_TOPIC, MODERATION_DLQ_TOPIC
from app.observability import PrometheusMetricsRecorder
from database import Database
from services.ports.metrics import get_metrics_recorder, set_metrics_recorder

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5

async def process_message(
    message_value: dict,
    ad_repo: AdvertisementRepository,
    mod_repo: ModerationResultRepository,
    kafka: KafkaProducerClient,
) -> None:
    item_id = message_value.get("item_id")
    task_id = message_value.get("task_id")
    if item_id is None or task_id is None:
        logger.error("Invalid message: missing item_id or task_id")
        return

    ad_with_user = await ad_repo.get_with_user(item_id)
    if ad_with_user is None:
        error_msg = f"Advertisement with id {item_id} not found"
        logger.warning(error_msg)
        await kafka.send_to_dlq(message_value, error_msg, retry_count=1)
        try:
            await mod_repo.set_failed(task_id, error_msg)
        except Exception as e:
            logger.warning("set_failed failed after sending to DLQ: %s", e)
        return

    last_error = None
    recorder = get_metrics_recorder()
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            features = build_features(ad_with_user)
            start = time.perf_counter()
            is_violation, probability = get_prediction(features)
            elapsed = time.perf_counter() - start
            recorder.observe_prediction_inference(inference_seconds=elapsed)

            result_label = "violation" if is_violation else "no_violation"
            recorder.record_prediction_result(result=result_label)
            recorder.observe_prediction_probability(probability=probability)

            await mod_repo.set_completed(task_id, is_violation, probability)
            logger.info(f"Task {task_id} completed: is_violation={is_violation}, probability={probability}")
            return
        except ModelNotLoadedError as e:
            last_error = str(e)
            recorder.record_prediction_error(error_type="model_unavailable")
            logger.warning(f"Attempt {attempt}/{MAX_RETRIES}: Model not loaded")
        except Exception as e:
            last_error = str(e)
            recorder.record_prediction_error(error_type="prediction_error")
            logger.warning(f"Attempt {attempt}/{MAX_RETRIES}: {e}", exc_info=True)

        if attempt < MAX_RETRIES:
            delay_seconds = RETRY_DELAY_SECONDS * (2 ** (attempt - 1))
            logger.info(f"Retrying in {delay_seconds} seconds...")
            await asyncio.sleep(delay_seconds)

    error_msg = last_error or "Unknown error after retries"
    await mod_repo.set_failed(task_id, error_msg)
    await kafka.send_to_dlq(message_value, error_msg, retry_count=MAX_RETRIES)
    logger.error(f"Task {task_id} failed after {MAX_RETRIES} attempts: {error_msg}")


async def run_worker() -> None:
    set_metrics_recorder(PrometheusMetricsRecorder())

    db = Database()
    await db.initialize()

    bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    consumer = AIOKafkaConsumer(
        MODERATION_TOPIC,
        bootstrap_servers=bootstrap,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        group_id="moderation-worker-group",
    )
    await consumer.start()

    kafka = KafkaProducerClient()
    await kafka.start()

    ad_repo = AdvertisementRepository()
    mod_repo = ModerationResultRepository()

    logger.info(f"Moderation worker started, consuming from {MODERATION_TOPIC}")

    try:
        async for msg in consumer:
            try:
                value = msg.value
                if not isinstance(value, dict):
                    logger.error("Unexpected message value type: %s", type(value))
                    continue
                await process_message(value, ad_repo, mod_repo, kafka)
            except Exception as e:
                logger.exception("Error processing message: %s", e)
    finally:
        await consumer.stop()
        await kafka.stop()
        await db.close()
        logger.info("Moderation worker stopped")


def main() -> None:
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
