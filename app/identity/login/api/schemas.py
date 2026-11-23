"""Esquemas HTTP de Login. Validan la forma; las reglas viven en el dominio."""

from datetime import UTC, datetime
from typing import Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from app.identity.login.application.views import LoginResult, SessionView
from app.identity.login.domain.status import DeviceType


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=3, max_length=255, examples=["ana@saga.test"])
    password: str = Field(min_length=1, max_length=1024)
    device_type: DeviceType = DeviceType.UNKNOWN


class UserOut(BaseModel):
    id: int
    email: str
    name: str
    last_name: str


class ActiveEnterpriseOut(BaseModel):
    id: int
    membership_id: int
    trade_name: str


class EnterpriseOut(ActiveEnterpriseOut):
    is_default: bool


class SessionResponse(BaseModel):
    expires_at: datetime
    session_id: UUID
    user: UserOut
    active_enterprise: ActiveEnterpriseOut
    enterprises: list[EnterpriseOut]
    is_multitenant: bool

    @field_serializer("expires_at")
    def _utc_milliseconds(self, value: datetime) -> str:
        return value.astimezone(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")

    @classmethod
    def from_view(cls, view: SessionView) -> Self:
        return cls(
            expires_at=view.expires_at,
            session_id=view.session_id,
            user=UserOut(
                id=view.user.id,
                email=str(view.user.email),
                name=view.user.name,
                last_name=view.user.last_name,
            ),
            active_enterprise=ActiveEnterpriseOut(
                id=view.active.enterprise_id,
                membership_id=view.active.membership_id,
                trade_name=view.active.trade_name,
            ),
            enterprises=[
                EnterpriseOut(
                    id=m.enterprise_id,
                    membership_id=m.membership_id,
                    trade_name=m.trade_name,
                    is_default=m.membership_id == view.default_membership_id,
                )
                for m in view.enterprises
            ],
            is_multitenant=view.is_multitenant,
        )


class LoginResponse(SessionResponse):
    access_token: str
    token_type: Literal["Bearer"] = "Bearer"  # noqa: S105 - esquema, no una contraseña

    @classmethod
    def from_result(cls, result: LoginResult) -> Self:
        base = SessionResponse.from_view(result.session)
        return cls(access_token=result.access_token, **base.model_dump())
