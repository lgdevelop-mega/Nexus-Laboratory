"""Dobles en memoria de los puertos de Login (login-05), para las pruebas de Codex.

Uso típico:

    store = InMemoryStore()
    saga = store.add_enterprise("Saga")
    ana = store.add_user("ana@saga.test", password="secreta")
    m = store.add_membership(ana, saga, joined_at=...)
    store.preferences[ana] = m
    use_case = LoginWithPassword(store.uow_factory, FakePasswordHasher(), opener)

``InMemoryStore`` es el "estado de la base". Cada ``uow_factory()`` devuelve una unidad de
trabajo sobre ese estado; ``commits`` y ``rollbacks`` cuentan las transacciones. Los
cambios se aplican al momento (no hay aislamiento): basta para pruebas unitarias.
"""

import hashlib
import itertools
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from types import TracebackType
from typing import Self
from uuid import UUID

from app.identity.login.application.ports import (
    ActiveSession,
    NewEnterprise,
    NewSession,
    NewUser,
    UnitOfWork,
)
from app.identity.login.domain.email import Email
from app.identity.login.domain.entities import Membership, User
from app.identity.login.domain.status import Status

EPOCH = datetime(2026, 1, 1, tzinfo=UTC)


@dataclass
class StoredEnterprise:
    id: int
    trade_name: str
    rfc: str
    status: Status = Status.ACTIVE


@dataclass
class StoredSession:
    data: NewSession
    revoked_at: datetime | None = None
    last_used_at: datetime | None = None


@dataclass
class InMemoryStore:
    now: datetime = EPOCH  # "UTC_TIMESTAMP(3)" de la base falsa
    users: dict[int, User] = field(default_factory=dict)
    enterprises: dict[int, StoredEnterprise] = field(default_factory=dict)
    memberships: dict[int, Membership] = field(default_factory=dict)
    preferences: dict[int, int | None] = field(default_factory=dict)
    sessions: list[StoredSession] = field(default_factory=list)
    commits: int = 0
    rollbacks: int = 0
    _ids: "itertools.count[int]" = field(default_factory=lambda: itertools.count(1))

    # --- Preparación de escenarios -------------------------------------------------

    def add_enterprise(
        self, trade_name: str, *, rfc: str | None = None, status: Status = Status.ACTIVE
    ) -> int:
        new_id = next(self._ids)
        self.enterprises[new_id] = StoredEnterprise(
            new_id, trade_name, rfc or f"RFC{new_id:010d}", status
        )
        return new_id

    def add_user(
        self,
        email: str,
        *,
        password: str | None = "secreta",  # noqa: S107 - dato ficticio de prueba
        status: Status = Status.ACTIVE,
        name: str = "Nombre",
        last_name: str = "Prueba",
    ) -> int:
        new_id = next(self._ids)
        password_hash = FakePasswordHasher.hash_sync(password) if password is not None else None
        self.users[new_id] = User(
            new_id, Email.parse(email), password_hash, status, name, last_name
        )
        return new_id

    def add_membership(
        self,
        user_id: int,
        enterprise_id: int,
        *,
        joined_at: datetime = EPOCH,
        status: Status = Status.ACTIVE,
    ) -> int:
        new_id = next(self._ids)
        enterprise = self.enterprises[enterprise_id]
        self.memberships[new_id] = Membership(
            membership_id=new_id,
            user_id=user_id,
            enterprise_id=enterprise_id,
            trade_name=enterprise.trade_name,
            status=status,
            enterprise_status=enterprise.status,
            joined_at=joined_at,
        )
        return new_id

    def set_user_status(self, user_id: int, status: Status) -> None:
        self.users[user_id] = replace(self.users[user_id], status=status)

    def set_enterprise_status(self, enterprise_id: int, status: Status) -> None:
        self.enterprises[enterprise_id].status = status

    def set_membership_status(self, membership_id: int, status: Status) -> None:
        self.memberships[membership_id] = replace(self.memberships[membership_id], status=status)

    def uow_factory(self) -> UnitOfWork:
        return FakeUnitOfWork(self)

    # --- Lecturas con el estado actual de la empresa ------------------------------

    def membership_view(self, membership_id: int) -> Membership:
        m = self.memberships[membership_id]
        enterprise = self.enterprises[m.enterprise_id]
        return replace(m, enterprise_status=enterprise.status, trade_name=enterprise.trade_name)


