"""Unidad de trabajo sobre una ``AsyncSession``: una transacción con los repositorios de Login."""

from types import TracebackType
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession

from app.identity.login.infrastructure.persistence.repositories import (
    SqlEnterpriseRepository,
    SqlMembershipRepository,
    SqlPreferenceRepository,
    SqlSessionRepository,
    SqlUserRepository,
)


class SqlUnitOfWork:
    """Cumple ``UnitOfWork``. Sin ``commit()`` explícito, al salir se revierte."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self.users = SqlUserRepository(session)
        self.enterprises = SqlEnterpriseRepository(session)
        self.memberships = SqlMembershipRepository(session)
        self.preferences = SqlPreferenceRepository(session)
        self.sessions = SqlSessionRepository(session)

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if self._session.in_transaction():
            await self._session.rollback()

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()
