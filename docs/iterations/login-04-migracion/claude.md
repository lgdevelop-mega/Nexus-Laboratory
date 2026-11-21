# login-04-migracion · Modelos de persistencia y migración `0001` de Login

**Autor:** Claude Code · **Fecha:** 2026-11-20 · **Estado:** implementado, pendiente de revisión de Codex y del responsable.
**Instrucción aplicada:** `docs/agents/herdr-login-04-migraciones.md` (especificación de la sección 5) y `docs/agents/claude-login-implementacion.md` (parte 3).
**Rama:** `worktree/claude_worktree` · Sin commits ni PR.

## 0. Aprobaciones y orden de trabajo

| Fecha | Aprobación del responsable |
|---|---|
| 2026-11-20 | **M-1** aprobada (sin FK hacia catálogos inexistentes). |
| 2026-11-20 | **M-2** aprobada (`status` como ENUM; se retiran `me`, `id_sso`, `status_id` y `account_status`). |
| 2026-11-20 | **M-3** aprobada (`enterprise_sso_config` se difiere a `login-07-sso`). |
| 2026-11-20 | **M-4**: "dejarlos en 255 por ahora". **Todos los `VARCHAR` quedan en 255**, también los que la especificación tenía más cortos (`rfc` 13, `phone` 20, `postal_code` 10, `email` 254) y `enterprises.full_address`, que tenía 500. |
| 2026-11-20 | **M-5** aprobada (`ck_users_email_normalized`). |
| 2026-11-20 | **Autorización para iniciar `login-04` antes de `login-03-dominio`.** Es una excepción al orden de la sección 5 de la instrucción general. |

**Desviación del ciclo:** la instrucción pide presentar la propuesta, detenerse y esperar la aprobación. El responsable resolvió todas las decisiones (M-1 a M-5) y autorizó el inicio antes de que existiera este documento. Por eso la propuesta y la entrega se hicieron en la misma sesión. **Codex todavía no revisó la propuesta**; puede revisar directamente la entrega.

## 1. Objetivo

Modelos de persistencia de las tablas de Login y migración reversible `0001`. Son 6 tablas, porque `enterprise_sso_config` se difiere por M-3.

## 2. Comprobaciones previas (sección 2 de la instrucción)

| Comando | Resultado |
|---|---|
| `git rev-parse --show-toplevel` | `~/.herdr/worktrees/NEXUS_API_v2.0/worktree-claude-worktree` |
| `git branch --show-current` | `worktree/claude_worktree` (no es `develop` ni `master`). |
| `git status -s` | Archivos de `login-02-base` sin commit, los dos `.DS_Store` quitados del índice, y `docs/agents/claude-login-implementacion.md` y `docs/agents/herdr-login-04-migraciones.md`, que son ajenos. Los conservé sin cambios. |
| `ls alembic/env.py app/core/db.py pyproject.toml uv.lock` | Los cuatro existen. `alembic/versions/` estaba vacío. |
| Dependencias | No se agregó ninguna. `uv.lock` sin cambios. |

## 3. Archivos

| Archivo | Acción |
|---|---|
| `app/identity/login/infrastructure/persistence/__init__.py` | Creado (vacío). |
| `app/identity/login/infrastructure/persistence/models.py` | Creado: 6 modelos de SQLAlchemy 2.0 (`Mapped`, `mapped_column`) con tipos del dialecto MySQL, sin relaciones ORM. |
| `app/core/db.py` | Modificado **solo** en `import_models()`: importa los modelos de Login y actualiza su docstring. |
| `alembic/versions/0001_login_base.py` | Creado con `alembic revision --autogenerate -m "login base" --rev-id 0001` y reescrito a mano (sección 5). |
| `docs/iterations/login-04-migracion/claude.md` | Este archivo. |
| `docs/notion/login-04-migracion-v1.md`, `docs/notion/login-04-migracion-v2.md` | Notas para Notion. |
| `docs/notion/README.md` | Solo se agregaron dos filas al índice. |

## 4. Especificación implementada

Es la de la sección 5 de `herdr-login-04-migraciones.md`, con M-3 y M-4 aplicadas.

**Convenciones comunes:**
- Tablas `InnoDB`, `utf8mb4`, `utf8mb4_0900_ai_ci`.
- Fechas `DATETIME(3)` en UTC; `created_at` con `CURRENT_TIMESTAMP(3)` y `updated_at` con `... ON UPDATE CURRENT_TIMESTAMP(3)`.
- Claves: `BIGINT UNSIGNED AUTO_INCREMENT` en las tablas de catálogo y `BINARY(16)` en sesiones y conexiones.
- Todas las FK son `RESTRICT`, salvo `presence_connections.session_id`, que es `CASCADE`.

