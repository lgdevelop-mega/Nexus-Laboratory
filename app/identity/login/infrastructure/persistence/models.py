"""Modelos de persistencia de Login (login-04-migracion, revisión R2).

Especificación: ``docs/agents/herdr-login-04-r2-migraciones.md``, sección 4.

- Estados, tipos de dispositivo y motivos de revocación son catálogos con FK, no ENUM
  (R2-04, R2-05).
- Sin áreas, países, ciudades, roles ni SSO (R2-01 a R2-03).
- Las FK hacia catálogos no tienen ``server_default``: la aplicación resuelve el ``id`` por
  ``name`` y siempre lo envía.

Los nombres de PK, UK, FK y CHECK los produce ``NAMING_CONVENTION`` (``app/core/db.py``).
Cada FK simple hacia un catálogo tiene un ``Index`` explícito para que MySQL no cree uno
con el nombre de la FK (sección 4.10). Los modelos no tienen relaciones ORM ni lógica, y
no salen de ``infrastructure/``.
"""

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.mysql import BIGINT, BINARY, DATETIME, VARCHAR
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base

ID = BIGINT(unsigned=True)
UUID_BYTES = BINARY(16)
TIMESTAMP_MS = DATETIME(fsp=3)
TEXT_255 = VARCHAR(255)  # M-4
EMAIL = VARCHAR(255, collation="utf8mb4_bin")  # M-4; comparación exacta del correo normalizado

CREATED_DEFAULT = text("CURRENT_TIMESTAMP(3)")
UPDATED_DEFAULT = text("CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3)")

MYSQL_TABLE_OPTIONS = {
    "mysql_engine": "InnoDB",
    "mysql_charset": "utf8mb4",
    "mysql_collate": "utf8mb4_0900_ai_ci",
}


def _restrict(target: str) -> ForeignKey:
    return ForeignKey(target, ondelete="RESTRICT")


# --- Catálogos (R2-04, R2-05, R2-06) ----------------------------------------------


class StatusModel(Base):
    """Estados ``active`` / ``inactive`` de usuarios, empresas y membresías."""

    __tablename__ = "statuses"
    __table_args__ = (UniqueConstraint("name"), MYSQL_TABLE_OPTIONS)

    id: Mapped[int] = mapped_column(ID, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(TEXT_255)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP_MS, server_default=CREATED_DEFAULT)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP_MS, server_default=UPDATED_DEFAULT)


class DeviceTypeModel(Base):
    """Tipo de dispositivo de una sesión. Solo informativo: nunca se usa para autorizar."""

    __tablename__ = "device_types"
    __table_args__ = (UniqueConstraint("name"), MYSQL_TABLE_OPTIONS)

    id: Mapped[int] = mapped_column(ID, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(TEXT_255)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP_MS, server_default=CREATED_DEFAULT)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP_MS, server_default=UPDATED_DEFAULT)


class RevokedReasonModel(Base):
    """Motivo de revocación de una sesión (LOG-14, LOG-16)."""

    __tablename__ = "revoked_reasons"
    __table_args__ = (UniqueConstraint("name"), MYSQL_TABLE_OPTIONS)

    id: Mapped[int] = mapped_column(ID, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(TEXT_255)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP_MS, server_default=CREATED_DEFAULT)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP_MS, server_default=UPDATED_DEFAULT)


# --- Tablas de Login ------------------------------------------------------------------


class UserModel(Base):
    """Identidad global (LOG-07, LOG-08, LOG-15)."""

    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email"),
        CheckConstraint("email = LOWER(TRIM(email))", name="email_normalized"),  # M-5
        Index("ix_users_status_id", "status_id"),
        MYSQL_TABLE_OPTIONS,
    )

    id: Mapped[int] = mapped_column(ID, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(EMAIL)
    password_hash: Mapped[str | None] = mapped_column(TEXT_255)  # R2-07: NULL permitido
    status_id: Mapped[int] = mapped_column(ID, _restrict("statuses.id"))
    name: Mapped[str] = mapped_column(TEXT_255)
    second_name: Mapped[str | None] = mapped_column(TEXT_255)
    last_name: Mapped[str] = mapped_column(TEXT_255)
    second_last_name: Mapped[str | None] = mapped_column(TEXT_255)
    phone_wa: Mapped[str | None] = mapped_column(TEXT_255)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP_MS, server_default=CREATED_DEFAULT)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP_MS, server_default=UPDATED_DEFAULT)


class EnterpriseModel(Base):
    """Empresa y estado operativo (LOG-01, LOG-16)."""

    __tablename__ = "enterprises"
    __table_args__ = (
        UniqueConstraint("rfc"),
        Index("ix_enterprises_status_id", "status_id"),
        MYSQL_TABLE_OPTIONS,
    )

    id: Mapped[int] = mapped_column(ID, primary_key=True, autoincrement=True)
    trade_name: Mapped[str] = mapped_column(TEXT_255)
    company_name: Mapped[str] = mapped_column(TEXT_255)
    rfc: Mapped[str] = mapped_column(TEXT_255)
    website: Mapped[str | None] = mapped_column(TEXT_255)
    contact_name: Mapped[str] = mapped_column(TEXT_255)
    email: Mapped[str] = mapped_column(TEXT_255)
    phone: Mapped[str] = mapped_column(TEXT_255)
    full_address: Mapped[str] = mapped_column(TEXT_255)
    postal_code: Mapped[str] = mapped_column(TEXT_255)
    status_id: Mapped[int] = mapped_column(ID, _restrict("statuses.id"))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP_MS, server_default=CREATED_DEFAULT)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP_MS, server_default=UPDATED_DEFAULT)


