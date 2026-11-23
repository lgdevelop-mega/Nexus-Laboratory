"""Repositorios MySQL de Login con SQLAlchemy Core sobre los modelos de ``models.py``.

- Los catálogos se resuelven por ``name`` dentro de cada consulta (subconsulta o JOIN): el
  dominio nunca ve un ``id`` de catálogo.
- ``DATETIME(3)`` se guarda en UTC sin zona; al leer se marca como UTC.
- La vigencia de la sesión se compara con ``UTC_TIMESTAMP(3)`` de MySQL, no con el reloj
  de la aplicación.
"""

from datetime import UTC, datetime
from typing import Any, cast
from uuid import UUID

from sqlalchemy import (
    ColumnElement,
    CursorResult,
    Select,
    and_,
    func,
    insert,
    literal_column,
    or_,
    select,
    update,
)
from sqlalchemy.dialects.mysql import DATETIME
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.identity.login.application.ports import (
    ActiveSession,
    NewEnterprise,
    NewSession,
    NewUser,
)
from app.identity.login.domain.email import Email
from app.identity.login.domain.entities import Membership, User
from app.identity.login.domain.status import DeviceType, Status
from app.identity.login.infrastructure.persistence.models import (
    AuthSessionModel,
    DeviceTypeModel,
    EnterpriseModel,
    MembershipModel,
    StatusModel,
    UserModel,
    UserPreferenceModel,
)

TOUCH_INTERVAL: ColumnElement[datetime] = literal_column(
    "UTC_TIMESTAMP(3) - INTERVAL 60 SECOND", type_=DATETIME(fsp=3)
)


def _to_db(value: datetime) -> datetime:
    return value.astimezone(UTC).replace(tzinfo=None)


def _from_db(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC)


def _status_id(status: Status) -> object:
    return select(StatusModel.id).where(StatusModel.name == status.value).scalar_subquery()


def _device_type_id(device_type: DeviceType) -> object:
    query = select(DeviceTypeModel.id).where(DeviceTypeModel.name == device_type.value)
    return query.scalar_subquery()


_user_status = aliased(StatusModel, name="user_status")
_membership_status = aliased(StatusModel, name="membership_status")
_enterprise_status = aliased(StatusModel, name="enterprise_status")


def _user_columns() -> tuple[object, ...]:
    return (
        UserModel.id,
        UserModel.email,
        UserModel.password_hash,
        _user_status.name.label("user_status"),
        UserModel.name,
        UserModel.last_name,
    )


def _membership_columns() -> tuple[object, ...]:
    return (
        MembershipModel.id.label("membership_id"),
        MembershipModel.user_id,
        MembershipModel.enterprise_id,
        EnterpriseModel.trade_name,
        _membership_status.name.label("membership_status"),
        _enterprise_status.name.label("enterprise_status"),
        MembershipModel.joined_at,
    )


def _user_from_row(row: object) -> User:
    return User(
        id=row.id,  # type: ignore[attr-defined]
        email=Email(row.email),  # type: ignore[attr-defined]
        password_hash=row.password_hash,  # type: ignore[attr-defined]
        status=Status(row.user_status),  # type: ignore[attr-defined]
        name=row.name,  # type: ignore[attr-defined]
        last_name=row.last_name,  # type: ignore[attr-defined]
    )


def _membership_from_row(row: object) -> Membership:
    return Membership(
        membership_id=row.membership_id,  # type: ignore[attr-defined]
        user_id=row.user_id,  # type: ignore[attr-defined]
        enterprise_id=row.enterprise_id,  # type: ignore[attr-defined]
        trade_name=row.trade_name,  # type: ignore[attr-defined]
        status=Status(row.membership_status),  # type: ignore[attr-defined]
        enterprise_status=Status(row.enterprise_status),  # type: ignore[attr-defined]
        joined_at=_from_db(row.joined_at),  # type: ignore[attr-defined]
    )


def _memberships_query() -> Select[tuple[object, ...]]:
    return (
        select(*_membership_columns())  # type: ignore[call-overload]
        .join(EnterpriseModel, EnterpriseModel.id == MembershipModel.enterprise_id)
        .join(_membership_status, _membership_status.id == MembershipModel.status_id)
        .join(_enterprise_status, _enterprise_status.id == EnterpriseModel.status_id)
    )


def _new_id(result: CursorResult[Any]) -> int:
    key = result.inserted_primary_key
    if key is None:  # no ocurre con un INSERT de una fila; protege el tipo
        raise RuntimeError("MySQL no devolvió el id insertado")
    return int(key[0])


class _SqlRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _insert(self, statement: Any) -> CursorResult[Any]:
        # INSERT devuelve un CursorResult; MySQL da el id con inserted_primary_key.
        return cast(CursorResult[Any], await self._session.execute(statement))


