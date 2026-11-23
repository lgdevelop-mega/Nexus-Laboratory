# login-04-migracion · Revisión R2 · Catálogos en lugar de ENUM y reducción de alcance

**Autor:** Claude Code · **Fecha:** 2026-11-23 · **Estado:** propuesta **aprobada por el responsable el 2026-11-23**; Codex no la revisó antes de la aprobación y revisará la entrega.
**Sustituye en parte a:** `claude.md` de esta carpeta (entrega R1, migración `0001` del commit `e1563c8`, fusionada en `develop` en `98a841c`).
**Rama:** `worktree/claude_worktree` · Sin código todavía.

## 0. Decisiones del responsable (2026-11-23)

| Id | Decisión | Efecto |
|---|---|---|
| R2-01 | Se quita todo lo que no tiene información todavía, **también de las migraciones**: áreas, países y ciudades. | Se eliminan `users.area_id`, `enterprises.country_id` y `enterprises.city_id`. M-1 queda sin objeto. |
| R2-02 | Se descartan los roles por empresa por ahora. Solo interesa un inicio de sesión correcto con lo que existe. | Se elimina `users_enterprises.role_id`. |
| R2-03 | El SSO se pospone. | Se eliminan `enterprises.sso_enabled` y `auth_sessions.auth_method`. M-3 sigue vigente (`enterprise_sso_config` en `login-07-sso`). |
| R2-04 | Se quitan los ENUM. Estatus solo `active` e `inactive`, en una tabla `statuses(id, name, created_at, updated_at)`. | `users`, `enterprises` y `users_enterprises` usan `status_id` con FK. Sustituye a M-2 en la parte de estatus. |
| R2-05 | `device_type` y `revoked_reason` pasan a tablas de catálogo. | Tablas `device_types` y `revoked_reasons` con la misma forma que `statuses`. |
| R2-06 | Los nombres de estatus son `active` / `inactive`. El código los busca por nombre. | `UNIQUE(name)` en los tres catálogos. |
| R2-07 | `users.password_hash` sigue opcional (NULL), pensando en el SSO futuro. | Sin cambio. El dominio rechaza el inicio de sesión de un usuario sin contraseña. |
| R2-08 | `0001` no se aplicó en ninguna base compartida: **se rehace `0001`**, no se crea `0002`. | Una sola migración limpia. Quien la tenga aplicada en una base local hace `alembic downgrade base` antes de actualizar. |

Siguen vigentes: M-4 (todos los `VARCHAR` en 255), M-5 (`ck_users_email_normalized`), el token Bearer con `token_hash`, las FK compuestas y los CHECK de fechas. Siguen retirados `id_sso`, `me` y `account_status`.

## 1. Catálogos nuevos

Las tres tablas tienen la misma forma:

| Columna | Tipo | Nulo | Default |
|---|---|---|---|
| `id` | BIGINT UNSIGNED AUTO_INCREMENT | NO | — |
| `name` | VARCHAR(255) | NO | — |
| `created_at` | DATETIME(3) | NO | CURRENT_TIMESTAMP(3) |
| `updated_at` | DATETIME(3) | NO | CURRENT_TIMESTAMP(3) ON UPDATE |

Restricciones: `pk_<tabla>`, `uq_<tabla>_name`.

### Datos iniciales

Se insertan dentro de `0001` con `op.bulk_insert`, con `id` explícito para que el resultado sea igual en todos los entornos. El código no depende del `id`: resuelve por `name`.

| Tabla | `id` · `name` |
|---|---|
| `statuses` | 1 · `active`, 2 · `inactive` |
| `device_types` | 1 · `unknown`, 2 · `desktop`, 3 · `mobile`, 4 · `tablet` |
| `revoked_reasons` | 1 · `logout`, 2 · `switched`, 3 · `user_inactive`, 4 · `membership_inactive`, 5 · `enterprise_inactive`, 6 · `admin` |

Los motivos `user_suspended`, `membership_revoked` y `enterprise_disabled` de R1 se renombran a `*_inactive`, porque ya no existen esos estados.

## 2. Tablas de Login después de R2

Todas las FK nuevas son `RESTRICT`: un valor de catálogo en uso no se puede borrar.

