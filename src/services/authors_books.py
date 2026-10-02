from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from src.schemas.saga import SagaStatus
from src.services.base import BaseService
from utils.request_id import get_request_id
from src.exceptions import NotFoundError
from src.schemas.authors import AuthorCreate, AuthorUpdate, AuthorResponse
from typing import List
from src.redis_client import redis_client
from src.repositories.author_repository import AuthorRepository
from src.clients.bio_client import BioServiceClient
from src.exceptions import ExternalServiceError, ExternalServiceUnavailableError
import logging
from src.schemas.saga import SagaResult
from src.services.saga import CreateAuthorSaga, DeleteAuthorSaga, saga_orchestrator

logger = logging.getLogger(__name__)


class AuthorsBooksService(BaseService):
    def __init__(self, db: AsyncSession, bio_client: BioServiceClient | None = None):
        self.db: AsyncSession = db
        self.request_id = get_request_id()
        self.author_repo = AuthorRepository(db)
        self.bio_client = bio_client or BioServiceClient()

    async def create_author(self, data: AuthorCreate) -> AuthorResponse:
        result: SagaResult = await saga_orchestrator.start_saga(
            saga_class=CreateAuthorSaga,
            db_session=self.db,
            author_data=data,
        )
        if result.status in (
            SagaStatus.COMPLETED.value,
            SagaStatus.COMPLETED_WITH_DEFERRED.value,
        ):
            author_id = UUID(result.context["author_id"])
            author = await self.author_repo.get(author_id)
            logger.info(
                "Author created",
                extra={"entity_id": str(author.id), "request_id": self.request_id},
            )
            return AuthorResponse.model_validate(author)
        logger.error(
            "Author create saga failed: %s",
            result.error,
            extra={"saga_id": result.saga_id, "request_id": self.request_id},
        )
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Saga failed: {result.error}")

    async def get_author(self, author_id: UUID) -> AuthorResponse:
        cache_key = f"author:{author_id}"
        cached = await redis_client.get_cached(cache_key, AuthorResponse)
        if cached:
            return cached

        author = await self.author_repo.get_with_books(author_id)
        if not author:
            raise NotFoundError("Author", str(author_id))

        response = AuthorResponse.model_validate(author)

        try:
            bio_data = await self.bio_client.get_bio_by_author_id(author.id)
            response.rating = bio_data.rating
            response.awards_count = bio_data.awards_count
        except ExternalServiceUnavailableError as e:
            logger.warning(
                "Bio service unavailable, returning author without bio: %s",
                e,
                extra={"author_id": str(author.id), "request_id": self.request_id},
            )
        except ExternalServiceError as e:
            logger.warning(
                "Bio service error, returning author without bio: %s",
                e,
                extra={"author_id": str(author.id), "request_id": self.request_id},
            )
        except NotFoundError:
            pass

        await redis_client.set_cached(cache_key, response)
        return response

    async def get_author_with_bio_required(self, author_id: UUID) -> AuthorResponse:
        author = await self.author_repo.get_with_books(author_id)
        if not author:
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"Author {author_id} not found")

        response = AuthorResponse.model_validate(author)
        try:
            bio_data = await self.bio_client.get_bio_by_author_id(author.id)
            response.rating = bio_data.rating
            response.awards_count = bio_data.awards_count
        except NotFoundError as e:
            raise HTTPException(status.HTTP_404_NOT_FOUND, str(e))
        except ExternalServiceUnavailableError as e:
            logger.error(
                "Bio service unavailable: %s",
                e,
                extra={"author_id": str(author.id), "request_id": self.request_id},
            )
            raise HTTPException(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                "Bio Service is temporarily unavailable. Please try again later",
            )
        except ExternalServiceError as e:
            logger.error(
                "Bio service error: %s",
                e,
                extra={"author_id": str(author.id), "request_id": self.request_id},
            )
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Bio Service error: {str(e)}")
        return response

    async def get_authors(self, skip: int = 0, limit: int = 100) -> List[AuthorResponse]:
        authors = await self.author_repo.get_all_with_relations(
            skip=skip,
            limit=limit,
            relations=["books"],
        )
        return AuthorResponse.from_model_list(authors)

    async def update_author(self, author_id: UUID, data: AuthorUpdate) -> AuthorResponse:
        author = await self.author_repo.get_with_books(author_id)
        if not author:
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"Author {author_id} not found")

        data.update_model(author)
        await redis_client.invalidate(f"author:{author_id}")
        return AuthorResponse.model_validate(author)

    async def delete_author(self, author_id: UUID) -> None:
        result: SagaResult = await saga_orchestrator.start_saga(
            saga_class=DeleteAuthorSaga,
            db_session=self.db,
            author_id=author_id,
        )
        if result.status == SagaStatus.COMPLETED.value:
            await redis_client.invalidate(f"author:{author_id}")
            logger.info(
                "Author deleted",
                extra={"entity_id": str(author_id), "request_id": self.request_id},
            )
            return
        logger.error(
            "Author delete saga failed: %s",
            result.error,
            extra={"saga_id": result.saga_id, "request_id": self.request_id},
        )
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Saga failed: {result.error}")
