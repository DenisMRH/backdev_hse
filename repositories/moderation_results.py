from typing import Optional

from database import Database
from models.domain import ModerationResult


class ModerationResultRepository:
    def __init__(self):
        self.db = Database()

    async def create_pending(self, item_id: int) -> ModerationResult:
        async with self.db.get_connection() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO moderation_results (item_id, status)
                VALUES ($1, 'pending')
                RETURNING id, item_id, status, is_violation, probability, error_message, created_at, processed_at
                """,
                item_id,
            )
            return self._row_to_model(row)

    async def get_by_id(self, task_id: int) -> Optional[ModerationResult]:
        async with self.db.get_connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, item_id, status, is_violation, probability, error_message, created_at, processed_at
                FROM moderation_results
                WHERE id = $1
                """,
                task_id,
            )
            if row is None:
                return None
            return self._row_to_model(row)

    async def set_completed(
        self, task_id: int, is_violation: bool, probability: float
    ) -> None:
        async with self.db.get_connection() as conn:
            await conn.execute(
                """
                UPDATE moderation_results
                SET status = 'completed', is_violation = $1, probability = $2, processed_at = NOW()
                WHERE id = $3
                """,
                is_violation,
                probability,
                task_id,
            )

    async def set_failed(self, task_id: int, error_message: str) -> None:
        async with self.db.get_connection() as conn:
            await conn.execute(
                """
                UPDATE moderation_results
                SET status = 'failed', error_message = $1, processed_at = NOW()
                WHERE id = $2
                """,
                error_message,
                task_id,
            )

    def _row_to_model(self, row) -> ModerationResult:
        return ModerationResult(
            id=row["id"],
            item_id=row["item_id"],
            status=row["status"],
            is_violation=row["is_violation"],
            probability=row["probability"],
            error_message=row["error_message"],
            created_at=row["created_at"],
            processed_at=row["processed_at"],
        )
