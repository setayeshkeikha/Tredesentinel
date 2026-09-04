"""
Structured (JSON) logging so log lines are directly queryable in any
log aggregator (CloudWatch, Loki, Datadog) without regex parsing. In dev,
falls back to human-readable console output since nobody wants to read
JSON in a terminal while iterating locally.

Call configure_logging() once, at process startup, before any other
module-level logger is used (main.py and scheduler.py both do this first).
"""
import json
import logging
import sys
from datetime import datetime, timezone

from app.core.config import settings

_RESERVED_LOG_RECORD_ATTRS = {
    "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
    "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
    "created", "msecs", "relativeCreated", "thread", "threadName",
    "processName", "process", "message", "taskName",
}


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)

        # Any extra=... fields passed to the logging call get merged in,
        # which is how we attach bot_id/symbol/etc. to a log line without
        # needing to remember to interpolate them into the message string.
        for key, value in record.__dict__.items():
            if key not in _RESERVED_LOG_RECORD_ATTRS and not key.startswith("_"):
                payload[key] = value

        return json.dumps(payload, default=str)


def configure_logging() -> None:
    root = logging.getLogger()
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    if settings.ENV == "prod":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)-8s %(name)s: %(message)s")
        )

    root.addHandler(handler)
    root.setLevel(logging.INFO)

    # Quiet down noisy third-party loggers; we care about our own app logs.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