| Tabla | Columnas | Cambios frente a R1 |
|---|---|---|
| `users` | `id`, `email`, `password_hash` NULL, `status_id`, `name`, `second_name` NULL, `last_name`, `second_last_name` NULL, `phone_wa` NULL, `created_at`, `updated_at` | `status` ENUM → `status_id` FK. Sin `area_id`. |
| `enterprises` | `id`, `trade_name`, `company_name`, `rfc`, `website` NULL, `contact_name`, `email`, `phone`, `full_address`, `postal_code`, `status_id`, `created_at`, `updated_at` | `status` ENUM → `status_id` FK. Sin `country_id`, `city_id` ni `sso_enabled`. |
| `users_enterprises` | `id`, `user_id`, `enterprise_id`, `status_id`, `joined_at`, `status_changed_at` | `status` ENUM → `status_id` FK. Sin `role_id`. |
| `user_preferences` | `user_id`, `default_membership_id` NULL, `updated_at` | Sin cambios. |
| `auth_sessions` | `id`, `token_hash`, `user_id`, `active_membership_id`, `device_type_id`, `created_at`, `last_used_at` NULL, `expires_at`, `revoked_at` NULL, `revoked_reason_id` NULL | Sin `auth_method`. `device_type` → `device_type_id` FK. `revoked_reason` → `revoked_reason_id` FK. |
| `presence_connections` | `id`, `session_id`, `connected_at`, `last_seen_at`, `valid_until` | Sin cambios. |

**Sin valores por defecto en las FK.** R1 tenía `DEFAULT 'active'` y `DEFAULT 'unknown'`. Con FK, un default tendría que ser un `id` fijo en el esquema. Propongo que el repositorio resuelva el `id` por `name` y siempre lo envíe. Si el responsable prefiere el default en la base, se usa `server_default '1'`, que depende de los `id` de la sección 1.

### Restricciones e índices que cambian

| Nombre | Tipo | Definición |
|---|---|---|
| `fk_users_status_id_statuses` | FK | `users.status_id → statuses.id` |
| `ix_users_status_id` | Índice | `users(status_id)` |
| `fk_enterprises_status_id_statuses` | FK | `enterprises.status_id → statuses.id` |
| `ix_enterprises_status_id` | Índice | `enterprises(status_id)` |
| `fk_users_enterprises_status_id_statuses` | FK | `users_enterprises.status_id → statuses.id` |
| `ix_users_enterprises_user_id_status_id_joined_at` | Índice | Sustituye a `..._user_id_status_joined_at` (LOG-05) |
| `ix_users_enterprises_enterprise_id_status_id` | Índice | Sustituye a `..._enterprise_id_status` |
| `ix_users_enterprises_status_id` | Índice | Soporte de la FK: los dos anteriores no empiezan por `status_id` |
| `fk_auth_sessions_device_type_id_device_types` | FK | `auth_sessions.device_type_id → device_types.id` |
| `ix_auth_sessions_device_type_id` | Índice | Soporte de la FK |
| `fk_auth_sessions_revoked_reason_id_revoked_reasons` | FK | `auth_sessions.revoked_reason_id → revoked_reasons.id` (50 caracteres, menos de 64) |
| `ix_auth_sessions_revoked_reason_id` | Índice | Soporte de la FK |
| `ck_auth_sessions_revocation_consistent` | CHECK | `(revoked_at IS NULL) = (revoked_reason_id IS NULL)` |

Se eliminan `ix_users_area_id`, `ix_enterprises_country_id`, `ix_enterprises_city_id` y `ix_users_enterprises_role_id`.

Los índices de soporte se declaran explícitos para que `alembic check` no detecte diferencias con los índices que MySQL crea solo para cada FK.

**Orden de creación en `0001`:** `statuses`, `device_types`, `revoked_reasons` → datos iniciales → `users` → `enterprises` → `users_enterprises` → `user_preferences` → `auth_sessions` → `presence_connections`. `downgrade()` borra las tablas en orden inverso.

## 3. Impacto en las reglas de negocio

Con dos estados, varias reglas que hablaban de "suspendido" o "revocado" pasan a "inactivo". No cambia el esquema, pero `login-03-dominio` lo debe reflejar:

| Regla | R1 | R2 |
|---|---|---|
| Usuario suspendido no inicia sesión (LOG-15) | `users.status = suspended` | `status = inactive` |
| Empresa deshabilitada revoca sesiones (LOG-16) | `enterprises.status = inactive` | Igual, motivo `enterprise_inactive` |
| Membresía revocada no se recrea con un ticket (CA-05) | `status = revoked` | `status = inactive`; la UK `(user_id, enterprise_id)` sigue impidiendo una segunda fila |
| Empresa elegible para iniciar sesión (LOG-05) | Membresía `active` más antigua | Igual, con `status_id` de `active` |

Ya no se distingue entre una membresía suspendida temporalmente y una revocada de forma definitiva. Si después hace falta, se agrega un valor al catálogo sin cambiar el esquema.

