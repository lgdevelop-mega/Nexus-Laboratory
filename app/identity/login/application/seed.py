"""Caso de uso: cargar empresas, usuarios y membresías a partir de un plan (seeder).

- Idempotente: empresas por ``rfc``, usuarios por correo y membresías por
  ``(user_id, enterprise_id)``. Lo que ya existe se reporta como ``existing`` y no se modifica.
- Una sola transacción: si algo falla, no queda nada a medias.
- ``dry_run`` recorre el plan sin escribir y revierte al final.

El plan ya llega validado por la capa de entrada (``cli/``). Este caso de uso y sus puertos
son los mismos que usará el alta por administrador (LOG-02).
"""

from dataclasses import dataclass, field
from enum import StrEnum

from app.identity.login.application.ports import (
    NewEnterprise,
    NewUser,
    PasswordHasher,
    UnitOfWork,
    UnitOfWorkFactory,
)
from app.identity.login.domain.email import Email
from app.identity.login.domain.status import Status

# --- Entrada ------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class SeedEnterprise:
    key: str
    data: NewEnterprise


@dataclass(frozen=True, slots=True)
class SeedMembership:
    enterprise_key: str
    status: Status


@dataclass(frozen=True, slots=True)
class SeedUser:
    email: Email
    password: str
    status: Status
    name: str
    last_name: str
    memberships: tuple[SeedMembership, ...]
    default_enterprise_key: str
    second_name: str | None = None
    second_last_name: str | None = None
    phone_wa: str | None = None


@dataclass(frozen=True, slots=True)
class SeedPlan:
    enterprises: tuple[SeedEnterprise, ...]
    users: tuple[SeedUser, ...]


# --- Salida -------------------------------------------------------------------------


class SeedResult(StrEnum):
    CREATED = "created"
    EXISTING = "existing"
    WOULD_CREATE = "would_create"


@dataclass(frozen=True, slots=True)
class EnterpriseReport:
    key: str
    id: int | None
    result: SeedResult


@dataclass(frozen=True, slots=True)
class MembershipReport:
    enterprise: str
    id: int | None
    result: SeedResult


@dataclass(frozen=True, slots=True)
class UserReport:
    email: str
    id: int | None
    result: SeedResult
    memberships: tuple[MembershipReport, ...]
    default_enterprise: str


@dataclass(frozen=True, slots=True)
class SeedReport:
    dry_run: bool
    enterprises: tuple[EnterpriseReport, ...] = field(default_factory=tuple)
    users: tuple[UserReport, ...] = field(default_factory=tuple)


# --- Caso de uso --------------------------------------------------------------------


class SeedLoginData:
    def __init__(self, uow_factory: UnitOfWorkFactory, hasher: PasswordHasher) -> None:
        self._uow_factory = uow_factory
        self._hasher = hasher

    async def execute(self, plan: SeedPlan, *, dry_run: bool = False) -> SeedReport:
        async with self._uow_factory() as uow:
            enterprise_ids: dict[str, int | None] = {}
            enterprise_reports = []
            for enterprise in plan.enterprises:
                report = await self._seed_enterprise(uow, enterprise, dry_run)
                enterprise_ids[enterprise.key] = report.id
                enterprise_reports.append(report)

            user_reports = [
                await self._seed_user(uow, user, enterprise_ids, dry_run) for user in plan.users
            ]

            if dry_run:
                await uow.rollback()
            else:
                await uow.commit()

        return SeedReport(dry_run, tuple(enterprise_reports), tuple(user_reports))

    async def _seed_enterprise(
        self, uow: UnitOfWork, enterprise: SeedEnterprise, dry_run: bool
    ) -> EnterpriseReport:
        existing = await uow.enterprises.get_id_by_rfc(enterprise.data.rfc)
        if existing is not None:
            return EnterpriseReport(enterprise.key, existing, SeedResult.EXISTING)
        if dry_run:
            return EnterpriseReport(enterprise.key, None, SeedResult.WOULD_CREATE)
        new_id = await uow.enterprises.add(enterprise.data)
        return EnterpriseReport(enterprise.key, new_id, SeedResult.CREATED)

    async def _seed_user(
        self,
        uow: UnitOfWork,
        user: SeedUser,
        enterprise_ids: dict[str, int | None],
        dry_run: bool,
    ) -> UserReport:
        existing = await uow.users.get_by_email(user.email)
        if existing is not None:
            user_id: int | None = existing.id
            user_result = SeedResult.EXISTING
        elif dry_run:
            user_id, user_result = None, SeedResult.WOULD_CREATE
        else:
            user_id = await uow.users.add(
                NewUser(
                    email=user.email,
                    password_hash=await self._hasher.hash(user.password),
                    status=user.status,
                    name=user.name,
                    last_name=user.last_name,
                    second_name=user.second_name,
                    second_last_name=user.second_last_name,
                    phone_wa=user.phone_wa,
                )
            )
            user_result = SeedResult.CREATED

        membership_reports = []
        membership_ids: dict[str, int | None] = {}
        for membership in user.memberships:
            enterprise_id = enterprise_ids[membership.enterprise_key]
            found = (
                await uow.memberships.get_id(user_id, enterprise_id)
                if user_id is not None and enterprise_id is not None
                else None
            )
            if found is not None:
                report = MembershipReport(membership.enterprise_key, found, SeedResult.EXISTING)
            elif dry_run or user_id is None or enterprise_id is None:
                report = MembershipReport(membership.enterprise_key, None, SeedResult.WOULD_CREATE)
            else:
                new_id = await uow.memberships.add(user_id, enterprise_id, membership.status)
                report = MembershipReport(membership.enterprise_key, new_id, SeedResult.CREATED)
            membership_ids[membership.enterprise_key] = report.id
            membership_reports.append(report)

        # LOG-02: la primera empresa queda como predeterminada. Solo se fija si aún no hay una.
        default_membership_id = membership_ids.get(user.default_enterprise_key)
        if (
            not dry_run
            and user_id is not None
            and default_membership_id is not None
            and await uow.preferences.get_default(user_id) is None
        ):
            await uow.preferences.set_default(user_id, default_membership_id)

        return UserReport(
            email=str(user.email),
            id=user_id,
            result=user_result,
            memberships=tuple(membership_reports),
            default_enterprise=user.default_enterprise_key,
        )
