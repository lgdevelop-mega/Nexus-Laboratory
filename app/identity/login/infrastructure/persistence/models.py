"""
Los nombres de PK, UK, FK y CHECK los produce ``NAMING_CONVENTION`` (``app/core/db.py``).
Los modelos no tienen relaciones ORM ni lógica, y no salen de ``infrastructure/``.
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.mysql import BIGINT, BINARY, DATETIME, ENUM, VARCHAR
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

USER_STATUSES = ("active", "suspended")
ENTERPRISE_STATUSES = ("active", "inactive")
MEMBERSHIP_STATUSES = ("active", "suspended", "revoked")
AUTH_METHODS = ("password", "sso")
DEVICE_TYPES = ("desktop", "mobile", "tablet", "unknown")
REVOKED_REASONS = (
    "logout",
    "switched",
    "user_suspended",
    "membership_revoked",
    "enterprise_disabled",
    "admin",
)


class UserModel(Base):
    """Identidad global (LOG-07, LOG-08, LOG-15)."""

    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email"),
        CheckConstraint("email = LOWER(TRIM(email))", name="email_normalized"),  # M-5
        Index("ix_users_area_id", "area_id"),
        MYSQL_TABLE_OPTIONS,
    )

    id: Mapped[int] = mapped_column(ID, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(EMAIL)
    password_hash: Mapped[str | None] = mapped_column(TEXT_255)
    status: Mapped[str] = mapped_column(ENUM(*USER_STATUSES), server_default=text("'active'"))
    name: Mapped[str] = mapped_column(TEXT_255)
    second_name: Mapped[str | None] = mapped_column(TEXT_255)
    last_name: Mapped[str] = mapped_column(TEXT_255)
    second_last_name: Mapped[str | None] = mapped_column(TEXT_255)
    phone_wa: Mapped[str | None] = mapped_column(TEXT_255)
    area_id: Mapped[int | None] = mapped_column(ID)  # M-1: sin FK
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP_MS, server_default=CREATED_DEFAULT)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP_MS, server_default=UPDATED_DEFAULT)


class EnterpriseModel(Base):
    """Empresa y estado operativo (LOG-01, LOG-06, LOG-16)."""

    __tablename__ = "enterprises"
    __table_args__ = (
        UniqueConstraint("rfc"),
        Index("ix_enterprises_country_id", "country_id"),
        Index("ix_enterprises_city_id", "city_id"),
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
    country_id: Mapped[int] = mapped_column(ID)  # M-1: sin FK
    city_id: Mapped[int] = mapped_column(ID)  # M-1: sin FK
    full_address: Mapped[str] = mapped_column(TEXT_255)
    postal_code: Mapped[str] = mapped_column(TEXT_255)
    status: Mapped[str] = mapped_column(
        ENUM(*ENTERPRISE_STATUSES), server_default=text("'active'")
    )  # M-2
    sso_enabled: Mapped[bool] = mapped_column(Boolean(), server_default=text("0"))  # tinyint(1)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP_MS, server_default=CREATED_DEFAULT)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP_MS, server_default=UPDATED_DEFAULT)


class MembershipModel(Base):
    """Membresía usuario-empresa (LOG-02, LOG-05, LOG-07, LOG-09, LOG-15, CA-05)."""

    __tablename__ = "users_enterprises"
    __table_args__ = (
        UniqueConstraint("user_id", "enterprise_id"),  # una membresía por empresa (CA-05)
        UniqueConstraint("id", "user_id"),  # destino de las FK compuestas
        Index("ix_users_enterprises_user_id_status_joined_at", "user_id", "status", "joined_at"),
        Index("ix_users_enterprises_enterprise_id_status", "enterprise_id", "status"),
        Index("ix_users_enterprises_role_id", "role_id"),
        MYSQL_TABLE_OPTIONS,
    )

    id: Mapped[int] = mapped_column(ID, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ID, ForeignKey("users.id", ondelete="RESTRICT"))
    enterprise_id: Mapped[int] = mapped_column(
        ID, ForeignKey("enterprises.id", ondelete="RESTRICT")
    )
    role_id: Mapped[int] = mapped_column(ID)  # M-1: sin FK
    status: Mapped[str] = mapped_column(ENUM(*MEMBERSHIP_STATUSES), server_default=text("'active'"))
    joined_at: Mapped[datetime] = mapped_column(TIMESTAMP_MS, server_default=CREATED_DEFAULT)
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
        ID, ForeignKey("users.id", ondelete="RESTRICT"), primary_key=True, autoincrement=False
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
        CheckConstraint(
            "(revoked_at IS NULL) = (revoked_reason IS NULL)", name="revocation_consistent"
        ),
        CheckConstraint("expires_at > created_at", name="expires_after_created"),
        MYSQL_TABLE_OPTIONS,
    )

    id: Mapped[bytes] = mapped_column(UUID_BYTES, primary_key=True)  # UUIDv7 desde la app
    token_hash: Mapped[bytes] = mapped_column(BINARY(32))
    user_id: Mapped[int] = mapped_column(ID, ForeignKey("users.id", ondelete="RESTRICT"))
    active_membership_id: Mapped[int] = mapped_column(ID)
    auth_method: Mapped[str] = mapped_column(ENUM(*AUTH_METHODS))
    # Solo informativo: nunca se usa para autorizar.
    device_type: Mapped[str] = mapped_column(ENUM(*DEVICE_TYPES), server_default=text("'unknown'"))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP_MS, server_default=CREATED_DEFAULT)
    last_used_at: Mapped[datetime | None] = mapped_column(TIMESTAMP_MS)
    expires_at: Mapped[datetime] = mapped_column(TIMESTAMP_MS)
    revoked_at: Mapped[datetime | None] = mapped_column(TIMESTAMP_MS)
    revoked_reason: Mapped[str | None] = mapped_column(ENUM(*REVOKED_REASONS))


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
