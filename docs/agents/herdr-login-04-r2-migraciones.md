# Instrucción para un agente Claude en herdr · Rehacer la migración `0001` de Login (`login-04-migracion`, revisión R2)

**Destinatario:** un agente Claude Code que se ejecuta desde herdr sin el historial de la conversación donde se tomaron estas decisiones.
**Fecha:** 2026-11-23 · **Estado:** lista para ejecutar. **El responsable ya aprobó el alcance** (R2, 2026-11-23): no hace falta una propuesta nueva ni esperar otra aprobación antes de implementar.
**Tarea:** `login-04-migracion`, revisión R2. Codex usa el mismo identificador.
**Sustituye:** la sección 5 de `docs/agents/herdr-login-04-migraciones.md` (R1). El resto de esa instrucción (reglas, verificaciones, Notion, entrega) sigue vigente salvo donde este archivo diga otra cosa.

Este archivo contiene todo lo necesario. **La especificación de la sección 4 es suficiente por sí sola:** no necesitas leer Notion. Si algo no está resuelto aquí ni en las fuentes de la sección 1, detente y pregunta al responsable.

---

## 0. Resumen

1. Leer las reglas del proyecto (sección 1).
2. Comprobar el worktree, la rama y el estado de `0001` (sección 2).
3. Reescribir `models.py` y `alembic/versions/0001_login_base.py` según la sección 4. **No se crea `0002`**: `0001` no se aplicó en ninguna base compartida (decisión R2-08).
4. Verificar (sección 5).
5. Registrar la entrega en `docs/iterations/login-04-migracion/claude-r2.md`, documentar la versión en Notion y entregar (secciones 6 y 7).

**Prohibido en esta tarea:**
- Repositorios, unidad de trabajo, casos de uso, endpoints y lógica de dominio.
- Tablas de áreas, países, ciudades, roles o SSO, y cualquier columna que apunte a ellas.
- ENUM de MySQL en cualquier columna.
- Instalar o cambiar dependencias.
- Leer, abrir o mostrar `.env`.
- Modificar `docs/iterations/login-04-migracion/claude.md` (registro de R1) o las notas `docs/notion/login-04-migracion-v1.md` y `-v2.md`.
- Editar páginas de Notion existentes.
- Hacer merge, rebase o trabajar en `develop` o `master`.

## 1. Lectura obligatoria, en este orden

1. `AGENTS.md` y `CLAUDE.md`: ciclo de trabajo y capas.
2. `codex.md` y `docs/agents/codex.md`: qué espera Codex.
3. `docs/agents/claude-login-implementacion.md`: instrucción general del módulo de Login.
4. `docs/iterations/login-04-migracion/claude-r2.md`: **la propuesta R2 aprobada**, con las decisiones R2-01 a R2-08 y el impacto en las reglas.
5. `docs/iterations/login-04-migracion/claude.md`: la entrega R1 que vas a sustituir (qué se corrigió a mano en la migración generada y por qué; en particular, `downgrade()` solo borra tablas porque borrar índices antes provoca el error 1553 de MySQL).
6. `docs/agents/herdr-login-04-migraciones.md`: secciones 6 (verificaciones), 7 (Notion) y 8 (entrega) siguen vigentes.
7. `app/core/db.py` (`Base`, `NAMING_CONVENTION`, `import_models()`), `alembic/env.py`, el `models.py` y la `0001` actuales.

## 2. Comprobaciones previas

```bash
git rev-parse --show-toplevel
git branch --show-current
git status -s
git log --oneline -3
ls app/identity/login/infrastructure/persistence/models.py alembic/versions/0001_login_base.py
```

- **Worktree y rama:** `~/.herdr/worktrees/NEXUS_API_v2.0/worktree-claude-worktree`, rama `worktree/claude_worktree`. Si estás en `develop` o `master`, detente.
- **Base del trabajo:** R1 está en el commit `e1563c8`, que `develop` ya fusionó (`98a841c`). `develop` tiene además commits que esta rama no tiene (por ejemplo `0d22731 fix main.py`). **No los traigas** sin autorización del responsable; anótalo en la entrega.
- **Cambios ajenos:** `docs/iterations/login-04-migracion/claude-r2.md` y este archivo pueden estar sin commit. Son del responsable y de Claude; consérvalos y solo agrega tu registro en la sección 7 de `claude-r2.md`.
- **Bases locales:** si tienes `0001` (R1) aplicada en tu MySQL local, ejecuta `uv run alembic downgrade base` **antes** de reescribir la migración. Usa siempre un MySQL desechable para la ida y vuelta.

