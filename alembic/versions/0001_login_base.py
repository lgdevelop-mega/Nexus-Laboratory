"""Login base: tablas globales del módulo de Login (login-04-migracion).

Revision ID: 0001
Revises:
Create Date: 2026-11-20

Especificación: docs/agents/herdr-login-04-migraciones.md, sección 5. Decisiones aprobadas
el 2026-11-20:

- M-1: sin FK hacia catálogos aún inexistentes (area_id, country_id, city_id, role_id).
- M-2: status como ENUM.
- M-3: enterprise_sso_config se difiere a login-07-sso.
- M-4: VARCHAR(255).
- M-5: ck_users_email_normalized.

Generada con autogenerate y revisada a mano:

- Orden de creación según la sección 5.9.
- downgrade() elimina solo las tablas, en orden inverso. Hacer DROP INDEX antes fallaría
  en MySQL (error 1553) en los índices que son el único soporte de una FK.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from alembic import op

revision: str = "0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLE_OPTIONS = {
    "mysql_engine": "InnoDB",
    "mysql_charset": "utf8mb4",
    "mysql_collate": "utf8mb4_0900_ai_ci",
}

ID = mysql.BIGINT(unsigned=True)
VARCHAR_255 = mysql.VARCHAR(length=255)
TIMESTAMP_MS = mysql.DATETIME(fsp=3)
CREATED_DEFAULT = sa.text("CURRENT_TIMESTAMP(3)")
UPDATED_DEFAULT = sa.text("CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3)")


def upgrade() -> None:
    # users: identidad global (LOG-07, LOG-08, LOG-15)
    op.create_table(
        "users",
        sa.Column("id", ID, autoincrement=True, nullable=False),
        sa.Column("email", mysql.VARCHAR(length=255, collation="utf8mb4_bin"), nullable=False),
        sa.Column("password_hash", VARCHAR_255, nullable=True),
        sa.Column(
            "status",
            mysql.ENUM("active", "suspended"),
            server_default=sa.text("'active'"),
            nullable=False,
        ),
        sa.Column("name", VARCHAR_255, nullable=False),
        sa.Column("second_name", VARCHAR_255, nullable=True),
        sa.Column("last_name", VARCHAR_255, nullable=False),
        sa.Column("second_last_name", VARCHAR_255, nullable=True),
        sa.Column("phone_wa", VARCHAR_255, nullable=True),
        sa.Column("area_id", ID, nullable=True),
        sa.Column("created_at", TIMESTAMP_MS, server_default=CREATED_DEFAULT, nullable=False),
        sa.Column("updated_at", TIMESTAMP_MS, server_default=UPDATED_DEFAULT, nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
        sa.CheckConstraint("email = LOWER(TRIM(email))", name=op.f("ck_users_email_normalized")),
        **TABLE_OPTIONS,
    )
    op.create_index("ix_users_area_id", "users", ["area_id"])

    # enterprises: empresa y estado operativo (LOG-01, LOG-06, LOG-16)
    op.create_table(
        "enterprises",
        sa.Column("id", ID, autoincrement=True, nullable=False),
        sa.Column("trade_name", VARCHAR_255, nullable=False),
        sa.Column("company_name", VARCHAR_255, nullable=False),
        sa.Column("rfc", VARCHAR_255, nullable=False),
        sa.Column("website", VARCHAR_255, nullable=True),
        sa.Column("contact_name", VARCHAR_255, nullable=False),
        sa.Column("email", VARCHAR_255, nullable=False),
        sa.Column("phone", VARCHAR_255, nullable=False),
        sa.Column("country_id", ID, nullable=False),
        sa.Column("city_id", ID, nullable=False),
        sa.Column("full_address", VARCHAR_255, nullable=False),
        sa.Column("postal_code", VARCHAR_255, nullable=False),
        sa.Column(
            "status",
            mysql.ENUM("active", "inactive"),
            server_default=sa.text("'active'"),
            nullable=False,
        ),
        sa.Column(
            "sso_enabled", sa.Boolean(), server_default=sa.text("0"), nullable=False
        ),
        sa.Column("created_at", TIMESTAMP_MS, server_default=CREATED_DEFAULT, nullable=False),
        sa.Column("updated_at", TIMESTAMP_MS, server_default=UPDATED_DEFAULT, nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_enterprises")),
        sa.UniqueConstraint("rfc", name=op.f("uq_enterprises_rfc")),
        **TABLE_OPTIONS,
    )
    op.create_index("ix_enterprises_country_id", "enterprises", ["country_id"])
    op.create_index("ix_enterprises_city_id", "enterprises", ["city_id"])

    # users_enterprises: membresías (LOG-02, LOG-05, LOG-07, LOG-09, LOG-15, CA-05)
    op.create_table(
        "users_enterprises",
        sa.Column("id", ID, autoincrement=True, nullable=False),
        sa.Column("user_id", ID, nullable=False),
        sa.Column("enterprise_id", ID, nullable=False),
        sa.Column("role_id", ID, nullable=False),
        sa.Column(
            "status",
            mysql.ENUM("active", "suspended", "revoked"),
            server_default=sa.text("'active'"),
            nullable=False,
        ),
        sa.Column("joined_at", TIMESTAMP_MS, server_default=CREATED_DEFAULT, nullable=False),
        sa.Column(
            "status_changed_at", TIMESTAMP_MS, server_default=CREATED_DEFAULT, nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users_enterprises")),
        sa.UniqueConstraint(
            "user_id", "enterprise_id", name=op.f("uq_users_enterprises_user_id_enterprise_id")
        ),
        sa.UniqueConstraint("id", "user_id", name=op.f("uq_users_enterprises_id_user_id")),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_users_enterprises_user_id_users"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["enterprise_id"],
            ["enterprises.id"],
            name=op.f("fk_users_enterprises_enterprise_id_enterprises"),
            ondelete="RESTRICT",
        ),
        **TABLE_OPTIONS,
    )
    op.create_index(
        "ix_users_enterprises_user_id_status_joined_at",
        "users_enterprises",
        ["user_id", "status", "joined_at"],
    )
    op.create_index(
        "ix_users_enterprises_enterprise_id_status", "users_enterprises", ["enterprise_id", "status"]
    )
    op.create_index("ix_users_enterprises_role_id", "users_enterprises", ["role_id"])

    # user_preferences: empresa predeterminada (LOG-04, LOG-05)
    op.create_table(
        "user_preferences",
        sa.Column("user_id", ID, autoincrement=False, nullable=False),
        sa.Column("default_membership_id", ID, nullable=True),
        sa.Column("updated_at", TIMESTAMP_MS, server_default=UPDATED_DEFAULT, nullable=False),
        sa.PrimaryKeyConstraint("user_id", name=op.f("pk_user_preferences")),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_user_preferences_user_id_users"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["default_membership_id", "user_id"],
            ["users_enterprises.id", "users_enterprises.user_id"],
            name=op.f("fk_user_preferences_default_membership_id_users_enterprises"),
            ondelete="RESTRICT",
        ),
        **TABLE_OPTIONS,
    )

    # auth_sessions: sesión y token Bearer (LOG-03, LOG-14, LOG-16, CU-06, CU-10, CU-11)
    op.create_table(
        "auth_sessions",
        sa.Column("id", sa.BINARY(length=16), nullable=False),
        sa.Column("token_hash", sa.BINARY(length=32), nullable=False),
        sa.Column("user_id", ID, nullable=False),
        sa.Column("active_membership_id", ID, nullable=False),
        sa.Column("auth_method", mysql.ENUM("password", "sso"), nullable=False),
        sa.Column(
            "device_type",
            mysql.ENUM("desktop", "mobile", "tablet", "unknown"),
            server_default=sa.text("'unknown'"),
            nullable=False,
        ),
        sa.Column("created_at", TIMESTAMP_MS, server_default=CREATED_DEFAULT, nullable=False),
        sa.Column("last_used_at", TIMESTAMP_MS, nullable=True),
        sa.Column("expires_at", TIMESTAMP_MS, nullable=False),
        sa.Column("revoked_at", TIMESTAMP_MS, nullable=True),
        sa.Column(
            "revoked_reason",
            mysql.ENUM(
                "logout",
                "switched",
                "user_suspended",
                "membership_revoked",
                "enterprise_disabled",
                "admin",
            ),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_auth_sessions")),
        sa.UniqueConstraint("token_hash", name=op.f("uq_auth_sessions_token_hash")),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_auth_sessions_user_id_users"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["active_membership_id", "user_id"],
            ["users_enterprises.id", "users_enterprises.user_id"],
            name=op.f("fk_auth_sessions_active_membership_id_users_enterprises"),
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "(revoked_at IS NULL) = (revoked_reason IS NULL)",
            name=op.f("ck_auth_sessions_revocation_consistent"),
        ),
        sa.CheckConstraint(
            "expires_at > created_at", name=op.f("ck_auth_sessions_expires_after_created")
        ),
        **TABLE_OPTIONS,
    )
    op.create_index(
        "ix_auth_sessions_active_membership_id_revoked_at_expires_at",
        "auth_sessions",
        ["active_membership_id", "revoked_at", "expires_at"],
    )
    op.create_index("ix_auth_sessions_user_id_revoked_at", "auth_sessions", ["user_id", "revoked_at"])

    # presence_connections: una fila por WebSocket (CU-07 a CU-10)
    op.create_table(
        "presence_connections",
        sa.Column("id", sa.BINARY(length=16), nullable=False),
        sa.Column("session_id", sa.BINARY(length=16), nullable=False),
        sa.Column("connected_at", TIMESTAMP_MS, server_default=CREATED_DEFAULT, nullable=False),
        sa.Column("last_seen_at", TIMESTAMP_MS, server_default=CREATED_DEFAULT, nullable=False),
        sa.Column("valid_until", TIMESTAMP_MS, nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_presence_connections")),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["auth_sessions.id"],
            name=op.f("fk_presence_connections_session_id_auth_sessions"),
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "valid_until >= connected_at",
            name=op.f("ck_presence_connections_valid_after_connected"),
        ),
        **TABLE_OPTIONS,
    )
    op.create_index(
        "ix_presence_connections_session_id_valid_until",
        "presence_connections",
        ["session_id", "valid_until"],
    )
    op.create_index("ix_presence_connections_valid_until", "presence_connections", ["valid_until"])


def downgrade() -> None:
    # Orden inverso. DROP TABLE elimina también los índices y las FK de cada tabla.
    op.drop_table("presence_connections")
    op.drop_table("auth_sessions")
    op.drop_table("user_preferences")
    op.drop_table("users_enterprises")
    op.drop_table("enterprises")
    op.drop_table("users")