## 4. Interfaces para Codex

- **Modelos:** `app/identity/login/infrastructure/persistence/models.py` agrega `StatusModel`, `DeviceTypeModel` y `RevokedReasonModel`, y quita las constantes de ENUM. Las constantes de nombres (`"active"`, `"inactive"`, etc.) pasan a vivir en el dominio en `login-03-dominio`.
- **Datos iniciales:** constantes con `(id, name)` en la migración, no importadas de la app, para que la migración no cambie si cambia el código.
- **Casos que Codex puede preparar:**
  - Insertar `users` con un `status_id` inexistente falla con error 1452.
  - Borrar `statuses` con `name = active` en uso falla con error 1451.
  - Insertar un segundo `statuses` con `name = active` falla con error 1062.
  - `auth_sessions` con `revoked_at` y sin `revoked_reason_id` falla con error 3819.
  - Las 16 pruebas de integridad de R1 se adaptan a `status_id`.

## 5. Verificaciones previstas

Las mismas V-01 a V-10 de `docs/agents/herdr-login-04-migraciones.md`: ruff, mypy, lint-imports, SQL fuera de línea, ida y vuelta en un MySQL 8.4 desechable, `alembic check` sin diferencias y longitud de nombres ≤ 64. Se agrega: los tres catálogos tienen exactamente las filas de la sección 1 después de `upgrade`.

## 6. Aprobación y siguiente paso

| Fecha | Aprobación |
|---|---|
| 2026-11-23 | El responsable aprueba R2 completa (R2-01 a R2-08 y el diseño de las secciones 1 a 5), incluida la propuesta de **no** poner valores por defecto en las FK hacia catálogos. |

Instrucción de construcción para el agente de herdr: `docs/agents/herdr-login-04-r2-migraciones.md`. El agente registra su entrega en la sección 7 de este archivo.

## 7. Registro de entrega (2026-11-23)

**Estado:** implementado, pendiente de revisión de Codex. Sin commit ni PR (no indicados por el responsable).

### 7.1 Comprobaciones previas y base del trabajo

| Comprobación | Resultado |
|---|---|
| Worktree / rama | `~/.herdr/worktrees/NEXUS_API_v2.0/worktree-claude-worktree` · `worktree/claude_worktree` (no es `develop` ni `master`). |
| `git log --oneline -3` | `e1563c8 migraciones_login_04` · `1fb12f1 iteration-login-01` · `a42cab6 base project`. **Commit de partida: `e1563c8`** (R1). |
| Commits de `develop` | **No se trajeron** (por ejemplo `0d22731 fix main.py`). La rama sigue en `e1563c8` más los cambios de esta tarea. |
| `git status -s` al empezar | Cambios ajenos que conservé: `docs/agents/claude-login-implementacion.md` (modificado), y `docs/agents/herdr-login-04-r2-migraciones.md` y este archivo (sin seguimiento). |
| `0001` de R1 aplicada en bases locales | No en las mías: las verificaciones de R1 usaron contenedores desechables que ya se eliminaron. |
| Archivos de la tarea | `models.py` y `0001_login_base.py` existían. |

### 7.2 Archivos modificados

| Archivo | Cambio |
|---|---|
| `app/identity/login/infrastructure/persistence/models.py` | Reescrito. Se agregan `StatusModel`, `DeviceTypeModel` y `RevokedReasonModel`. Se quitan las constantes de ENUM y los imports de `ENUM` y `Boolean`. `status_id`, `device_type_id` y `revoked_reason_id` son FK `RESTRICT` sin `server_default`, con índice explícito. Se eliminan `area_id`, `country_id`, `city_id`, `role_id`, `sso_enabled` y `auth_method`. |
| `alembic/versions/0001_login_base.py` | Reescrita a mano (sin autogenerate), con `revision = "0001"` y `down_revision = None`. Los tres catálogos se crean con `op.bulk_insert` y `id` explícito; las filas son constantes de la migración y no se importan de `app/`. `downgrade()` solo hace `drop_table`, en orden inverso. |
| `docs/iterations/login-04-migracion/claude-r2.md` | Solo esta sección 7. |
| `docs/notion/login-04-migracion-v3.md` y `docs/notion/README.md` | Nota v3 nueva y una fila en el índice. |

No toqué `app/core/db.py`, R1 (`claude.md`), las notas v1 y v2, `docs/agents/` ni `uv.lock`. No se instalaron dependencias.

### 7.3 Aprobado frente a entregado

