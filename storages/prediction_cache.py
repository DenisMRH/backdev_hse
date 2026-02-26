import json
from typing import Optional

import redis.exceptions
from app.clients.redis_client import RedisClient


PREDICTION_AD_TTL = 3600
MODERATION_RESULT_TTL = 86400


class PredictionCacheStorage:
    def __init__(self):
        self.redis = RedisClient()

    def _ad_key(self, advertisement_id: int) -> str:
        return f"prediction:ad:{advertisement_id}"

    def _moderation_key(self, task_id: int) -> str:
        return f"moderation_result:{task_id}"

    async def get_prediction_by_ad(self, advertisement_id: int) -> Optional[tuple[bool, float]]:
        if not self.redis.is_connected():
            return None
        try:
            key = self._ad_key(advertisement_id)
            data = await self.redis.client.get(key)
            if data is None:
                return None
            obj = json.loads(data)
            return obj["is_violation"], obj["probability"]
        except redis.exceptions.ConnectionError:
            return None

    async def set_prediction_by_ad(
        self, advertisement_id: int, is_violation: bool, probability: float
    ) -> None:
        if not self.redis.is_connected():
            return
        try:
            key = self._ad_key(advertisement_id)
            value = json.dumps({"is_violation": is_violation, "probability": probability})
            await self.redis.client.setex(key, PREDICTION_AD_TTL, value)
        except redis.exceptions.ConnectionError:
            pass

    async def delete_prediction_by_ad(self, advertisement_id: int) -> None:
        if not self.redis.is_connected():
            return
        try:
            await self.redis.client.delete(self._ad_key(advertisement_id))
        except redis.exceptions.ConnectionError:
            pass

    async def get_moderation_result(self, task_id: int) -> Optional[dict]:
        if not self.redis.is_connected():
            return None
        try:
            key = self._moderation_key(task_id)
            data = await self.redis.client.get(key)
            if data is None:
                return None
            return json.loads(data)
        except redis.exceptions.ConnectionError:
            return None

    async def set_moderation_result(self, task_id: int, result: dict) -> None:
        if not self.redis.is_connected():
            return
        try:
            key = self._moderation_key(task_id)
            value = json.dumps(result)
            await self.redis.client.setex(key, MODERATION_RESULT_TTL, value)
        except redis.exceptions.ConnectionError:
            pass

    async def delete_moderation_result(self, task_id: int) -> None:
        if not self.redis.is_connected():
            return
        try:
            await self.redis.client.delete(self._moderation_key(task_id))
        except redis.exceptions.ConnectionError:
            pass

    async def delete_moderation_results_by_task_ids(self, task_ids: list[int]) -> None:
        if not self.redis.is_connected() or not task_ids:
            return
        try:
            keys = [self._moderation_key(tid) for tid in task_ids]
            await self.redis.client.delete(*keys)
        except redis.exceptions.ConnectionError:
            pass
