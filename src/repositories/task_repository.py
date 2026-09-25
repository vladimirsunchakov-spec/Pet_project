from typing import Optional, List
from uuid import UUID
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
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
        max_attempts: int = 5,
    ) -> TaskModel:
        task = TaskModel(
            task_type=task_type,
            payload=payload,
            status=TaskStatus.PENDING,
            attempts=0,
            max_attempts=max_attempts,
        )
        self.db.add(task)
        await self.db.flush()
        await self.db.refresh(task)

        logger.info(
            f"Created task {task.id} of type '{task_type}'"
        )
        return task

    async def claim_pending_tasks(
        self,
        limit: int = 100,
        retry_backoff_seconds: int = 60,
        processing_timeout_seconds: int = 300
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

        task_ids = [t.id for t in tasks]
        await self.db.execute(
            update(TaskModel)
            .where(TaskModel.id.in_(task_ids))
            .values(
                status=TaskStatus.PROCESSING,
                updated_at=now,
            )
        )
        await self.db.flush()

        for task in tasks:
            task.status = TaskStatus.PROCESSING
            task.updated_at = now
        logger.info(f"Claimed {len(tasks)} tasks: {task_ids}")
        return tasks

    async def mark_done(self, task_id: UUID) -> None:
        await self.db.execute(
            update(TaskModel)
            .where(TaskModel.id == task_id)
            .values(
                status=TaskStatus.DONE,
                updated_at=datetime.now(timezone.utc),
                error=None,
            )
        )
        await self.db.flush()
        logger.info(f"Task {task_id} marked as done")

    async def mark_retry(self, task_id: UUID, error: str) -> None:
        task = await self.get(task_id)
        if not task:
            logger.warning(f"Task {task_id} not found for retry")
            return

        task.attempts += 1
        now = datetime.now(timezone.utc)

        if task.attempts >= task.max_attempts:
            task.status = TaskStatus.FAILED
            logger.error(f"Task {task_id} failed after {task.attempts} attempts: {error}")
        else:
            task.status = TaskStatus.RETRY
            logger.warning(
                f"Task {task_id} marked for retry "
                f"(attempt {task.attempts}/{task.max_attempts}: {error})"
            )

        task.error = error
        task.updated_at = now
        await self.db.flush()

    async def mark_failed(self, task_id: UUID, error: str) -> None:
        await self.db.execute(
            update(TaskModel)
            .where(TaskModel.id == task_id)
            .values(
                status=TaskStatus.FAILED,
                attempts=TaskModel.attempts + 1,
                error=error,
                updated_at=datetime.now(timezone.utc),
            )
        )
        await self.db.flush()
        logger.error(f"Task {task_id} marked as failed: {error}")

    async def get_by_status(
        self,
        status: str,
        limit: int = 100
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
        stmt = (
            select(TaskModel)
            .where(
                TaskModel.status.in_([TaskStatus.DONE, TaskStatus.FAILED]),
                TaskModel.updated_at < threshold,
            )
        )
        result = await self.db.execute(stmt)
        tasks = list(result.scalars().all())

        for task in tasks:
            await self.db.delete(task)

        await self.db.flush()
        logger.info(f"Cleaned up {len(tasks)} completed tasks")
        return len(tasks)