## 3. Archivos de la tarea

| Archivo | Acción |
|---|---|
| `app/identity/login/infrastructure/persistence/models.py` | Reescribir según la sección 4. Quitar las constantes de ENUM (`USER_STATUSES`, `ENTERPRISE_STATUSES`, `MEMBERSHIP_STATUSES`, `AUTH_METHODS`, `DEVICE_TYPES`, `REVOKED_REASONS`) y el import de `ENUM` y `Boolean`. Agregar `StatusModel`, `DeviceTypeModel` y `RevokedReasonModel`. Sin relaciones ORM ni lógica. |
| `alembic/versions/0001_login_base.py` | Reescribir. Mantener `revision = "0001"` y `down_revision = None`. Puedes regenerarla con `uv run alembic revision --autogenerate -m "login base" --rev-id 0001` contra una base vacía (borra antes el archivo anterior) y después **revisarla a mano** contra la sección 4. |
| `app/core/db.py` | Sin cambios. `import_models()` ya importa los modelos de Login. |
| `docs/iterations/login-04-migracion/claude-r2.md` | Completar solo la sección 7, "Registro de entrega". |
| `docs/notion/login-04-migracion-v3.md` y `docs/notion/README.md` | Solo si no puedes publicar en Notion (sección 6). |

## 4. Especificación

### 4.1 Convenciones (sin cambios respecto a R1)

- `InnoDB`, `utf8mb4`, `utf8mb4_0900_ai_ci`; `users.email` usa `utf8mb4_bin`.
- Fechas `DATETIME(3)` en UTC. `created_at` con `CURRENT_TIMESTAMP(3)`; `updated_at` con `CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3)`.
- Claves `BIGINT UNSIGNED AUTO_INCREMENT`, salvo `auth_sessions.id` y `presence_connections.id`, que son `BINARY(16)` sin default.
- **Todos los `VARCHAR` son de 255** (M-4).
- Nombres de restricciones: los produce `NAMING_CONVENTION`. No la cambies. Ningún nombre supera 64 caracteres.
- Todas las FK son `RESTRICT`, salvo `presence_connections.session_id`, que es `CASCADE`.
- **Ninguna FK hacia un catálogo tiene `server_default`** (aprobado). La aplicación siempre envía el `id`.

### 4.2 Catálogos: `statuses`, `device_types`, `revoked_reasons`

Las tres tablas tienen la misma forma:

| Columna | Tipo | Nulo | Default |
|---|---|---|---|
| `id` | BIGINT UNSIGNED AUTO_INCREMENT | NO | — |
| `name` | VARCHAR(255) | NO | — |
| `created_at` | DATETIME(3) | NO | CURRENT_TIMESTAMP(3) |
| `updated_at` | DATETIME(3) | NO | CURRENT_TIMESTAMP(3) ON UPDATE |

Restricciones: `pk_<tabla>` y `uq_<tabla>_name` (`name`).

**Datos iniciales.** Se insertan en `upgrade()` con `op.bulk_insert`, justo después de crear cada catálogo, con `id` explícito. Define las filas como constantes **dentro de la migración**; no las importes de `app/`.

| Tabla | Filas (`id`, `name`) |
|---|---|
| `statuses` | (1, `active`), (2, `inactive`) |
| `device_types` | (1, `unknown`), (2, `desktop`), (3, `mobile`), (4, `tablet`) |
| `revoked_reasons` | (1, `logout`), (2, `switched`), (3, `user_inactive`), (4, `membership_inactive`), (5, `enterprise_inactive`), (6, `admin`) |

Para `op.bulk_insert` necesitas un `sa.table(...)` ligero con las columnas `id` y `name`; `created_at` y `updated_at` toman su default.

