"""Entidades de Login usadas por el inicio de sesión."""

from dataclasses import dataclass
from datetime import datetime

from app.identity.login.domain.email import Email
from app.identity.login.domain.status import Status


@dataclass(frozen=True, slots=True)
class User:
    id: int
    email: Email
    password_hash: str | None
    status: Status
    name: str
    last_name: str


@dataclass(frozen=True, slots=True)
class Membership:
    """Membresía de un usuario con el estado de su empresa."""

    membership_id: int
    user_id: int
    enterprise_id: int
    trade_name: str
    status: Status
    enterprise_status: Status
    joined_at: datetime

    @property
    def is_available(self) -> bool:
        """Habilita el acceso: membresía vigente en una empresa activa (modelo funcional)."""
        return self.status is Status.ACTIVE and self.enterprise_status is Status.ACTIVE
