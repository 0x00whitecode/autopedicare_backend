import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)


def get_request_id() -> str | None:
    return request_id_var.get()


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = getattr(record, "request_id", None) or get_request_id()
        return True


class SafeContextFormatter(logging.Formatter):
    SAFE_EXTRA_KEYS = (
        "user_id",
        "provider",
        "event",
        "endpoint",
        "status_code",
        "duration_ms",
        "token_family_id",
        "method",
        "path",
    )

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(record.created, tz=timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        request_id = getattr(record, "request_id", None)

        parts = [
            timestamp,
            record.levelname,
            record.name,
        ]

        if request_id:
            parts.append(f"request_id={request_id}")

        message = record.getMessage()
        extra_items = []

        for key in self.SAFE_EXTRA_KEYS:
            value = getattr(record, key, None)
            if value is not None:
                extra_items.append(f"{key}={value}")

        if extra_items:
            message = f"{message} | {' | '.join(extra_items)}"

        return " | ".join(parts) + f" | {message}"


def setup_logging(debug: bool = False) -> None:
    log_level = logging.DEBUG if debug else logging.INFO

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)
        handler.close()

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    handler.addFilter(RequestIdFilter())
    handler.setFormatter(SafeContextFormatter())

    root_logger.addHandler(handler)

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

    if debug:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)