"""Conexión MySQL asíncrona con asyncmy (login-02-base §4.3, D-02).

- Cada conexión fija ``time_zone = '+00:00'`` para que ``DATETIME(3)`` y
  ``UTC_TIMESTAMP(3)`` trabajen en UTC.
- Al arrancar se exige MySQL >= 8.0.16 (restricciones CHECK del ER v2) y ``sql_mode``
  con ``STRICT_TRANS_TABLES``.
- ``Base`` usa una convención de nombres determinista para que las migraciones puedan
  eliminar FK e índices por nombre al revertirse.
"""

import re
from collections.abc import AsyncIterator
from typing import Any

from fastapi import Request
from sqlalchemy import MetaData, event, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.core.config import Settings

MIN_MYSQL_VERSION = (8, 0, 16)
REQUIRED_SQL_MODE = "STRICT_TRANS_TABLES"

NAMING_CONVENTION = {
    "pk": "pk_%(table_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class DatabaseConfigurationError(RuntimeError):
    """El servidor MySQL no cumple los requisitos mínimos."""


def import_models() -> None:
    """Importa los modelos de persistencia de cada módulo para registrar su metadata.

    Alembic lo invoca antes de comparar esquemas. Cada módulo agrega aquí su import
    cuando crea tablas. Los imports son locales para que ``app.core`` no cargue los
    módulos al importarse.

    - Login (login-04-migracion): 6 tablas; ``enterprise_sso_config`` se difiere (M-3).
    """
    import app.identity.login.infrastructure.persistence.models  # noqa: F401


def _set_utc_time_zone(dbapi_connection: Any, connection_record: Any) -> None:
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("SET time_zone = '+00:00'")
    finally:
        cursor.close()


def create_engine(settings: Settings) -> AsyncEngine:
    """Engine de la aplicación. No abre conexiones hasta la primera consulta."""
    engine = create_async_engine(
        settings.database_url.get_secret_value(),
        pool_size=settings.db_pool_size,
        pool_recycle=settings.db_pool_recycle_seconds,
        pool_pre_ping=True,
        echo=settings.db_echo,
    )
    event.listen(engine.sync_engine, "connect", _set_utc_time_zone)
    return engine


def create_migration_engine(settings: Settings) -> AsyncEngine:
    """Engine sin pool para Alembic, con la misma zona horaria UTC."""
    engine = create_async_engine(settings.database_url.get_secret_value(), poolclass=NullPool)
    event.listen(engine.sync_engine, "connect", _set_utc_time_zone)
    return engine


def create_sessionmaker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


def parse_server_version(raw: str) -> tuple[int, int, int]:
    match = re.match(r"(\d+)\.(\d+)\.(\d+)", raw)
    if match is None:
        raise DatabaseConfigurationError(f"Versión de MySQL no reconocida: {raw!r}")
    major, minor, patch = (int(part) for part in match.groups())
    return major, minor, patch


def check_server(version: str, sql_mode: str) -> None:
    """Valida versión y ``sql_mode``; lanza ``DatabaseConfigurationError`` si no cumplen."""
    if "mariadb" in version.lower():
        raise DatabaseConfigurationError(f"Se requiere MySQL, no MariaDB ({version})")
    if parse_server_version(version) < MIN_MYSQL_VERSION:
        required = ".".join(map(str, MIN_MYSQL_VERSION))
        raise DatabaseConfigurationError(f"Se requiere MySQL >= {required}; servidor: {version}")
    if REQUIRED_SQL_MODE not in sql_mode.upper().split(","):
        raise DatabaseConfigurationError(f"sql_mode debe incluir {REQUIRED_SQL_MODE}: {sql_mode!r}")


async def verify_server(engine: AsyncEngine) -> None:
    async with engine.connect() as connection:
        version = (await connection.execute(text("SELECT VERSION()"))).scalar_one()
        sql_mode = (await connection.execute(text("SELECT @@SESSION.sql_mode"))).scalar_one()
    check_server(str(version), str(sql_mode))


async def get_db_session(request: Request) -> AsyncIterator[AsyncSession]:
    """Una sesión por petición. El commit o rollback es responsabilidad del UnitOfWork."""
    sessionmaker: async_sessionmaker[AsyncSession] = request.app.state.sessionmaker
    async with sessionmaker() as session:
        yield session
