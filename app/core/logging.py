"""Configuración de logging (login-02-base §4.9).

Texto legible en ``local`` y JSON en el resto. Un filtro elimina tokens de la cabecera
``Authorization`` de cualquier registro: el token nunca se escribe en los logs.
"""

import json
import logging
import re
from datetime import UTC, datetime

from app.core.config import Settings

_HANDLER_NAME = "nexus"

_AUTHORIZATION = re.compile(r"(?i)(authorization['\"]?\s*[:=]\s*['\"]?)(bearer\s+)?[^\s'\",}]+")
_BEARER = re.compile(r"(?i)\bbearer\s+[A-Za-z0-9\-._~+/]+=*")
REDACTED = "[REDACTED]"


def redact(message: str) -> str:
    message = _AUTHORIZATION.sub(lambda m: f"{m.group(1)}{m.group(2) or ''}{REDACTED}", message)
    return _BEARER.sub(f"Bearer {REDACTED}", message)


class RedactAuthorizationFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        cleaned = redact(message)
        if cleaned != message:
            record.msg = cleaned
            record.args = None
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.fromtimestamp(record.created, UTC).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = redact(self.formatException(record.exc_info))
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(settings: Settings) -> None:
    root = logging.getLogger()
    for handler in list(root.handlers):
        if handler.get_name() == _HANDLER_NAME:
            root.removeHandler(handler)

    handler = logging.StreamHandler()
    handler.set_name(_HANDLER_NAME)
    handler.addFilter(RedactAuthorizationFilter())
    if settings.app_env == "local":
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s · %(message)s"))
    else:
        handler.setFormatter(JsonFormatter())

    root.addHandler(handler)
    root.setLevel(settings.log_level)
