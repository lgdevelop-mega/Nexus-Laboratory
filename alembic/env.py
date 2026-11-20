"""Entorno de Alembic en modo async (asyncmy, D-02).

Crear una revisión con identificador explícito:
    uv run alembic revision -m "login base" --rev-id 0001
"""

import asyncio
from logging.config import fileConfig

from sqlalchemy.engine import Connection

from alembic import context
from app.core.config import load_settings
from app.core.db import Base, create_migration_engine, import_models

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

import_models()
target_metadata = Base.metadata


def _configure(**kwargs: object) -> None:
    context.configure(
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
        **kwargs,
    )


def run_migrations_offline() -> None:
    _configure(
        url=load_settings().database_url.get_secret_value(),
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def _run_sync(connection: Connection) -> None:
    _configure(connection=connection)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    engine = create_migration_engine(load_settings())
    try:
        async with engine.connect() as connection:
            await connection.run_sync(_run_sync)
    finally:
        await engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