class MembershipModel(Base):
    """Membresía usuario-empresa (LOG-02, LOG-05, LOG-07, LOG-15, CA-05)."""

    __tablename__ = "users_enterprises"
    __table_args__ = (
        UniqueConstraint("user_id", "enterprise_id"),  # una membresía por empresa (CA-05)
        UniqueConstraint("id", "user_id"),  # destino de las FK compuestas
        Index(
            "ix_users_enterprises_user_id_status_id_joined_at",
            "user_id",
            "status_id",
            "joined_at",
        ),  # LOG-05: membresía activa más antigua
        Index("ix_users_enterprises_enterprise_id_status_id", "enterprise_id", "status_id"),
        Index("ix_users_enterprises_status_id", "status_id"),  # soporte de la FK
        MYSQL_TABLE_OPTIONS,
    )

    id: Mapped[int] = mapped_column(ID, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ID, _restrict("users.id"))
    enterprise_id: Mapped[int] = mapped_column(ID, _restrict("enterprises.id"))
    status_id: Mapped[int] = mapped_column(ID, _restrict("statuses.id"))
    joined_at: Mapped[datetime] = mapped_column(TIMESTAMP_MS, server_default=CREATED_DEFAULT)
    # Sin ON UPDATE: lo actualiza la aplicación al cambiar el estado (H-06).
    status_changed_at: Mapped[datetime] = mapped_column(
        TIMESTAMP_MS, server_default=CREATED_DEFAULT
    )


class UserPreferenceModel(Base):
    """Empresa predeterminada (LOG-04, LOG-05)."""

    __tablename__ = "user_preferences"
    __table_args__ = (
        # La predeterminada pertenece al mismo usuario. Con NULL, MySQL no evalúa la FK.
        ForeignKeyConstraint(
            ["default_membership_id", "user_id"],
            ["users_enterprises.id", "users_enterprises.user_id"],
            ondelete="RESTRICT",
        ),
        MYSQL_TABLE_OPTIONS,
    )

    user_id: Mapped[int] = mapped_column(
        ID, _restrict("users.id"), primary_key=True, autoincrement=False
    )
    default_membership_id: Mapped[int | None] = mapped_column(ID)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP_MS, server_default=UPDATED_DEFAULT)


class AuthSessionModel(Base):
    """Sesión y token Bearer (LOG-03, LOG-14, LOG-16, CU-06, CU-10, CU-11)."""

    __tablename__ = "auth_sessions"
    __table_args__ = (
        UniqueConstraint("token_hash"),  # SHA-256 del token; el token en claro no se guarda
        ForeignKeyConstraint(
            ["active_membership_id", "user_id"],
            ["users_enterprises.id", "users_enterprises.user_id"],
            ondelete="RESTRICT",
        ),
        Index(
            "ix_auth_sessions_active_membership_id_revoked_at_expires_at",
            "active_membership_id",
            "revoked_at",
            "expires_at",
        ),
        Index("ix_auth_sessions_user_id_revoked_at", "user_id", "revoked_at"),
        Index("ix_auth_sessions_device_type_id", "device_type_id"),
        Index("ix_auth_sessions_revoked_reason_id", "revoked_reason_id"),
        CheckConstraint(
            "(revoked_at IS NULL) = (revoked_reason_id IS NULL)", name="revocation_consistent"
        ),
        CheckConstraint("expires_at > created_at", name="expires_after_created"),
        MYSQL_TABLE_OPTIONS,
    )

    id: Mapped[bytes] = mapped_column(UUID_BYTES, primary_key=True)  # UUIDv7 desde la app
    token_hash: Mapped[bytes] = mapped_column(BINARY(32))
    user_id: Mapped[int] = mapped_column(ID, _restrict("users.id"))
    active_membership_id: Mapped[int] = mapped_column(ID)
    device_type_id: Mapped[int] = mapped_column(ID, _restrict("device_types.id"))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP_MS, server_default=CREATED_DEFAULT)
    last_used_at: Mapped[datetime | None] = mapped_column(TIMESTAMP_MS)
    expires_at: Mapped[datetime] = mapped_column(TIMESTAMP_MS)
    revoked_at: Mapped[datetime | None] = mapped_column(TIMESTAMP_MS)
    revoked_reason_id: Mapped[int | None] = mapped_column(ID, _restrict("revoked_reasons.id"))


class PresenceConnectionModel(Base):
    """Una fila por conexión WebSocket (CU-07 a CU-10)."""

    __tablename__ = "presence_connections"
    __table_args__ = (
        Index("ix_presence_connections_session_id_valid_until", "session_id", "valid_until"),
        Index("ix_presence_connections_valid_until", "valid_until"),
        CheckConstraint("valid_until >= connected_at", name="valid_after_connected"),
        MYSQL_TABLE_OPTIONS,
    )

    id: Mapped[bytes] = mapped_column(UUID_BYTES, primary_key=True)
    session_id: Mapped[bytes] = mapped_column(
        UUID_BYTES, ForeignKey("auth_sessions.id", ondelete="CASCADE")
    )
    connected_at: Mapped[datetime] = mapped_column(TIMESTAMP_MS, server_default=CREATED_DEFAULT)
    last_seen_at: Mapped[datetime] = mapped_column(TIMESTAMP_MS, server_default=CREATED_DEFAULT)
    valid_until: Mapped[datetime] = mapped_column(TIMESTAMP_MS)
