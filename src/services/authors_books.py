from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from src.services.base import BaseService
from utils.request_id import get_request_id
from src.exceptions import NotFoundError
from src.schemas.authors import AuthorCreate, AuthorUpdate, AuthorResponse
from typing import List
from src.redis_client import redis_client
from src.repositories.author_repository import AuthorRepository
from src.clients.bio_client import BioServiceClient, BioServiceError
import logging
from src.schemas.saga import SagaResult
from src.services.saga import CreateAuthorSaga, DeleteAuthorSaga, saga_orchestrator

logger = logging.getLogger(__name__)

class AuthorsBooksService(BaseService):
    def __init__(self, db: AsyncSession):
        self.db: AsyncSession = db
        self.request_id = get_request_id()
        self.author_repo = AuthorRepository(db)
        self.bio_client = BioServiceClient()

    async def create_author(self, data: AuthorCreate) -> AuthorResponse:
        try:
            result: SagaResult = await saga_orchestrator.start_saga(
                saga_class=CreateAuthorSaga,
                db_session=self.db,
                author_data=data.model_dump()
            )
            if result.status == "completed":
                author_id = UUID(result.context["author_id"])
                author = await self.author_repo.get(author_id)

                logger.info("Author created via saga", extra={"entity_id":str(author.id), "request_id": self.request_id})
                return AuthorResponse.model_validate(author)
            else:
                logger.error(f"Saga failed: {result.error}", extra={"saga_id": result.saga_id, "request_id": self.request_id})
                raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Saga failed: {result.error}")
        except Exception as e:
            logger.error(f"Author creation failed: {e}", extra={"request_id": self.request_id}, exc_info=True)
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Failed to create author: {str(e)}")

    async def get_author(self, author_id: UUID) -> AuthorResponse:
        cache_key = f"author:{author_id}"
        cached = await redis_client.get_cached(cache_key, AuthorResponse)
        if cached:
            return cached

        author = await self.author_repo.get_with_books(author_id)
        if not author:
            logger.warning("Author not found", extra={"author_id": str(author_id), "request_id": self.request_id})
            raise NotFoundError("Author", str(author_id))

        response = AuthorResponse.model_validate(author)

        try:
            bio_data = await self.bio_client.get_bio_by_author_id(author.id)
            if bio_data:
                response.rating = bio_data.rating
                response.awards_count = bio_data.awards_count
        except BioServiceError as e:
            logger.warning(f"Bio Service unavailable, returning author without bio: {e}", extra={"author_id": str(author.id), "request_id": self.request_id})
        except NotFoundError as e:
            pass
        except Exception as e:
            logger.error(f"Unexpected error getting bio: {e}", extra={"author_id": str(author.id), "request_id": self.request_id}, exc_info=True)

        await redis_client.set_cached(cache_key, response)
        return response

    async def get_author_with_bio_required(self, author_id: UUID) -> AuthorResponse:
        author = await self.author_repo.get_with_books(author_id)
        if not author:
            logger.warning("Author not found", extra={"author_id": str(author_id), "request_id": self.request_id})
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"Author {author_id} not found")

        response = AuthorResponse.model_validate(author)
        try:
            bio_data = await self.bio_client.get_bio_by_author_id(author.id)
            if not bio_data:
                logger.warning("Bio not found for author", extra={"author_id": str(author_id), "request_id": self.request_id})
                raise HTTPException(status.HTTP_404_NOT_FOUND, f"Bio not found for author: {author_id}")
            response.rating = bio_data.get("rating")
            response.awards_count = bio_data.get("awards_count")

        except BioServiceError as e:
            logger.error(f"Bio Service error: {e}", extra={"author_id": str(author.id), "request_id": self.request_id})
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, f"Bio Service is temporarily unavailable. Please try again later")

        except NotFoundError as e:
            logger.warning(f"Bio not found: {e}", extra={"author_id": str(author.id), "request_id": self.request_id})
            raise HTTPException(status.HTTP_404_NOT_FOUND, str(e))

        return response

    async def get_authors(self, skip: int = 0, limit: int = 100) -> List[AuthorResponse]:
        authors = await self.author_repo.get_all_with_relations(
            skip=skip,
            limit=limit,
            relations=["books"],
        )

        logger.info("Authors fetched", extra={"count": len(authors), "request_id": self.request_id})

        return AuthorResponse.from_model_list(authors)

    async def update_author(self, author_id: UUID, data: AuthorUpdate) -> AuthorResponse:

        author = await self.author_repo.get_with_books(author_id)
        if not author:
            logger.warning("Author not found for update", extra={"author_id": str(author_id), "request_id": self.request_id})
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"Author {author_id} not found")

        data.update_model(author)
        await redis_client.invalidate(f"author:{author_id}")

        logger.info("Author updated", extra={"author_id": str(author_id), "request_id": self.request_id})
        return AuthorResponse.model_validate(author)

    async def delete_author(self, author_id: UUID) -> None:
        try:
            result: SagaResult = await saga_orchestrator.start_saga(
                saga_class=DeleteAuthorSaga,
                db_session=self.db,
                author_id=author_id,
            )
            if result.status == "completed":
                await redis_client.invalidate(f"author:{author_id}")
                logger.info("Author deleted via saga", extra={"entity_id": str(author_id), "request_id": self.request_id})
            else:
                logger.error(f"Saga failed: {result.error}", extra={"saga_id": result.saga_id, "request_id": self.request_id})
                raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Saga failed: {result.error}")

        except Exception as e:
            logger.error(f"Failed to delete author: {e}", extra={"author_id": str(author_id), "request_id": self.request_id})
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Failed to delete author: {str(e)}")