class SqlUserRepository(_SqlRepository):
    async def get_by_email(self, email: Email) -> User | None:
        query = (
            select(*_user_columns())  # type: ignore[call-overload]
            .join(_user_status, _user_status.id == UserModel.status_id)
            .where(UserModel.email == email.value)
        )
        row = (await self._session.execute(query)).one_or_none()
        return _user_from_row(row) if row else None

    async def add(self, new_user: NewUser) -> int:
        result = await self._insert(
            insert(UserModel).values(
                email=new_user.email.value,
                password_hash=new_user.password_hash,
                status_id=_status_id(new_user.status),
                name=new_user.name,
                second_name=new_user.second_name,
                last_name=new_user.last_name,
                second_last_name=new_user.second_last_name,
                phone_wa=new_user.phone_wa,
            )
        )
        return _new_id(result)


class SqlEnterpriseRepository(_SqlRepository):
    async def get_id_by_rfc(self, rfc: str) -> int | None:
        found = await self._session.scalar(
            select(EnterpriseModel.id).where(EnterpriseModel.rfc == rfc)
        )
        return int(found) if found is not None else None

    async def add(self, new_enterprise: NewEnterprise) -> int:
        result = await self._insert(
            insert(EnterpriseModel).values(
                trade_name=new_enterprise.trade_name,
                company_name=new_enterprise.company_name,
                rfc=new_enterprise.rfc,
                website=new_enterprise.website,
                contact_name=new_enterprise.contact_name,
                email=new_enterprise.email,
                phone=new_enterprise.phone,
                full_address=new_enterprise.full_address,
                postal_code=new_enterprise.postal_code,
                status_id=_status_id(new_enterprise.status),
            )
        )
        return _new_id(result)


class SqlMembershipRepository(_SqlRepository):
    async def list_for_user(self, user_id: int) -> list[Membership]:
        query = _memberships_query().where(MembershipModel.user_id == user_id)
        rows = (await self._session.execute(query)).all()
        return [_membership_from_row(row) for row in rows]

    async def get_id(self, user_id: int, enterprise_id: int) -> int | None:
        found = await self._session.scalar(
            select(MembershipModel.id).where(
                MembershipModel.user_id == user_id,
                MembershipModel.enterprise_id == enterprise_id,
            )
        )
        return int(found) if found is not None else None

    async def add(self, user_id: int, enterprise_id: int, status: Status) -> int:
        result = await self._insert(
            insert(MembershipModel).values(
                user_id=user_id, enterprise_id=enterprise_id, status_id=_status_id(status)
            )
        )
        return _new_id(result)


class SqlPreferenceRepository(_SqlRepository):
    async def get_default(self, user_id: int) -> int | None:
        found = await self._session.scalar(
            select(UserPreferenceModel.default_membership_id).where(
                UserPreferenceModel.user_id == user_id
            )
        )
        return int(found) if found is not None else None

    async def set_default(self, user_id: int, membership_id: int) -> None:
        statement = mysql_insert(UserPreferenceModel).values(
            user_id=user_id, default_membership_id=membership_id
        )
        await self._session.execute(
            statement.on_duplicate_key_update(default_membership_id=membership_id)
        )


class SqlSessionRepository(_SqlRepository):
    async def add(self, new_session: NewSession) -> None:
        await self._session.execute(
            insert(AuthSessionModel).values(
                id=new_session.id.bytes,
                token_hash=new_session.token_hash,
                user_id=new_session.user_id,
                active_membership_id=new_session.membership_id,
                device_type_id=_device_type_id(new_session.device_type),
                created_at=_to_db(new_session.created_at),
                expires_at=_to_db(new_session.expires_at),
            )
        )

    async def find_active(self, token_hash: bytes) -> ActiveSession | None:
        query = (
            select(
                AuthSessionModel.id.label("session_id"),
                AuthSessionModel.expires_at,
                *_user_columns(),
                *_membership_columns(),
            )
            .select_from(AuthSessionModel)
            .join(UserModel, UserModel.id == AuthSessionModel.user_id)
            .join(_user_status, _user_status.id == UserModel.status_id)
            .join(MembershipModel, MembershipModel.id == AuthSessionModel.active_membership_id)
            .join(EnterpriseModel, EnterpriseModel.id == MembershipModel.enterprise_id)
            .join(_membership_status, _membership_status.id == MembershipModel.status_id)
            .join(_enterprise_status, _enterprise_status.id == EnterpriseModel.status_id)
            .where(
                AuthSessionModel.token_hash == token_hash,
                AuthSessionModel.revoked_at.is_(None),
                AuthSessionModel.expires_at > func.utc_timestamp(3),
            )
        )
        row = (await self._session.execute(query)).one_or_none()
        if row is None:
            return None
        return ActiveSession(
            session_id=UUID(bytes=row.session_id),
            expires_at=_from_db(row.expires_at),
            user=_user_from_row(row),
            membership=_membership_from_row(row),
        )

    async def touch(self, session_id: UUID) -> None:
        await self._session.execute(
            update(AuthSessionModel)
            .where(
                and_(
                    AuthSessionModel.id == session_id.bytes,
                    or_(
                        AuthSessionModel.last_used_at.is_(None),
                        AuthSessionModel.last_used_at < TOUCH_INTERVAL,
                    ),
                )
            )
            .values(last_used_at=func.utc_timestamp(3))
        )
