import asyncio
from typing import Optional
from uuid import UUID
from src.models.task import TaskModel
from src.repositories.task_repository import TaskRepository
from src.clients.bio_client import BioServiceClient
from src.exceptions import (ExternalServiceError, ExternalServiceUnavailableError)
import logging

logger = logging.getLogger(__name__)

class BioCreationWorker:
    def __init__(self, task_repo: TaskRepository, bio_client: BioServiceClient) -> None:
        self._task_repo = task_repo
        self._bio_client = bio_client
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self):
        self._running = True
        self._task = asyncio.create_task(self._process_queue())
        logger.info("BioCreationWorker started")

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("BioCreationWorker stopped")

    async def _process_queue(self):
        while self._running:
            try:
                tasks = await self._task_repo.claim_pending_tasks(
                    limit=10,
                    retry_backoff_seconds=60,
                    processing_timeout_seconds=300,
                )
                if tasks:
                    for task in tasks:
                        await self._process_task(task)
                else:
                    await asyncio.sleep(5)
            except asyncio.CancelledError:
                logger.info("BioCreationWorker cancelled")
                raise

            except Exception as e:
                logger.error(f"Error processing queue: {e}")
                await asyncio.sleep(5)

    async def _process_task(self, task: TaskModel):
        task_type = task.task_type
        payload = task.payload

        logger.info(f"Processing task: {task.id} of type: '{task_type}'")

        try:
            if task_type == "create_bio":
                await self._handle_create_bio(task, payload)
            else:
                logger.error(f"Unknown task type: {task_type}")
                await self._task_repo.mark_failed(
                    task.id, f"Unknown task type: {task_type}"
                )
        except ExternalServiceUnavailableError as e:
            logger.warning(f"Task {task.id}: service unavailable, will retry: {e}")
            await self._task_repo.mark_retry(task.id, str(e))

        except ExternalServiceError as e:
            logger.error(f"Task {task.id}: client error, marking as failed: {e}")
            await self._task_repo.mark_failed(task.id, str(e))

        except Exception as e:
            logger.error(f"Task {task.id}: unexpected error, will retry: {e}", exc_info=True)
            await self._task_repo.mark_retry(task.id, str(e))

    async def _handle_create_bio(self, task: TaskModel, payload: dict):
        author_id = UUID(payload["author_id"])
        rating = payload.get("rating", 0.0)
        awards_count = payload.get("awards_count", 0)

        await self._bio_client.create_bio(
            author_id=author_id,
            rating=rating,
            awards_count=awards_count
        )
        await self._task_repo.mark_done(task.id)
        logger.info(f"Bio created for author {author_id} (task {task.id})")

def create_bio_worker(
    task_repo: TaskRepository,
    bio_client: BioServiceClient,
) -> BioCreationWorker:
    return BioCreationWorker(
        task_repo=task_repo,
        bio_client=bio_client,
    )

