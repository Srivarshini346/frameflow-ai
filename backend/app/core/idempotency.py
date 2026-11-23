import hashlib
import json
import sqlite3
import threading
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
from app.config import settings
from app.core.exceptions import IdempotencyKeyReusedError
from app.core.logger import logger

class IdempotencyManager:
    """
    Thread-safe and persistent store for idempotency keys.
    Validates request payload hash:
    - Same key + same body -> returns cached response (no repeat work).
    - Same key + different body -> raises 409 IDEMPOTENCY_KEY_REUSED.
    """
    def __init__(self, db_path: Optional[Path] = None):
        self._db_path = db_path or (settings.storage_dir / "idempotency.db")
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        with self._lock:
            with sqlite3.connect(self._db_path, timeout=30.0) as conn:
                conn.execute("PRAGMA journal_mode=WAL;")
                conn.execute("PRAGMA busy_timeout=30000;")
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS idempotency_records (
                        idempotency_key TEXT PRIMARY KEY,
                        payload_hash TEXT NOT NULL,
                        response_json TEXT NOT NULL,
                        created_at REAL NOT NULL
                    )
                """)
                conn.commit()

    @staticmethod
    def compute_hash(payload: Any) -> str:
        if isinstance(payload, bytes):
            b = payload
        elif isinstance(payload, str):
            b = payload.encode("utf-8")
        else:
            b = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        return hashlib.sha256(b).hexdigest()

    def check_or_set(
        self,
        key: str,
        payload: Any,
        response_to_store: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        If key exists:
          Checks hash match. If match, returns cached response. If mismatch, raises IdempotencyKeyReusedError.
        If key does not exist and response_to_store is provided:
          Stores key, hash, response, and returns response_to_store.
        """
        payload_hash = self.compute_hash(payload)

        with self._lock:
            with sqlite3.connect(self._db_path) as conn:
                cur = conn.execute(
                    "SELECT payload_hash, response_json FROM idempotency_records WHERE idempotency_key = ?",
                    (key,)
                )
                row = cur.fetchone()
                if row:
                    stored_hash, stored_resp = row
                    if stored_hash != payload_hash:
                        raise IdempotencyKeyReusedError(key=key)
                    return json.loads(stored_resp)

                if response_to_store is not None:
                    import time
                    conn.execute(
                        "INSERT INTO idempotency_records (idempotency_key, payload_hash, response_json, created_at) VALUES (?, ?, ?, ?)",
                        (key, payload_hash, json.dumps(response_to_store, default=str), time.time())
                    )
                    conn.commit()
                    return response_to_store

        return None

    def store_response(self, key: str, payload: Any, response: Dict[str, Any]):
        payload_hash = self.compute_hash(payload)
        import time
        with self._lock:
            with sqlite3.connect(self._db_path) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO idempotency_records (idempotency_key, payload_hash, response_json, created_at) VALUES (?, ?, ?, ?)",
                    (key, payload_hash, json.dumps(response, default=str), time.time())
                )
                conn.commit()

idempotency_store = IdempotencyManager()
