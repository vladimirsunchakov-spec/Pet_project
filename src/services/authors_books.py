from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from src.services.base import BaseService
from src.middleware.request_id import get_request_id
from src.exceptions import NotFoundError
from src.schemas.authors import AuthorCreate, AuthorUpdate, AuthorResponse
from typing import List
from src.core.redis import redis_client
from src.repositories.author_repository import AuthorRepository
from src.clients.bio_client import BioServiceClient
import logging

logger = logging.getLogger(__name__)

class AuthorsBooksService(BaseService):
    def __init__(self, db: AsyncSession):
        self.db: AsyncSession = db
        self.request_id = get_request_id()
        self.author_repo = AuthorRepository(db)
        self.bio_client = BioServiceClient()

    async def create_author(self, data: AuthorCreate) -> AuthorResponse:
        self._log_info("Creating author", request_id=self.request_id, name=data.name, books_count=len(data.books))

        author = data.to_model()
        self.db.add(author)
        await self.db.refresh(author)

        try:
            bio_result = await self.bio_client.create_bio(
                author_id=author.id,
                rating=0.0,
                awards_count=0
            )
            if bio_result:
                self._log_info("Bio created for author", author_id=author.id, request_id=self.request_id)
            else:
                self._log_warning("Failed to create bio for author", author_id=author.id, request_id=self.request_id)
        except Exception as e:
            self._log_error(f"Error creating bio for author: {e}", author_id=author.id, request_id=self.request_id)
        self._log_info("Author created", entity_id=author.id, request_id=self.request_id)

        return AuthorResponse.model_validate(author)

    async def get_author(self, author_id: UUID) -> AuthorResponse:
        self._log_info("Fetching author", entity_id=author_id, request_id=self.request_id)

        cache_key = f"author:{author_id}"
        cached = await redis_client.get_cached(cache_key, AuthorResponse)
        if cached:
            self._log_info("Cache HIT for author", author_id=author_id, request_id=self.request_id)
            return cached

        self._log_info("Cache MISS for author", author_id=author_id, request_id=self.request_id)

        author = await self.author_repo.get_with_books(author_id)
        if not author:
            self._log_warning("Author not found", author_id=author_id, request_id=self.request_id)
            raise NotFoundError("Author", str(author_id))

        response = AuthorResponse.model_validate(author)

        try:
            bio_data = await self.bio_client.get_bio_by_author_id(author.id)
            if bio_data:
                self._log_info("Bio data found", author_id=author.id, request_id=self.request_id)
                response.rating = bio_data.get("rating")
                response.awards_count = bio_data.get("awards_count")
            else:
                self._log_info("No bio data for author", author_id=author.id, request_id=self.request_id)
        except Exception as e:
            self._log_warning(f"Error fetching bio for author: {e}", author_id=author.id, request_id=self.request_id)

        await redis_client.set_cached(cache_key, response)

        return response

    async def get_authors(self, skip: int = 0, limit: int = 100) -> List[AuthorResponse]:
        self._log_info("Fetching authors", skip=skip, limit=limit, request_id=self.request_id)

        authors = await self.author_repo.get_all_with_relations(
            skip=skip,
            limit=limit,
            relations=["books"],
            for_update=True
        )
        self._log_info("Authors fetched", count=len(authors), request_id=self.request_id)

        return AuthorResponse.from_model_list(authors)

    async def update_author(self, author_id: UUID, data: AuthorUpdate) -> AuthorResponse:
        self._log_info("Updating author", entity_id=author_id, request_id=self.request_id)

        author = await self.author_repo.get_with_books(author_id)
        if not author:
            self._log_warning("Author not found for update", entity_id=author_id, request_id=self.request_id)
            raise NotFoundError("Author", str(author_id))

        data.update_model(author)

        await redis_client.invalidate(f"author:{author_id}")

        self._log_info("Author updated", author_id=author_id, request_id=self.request_id)
        return AuthorResponse.model_validate(author)

    async def delete_author(self, author_id: UUID) -> None:
        self._log_info("Deleting author", entity_id=author_id, request_id=self.request_id)
        deleted = await self.author_repo.soft_delete(author_id)
        if not deleted:
            self._log_warning("Author not found for delete", entity_id=author_id, request_id=self.request_id)
            raise NotFoundError("Author", str(author_id))

        await redis_client.invalidate(f"author: {author_id}")

        self._log_info("Author deleted", entity_id=author_id, request_id=self.request_id)