class FakeUserRepository:
    def __init__(self, store: InMemoryStore) -> None:
        self._store = store

    async def get_by_email(self, email: Email) -> User | None:
        return next((u for u in self._store.users.values() if u.email == email), None)

    async def add(self, new_user: NewUser) -> int:
        new_id = next(self._store._ids)
        self._store.users[new_id] = User(
            new_id,
            new_user.email,
            new_user.password_hash,
            new_user.status,
            new_user.name,
            new_user.last_name,
        )
        return new_id


class FakeEnterpriseRepository:
    def __init__(self, store: InMemoryStore) -> None:
        self._store = store

    async def get_id_by_rfc(self, rfc: str) -> int | None:
        return next((e.id for e in self._store.enterprises.values() if e.rfc == rfc), None)

    async def add(self, new_enterprise: NewEnterprise) -> int:
        return self._store.add_enterprise(
            new_enterprise.trade_name, rfc=new_enterprise.rfc, status=new_enterprise.status
        )


class FakeMembershipRepository:
    def __init__(self, store: InMemoryStore) -> None:
        self._store = store

    async def list_for_user(self, user_id: int) -> list[Membership]:
        return [
            self._store.membership_view(m.membership_id)
            for m in self._store.memberships.values()
            if m.user_id == user_id
        ]

    async def get_id(self, user_id: int, enterprise_id: int) -> int | None:
        return next(
            (
                m.membership_id
                for m in self._store.memberships.values()
                if m.user_id == user_id and m.enterprise_id == enterprise_id
            ),
            None,
        )

    async def add(self, user_id: int, enterprise_id: int, status: Status) -> int:
        return self._store.add_membership(
            user_id, enterprise_id, joined_at=self._store.now, status=status
        )


class FakePreferenceRepository:
    def __init__(self, store: InMemoryStore) -> None:
        self._store = store

    async def get_default(self, user_id: int) -> int | None:
        return self._store.preferences.get(user_id)

    async def set_default(self, user_id: int, membership_id: int) -> None:
        self._store.preferences[user_id] = membership_id


class FakeSessionRepository:
    def __init__(self, store: InMemoryStore) -> None:
        self._store = store

    async def add(self, new_session: NewSession) -> None:
        self._store.sessions.append(StoredSession(new_session))

    async def find_active(self, token_hash: bytes) -> ActiveSession | None:
        for stored in self._store.sessions:
            data = stored.data
            if (
                data.token_hash == token_hash
                and stored.revoked_at is None
                and data.expires_at > self._store.now
            ):
                return ActiveSession(
                    session_id=data.id,
                    expires_at=data.expires_at,
                    user=self._store.users[data.user_id],
                    membership=self._store.membership_view(data.membership_id),
                )
        return None

    async def touch(self, session_id: UUID) -> None:
        for stored in self._store.sessions:
            if stored.data.id == session_id:
                stored.last_used_at = self._store.now


class FakeUnitOfWork:
    def __init__(self, store: InMemoryStore) -> None:
        self._store = store
        self.users = FakeUserRepository(store)
        self.enterprises = FakeEnterpriseRepository(store)
        self.memberships = FakeMembershipRepository(store)
        self.preferences = FakePreferenceRepository(store)
        self.sessions = FakeSessionRepository(store)

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        return None

    async def commit(self) -> None:
        self._store.commits += 1

    async def rollback(self) -> None:
        self._store.rollbacks += 1


class FakePasswordHasher:
    """Hash legible ``fake$<contraseña>``. Registra cuántas veces se verificó sin usuario."""

    def __init__(self) -> None:
        self.verify_without_user = 0

    @staticmethod
    def hash_sync(password: str) -> str:
        return f"fake${password}"

    async def hash(self, password: str) -> str:
        return self.hash_sync(password)

    async def verify(self, password_hash: str | None, password: str) -> bool:
        if password_hash is None:
            self.verify_without_user += 1
            return False
        return password_hash == self.hash_sync(password)


class FakeTokenService:
    """Tokens ``token-1``, ``token-2``…; el hash es SHA-256 como el real."""

    def __init__(self) -> None:
        self._counter = itertools.count(1)

    def new_token(self) -> str:
        return f"token-{next(self._counter)}"

    def hash_token(self, token: str) -> bytes:
        return hashlib.sha256(token.encode("utf-8")).digest()


class FakeIdGenerator:
    """UUIDs secuenciales y predecibles."""

    def __init__(self) -> None:
        self._counter = itertools.count(1)

    def new_session_id(self) -> UUID:
        return UUID(int=next(self._counter))