### Tablas, columnas y valores de los ENUM

| Tabla | Columnas | ENUM y valores por defecto |
|---|---|---|
| `users` | `id`, `email` (255, `utf8mb4_bin`), `password_hash` NULL, `status`, `name`, `second_name` NULL, `last_name`, `second_last_name` NULL, `phone_wa` NULL, `area_id` NULL, `created_at`, `updated_at` | `status`: `active` \| `suspended`, por defecto `active` |
| `enterprises` | `id`, `trade_name`, `company_name`, `rfc`, `website` NULL, `contact_name`, `email`, `phone`, `country_id`, `city_id`, `full_address`, `postal_code`, `status`, `sso_enabled`, `created_at`, `updated_at` | `status`: `active` \| `inactive`, por defecto `active`; `sso_enabled` `tinyint(1)`, por defecto 0 |
| `users_enterprises` | `id`, `user_id`, `enterprise_id`, `role_id`, `status`, `joined_at`, `status_changed_at` | `status`: `active` \| `suspended` \| `revoked`, por defecto `active` |
| `user_preferences` | `user_id` (PK), `default_membership_id` NULL, `updated_at` | — |
| `auth_sessions` | `id` BINARY(16), `token_hash` BINARY(32), `user_id`, `active_membership_id`, `auth_method`, `device_type`, `created_at`, `last_used_at` NULL, `expires_at`, `revoked_at` NULL, `revoked_reason` NULL | `auth_method`: `password` \| `sso`; `device_type`: `desktop` \| `mobile` \| `tablet` \| `unknown`, por defecto `unknown`; `revoked_reason`: `logout` \| `switched` \| `user_suspended` \| `membership_revoked` \| `enterprise_disabled` \| `admin` |
| `presence_connections` | `id` BINARY(16), `session_id` BINARY(16), `connected_at`, `last_seen_at`, `valid_until` | — |

### Restricciones e índices, con la regla que los respalda

| Nombre | Tipo | Definición | Respaldo |
|---|---|---|---|
| `uq_users_email` | UK | `users(email)` | LOG-07 (el correo identifica al usuario entre vías) |
| `ck_users_email_normalized` | CHECK | `email = LOWER(TRIM(email))` | LOG-07, M-5 |
| `ix_users_area_id` | Índice | `users(area_id)`, sin FK | M-1 |
| `uq_enterprises_rfc` | UK | `enterprises(rfc)` | LOG-01 |
| `ix_enterprises_country_id`, `ix_enterprises_city_id` | Índice | Sin FK | M-1 |
| `uq_users_enterprises_user_id_enterprise_id` | UK | `(user_id, enterprise_id)` | LOG-07, CA-05 (un ticket no recrea una membresía revocada) |
| `uq_users_enterprises_id_user_id` | UK | `(id, user_id)` | Destino de las FK compuestas |
| `fk_users_enterprises_user_id_users`, `fk_users_enterprises_enterprise_id_enterprises` | FK | RESTRICT | LOG-02, LOG-15 (no se borran: cambian de estado) |
| `ix_users_enterprises_user_id_status_joined_at` | Índice | `(user_id, status, joined_at)` | LOG-05 (membresía vigente más antigua) |
| `ix_users_enterprises_enterprise_id_status` | Índice | `(enterprise_id, status)` | Directorio de presencia por empresa (CU-07 a CU-10) |
| `ix_users_enterprises_role_id` | Índice | Sin FK | M-1 |
| `fk_user_preferences_user_id_users` | FK | RESTRICT | LOG-04 |
| `fk_user_preferences_default_membership_id_users_enterprises` | FK compuesta | `(default_membership_id, user_id) → users_enterprises(id, user_id)` | LOG-04, LOG-05 (la predeterminada es del mismo usuario) |
| `uq_auth_sessions_token_hash` | UK | `token_hash` (SHA-256) | Instrucción §3.1 (solo se guarda el hash) |
| `fk_auth_sessions_user_id_users` | FK | RESTRICT | LOG-03, LOG-16 |
| `fk_auth_sessions_active_membership_id_users_enterprises` | FK compuesta | `(active_membership_id, user_id) → users_enterprises(id, user_id)` | LOG-16, CU-06 (la sesión opera en una membresía del mismo usuario) |
| `ix_auth_sessions_active_membership_id_revoked_at_expires_at` | Índice | | LOG-16, CU-11 (revocar por pérdida de acceso) |
| `ix_auth_sessions_user_id_revoked_at` | Índice | | LOG-15 (revocar por suspensión del usuario) |
| `ck_auth_sessions_revocation_consistent` | CHECK | `(revoked_at IS NULL) = (revoked_reason IS NULL)` | LOG-14, LOG-16 |
| `ck_auth_sessions_expires_after_created` | CHECK | `expires_at > created_at` | LOG-16 |
| `fk_presence_connections_session_id_auth_sessions` | FK | CASCADE | CU-10 (el logout borra las conexiones) |
| `ix_presence_connections_session_id_valid_until` | Índice | | CU-08, CU-09 (heartbeat) |
| `ix_presence_connections_valid_until` | Índice | | Limpieza por lotes (CU-09) |
| `ck_presence_connections_valid_after_connected` | CHECK | `valid_until >= connected_at` | CU-07 |

