"""Valores de los catálogos ``statuses`` y ``device_types`` (R2-04 a R2-06).

Son los ``name`` de cada fila: el código los usa por nombre, nunca por ``id``.
"""

from enum import StrEnum


class Status(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class DeviceType(StrEnum):
    """Solo informativo: nunca se usa para autorizar."""

    UNKNOWN = "unknown"
    DESKTOP = "desktop"
    MOBILE = "mobile"
    TABLET = "tablet"
