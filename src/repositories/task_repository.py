from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from src.config import settings
from src.models.task import TaskModel
from src.repositories.base import BaseRepository
import logging

logger = logging.getLogger(__name__)


class TaskStatus:
    PENDING = "pending"
    PROCESSING = "processing"
    RETRY = "retry"
    DONE = "done"
    FAILED = "failed"


class TaskRepository(BaseRepository[TaskModel]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, TaskModel)

    async def create_task(
        self,
        task_type: str,
        payload: dict,
        max_attempts: Optional[int] = None,
    ) -> TaskModel:
        task = TaskModel(
            task_type=task_type,
            payload=payload,
            status=TaskStatus.PENDING,
            attempts=0,
            max_attempts=(
                max_attempts
                if max_attempts is not None
                else settings.bio_worker_max_attempts
            ),
        )
        self.db.add(task)
        await self.db.flush()
        await self.db.refresh(task)
        return task

    async def claim_pending_tasks(
        self,
        limit: int = 100,
        retry_backoff_seconds: int = 60,
        processing_timeout_seconds: int = 300,
    ) -> List[TaskModel]:
        now = datetime.now(timezone.utc)
        retry_threshold = now - timedelta(seconds=retry_backoff_seconds)
        processing_threshold = now - timedelta(seconds=processing_timeout_seconds)

        stmt = (
            select(TaskModel)
            .where(
                TaskModel.status.in_([
                    TaskStatus.PENDING,
                    TaskStatus.RETRY,
                    TaskStatus.PROCESSING,
                ]),
                TaskModel.attempts < TaskModel.max_attempts,
                (
                    (TaskModel.status == TaskStatus.PENDING)
                    | (
                        (TaskModel.status == TaskStatus.RETRY)
                        & (TaskModel.updated_at < retry_threshold)
                    )
                    | (
                        (TaskModel.status == TaskStatus.PROCESSING)
                        & (TaskModel.updated_at < processing_threshold)
                    )
                ),
            )
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        result = await self.db.execute(stmt)
        tasks = list(result.scalars().all())

        if not tasks:
            return []

        for task in tasks:
            attempt_id = uuid4()
            await self.db.execute(
                update(TaskModel)
                .where(TaskModel.id == task.id)
                .values(
                    status=TaskStatus.PROCESSING,
                    attempt_id=attempt_id,
                    updated_at=now,
                )
            )
            task.status = TaskStatus.PROCESSING
            task.attempt_id = attempt_id
            task.updated_at = now

        await self.db.flush()
        return tasks

    async def mark_done(self, task_id: UUID, attempt_id: UUID) -> bool:
        result = await self.db.execute(
            update(TaskModel)
            .where(
                TaskModel.id == task_id,
                TaskModel.attempt_id == attempt_id,
            )
            .values(
                status=TaskStatus.DONE,
                updated_at=datetime.now(timezone.utc),
                error=None,
            )
            .returning(TaskModel.id)
        )
        await self.db.flush()
        updated = result.scalar_one_or_none()
        if updated is None:
            logger.warning(
                "Task %s mark_done skipped: attempt_id mismatch or missing",
                task_id,
            )
        return updated is not None

    async def mark_retry(self, task_id: UUID, attempt_id: UUID, error: str) -> str:
        stmt = (
            select(TaskModel)
            .where(
                TaskModel.id == task_id,
                TaskModel.attempt_id == attempt_id,
            )
            .with_for_update()
        )
        result = await self.db.execute(stmt)
        task = result.scalar_one_or_none()
        if not task:
            logger.warning(
                "Task %s mark_retry skipped: attempt_id mismatch or missing",
                task_id,
            )
            return TaskStatus.FAILED

        task.attempts += 1
        now = datetime.now(timezone.utc)

        if task.attempts >= task.max_attempts:
            task.status = TaskStatus.FAILED
            logger.error(
                "Task %s failed after %s attempts: %s",
                task_id,
                task.attempts,
                error,
            )
        else:
            task.status = TaskStatus.RETRY
            logger.warning(
                "Task %s marked for retry (%s/%s): %s",
                task_id,
                task.attempts,
                task.max_attempts,
                error,
            )

        task.error = error
        task.updated_at = now
        await self.db.flush()
        return task.status

    async def mark_failed(self, task_id: UUID, attempt_id: UUID, error: str) -> bool:
        result = await self.db.execute(
            update(TaskModel)
            .where(
                TaskModel.id == task_id,
                TaskModel.attempt_id == attempt_id,
            )
            .values(
                status=TaskStatus.FAILED,
                attempts=TaskModel.attempts + 1,
                error=error,
                updated_at=datetime.now(timezone.utc),
            )
            .returning(TaskModel.id)
        )
        await self.db.flush()
        updated = result.scalar_one_or_none()
        if updated:
            logger.error("Task %s marked as failed: %s", task_id, error)
        else:
            logger.warning(
                "Task %s mark_failed skipped: attempt_id mismatch or missing",
                task_id,
            )
        return updated is not None

    async def get_by_status(
        self,
        status: str,
        limit: int = 100,
    ) -> List[TaskModel]:
        stmt = (
            select(TaskModel)
            .where(TaskModel.status == status)
            .order_by(TaskModel.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def cleanup_done(self, days: int = 7) -> int:
        threshold = datetime.now(timezone.utc) - timedelta(days=days)
        result = await self.db.execute(
            delete(TaskModel)
            .where(
                TaskModel.status.in_([TaskStatus.DONE, TaskStatus.FAILED]),
                TaskModel.updated_at < threshold,
            )
            .returning(TaskModel.id)
        )
        deleted_ids = list(result.scalars().all())
        await self.db.flush()
        return len(deleted_ids)