Los nombres de PK son `pk_<tabla>`. MySQL crea además dos índices implícitos con el nombre de las FK compuestas: `fk_user_preferences_default_membership_id_users_enterprises` y `fk_auth_sessions_active_membership_id_users_enterprises`. Los crea porque ningún índice declarado empieza por esas dos columnas. `alembic check` los ignora (V-07).

## 5. Revisión a mano de la migración generada

| Problema de autogenerate | Corrección |
|---|---|
| Creaba `enterprises` antes que `users` y `auth_sessions` antes que `user_preferences`. | Orden de la sección 5.9: `users` → `enterprises` → `users_enterprises` → `user_preferences` → `auth_sessions` → `presence_connections`. |
| `downgrade()` hacía `DROP INDEX` antes de `DROP TABLE`. En MySQL falla con el error 1553 en los índices que son el único soporte de una FK: `ix_users_enterprises_enterprise_id_status`, `ix_auth_sessions_user_id_revoked_at` e `ix_presence_connections_session_id_valid_until`. | `downgrade()` solo elimina las tablas, en orden inverso. Los índices y las FK caen con cada tabla. |
| `sso_enabled` como `TINYINT(display_width=1)`: MySQL 8.4 avisa "Integer display width is deprecated". | `sa.Boolean()`. MySQL lo guarda como `tinyint(1)` sin aviso y Python recibe `bool`. |
| Los CHECK con nombre y los `server_default` con `ON UPDATE` | Autogenerate los incluyó correctamente; comprobado en V-04 y V-08. |

## 6. Verificaciones y resultados reales

Entorno: MySQL 8.4.13 en un contenedor desechable (`docker compose -p nexus-login04-verify`, puerto 3307, credenciales temporales), eliminado al terminar. Tu MySQL del puerto 3306 no se tocó y `.env` no se leyó.

| # | Verificación | Resultado |
|---|---|---|
| V-01 | `uv run ruff check . && uv run ruff format --check .` | OK (`All checks passed!`, 29 archivos formateados). El primer intento pidió reformatear `models.py`; ya está corregido. |
| V-02 | `uv run mypy app` | OK (18 archivos). |
| V-03 | `uv run lint-imports` | OK, 4 de 4 contratos. |
| V-04 | `alembic upgrade head --sql` con URL ficticia, guardado fuera del repositorio | OK: 123 líneas, 7 `CREATE TABLE` (6 + `alembic_version`), 10 `CREATE INDEX`, 7 FK, 4 CHECK. Todas las tablas son `InnoDB` y `utf8mb4_0900_ai_ci`, y `users.email` es `utf8mb4_bin`. |
| V-05 | Longitud de nombres | OK: el más largo mide 59 caracteres (`ix_auth_sessions_active_membership_id_revoked_at_expires_at` y `fk_user_preferences_default_membership_id_users_enterprises`). |
| V-06 | `upgrade head` → `downgrade base` → `upgrade head`, dos veces | OK, sin errores ni avisos tras el cambio a `Boolean`. `alembic current` = `0001 (head)`. |
| V-07 | `uv run alembic check` | OK: `No new upgrade operations detected.` No hubo falsos positivos por `ON UPDATE` ni por los índices implícitos. |
| V-08 | `SHOW CREATE TABLE` de las 6 tablas | Coinciden con la sección 4: tipos, nulabilidad, valores por defecto, collation, UK, FK, CHECK e índices. |
| V-09 | Integridad con datos ficticios (Ana y Bruno; Saga y Mega) | **16/16 como se esperaba** (detalle abajo). |
| V-10 | `uv run pytest` | `no tests ran`: todavía no hay pruebas. Sin regresiones. |

**Detalle de V-09:**

