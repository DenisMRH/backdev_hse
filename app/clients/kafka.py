import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

from aiokafka import AIOKafkaProducer
from aiokafka.admin import AIOKafkaAdminClient, NewTopic

logger = logging.getLogger(__name__)

MODERATION_TOPIC = "moderation"
MODERATION_DLQ_TOPIC = "moderation_dlq"


async def ensure_topics(bootstrap_servers: str) -> None:
    admin = AIOKafkaAdminClient(bootstrap_servers=bootstrap_servers)
    try:
        await admin.start()
        await admin.create_topics(
            new_topics=[
                NewTopic(name=MODERATION_TOPIC, num_partitions=1, replication_factor=1),
                NewTopic(name=MODERATION_DLQ_TOPIC, num_partitions=1, replication_factor=1),
            ],
            validate_only=False,
        )
        logger.info("Kafka topics ensured: %s, %s", MODERATION_TOPIC, MODERATION_DLQ_TOPIC)
    except Exception as e:
        if "TopicAlreadyExistsError" in type(e).__name__ or "already exists" in str(e).lower():
            logger.debug("Topics already exist: %s", e)
        else:
            logger.warning("Could not create topics (may already exist): %s", e)
    finally:
        await admin.close()


class KafkaProducerClient:
    _instance = None
    _producer: AIOKafkaProducer | None = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _bootstrap_servers(self) -> str:
        return os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

    async def start(self) -> None:
        if self._producer is not None:
            return
        bootstrap = self._bootstrap_servers()
        await ensure_topics(bootstrap)
        self._producer = AIOKafkaProducer(
            bootstrap_servers=bootstrap,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
        await self._producer.start()
        logger.info("Kafka producer started")

    async def stop(self) -> None:
        if self._producer is not None:
            await self._producer.stop()
            self._producer = None
            logger.info("Kafka producer stopped")

    async def send_moderation_request(self, item_id: int, task_id: int) -> None:
        if self._producer is None:
            await self.start()
        message = {
            "item_id": item_id,
            "task_id": task_id,
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        }
        await self._producer.send_and_wait(MODERATION_TOPIC, value=message)
        logger.info(f"Sent moderation request for item_id={item_id}, task_id={task_id} to topic {MODERATION_TOPIC}")

    async def send_to_dlq(
        self,
        original_message: dict[str, Any],
        error: str,
        retry_count: int = 1,
    ) -> None:
        if self._producer is None:
            await self.start()
        dlq_message = {
            "original_message": original_message,
            "error": error,
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "retry_count": retry_count,
        }
        await self._producer.send_and_wait(MODERATION_DLQ_TOPIC, value=dlq_message)
        logger.warning(f"Sent message to DLQ: error={error}, retry_count={retry_count}")
