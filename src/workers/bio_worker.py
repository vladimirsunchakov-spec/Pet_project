import asyncio
from typing import Optional
import json
import httpx
from src.redis_client import redis_client
from src.clients.bio_client import BioServiceClient, BioServiceError
import logging

logger = logging.getLogger(__name__)

class BioCreationWorker:
    QUEUE_KEY = "bio_creation_queue"
    FAILED_KEY = "bio_creation_queue_failed"

    def __init__(self):
        self._bio_client = BioServiceClient()
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._current_task: Optional[dict] = None
        self._task_completed = asyncio.Event()

    async def start(self):
        self._running = True
        self._task = asyncio.create_task(self._process_queue())
        logger.info("BioCreationWorker started")

    async def stop(self):
        self._running = False
        if self._current_task:
            logger.info("Waiting for current task to complete")
            try:
                await asyncio.wait_for(self._task_completed.wait(), timeout=30.0)
                logger.info("Current task is complete")
            except asyncio.TimeoutError:
                logger.warning("Current task did not complete in time, forcing stop")

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        logger.info("BioCreationWorker stopped")

    async def schedule_bio_creation(self, author_id, rating: float = 0.0, awards_count: int = 0):
        task = {
            "author_id": str(author_id),
            "rating": rating,
            "awards_count": awards_count,
        }
        await redis_client.rpush(self.QUEUE_KEY, json.dumps(task))
        logger.info(f"Scheduled bio creation for author {author_id}")

    async def _process_queue(self):
        while self._running:
            try:
                task_data = await redis_client.lpop(self.QUEUE_KEY)
                if task_data:
                    task = json.loads(task_data)
                    self._current_task = task
                    self._task_completed.clear()

                    await self._create_bio(task)

                    self._current_task = None
                    self._task_completed.set()
                else:
                    await asyncio.sleep(1)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing queue: {e}")
                await asyncio.sleep(5)

    async def _create_bio(self, task: dict):
        author_id = task["author_id"]
        rating = task.get("rating", 0.0)
        awards_count = task.get("awards_count", 0)

        try:
            await self._bio_client.create_bio(
                author_id=author_id,
                rating=rating,
                awards_count=awards_count
            )
            logger.info(f"Bio created for author {author_id} (worker)")

        except BioServiceError as e:
            logger.error(f"Bio creation failed for author {author_id}, after all retries: {e}")
            await self._save_failed_task(task, str(e))

        except Exception as e:
            logger.error(f"Unexpected error creating bio for author {author_id}: {e}")
            await  self._save_failed_task(task, str(e))

    async def _save_failed_task(self, task: dict, error: str):
        task["error"] = error
        await redis_client.rpush(self.FAILED_KEY, json.dumps(task))
        logger.warning(f"Failed task saved to {self.FAILED_KEY}")

    async def retry_failed_task(self, task_data: str):
        try:
            task = json.loads(task_data)
            await redis_client.rpush(self.QUEUE_KEY, json.dumps(task))
            logger.info(f"Retried failed task for author {task.get('author_id')} ")
        except Exception as e:
            logger.error(f"Failed to retry task: {e}")

bio_worker = BioCreationWorker()