| Caso | Resultado |
|---|---|
| Correo duplicado | ERROR 1062 en `uq_users_email`. |
| Correo con mayúsculas / con espacio inicial | ERROR 3819 en `ck_users_email_normalized` (ambos). |
| Segunda membresía de Ana en Saga | ERROR 1062 en `uq_users_enterprises_user_id_enterprise_id`. |
| Preferencia de Bruno apuntando a una membresía de Ana | ERROR 1452 en `fk_user_preferences_default_membership_id_users_enterprises`. |
| Preferencia propia / preferencia NULL | OK / OK. |
| Sesión de Bruno con una membresía de Ana | ERROR 1452 en `fk_auth_sessions_active_membership_id_users_enterprises`. |
| `revoked_at` sin `revoked_reason` | ERROR 3819 en `ck_auth_sessions_revocation_consistent`. |
| `expires_at` anterior a `created_at` | ERROR 3819 en `ck_auth_sessions_expires_after_created`. |
| `token_hash` duplicado | ERROR 1062 en `uq_auth_sessions_token_hash`. |
| Borrar una membresía con sesiones | ERROR 1451 (RESTRICT). |
| Borrar una sesión con 2 conexiones | Quedan 0 conexiones (CASCADE). |
| `UPDATE` de un usuario | `updated_at` avanza (`ON UPDATE`). |

## 7. Interfaces para Codex

- **Modelos:** `app/identity/login/infrastructure/persistence/models.py`: `UserModel`, `EnterpriseModel`, `MembershipModel`, `UserPreferenceModel`, `AuthSessionModel` y `PresenceConnectionModel`.
- **Constantes de los ENUM:** `USER_STATUSES`, `ENTERPRISE_STATUSES`, `MEMBERSHIP_STATUSES`, `AUTH_METHODS`, `DEVICE_TYPES` y `REVOKED_REASONS`.
- **Nombres exactos:** tablas, columnas, valores de los ENUM y restricciones están en la sección 4.
- **Fuera de esta tarea:** no se crean puertos ni repositorios. Llegan con los casos de uso (los repositorios de cada parte que los necesite).
- **Reglas cubiertas por restricciones:** LOG-04, LOG-05, LOG-07, LOG-09 (vía `status` y el índice de membresías vigentes), LOG-15, LOG-16, CA-05 y CU-06 a CU-11.
- **Escenarios de integración:** los 16 casos de V-09 se ejecutaron con SQL manual. Si se autoriza una tarea de integración, Codex puede convertirlos en pruebas contra `nexus_test`, que aún no existe en `docker-compose.yml` (ver `login-02-base`).

## 8. Fuera de alcance

Repositorios, unidad de trabajo, casos de uso, endpoints, datos semilla, tablas de contraseñas o de catálogos del ERP, `enterprise_sso_config` (M-3) y cambios de dependencias.

## 9. Pendientes y observaciones

| ID | Tema |
|---|---|
| P-1 | **M-4 provisional:** antes de producción, revisar las longitudes reales. `full_address` bajó de 500 a 255 respecto a la especificación. |
| P-2 | `enterprises` no tiene un código corto. El contrato SSO de `login-01` usaba `enterprise_code`. `login-07-sso` debe decidir si identifica la empresa por `id`, por `rfc` o con una columna nueva (sería una migración nueva). |
| P-3 | La generación de UUIDv7 para `auth_sessions.id` y `presence_connections.id` llega con la tarea que inserte sesiones. Python 3.12 no la trae en la librería estándar; habrá que proponer cómo hacerlo. |
| P-4 | Las FK hacia catálogos (`area_id`, `country_id`, `city_id`, `role_id`) se agregarán en la migración del módulo de catálogos y roles (M-1). |
| P-5 | Notion: notas en `docs/notion/login-04-migracion-v1.md` y `-v2.md`, listas para publicar en NEXUS ERP. |

## Registro de entrega (2026-11-20)

- **Rama:** `worktree/claude_worktree`. **Sin commits ni PR**; los archivos de `login-02-base` y de esta tarea están sin seguimiento en el mismo worktree. Cuando autorices el commit, conviene separarlos en dos commits (instrucción §8).
- **Archivos:** sección 3.
- **Acordado frente a entregado:**
  - Especificación de la sección 5 con M-1 a M-5 aplicadas.
  - `sso_enabled` como `Boolean` (sigue siendo `tinyint(1)` en MySQL).
  - `downgrade()` simplificado por el error 1553.
- **Verificaciones:** sección 6. Las 10 se ejecutaron; V-10 no tiene pruebas que correr.
- **Traspaso a Codex:** sección 7.
