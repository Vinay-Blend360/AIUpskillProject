"""Rate limiting strategies (Strategy pattern).

Fetchers depend on the ``RateLimitStrategy`` interface, not a concrete
algorithm, so the limiting behavior can be swapped per fetcher without
touching fetcher code.
"""

from __future__ import annotations

import asyncio
import time
from abc import ABC, abstractmethod
from types import TracebackType


class RateLimitStrategy(ABC):
    """Caps how fast/how many operations may proceed concurrently."""

    @abstractmethod
    async def acquire(self) -> None:
        """Block until the caller is allowed to proceed."""
        raise NotImplementedError

    @abstractmethod
    async def release(self) -> None:
        """Release whatever ``acquire`` held, if anything."""
        raise NotImplementedError

    async def __aenter__(self) -> "RateLimitStrategy":
        await self.acquire()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.release()


class SemaphoreStrategy(RateLimitStrategy):
    """Caps the number of operations running concurrently."""

    def __init__(self, max_concurrent: int = 10) -> None:
        self._semaphore = asyncio.Semaphore(max_concurrent)

    async def acquire(self) -> None:
        await self._semaphore.acquire()

    async def release(self) -> None:
        self._semaphore.release()


class TokenBucketStrategy(RateLimitStrategy):
    """Caps the rate of operations to ``rate`` per ``per`` seconds.

    Unlike a semaphore (concurrency cap), this caps throughput over time:
    at most ``rate`` acquisitions are allowed in any ``per``-second window.
    """

    def __init__(self, rate: int = 10, per: float = 1.0) -> None:
        self.rate = rate
        self.per = per
        self._tokens = float(rate)
        self._updated_at = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        while True:
            async with self._lock:
                self._refill()
                if self._tokens >= 1:
                    self._tokens -= 1
                    return
                wait_time = (1 - self._tokens) * (self.per / self.rate)
            await asyncio.sleep(wait_time)

    async def release(self) -> None:
        """No-op: tokens are time-based, not returned on completion."""

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._updated_at
        self._tokens = min(self.rate, self._tokens + elapsed * (self.rate / self.per))
        self._updated_at = now
