"""Login base: catálogos y tablas globales del módulo de Login (login-04-migracion, R2).

Revision ID: 0001
Revises:
Create Date: 2026-11-23

Especificación: docs/agents/herdr-login-04-r2-migraciones.md, sección 4. Propuesta aprobada:
docs/iterations/login-04-migracion/claude-r2.md (R2-01 a R2-08). Sustituye a la 0001 de R1
(commit e1563c8), que no se aplicó en ninguna base compartida (R2-08).

- Catálogos statuses, device_types y revoked_reasons en lugar de ENUM, con datos iniciales
  e id explícito. Las filas están definidas aquí, no se importan de app/.
- Sin áreas, países, ciudades, roles ni SSO.
- Sin server_default en las FK hacia catálogos: la aplicación siempre envía el id.
- downgrade() elimina solo las tablas, en orden inverso. Hacer DROP INDEX antes fallaría en
  MySQL (error 1553) en los índices que son el único soporte de una FK.
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

# Datos iniciales (sección 4.2). El código resuelve por name; el id fijo da el mismo
# resultado en todos los entornos.
STATUSES = [(1, "active"), (2, "inactive")]
DEVICE_TYPES = [(1, "unknown"), (2, "desktop"), (3, "mobile"), (4, "tablet")]
REVOKED_REASONS = [
    (1, "logout"),
    (2, "switched"),
    (3, "user_inactive"),
    (4, "membership_inactive"),
    (5, "enterprise_inactive"),
    (6, "admin"),
]


def _restrict_fk(table: str, column: str, target: str) -> sa.ForeignKeyConstraint:
    return sa.ForeignKeyConstraint(
        [column],
        [f"{target}.id"],
        name=op.f(f"fk_{table}_{column}_{target}"),
        ondelete="RESTRICT",
    )


def _create_catalog(table: str, rows: list[tuple[int, str]]) -> None:
    op.create_table(
        table,
        sa.Column("id", ID, autoincrement=True, nullable=False),
        sa.Column("name", VARCHAR_255, nullable=False),
        sa.Column("created_at", TIMESTAMP_MS, server_default=CREATED_DEFAULT, nullable=False),
        sa.Column("updated_at", TIMESTAMP_MS, server_default=UPDATED_DEFAULT, nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f(f"pk_{table}")),
        sa.UniqueConstraint("name", name=op.f(f"uq_{table}_name")),
        **TABLE_OPTIONS,
    )
    rows_table = sa.table(table, sa.column("id", ID), sa.column("name", VARCHAR_255))
    op.bulk_insert(rows_table, [{"id": row_id, "name": name} for row_id, name in rows])


def upgrade() -> None:
    # Catálogos con datos iniciales (R2-04, R2-05, R2-06)
    _create_catalog("statuses", STATUSES)
    _create_catalog("device_types", DEVICE_TYPES)
    _create_catalog("revoked_reasons", REVOKED_REASONS)

    # users: identidad global (LOG-07, LOG-08, LOG-15)
    op.create_table(
        "users",
        sa.Column("id", ID, autoincrement=True, nullable=False),
        sa.Column("email", mysql.VARCHAR(length=255, collation="utf8mb4_bin"), nullable=False),
        sa.Column("password_hash", VARCHAR_255, nullable=True),
        sa.Column("status_id", ID, nullable=False),
        sa.Column("name", VARCHAR_255, nullable=False),
        sa.Column("second_name", VARCHAR_255, nullable=True),
        sa.Column("last_name", VARCHAR_255, nullable=False),
        sa.Column("second_last_name", VARCHAR_255, nullable=True),
        sa.Column("phone_wa", VARCHAR_255, nullable=True),
        sa.Column("created_at", TIMESTAMP_MS, server_default=CREATED_DEFAULT, nullable=False),
        sa.Column("updated_at", TIMESTAMP_MS, server_default=UPDATED_DEFAULT, nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
        _restrict_fk("users", "status_id", "statuses"),
        sa.CheckConstraint("email = LOWER(TRIM(email))", name=op.f("ck_users_email_normalized")),
        **TABLE_OPTIONS,
    )
    op.create_index("ix_users_status_id", "users", ["status_id"])

    # enterprises: empresa y estado operativo (LOG-01, LOG-16)
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
        sa.Column("full_address", VARCHAR_255, nullable=False),
        sa.Column("postal_code", VARCHAR_255, nullable=False),
        sa.Column("status_id", ID, nullable=False),
        sa.Column("created_at", TIMESTAMP_MS, server_default=CREATED_DEFAULT, nullable=False),
        sa.Column("updated_at", TIMESTAMP_MS, server_default=UPDATED_DEFAULT, nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_enterprises")),
        sa.UniqueConstraint("rfc", name=op.f("uq_enterprises_rfc")),
        _restrict_fk("enterprises", "status_id", "statuses"),
        **TABLE_OPTIONS,
    )
    op.create_index("ix_enterprises_status_id", "enterprises", ["status_id"])

    # users_enterprises: membresías (LOG-02, LOG-05, LOG-07, LOG-15, CA-05)
    op.create_table(
        "users_enterprises",
        sa.Column("id", ID, autoincrement=True, nullable=False),
        sa.Column("user_id", ID, nullable=False),
        sa.Column("enterprise_id", ID, nullable=False),
        sa.Column("status_id", ID, nullable=False),
        sa.Column("joined_at", TIMESTAMP_MS, server_default=CREATED_DEFAULT, nullable=False),
        sa.Column(
            "status_changed_at", TIMESTAMP_MS, server_default=CREATED_DEFAULT, nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users_enterprises")),
        sa.UniqueConstraint(
            "user_id", "enterprise_id", name=op.f("uq_users_enterprises_user_id_enterprise_id")
        ),
        sa.UniqueConstraint("id", "user_id", name=op.f("uq_users_enterprises_id_user_id")),
        _restrict_fk("users_enterprises", "user_id", "users"),
        _restrict_fk("users_enterprises", "enterprise_id", "enterprises"),
        _restrict_fk("users_enterprises", "status_id", "statuses"),
        **TABLE_OPTIONS,
    )
    op.create_index(
        "ix_users_enterprises_user_id_status_id_joined_at",
        "users_enterprises",
        ["user_id", "status_id", "joined_at"],
    )
    op.create_index(
        "ix_users_enterprises_enterprise_id_status_id",
        "users_enterprises",
        ["enterprise_id", "status_id"],
    )
    op.create_index("ix_users_enterprises_status_id", "users_enterprises", ["status_id"])

    # user_preferences: empresa predeterminada (LOG-04, LOG-05)
    op.create_table(
        "user_preferences",
        sa.Column("user_id", ID, autoincrement=False, nullable=False),
        sa.Column("default_membership_id", ID, nullable=True),
        sa.Column("updated_at", TIMESTAMP_MS, server_default=UPDATED_DEFAULT, nullable=False),
        sa.PrimaryKeyConstraint("user_id", name=op.f("pk_user_preferences")),
        _restrict_fk("user_preferences", "user_id", "users"),
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
        sa.Column("device_type_id", ID, nullable=False),
        sa.Column("created_at", TIMESTAMP_MS, server_default=CREATED_DEFAULT, nullable=False),
        sa.Column("last_used_at", TIMESTAMP_MS, nullable=True),
        sa.Column("expires_at", TIMESTAMP_MS, nullable=False),
        sa.Column("revoked_at", TIMESTAMP_MS, nullable=True),
        sa.Column("revoked_reason_id", ID, nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_auth_sessions")),
        sa.UniqueConstraint("token_hash", name=op.f("uq_auth_sessions_token_hash")),
        _restrict_fk("auth_sessions", "user_id", "users"),
        sa.ForeignKeyConstraint(
            ["active_membership_id", "user_id"],
            ["users_enterprises.id", "users_enterprises.user_id"],
            name=op.f("fk_auth_sessions_active_membership_id_users_enterprises"),
            ondelete="RESTRICT",
        ),
        _restrict_fk("auth_sessions", "device_type_id", "device_types"),
        _restrict_fk("auth_sessions", "revoked_reason_id", "revoked_reasons"),
        sa.CheckConstraint(
            "(revoked_at IS NULL) = (revoked_reason_id IS NULL)",
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
    op.create_index("ix_auth_sessions_device_type_id", "auth_sessions", ["device_type_id"])
    op.create_index("ix_auth_sessions_revoked_reason_id", "auth_sessions", ["revoked_reason_id"])

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
    # Orden inverso. DROP TABLE elimina también índices, FK y datos de catálogo.
    op.drop_table("presence_connections")
    op.drop_table("auth_sessions")
    op.drop_table("user_preferences")
    op.drop_table("users_enterprises")
    op.drop_table("enterprises")
    op.drop_table("users")
    op.drop_table("revoked_reasons")
    op.drop_table("device_types")
    op.drop_table("statuses")