### 4.3 `users` (LOG-07, LOG-08, LOG-15)

| Columna | Tipo | Nulo | Default |
|---|---|---|---|
| `id` | BIGINT UNSIGNED AUTO_INCREMENT | NO | — |
| `email` | VARCHAR(255) COLLATE utf8mb4_bin | NO | — |
| `password_hash` | VARCHAR(255) | SÍ | NULL |
| `status_id` | BIGINT UNSIGNED | NO | — |
| `name` | VARCHAR(255) | NO | — |
| `second_name` | VARCHAR(255) | SÍ | NULL |
| `last_name` | VARCHAR(255) | NO | — |
| `second_last_name` | VARCHAR(255) | SÍ | NULL |
| `phone_wa` | VARCHAR(255) | SÍ | NULL |
| `created_at` | DATETIME(3) | NO | CURRENT_TIMESTAMP(3) |
| `updated_at` | DATETIME(3) | NO | CURRENT_TIMESTAMP(3) ON UPDATE |

- `pk_users`, `uq_users_email`
- `ck_users_email_normalized`: `email = LOWER(TRIM(email))` (M-5)
- `fk_users_status_id_statuses`, `ix_users_status_id`
- **Ya no existe** `area_id` ni `ix_users_area_id` (R2-01).

### 4.4 `enterprises` (LOG-01, LOG-16)

| Columna | Tipo | Nulo | Default |
|---|---|---|---|
| `id` | BIGINT UNSIGNED AUTO_INCREMENT | NO | — |
| `trade_name` | VARCHAR(255) | NO | — |
| `company_name` | VARCHAR(255) | NO | — |
| `rfc` | VARCHAR(255) | NO | — |
| `website` | VARCHAR(255) | SÍ | NULL |
| `contact_name` | VARCHAR(255) | NO | — |
| `email` | VARCHAR(255) | NO | — |
| `phone` | VARCHAR(255) | NO | — |
| `full_address` | VARCHAR(255) | NO | — |
| `postal_code` | VARCHAR(255) | NO | — |
| `status_id` | BIGINT UNSIGNED | NO | — |
| `created_at` | DATETIME(3) | NO | CURRENT_TIMESTAMP(3) |
| `updated_at` | DATETIME(3) | NO | CURRENT_TIMESTAMP(3) ON UPDATE |

- `pk_enterprises`, `uq_enterprises_rfc`
- `fk_enterprises_status_id_statuses`, `ix_enterprises_status_id`
- **Ya no existen** `country_id`, `city_id`, `sso_enabled` ni sus índices (R2-01, R2-03).

### 4.5 `users_enterprises` (LOG-02, LOG-05, LOG-07, LOG-15, CA-05)

| Columna | Tipo | Nulo | Default |
|---|---|---|---|
| `id` | BIGINT UNSIGNED AUTO_INCREMENT | NO | — |
| `user_id` | BIGINT UNSIGNED | NO | — |
| `enterprise_id` | BIGINT UNSIGNED | NO | — |
| `status_id` | BIGINT UNSIGNED | NO | — |
| `joined_at` | DATETIME(3) | NO | CURRENT_TIMESTAMP(3) |
| `status_changed_at` | DATETIME(3) | NO | CURRENT_TIMESTAMP(3) |

- `pk_users_enterprises`
- `uq_users_enterprises_user_id_enterprise_id`, `uq_users_enterprises_id_user_id`
- `fk_users_enterprises_user_id_users`, `fk_users_enterprises_enterprise_id_enterprises`, `fk_users_enterprises_status_id_statuses`
- `ix_users_enterprises_user_id_status_id_joined_at` (`user_id`, `status_id`, `joined_at`): membresía activa más antigua (LOG-05)
- `ix_users_enterprises_enterprise_id_status_id` (`enterprise_id`, `status_id`)
- `ix_users_enterprises_status_id` (`status_id`): soporte de la FK
- **Ya no existe** `role_id` ni `ix_users_enterprises_role_id` (R2-02).
- `status_changed_at` sigue sin `ON UPDATE`: lo actualiza la aplicación (hallazgo H-06 de BIT-0001, sin cambio).