Se entregó tal como se aprobó (secciones 0 a 5, y la sección 4 de la instrucción). Hay tres matices:

| Tema | Detalle |
|---|---|
| V-04, número de `INSERT` | La instrucción esperaba "los 3 `INSERT` de catálogos". En modo `--sql`, Alembic escribe **un `INSERT` por fila**: aparecen 12 (2 + 4 + 6), más el de `alembic_version`. Con base real, `bulk_insert` hace un `executemany` por catálogo. El contenido es el esperado (V-11). |
| Docstring de `import_models()` | Sigue diciendo "6 tablas" (de R1). La instrucción prohíbe tocar `app/core/db.py`, así que queda pendiente para la próxima tarea que lo modifique. Es solo un comentario; el import es correcto. |
| `docker-compose.yml` | Ahora lo ignora `.gitignore` (cambio del responsable) y no está en el commit `e1563c8`. Usé la copia local para V-06. El `README.md` aún lo menciona como parte del repositorio. |

### 7.4 Verificaciones y resultados reales

MySQL 8.4 en un contenedor desechable (`docker compose -p nexus-login04r2-verify`, puerto 3307, credenciales temporales en variables de entorno), eliminado al terminar. `.env` no se leyó; el MySQL local del puerto 3306 no se tocó.

| # | Comando o método | Resultado |
|---|---|---|
| V-01 | `uv run ruff check . && uv run ruff format --check .` | OK, tras acortar una línea de 101 caracteres del docstring de `models.py` (primer intento: E501). |
| V-02 | `uv run mypy app` | OK (18 archivos). |
| V-03 | `uv run lint-imports` | OK, 4 de 4. |
| V-04 | `alembic upgrade head --sql` con URL ficticia, guardado fuera del repositorio | OK: **10 `CREATE TABLE`** (9 + `alembic_version`), 12 `INSERT` de catálogos, **0 `ENUM`**, 11 `CREATE INDEX`, 12 FK y 4 CHECK. Ninguna aparición de `area_id`, `country_id`, `city_id`, `role_id`, `sso_enabled` ni `auth_method`. |
| V-05 | Longitud de nombres | OK: el máximo es 59. `fk_auth_sessions_revoked_reason_id_revoked_reasons` aparece (50). |
| V-06 | `upgrade head` → `downgrade base` → `upgrade head` → `downgrade base` → `upgrade head` | OK, sin errores ni avisos. `alembic current` = `0001 (head)`. |
| V-07 | `uv run alembic check` | OK: `No new upgrade operations detected.` |
| V-08 | `SHOW CREATE TABLE` de las 9 tablas | Coincide con la sección 4 de la instrucción. 0 apariciones de columnas retiradas o de `enum(`. Solo las dos FK compuestas conservan su índice implícito (igual que en R1). Las 5 FK hacia catálogos usan los índices explícitos. |
| V-09 | Integridad con datos ficticios (Ana, Bruno, Saga, Mega) | **24/24 como se esperaba** (detalle abajo). |
| V-10 | `uv run pytest` | `no tests ran`: aún no hay pruebas. Sin regresiones. |
| V-11 | `SELECT id, name` de los catálogos tras `upgrade` | `statuses`: 1·active, 2·inactive. `device_types`: 1·unknown, 2·desktop, 3·mobile, 4·tablet. `revoked_reasons`: 1·logout, 2·switched, 3·user_inactive, 4·membership_inactive, 5·enterprise_inactive, 6·admin. **Exacto.** |

**Detalle de V-09:**

| Caso | Resultado |
|---|---|
| `users.status_id = 99` | 1452 `fk_users_status_id_statuses` |
| `users` sin `status_id` | 1364 "doesn't have a default value" (confirma que no hay `server_default`) |
| Borrar `statuses` `active` en uso | 1451 |
| Segundo `statuses` con `name = 'active'` | 1062 `uq_statuses_name` |
| Correo duplicado / con mayúsculas | 1062 `uq_users_email` / 3819 `ck_users_email_normalized` |
| Segunda membresía de Ana en Saga | 1062 `uq_users_enterprises_user_id_enterprise_id` |
| Membresía / empresa con `status_id` inexistente | 1452 / 1452 |
| Preferencia de Bruno a una membresía de Ana | 1452 (FK compuesta) |
| Preferencia propia y preferencia NULL | OK |
| Sesión de Bruno con una membresía de Ana | 1452 (FK compuesta) |
| `device_type_id` inexistente | 1452 `fk_auth_sessions_device_type_id_device_types` |
| `revoked_at` sin `revoked_reason_id` / `revoked_reason_id` sin `revoked_at` | 3819 / 3819 `ck_auth_sessions_revocation_consistent` |
| `revoked_reason_id` inexistente | 1452 `fk_auth_sessions_revoked_reason_id_revoked_reasons` |
| `expires_at` anterior a `created_at` | 3819 `ck_auth_sessions_expires_after_created` |
| Sesión válida, sesión revocada válida (`logout`) y 2 conexiones | OK |
| `token_hash` duplicado | 1062 |
| Borrar un `device_types` en uso / una membresía con sesiones | 1451 / 1451 |
| Borrar una sesión con 2 conexiones | Quedan 0 conexiones (CASCADE) |
| `UPDATE` de un usuario | `updated_at` avanza |
| Inactivar una membresía (`status_id` → `inactive`, resuelto por `name`) | OK |

