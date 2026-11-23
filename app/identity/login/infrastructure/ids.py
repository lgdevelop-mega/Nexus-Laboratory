"""Identificadores UUIDv7 (RFC 9562). Python 3.12 no trae ``uuid.uuid7``.

Los primeros 48 bits son milisegundos Unix: los ids crecen con el tiempo y se indexan bien
en ``BINARY(16)``.
"""

import secrets
import time
from uuid import UUID


def uuid7() -> UUID:
    unix_ms = time.time_ns() // 1_000_000
    raw = bytearray(unix_ms.to_bytes(6, "big") + secrets.token_bytes(10))
    raw[6] = (raw[6] & 0x0F) | 0x70  # versión 7
    raw[8] = (raw[8] & 0x3F) | 0x80  # variante RFC 9562
    return UUID(bytes=bytes(raw))


class Uuid7Generator:
    """Cumple ``IdGenerator``."""

    def new_session_id(self) -> UUID:
        return uuid7()
