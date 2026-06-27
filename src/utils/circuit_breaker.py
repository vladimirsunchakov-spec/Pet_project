import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)

class CircuitState(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

class CircuitBreaker:
    def __init__(
            self,
            failure_threshold: int = 5,
            recovery_timeout: int = 30,
            half_open_max_attempts: int = 1,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_attempts = half_open_max_attempts

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._half_open_attempts = 0
        self._last_failure_time: Optional[datetime] = None

    @property
    def state(self) -> CircuitState:
        if self._state == CircuitState.OPEN:
            if self._last_failure_time and datetime.now() >= self._last_failure_time + timedelta(seconds=self.recovery_timeout):
                self._state = CircuitState.HALF_OPEN
                self._half_open_attempts = 0
        return self._state

    def record_success(self) -> None:
        logger.info(f"Circuit Breaker: recording SUCCESS, current state={self.state}")
        if self._state == CircuitState.HALF_OPEN:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._half_open_attempts = 0
        else:
            self._failure_count = 0

    def record_failure(self) -> None:
        logger.warning(f"Circuit Breaker: recording FAILURE, current state={self.state}, failure_count={self._failure_count}")
        if self._state == CircuitState.HALF_OPEN:
            self._half_open_attempts += 1
            if self._half_open_attempts >= self.half_open_max_attempts:
                self._state = CircuitState.OPEN
                self._last_failure_time = datetime.now()
                logger.warning(f"Circuit Breaker: OPEN after {self._half_open_attempts} failures in HALF_OPEN")
        elif self._state == CircuitState.CLOSED:
            self._failure_count += 1
            if self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN
                self._last_failure_time = datetime.now()
                logger.warning(f"Circuit Breaker: OPEN after {self._failure_count} failures")

    def is_allowed(self) -> bool:
        allowed = self.state in (CircuitState.CLOSED, CircuitState.HALF_OPEN)
        if not allowed:
            logger.warning(f"Circuit Breaker: REQUEST BLOCKED, state={self.state}")
        return allowed


