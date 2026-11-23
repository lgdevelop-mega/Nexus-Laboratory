"""Apertura de sesión compartida por el login convencional, el SSO (login-07) y el cambio
de empresa (login-08). No hace commit: lo decide el caso de uso que la invoca."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID

from app.identity.login.application.ports import (
    Clock,
    IdGenerator,
    NewSession,
    TokenService,
    UnitOfWork,
)
from app.identity.login.domain.entities import Membership, User
from app.identity.login.domain.status import DeviceType


@dataclass(frozen=True, slots=True)
class OpenedSession:
    session_id: UUID
    access_token: str
    expires_at: datetime


class SessionOpener:
    def __init__(
        self,
        tokens: TokenService,
        ids: IdGenerator,
        clock: Clock,
        session_ttl: timedelta,
    ) -> None:
        self._tokens = tokens
        self._ids = ids
        self._clock = clock
        self._ttl = session_ttl

    async def open(
        self, uow: UnitOfWork, user: User, membership: Membership, device_type: DeviceType
    ) -> OpenedSession:
        token = self._tokens.new_token()
        now = self._clock.now()
        session = NewSession(
            id=self._ids.new_session_id(),
            token_hash=self._tokens.hash_token(token),
            user_id=user.id,
            membership_id=membership.membership_id,
            device_type=device_type,
            created_at=now,
            expires_at=now + self._ttl,  # L-03: vigencia absoluta
        )
        await uow.sessions.add(session)
        return OpenedSession(session.id, token, session.expires_at)
