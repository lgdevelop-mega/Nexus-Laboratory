"""Capa de entrada del seeder de Login (L-04): contrato de entrada y salida.

- **Entrada** (``SeedFile``): JSON validado con Pydantic. Otro archivo produce otros datos
  sin tocar código. Versión del formato: ``SEED_FORMAT_VERSION``.
- **Salida**: ``report_to_json`` convierte el ``SeedReport`` del caso de uso en el JSON que
  imprime el comando.

El comando ejecutable está en ``app/cli.py``, que conecta los adaptadores.
"""

import json
from pathlib import Path
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.identity.login.application.ports import NewEnterprise
from app.identity.login.application.seed import (
    SeedEnterprise,
    SeedMembership,
    SeedPlan,
    SeedReport,
    SeedUser,
)
from app.identity.login.domain.email import Email
from app.identity.login.domain.errors import InvalidEmail
from app.identity.login.domain.status import Status

SEED_FORMAT_VERSION = 1

Text = Field(min_length=1, max_length=255)  # M-4: todos los VARCHAR son de 255


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class EnterpriseIn(_Strict):
    key: str = Field(min_length=1, max_length=50, pattern=r"^[a-z0-9_-]+$")
    trade_name: str = Text
    company_name: str = Text
    rfc: str = Text
    website: str | None = Field(default=None, max_length=255)
    contact_name: str = Text
    email: str = Text
    phone: str = Text
    full_address: str = Text
    postal_code: str = Text
    status: Status = Status.ACTIVE


class MembershipIn(_Strict):
    enterprise: str = Field(min_length=1, max_length=50)
    status: Status = Status.ACTIVE


class UserIn(_Strict):
    email: str = Text
    password: str = Field(min_length=8, max_length=1024)
    name: str = Text
    second_name: str | None = Field(default=None, max_length=255)
    last_name: str = Text
    second_last_name: str | None = Field(default=None, max_length=255)
    phone_wa: str | None = Field(default=None, max_length=255)
    status: Status = Status.ACTIVE
    memberships: list[MembershipIn] = Field(min_length=1)
    default_enterprise: str

    @model_validator(mode="after")
    def _check_user(self) -> Self:
        try:
            self.email = Email.parse(self.email).value
        except InvalidEmail as exc:
            raise ValueError(f"correo inválido: {self.email!r}") from exc
        keys = [m.enterprise for m in self.memberships]
        if len(keys) != len(set(keys)):
            raise ValueError(f"{self.email}: membresía repetida en la misma empresa")
        if self.default_enterprise not in keys:
            raise ValueError(
                f"{self.email}: default_enterprise {self.default_enterprise!r} "
                "no está entre sus membresías"
            )
        return self


class SeedFile(_Strict):
    version: Literal[1]
    enterprises: list[EnterpriseIn]
    users: list[UserIn]

    @model_validator(mode="after")
    def _check_references(self) -> Self:
        _require_unique("key de empresa", [e.key for e in self.enterprises])
        _require_unique("rfc", [e.rfc for e in self.enterprises])
        _require_unique("correo", [u.email for u in self.users])
        known = {e.key for e in self.enterprises}
        for user in self.users:
            missing = {m.enterprise for m in user.memberships} - known
            if missing:
                raise ValueError(f"{user.email}: empresas no declaradas {sorted(missing)}")
        return self

    def to_plan(self) -> SeedPlan:
        return SeedPlan(
            enterprises=tuple(
                SeedEnterprise(
                    key=e.key,
                    data=NewEnterprise(
                        trade_name=e.trade_name,
                        company_name=e.company_name,
                        rfc=e.rfc,
                        website=e.website,
                        contact_name=e.contact_name,
                        email=e.email,
                        phone=e.phone,
                        full_address=e.full_address,
                        postal_code=e.postal_code,
                        status=e.status,
                    ),
                )
                for e in self.enterprises
            ),
            users=tuple(
                SeedUser(
                    email=Email(u.email),
                    password=u.password,
                    status=u.status,
                    name=u.name,
                    last_name=u.last_name,
                    second_name=u.second_name,
                    second_last_name=u.second_last_name,
                    phone_wa=u.phone_wa,
                    memberships=tuple(
                        SeedMembership(enterprise_key=m.enterprise, status=m.status)
                        for m in u.memberships
                    ),
                    default_enterprise_key=u.default_enterprise,
                )
                for u in self.users
            ),
        )


def _require_unique(label: str, values: list[str]) -> None:
    repeated = sorted({v for v in values if values.count(v) > 1})
    if repeated:
        raise ValueError(f"{label} repetido: {repeated}")


def load_seed_file(path: Path) -> SeedPlan:
    """Lee y valida el archivo. Lanza ``pydantic.ValidationError`` o ``ValueError``."""
    return SeedFile.model_validate_json(path.read_text(encoding="utf-8")).to_plan()


def report_to_json(report: SeedReport) -> str:
    return json.dumps(
        {
            "dry_run": report.dry_run,
            "enterprises": [
                {"key": e.key, "id": e.id, "result": e.result.value} for e in report.enterprises
            ],
            "users": [
                {
                    "email": u.email,
                    "id": u.id,
                    "result": u.result.value,
                    "memberships": [
                        {"enterprise": m.enterprise, "id": m.id, "result": m.result.value}
                        for m in u.memberships
                    ],
                    "default_enterprise": u.default_enterprise,
                }
                for u in report.users
            ],
        },
        ensure_ascii=False,
        indent=2,
    )
