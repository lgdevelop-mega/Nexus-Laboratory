"""Salud del servicio (login-02-base §4.8). No expone versión ni configuración."""

import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db_session
from app.core.errors import ServiceUnavailable

READY_TIMEOUT_SECONDS = 3

router = APIRouter(prefix="/api/v1/health", tags=["health"])


@router.get("")
async def liveness() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
async def readiness(session: Annotated[AsyncSession, Depends(get_db_session)]) -> dict[str, str]:
    try:
        async with asyncio.timeout(READY_TIMEOUT_SECONDS):
            await session.execute(text("SELECT 1"))
    except (SQLAlchemyError, OSError, TimeoutError) as exc:
        raise ServiceUnavailable("La base de datos no responde.") from exc
    return {"status": "ready", "database": "ok"}
