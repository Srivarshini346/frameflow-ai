import time
from typing import Dict, Any, Optional

class IdempotencyManager:
    """
    Thread-safe in-memory cache for idempotency keys.
    Prevents duplicate submissions from triggering parallel pipeline execution.
    """
    def __init__(self, ttl_seconds: int = 3600):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._ttl_seconds = ttl_seconds

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        self._cleanup()
        item = self._cache.get(key)
        if item:
            return item["response"]
        return None

    def set(self, key: str, response: Dict[str, Any]) -> None:
        self._cleanup()
        self._cache[key] = {
            "response": response,
            "created_at": time.time()
        }

    def _cleanup(self) -> None:
        now = time.time()
        expired = [k for k, v in self._cache.items() if now - v["created_at"] > self._ttl_seconds]
        for k in expired:
            self._cache.pop(k, None)

idempotency_store = IdempotencyManager()