### 4.6 `user_preferences` (LOG-04, LOG-05), sin cambios

| Columna | Tipo | Nulo | Default |
|---|---|---|---|
| `user_id` | BIGINT UNSIGNED | NO | — |
| `default_membership_id` | BIGINT UNSIGNED | SÍ | NULL |
| `updated_at` | DATETIME(3) | NO | CURRENT_TIMESTAMP(3) ON UPDATE |

- `pk_user_preferences` (`user_id`), `fk_user_preferences_user_id_users`
- `fk_user_preferences_default_membership_id_users_enterprises`: FK compuesta `(default_membership_id, user_id) → users_enterprises(id, user_id)`

### 4.7 `auth_sessions` (LOG-03, LOG-14, LOG-16, CU-06, CU-10, CU-11)

| Columna | Tipo | Nulo | Default |
|---|---|---|---|
| `id` | BINARY(16) | NO | — |
| `token_hash` | BINARY(32) | NO | — |
| `user_id` | BIGINT UNSIGNED | NO | — |
| `active_membership_id` | BIGINT UNSIGNED | NO | — |
| `device_type_id` | BIGINT UNSIGNED | NO | — |
| `created_at` | DATETIME(3) | NO | CURRENT_TIMESTAMP(3) |
| `last_used_at` | DATETIME(3) | SÍ | NULL |
| `expires_at` | DATETIME(3) | NO | — |
| `revoked_at` | DATETIME(3) | SÍ | NULL |
| `revoked_reason_id` | BIGINT UNSIGNED | SÍ | NULL |

- `pk_auth_sessions`, `uq_auth_sessions_token_hash`
- `fk_auth_sessions_user_id_users`
- `fk_auth_sessions_active_membership_id_users_enterprises`: FK compuesta `(active_membership_id, user_id) → users_enterprises(id, user_id)`
- `fk_auth_sessions_device_type_id_device_types`, `ix_auth_sessions_device_type_id`
- `fk_auth_sessions_revoked_reason_id_revoked_reasons` (50 caracteres), `ix_auth_sessions_revoked_reason_id`
- `ix_auth_sessions_active_membership_id_revoked_at_expires_at`, `ix_auth_sessions_user_id_revoked_at`
- `ck_auth_sessions_revocation_consistent`: `(revoked_at IS NULL) = (revoked_reason_id IS NULL)`
- `ck_auth_sessions_expires_after_created`: `expires_at > created_at`
- **Ya no existe** `auth_method` (R2-03).

### 4.8 `presence_connections` (CU-07 a CU-10), sin cambios

| Columna | Tipo | Nulo | Default |
|---|---|---|---|
| `id` | BINARY(16) | NO | — |
| `session_id` | BINARY(16) | NO | — |
| `connected_at` | DATETIME(3) | NO | CURRENT_TIMESTAMP(3) |
| `last_seen_at` | DATETIME(3) | NO | CURRENT_TIMESTAMP(3) |
| `valid_until` | DATETIME(3) | NO | — |

- `pk_presence_connections`
- `fk_presence_connections_session_id_auth_sessions` con `CASCADE`
- `ix_presence_connections_session_id_valid_until`, `ix_presence_connections_valid_until`
- `ck_presence_connections_valid_after_connected`: `valid_until >= connected_at`

### 4.9 Orden en la migración

- **`upgrade()`:** `statuses` + datos → `device_types` + datos → `revoked_reasons` + datos → `users` → `enterprises` → `users_enterprises` → `user_preferences` → `auth_sessions` → `presence_connections`.
- **`downgrade()`:** `drop_table` en orden inverso, sin borrar índices antes (error 1553, ver R1). Al borrar las tablas de catálogo se van sus datos; no hace falta `DELETE`.

### 4.10 Índices explícitos

Declara en el modelo un `Index` para cada FK simple hacia un catálogo (`ix_users_status_id`, `ix_enterprises_status_id`, `ix_users_enterprises_status_id`, `ix_auth_sessions_device_type_id`, `ix_auth_sessions_revoked_reason_id`). Si no, MySQL crea uno con el nombre de la FK y `alembic check` detecta diferencias.

