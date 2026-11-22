import logging
import json
import time
import sys
from contextvars import ContextVar
from typing import Optional

# Context variables for request tracing
current_job_id: ContextVar[Optional[str]] = ContextVar("current_job_id", default=None)
current_correlation_id: ContextVar[Optional[str]] = ContextVar("current_correlation_id", default=None)

class JSONFormatter(logging.Formatter):
    """
    Format logs as single-line JSON objects with timestamp, level,
    job_id, correlation_id, and structured metadata.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(record.created)),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "job_id": current_job_id.get(),
            "correlation_id": current_correlation_id.get(),
        }

        # Allow explicit record attributes to override context
        if hasattr(record, "job_id") and record.job_id:
            log_data["job_id"] = record.job_id
        if hasattr(record, "correlation_id") and record.correlation_id:
            log_data["correlation_id"] = record.correlation_id

        if hasattr(record, "extra_data") and isinstance(record.extra_data, dict):
            log_data.update(record.extra_data)

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)

def get_logger(name: str = "frameflow") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

logger = get_logger("frameflow")
