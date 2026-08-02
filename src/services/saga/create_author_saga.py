from uuid import UUID
from typing import Optional
from src.services.saga.base_saga import BaseSaga
from src.repositories.author_repository import AuthorRepository
from src.clients.bio_client import BioServiceClient, BioServiceError
from src.schemas.authors import AuthorCreate
from src.worker import bio_worker
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import asyncio

logger = logging.getLogger(__name__)

class CreateAuthorSaga(BaseSaga):
    def __init__(
        self,
        db_session: AsyncSession,
        author_data: dict,
        saga_id: Optional[str] = None
    ):
        super().__init__(saga_id)
        self.db_session = db_session
        self.author_data = author_data
        self.author_repo = AuthorRepository(db_session)
        self.bio_client = BioServiceClient()

        self.state.context["author_data"] = author_data
        self._build_saga()

    def _build_saga(self):
        self.add_step(
            name="create_author",
            action=self._create_author,
            compensation=self._compensate_author
        )

        self.add_step(
            name="create_bio",
            action=self._create_bio_with_retry,
            compensation=self._compensate_bio
        )

    async def _create_author(self) -> dict:
        logger.info(f"Saga {self.saga_id} Created author")

        author_create = AuthorCreate(**self.author_data)
        author = author_create.to_model()

        created_author = await self.author_repo.create_author(author)

        self.state.context["author_id"] = str(created_author.id)

        logger.info(f"Saga {self.saga_id}: Author created with id {created_author.id}")

        return {
            "author_id": str(created_author.id),
            "author": created_author
        }

    async def _create_bio_with_retry(self) -> dict:
        author_id = UUID(self.state.context["author_id"])
        logger.info(f"Saga {self.saga_id}: Creating bio for author {author_id} ")

        max_retries = 3
        last_error = None

        for attempt in range(1, max_retries + 1):
            try:
                bio_data = await self.bio_client.create_bio(author_id=author_id)

                logger.info(
                    f"Saga {self.saga_id}: Bio created successfully"
                    f" (attempt {attempt}/{max_retries})"
                )

                self.state.context["bio_data"] = bio_data

                return {
                    "bio_created": True,
                    "bio_data": bio_data,
                    "attempt": attempt
                }
            except BioServiceError as e:
                last_error = e
                logger.warning(f"Saga {self.saga_id}: Bio creation attempt {attempt}/{max_retries} failed: {e}")

                if attempt < max_retries:
                    wait_time = 2 ** attempt
                    logger.info(f"Saga {self.saga_id}: Waiting {wait_time}s before retry")
                    await asyncio.sleep(wait_time)

        logger.warning(
            f"Saga {self.saga_id}: All {max_retries} retries failed."
            f"Scheduling bio creation in worker. Last error: {last_error}"
        )

        await bio_worker.schedule_bio_creation(author_id)
        bio_created = await self._wait_for_bio_completion(author_id)

        if bio_created:
            logger.info(f"Saga {self.saga_id}: Bio created via worker")
            return {
                "bio_created": True,
                "bio_data": self.state.context["bio_data"],
                "via_worker": True
            }
        else:
            raise Exception(f"Bio not created for author {author_id} after worker processing")

    async def _wait_for_bio_completion(self, author_id: UUID) -> bool:
        logger.info(f"Saga {self.saga_id}: Waiting for bio completion via worker")

        max_checks = 10
        check_interval = 1

        for check in range(1, max_checks + 1):
            await asyncio.sleep(check_interval)

            try:
                bio_data = await self.bio_client.get_bio_by_author_id(author_id)
                if bio_data:
                    self.state.context["bio_data"] = bio_data
                    logger.info(
                        f"Saga {self.saga_id}: Bio confirmed in worker"
                        f" (check {check}/{max_checks})"
                    )
                    return True
            except Exception as e:
                logger.debug(f"Saga {self.saga_id}: Bio not ready yet (check {check}/{max_checks}): {e}")

        logger.warning(f"Saga {self.saga_id}: Bio not found after {max_checks} checks")
        return False

    async def _compensate_author(self):
        author_id = self.state.context.get("author_id")
        if not author_id:
            logger.warning(f"Saga {self.saga_id}: No author to compensate")
            return
        logger.info(f"Saga {self.saga_id}: Compensating author {author_id}")

        try:
            deleted = await self.author_repo.soft_delete(UUID(author_id))

            if deleted:
                logger.info(f"Saga {self.saga_id}: Author {author_id} deleted (compensated)")
            else:
                logger.warning(f"Saga {self.saga_id}: Author {author_id} not found for compensation")

        except Exception as e:
            logger.error(f"Saga {self.saga_id}: Author compensation failed: {e}")
            self.state.context["compensation_error"] = str(e)
            raise

    async def _compensate_bio(self):
        author_id = self.state.context.get("author_id")
        if not author_id:
            logger.warning(f"Saga {self.saga_id}: No author to compensation bio")
            return

        bio_data = self.state.context.get("bio_data")
        if not bio_data:
            logger.info(f"Saga {self.saga_id}: No bio to compensate")
            return

        logger.info(f"Saga {self.saga_id}: Compensating bio for author {author_id}")

        try:
            logger.info(
                f"Saga {self.saga_id}: Bio for author {author_id} would be deleted"
                f" (compensated)"
            )
        except Exception as e:
            logger.error(f"Saga {self.saga_id}: Bio compensation failed: {e}")
            self.state.context["compensation_error"] = str(e)
            raise