## 5. Verificaciones

Las de la sección 6 de `herdr-login-04-migraciones.md` (V-01 a V-10), con estos ajustes. Anota cada comando y su resultado real, también los fallos.

| # | Ajuste |
|---|---|
| V-04 | El SQL fuera de línea debe tener 10 `CREATE TABLE`, los 3 `INSERT` de catálogos y ningún `ENUM`. Comprueba con `grep -c "ENUM"` que da 0. |
| V-05 | Ningún nombre supera 64 caracteres. Debe aparecer `fk_auth_sessions_revoked_reason_id_revoked_reasons`. |
| V-06 | Ida y vuelta `upgrade head` → `downgrade base` → `upgrade head` en un MySQL 8.4 desechable. |
| V-07 | `uv run alembic check`: "No new upgrade operations detected." |
| V-08 | `SHOW CREATE TABLE` de las 9 tablas. Ninguna columna `area_id`, `country_id`, `city_id`, `role_id`, `sso_enabled` ni `auth_method`. |
| V-09 | Integridad con datos ficticios (Saga, Mega, Ana). Además de los casos de R1 adaptados a `status_id`, comprueba que se rechazan: <br>• `users.status_id = 99` (error 1452). <br>• Borrar `statuses` `active` en uso (error 1451). <br>• Un segundo `statuses` con `name = 'active'` (error 1062). <br>• `revoked_at` sin `revoked_reason_id` (error 3819). <br>• `auth_sessions.device_type_id` inexistente (error 1452). |
| V-11 (nueva) | Tras `upgrade head`: `SELECT id, name FROM statuses`, `device_types` y `revoked_reasons` devuelven exactamente las filas de la sección 4.2. |

Al terminar, elimina el contenedor desechable y no dejes credenciales en ningún archivo.

## 6. Documentación en Notion

Sigue la sección 7 de `herdr-login-04-migraciones.md` con estos datos:
- **Título:** `NEXUS ERP · Login · login-04-migracion · v3`. Reemplaza a v2. No edites v1 ni v2.
- **Estado:** "Implementado, pendiente de revisión".
- **Contenido:** cambios respecto a v2 (decisiones R2-01 a R2-08), diagrama ER en Mermaid de las 9 tablas, tablas con restricciones y la regla que respalda cada una, datos iniciales, verificaciones con resultados reales, pendientes y traspaso a Codex.
- **Sin herramienta de Notion:** `docs/notion/login-04-migracion-v3.md` más una fila en el índice de `docs/notion/README.md`.

La entrada de la bitácora de cambios en Notion (BIT-0003) la registra Claude al revisar tu entrega. No la crees tú.

## 7. Entrega

1. Completa la sección 7 de `docs/iterations/login-04-migracion/claude-r2.md`:
   - Comprobaciones previas y la base del trabajo (commit de partida, si traes o no `develop`).
   - Archivos modificados.
   - Lo aprobado frente a lo entregado, con cualquier diferencia y su motivo.
   - Verificaciones y resultados.
   - Pendientes y traspaso a Codex: nombres exactos de tablas, columnas, catálogos con sus filas, restricciones y los casos de V-09 que no pudiste ejecutar.
2. **Commit y PR, solo si el responsable lo indica.** Si lo indica:
   - Un commit solo con esta tarea, con un mensaje descriptivo (por ejemplo `login-04 R2: catálogos en lugar de ENUM y reducción de alcance`).
   - Excluye `__pycache__/`, `.DS_Store`, `.venv/` y `.env`.
   - Termina el mensaje con la línea de atribución que indique el sistema.
   - El merge lo decide el responsable, después de la revisión de Codex.
3. Informa al responsable: rama, estado del commit y del PR, dónde está la documentación, verificaciones pendientes y qué debe revisar Codex.

Si Codex reporta un defecto: revisa el caso y la regla, corrige dentro de este alcance y documenta una versión nueva (`v4`). Mientras `0001` no se haya aplicado en un entorno compartido, se corrige en la misma `0001`; después, con una migración nueva.
