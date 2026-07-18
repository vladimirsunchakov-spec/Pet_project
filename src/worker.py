import asyncio
from typing import Optional
from src.clients.bio_client import BioServiceClient
import logging

logger = logging.getLogger(__name__)

class BioCreationWorker:
    def __init__(self):
        self._bio_client = BioServiceClient()
        self._queue: asyncio.Queue() = asyncio.Queue()
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self):
        self._running = True
        self._task = asyncio.create_task(self._process_queue())
        logger.info(f"BioCreationWorker started")

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info(f"BioCreationWorker stopped")

    async def schedule_bio_creation(self, author_id, rating: float = 0.0, awards_count: int = 0):
        await self._queue.put({
            "author_id": author_id,
            "rating": rating,
            "awards_count": awards_count,
        })
        logger.info(f"Scheduled bio creation for author {author_id}")

    async def _process_queue(self):
        while self._running:
            try:
                task = await self._queue.get()
                await self._create_bio_with_retry(**task)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing queue: {e}")

    async def _create_bio_with_retry(self, author_id, rating, awards_count):
        while True:
            try:
                result = await self._bio_client.create_bio(
                    author_id=author_id,
                    rating=rating,
                    awards_count=awards_count
                )
                if result:
                    logger.info(f"Bio created for author {author_id} (worker)")
                    break
                else:
                    logger.warning(f"Bio creation failed for author {author_id}, retrying... ")
                    await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Error creating bio for author {author_id}: {e}")
                await asyncio.sleep(5)

bio_worker = BioCreationWorker()
