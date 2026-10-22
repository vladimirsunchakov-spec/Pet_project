import asyncio
import logging
from typing import Optional
from uuid import UUID

from src.clients.bio_client import BioServiceClient
from src.config import settings
from src.db import get_session
from src.exceptions import ExternalServiceError, ExternalServiceUnavailableError
from src.models.task import TaskModel
from src.repositories.task_repository import TaskRepository, TaskStatus
from src.schemas.bio import BioCreateRequest
from src.services.author import saga_orchestrator

logger = logging.getLogger(__name__)


class BioCreationWorker:
    def __init__(self, bio_client: BioServiceClient) -> None:
        self._bio_client = bio_client
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._semaphore = asyncio.Semaphore(settings.bio_worker_max_concurrency)

    async def start(self) -> None:
        self._running = True
        self._task = asyncio.create_task(self._process_queue())
        logger.info("BioCreationWorker started")

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("BioCreationWorker stopped")

    async def _process_queue(self) -> None:
        while self._running:
            try:
                tasks = await self._claim_tasks()
                if not tasks:
                    await asyncio.sleep(settings.bio_worker_poll_interval_seconds)
                    continue

                results = await asyncio.gather(
                    *(self._process_task_guarded(task) for task in tasks),
                    return_exceptions=True,
                )
                for task, result in zip(tasks, results):
                    if isinstance(result, Exception):
                        logger.error(
                            "Task %s failed in gather: %s",
                            task.id,
                            result,
                            exc_info=result,
                        )

            except asyncio.CancelledError:
                logger.info("BioCreationWorker cancelled")
                raise
            except Exception as e:
                logger.error("Error processing queue: %s", e)
                await asyncio.sleep(settings.bio_worker_poll_interval_seconds)

    async def _claim_tasks(self) -> list[TaskModel]:
        async with get_session() as session:
            return await TaskRepository(session).claim_pending_tasks(
                limit=settings.bio_worker_claim_limit,
                retry_backoff_seconds=settings.bio_worker_retry_backoff_seconds,
                processing_timeout_seconds=settings.bio_worker_processing_timeout_seconds,
            )

    async def _process_task_guarded(self, task: TaskModel) -> None:
        async with self._semaphore:
            await self._process_task(task)

    async def _process_task(self, task: TaskModel) -> None:
        if task.attempt_id is None:
            logger.error("Task %s has no attempt_id, skipping", task.id)
            return

        try:
            if task.task_type == "create_bio":
                await self._handle_create_bio(task)
            else:
                logger.error("Unknown task type: %s", task.task_type)
                await self._mark_failed(task.id, task.attempt_id, f"Unknown task type: {task.task_type}")
                await self._fail_deferred_saga(task, f"Unknown task type: {task.task_type}")
        except ExternalServiceUnavailableError as e:
            logger.warning("Task %s: service unavailable, will retry: %s", task.id, e)
            status = await self._mark_retry(task.id, task.attempt_id, str(e))
            if status == TaskStatus.FAILED:
                await self._fail_deferred_saga(task, str(e))
        except ExternalServiceError as e:
            logger.error("Task %s: client error, marking as failed: %s", task.id, e)
            await self._mark_failed(task.id, task.attempt_id, str(e))
            await self._fail_deferred_saga(task, str(e))
        except Exception as e:
            logger.error("Task %s: unexpected error, will retry: %s", task.id, e, exc_info=True)
            status = await self._mark_retry(task.id, task.attempt_id, str(e))
            if status == TaskStatus.FAILED:
                await self._fail_deferred_saga(task, str(e))

    async def _handle_create_bio(self, task: TaskModel) -> None:
        payload = task.payload
        author_id = UUID(payload["author_id"])
        request = BioCreateRequest(
            author_id=author_id,
            rating=payload.get("rating", settings.bio_default_rating),
            awards_count=payload.get("awards_count", settings.bio_default_awards_count),
        )
        idempotency_key = payload.get("idempotency_key", str(task.id))

        await self._bio_client.create_bio(
            request=request,
            idempotency_key=idempotency_key,
        )
        await self._mark_done(task.id, task.attempt_id)
        await self._complete_deferred_saga(task)
        logger.info("Bio created for author %s (task %s)", author_id, task.id)

    async def _complete_deferred_saga(self, task: TaskModel) -> None:
        saga_id = task.payload.get("saga_id")
        if not saga_id:
            return
        await saga_orchestrator.complete_deferred_saga(saga_id)

    async def _fail_deferred_saga(self, task: TaskModel, error: str) -> None:
        saga_id = task.payload.get("saga_id")
        if not saga_id:
            return
        await saga_orchestrator.complete_deferred_saga(saga_id, error=error)

    async def _mark_done(self, task_id: UUID, attempt_id: UUID) -> None:
        async with get_session() as session:
            await TaskRepository(session).mark_done(task_id, attempt_id)

    async def _mark_retry(self, task_id: UUID, attempt_id: UUID, error: str) -> str:
        async with get_session() as session:
            return await TaskRepository(session).mark_retry(task_id, attempt_id, error)

    async def _mark_failed(self, task_id: UUID, attempt_id: UUID, error: str) -> None:
        async with get_session() as session:
            await TaskRepository(session).mark_failed(task_id, attempt_id, error)


def create_bio_worker(bio_client: BioServiceClient) -> BioCreationWorker:
    return BioCreationWorker(bio_client=bio_client)
