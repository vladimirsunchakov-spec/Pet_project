import asyncio
import random
import logging
from functools import wraps
from typing import Any, Callable, Type, Tuple, TypeVar

T = TypeVar("T")
logger = logging.getLogger(__name__)

class RetryConfig:
    def __init__(
            self,
            exceptions: Tuple[Type[Exception],...] = (Exception,),
            attempts: int = 3,
            base_delay: float = 1.0,
            max_delay: float = 10.0,
            jitter: bool = True
    ):
        self.exceptions = exceptions
        self.attempts = attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.jitter = jitter

def with_retry(config: RetryConfig):
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_exception = None

            for attempt in range(1, config.attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except config.exceptions as e:
                    last_exception = e

                    if attempt == config.attempts:
                        logger.error(f"Retry failed after {attempt} attempts: {e}")
                        raise

                    delay = min(config.max_delay, config.base_delay * (2 ** (attempt - 1)))

                    if config.jitter:
                        delay = random.uniform(0, delay)

                    logger.warning(
                        f"Attempt {attempt} failed for {func.__name__}: {e}."
                        f"Retrying in {delay:.2f}s..."
                    )
                    await asyncio.sleep(delay)
            if last_exception:
                raise last_exception
        return wrapper
    return decorator