### 7.5 Pendientes y traspaso a Codex

**Nombres exactos:**

| Tabla | Columnas | Restricciones e índices |
|---|---|---|
| `statuses`, `device_types`, `revoked_reasons` | `id`, `name`, `created_at`, `updated_at` | `pk_<tabla>`, `uq_<tabla>_name` |
| `users` | `id`, `email`, `password_hash`, `status_id`, `name`, `second_name`, `last_name`, `second_last_name`, `phone_wa`, `created_at`, `updated_at` | `pk_users`, `uq_users_email`, `ck_users_email_normalized`, `fk_users_status_id_statuses`, `ix_users_status_id` |
| `enterprises` | `id`, `trade_name`, `company_name`, `rfc`, `website`, `contact_name`, `email`, `phone`, `full_address`, `postal_code`, `status_id`, `created_at`, `updated_at` | `pk_enterprises`, `uq_enterprises_rfc`, `fk_enterprises_status_id_statuses`, `ix_enterprises_status_id` |
| `users_enterprises` | `id`, `user_id`, `enterprise_id`, `status_id`, `joined_at`, `status_changed_at` | `pk_users_enterprises`, `uq_users_enterprises_user_id_enterprise_id`, `uq_users_enterprises_id_user_id`, `fk_users_enterprises_{user_id_users,enterprise_id_enterprises,status_id_statuses}`, `ix_users_enterprises_user_id_status_id_joined_at`, `ix_users_enterprises_enterprise_id_status_id`, `ix_users_enterprises_status_id` |
| `user_preferences` | `user_id`, `default_membership_id`, `updated_at` | `pk_user_preferences`, `fk_user_preferences_user_id_users`, `fk_user_preferences_default_membership_id_users_enterprises` |
| `auth_sessions` | `id`, `token_hash`, `user_id`, `active_membership_id`, `device_type_id`, `created_at`, `last_used_at`, `expires_at`, `revoked_at`, `revoked_reason_id` | `pk_auth_sessions`, `uq_auth_sessions_token_hash`, `fk_auth_sessions_user_id_users`, `fk_auth_sessions_active_membership_id_users_enterprises`, `fk_auth_sessions_device_type_id_device_types`, `fk_auth_sessions_revoked_reason_id_revoked_reasons`, `ix_auth_sessions_active_membership_id_revoked_at_expires_at`, `ix_auth_sessions_user_id_revoked_at`, `ix_auth_sessions_device_type_id`, `ix_auth_sessions_revoked_reason_id`, `ck_auth_sessions_revocation_consistent`, `ck_auth_sessions_expires_after_created` |
| `presence_connections` | `id`, `session_id`, `connected_at`, `last_seen_at`, `valid_until` | `pk_presence_connections`, `fk_presence_connections_session_id_auth_sessions` (CASCADE), `ix_presence_connections_session_id_valid_until`, `ix_presence_connections_valid_until`, `ck_presence_connections_valid_after_connected` |

**Catálogos:** las filas son las de V-11.

**Modelos:** `app/identity/login/infrastructure/persistence/models.py`. Los repositorios llegarán en una tarea posterior; deben resolver los `id` por `name`.

**Casos de V-09 no ejecutados:** ninguno. Los 24 se ejecutaron con SQL manual y pueden convertirse en pruebas de integración cuando se autorice esa tarea (no existe aún una base `nexus_test`).

**Pendientes:**
- Docstring de `import_models()` (sección 7.3).
- Decidir si `docker-compose.yml` vuelve al repositorio o se ajusta el `README.md` (sección 7.3).
- Traer `develop` a esta rama cuando el responsable lo autorice.
- La entrada BIT-0003 de la bitácora la registra Claude al revisar esta entrega (instrucción §6).
