"""Puertos de Login. ``infrastructure/`` los implementa; ``app/bootstrap.py`` los conecta.

Los repositorios trabajan con los ``name`` de los catálogos (``Status``, ``DeviceType``):
resolver el ``id`` de cada fila es asunto del adaptador.
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from types import TracebackType
from typing import Protocol, Self
from uuid import UUID

from app.identity.login.domain.email import Email
from app.identity.login.domain.entities import Membership, User
from app.identity.login.domain.status import DeviceType, Status

# --- Datos que cruzan los puertos ---------------------------------------------------


@dataclass(frozen=True, slots=True)
class NewEnterprise:
    trade_name: str
    company_name: str
    rfc: str
    contact_name: str
    email: str
    phone: str
    full_address: str
    postal_code: str
    status: Status
    website: str | None = None


@dataclass(frozen=True, slots=True)
class NewUser:
    email: Email
    password_hash: str
    status: Status
    name: str
    last_name: str
    second_name: str | None = None
    second_last_name: str | None = None
    phone_wa: str | None = None


@dataclass(frozen=True, slots=True)
class NewSession:
    id: UUID
    token_hash: bytes
    user_id: int
    membership_id: int
    device_type: DeviceType
    created_at: datetime
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class ActiveSession:
    """Sesión no revocada ni vencida (según ``UTC_TIMESTAMP(3)``), con su usuario y membresía."""

    session_id: UUID
    expires_at: datetime
    user: User
    membership: Membership


# --- Repositorios -------------------------------------------------------------------


class UserRepository(Protocol):
    async def get_by_email(self, email: Email) -> User | None: ...

    async def add(self, new_user: NewUser) -> int: ...


class EnterpriseRepository(Protocol):
    async def get_id_by_rfc(self, rfc: str) -> int | None: ...

    async def add(self, new_enterprise: NewEnterprise) -> int: ...


class MembershipRepository(Protocol):
    async def list_for_user(self, user_id: int) -> list[Membership]:
        """Todas las membresías del usuario, con el estado de su empresa."""
        ...

    async def get_id(self, user_id: int, enterprise_id: int) -> int | None: ...

    async def add(self, user_id: int, enterprise_id: int, status: Status) -> int: ...


class PreferenceRepository(Protocol):
    async def get_default(self, user_id: int) -> int | None:
        """``None`` si no hay fila o si la predeterminada es NULL."""
        ...

    async def set_default(self, user_id: int, membership_id: int) -> None:
        """Crea o actualiza la fila de preferencias."""
        ...


class SessionRepository(Protocol):
    async def add(self, new_session: NewSession) -> None: ...

    async def find_active(self, token_hash: bytes) -> ActiveSession | None: ...

    async def touch(self, session_id: UUID) -> None:
        """Actualiza ``last_used_at``, como máximo una vez por minuto."""
        ...


class UnitOfWork(Protocol):
    """Una transacción. Sin ``commit()`` explícito, al salir se revierte."""

    @property
    def users(self) -> UserRepository: ...

    @property
    def enterprises(self) -> EnterpriseRepository: ...

    @property
    def memberships(self) -> MembershipRepository: ...

    @property
    def preferences(self) -> PreferenceRepository: ...

    @property
    def sessions(self) -> SessionRepository: ...

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None: ...

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...


UnitOfWorkFactory = Callable[[], UnitOfWork]


# --- Servicios ----------------------------------------------------------------------


class PasswordHasher(Protocol):
    async def hash(self, password: str) -> str: ...

    async def verify(self, password_hash: str | None, password: str) -> bool:
        """Con ``password_hash`` ``None`` hace el mismo trabajo y devuelve ``False``,
        para que un correo inexistente tarde lo mismo que una contraseña incorrecta."""
        ...


class TokenService(Protocol):
    def new_token(self) -> str:
        """Token opaco de 256 bits, apto para ``Authorization: Bearer``."""
        ...

    def hash_token(self, token: str) -> bytes:
        """SHA-256 del token (32 bytes). Es lo único que se guarda."""
        ...


class IdGenerator(Protocol):
    def new_session_id(self) -> UUID: ...


class Clock(Protocol):
    def now(self) -> datetime: ...
