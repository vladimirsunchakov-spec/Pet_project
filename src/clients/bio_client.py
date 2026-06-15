import httpx
from typing import Optional
from uuid import UUID
from src.config import settings
from src.core.retry import with_retry, RetryConfig

class BioServiceClient:
    def __init__(self):
        self._base_url = settings.bio_service_url

    @with_retry(RetryConfig(
        exceptions=(httpx.TimeoutException, httpx.HTTPStatusError),
        attempts=3,
        base_delay=1.0,
        max_delay=10.0,
        jitter=True
    ))
    async def get_bio_by_author_id(self, author_id: UUID) -> Optional[dict]:
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                response = await client.get(f"{self._base_url}/bio/{author_id}", headers={"Content-Type": "application/json"})
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    return None
                else:
                    response.raise_for_status()
            except (httpx.TimeoutException, httpx.HTTPStatusError) as e:
                raise e

    @with_retry(RetryConfig(
        exceptions=(httpx.TimeoutException, httpx.HTTPStatusError),
        attempts=3,
        base_delay=1.0,
        max_delay=10.0,
        jitter=True
    ))
    async def create_bio(self, author_id: UUID, rating: float = 0.0, awards_count: int = 0 ) -> Optional[dict]:
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                response = await client.post(f"{self._base_url}/bio/", json={
                    "author_id": str(author_id),
                    "rating": rating,
                    "awards_count": awards_count,
                    "biography": None
                },
                headers={"Content-Type": "application/json"}
                )
                if response.status_code == 201:
                    return response.json()
                else:
                    response.raise_for_status()
            except (httpx.TimeoutException, httpx.HTTPStatusError) as e:
                raise e
    @with_retry(RetryConfig(
        exceptions=(httpx.TimeoutException, httpx.HTTPStatusError),
        attempts=3,
        base_delay=1.0,
        max_delay=10.0,
        jitter=True
    ))
    async def update_bio(self, author_id: UUID, rating: Optional[float] = None, awards_count: Optional[int] = None ) -> Optional[dict]:
        data ={}
        if rating is not None:
            data["rating"] = rating
        if awards_count is not None:
            data["awards_count"] = awards_count

        if not data:
            return None

        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                response = await client.put(f"{self._base_url}/bio/{author_id}", json=data, headers={"Content-Type": "application/json"})
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    return None
                else:
                    response.raise_for_status()
            except (httpx.TimeoutException, httpx.HTTPStatusError) as e:
                raise e
    @with_retry(RetryConfig(
        exceptions=(httpx.TimeoutException, httpx.HTTPStatusError),
        attempts=3,
        base_delay=1.0,
        max_delay=10.0,
        jitter=True
    ))
    async def delete_bio(self, author_id: UUID) -> bool:
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                response = await client.delete(f"{self._base_url}/bio/{author_id}", headers={"Content-Type": "application/json"})
                return response.status_code == 204
            except (httpx.TimeoutException, httpx.HTTPStatusError) as e:
                raise e


