"""Resultados de los casos de uso de sesión. La API los traduce a JSON."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.identity.login.domain.entities import Membership, User
from app.identity.login.domain.login_policy import is_multitenant


@dataclass(frozen=True, slots=True)
class SessionView:
    session_id: UUID
    expires_at: datetime
    user: User
    active: Membership
    enterprises: tuple[Membership, ...]
    default_membership_id: int | None

    @property
    def is_multitenant(self) -> bool:
        return is_multitenant(self.enterprises)


@dataclass(frozen=True, slots=True)
class LoginResult:
    access_token: str
    session: SessionView


@dataclass(frozen=True, slots=True)
class AuthenticatedSession:
    """Lo que recibe un endpoint protegido a través de ``current_session``."""

    session_id: UUID
    expires_at: datetime
    user: User
    membership: Membership
