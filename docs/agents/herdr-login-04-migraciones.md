# Instrucción para un agente Claude en herdr · Migraciones de Login (`login-04-migracion`)

**Destinatario:** un agente Claude Code que se ejecuta desde herdr sin el historial de la conversación donde se diseñó el modelo.
**Fecha:** 2026-11-20 · **Estado:** instrucción lista para ejecutar.
**Tarea:** `login-04-migracion` (parte 3 de `docs/agents/claude-login-implementacion.md`). Codex usa el mismo identificador.
**Requisito previo:** `login-02-base`, implementada en el worktree `worktree-claude-worktree` y pendiente de revisión.

Este archivo contiene todo lo necesario para crear las tablas del módulo de Login. **La especificación de la sección 5 es suficiente por sí sola:** no necesitas leer Notion para implementarla. Si tienes una duda que estas fuentes no resuelven, detente y pregunta al responsable.

---

## 0. Resumen de lo que debes hacer

1. Leer las reglas del proyecto (sección 1).
2. Comprobar el worktree, la rama y que `login-02-base` esté presente (sección 2).
3. Escribir la propuesta en `docs/iterations/login-04-migracion/claude.md` y documentarla como v1 (secciones 3 y 7).
4. **Detenerte y esperar la aprobación del responsable.** Codex revisa la propuesta.
5. Con la aprobación:
   - Crear los modelos de persistencia.
   - Registrarlos en `import_models()`.
   - Generar la migración `0001` y revisarla a mano según la sección 5.
6. Verificar (sección 6), registrar la entrega, documentar la versión de entrega y entregar (sección 8).

**Prohibido en esta tarea:**
- Repositorios, unidad de trabajo, casos de uso, endpoints y datos semilla.
- Tablas de contraseñas o de catálogos del ERP.
- Instalar o cambiar dependencias sin aprobación.
- Leer, abrir o mostrar `.env`.
- Editar archivos de `login-02-base`, salvo los que autoriza la sección 4.
- Editar páginas de Notion existentes o versiones anteriores en `docs/notion/`.
- Hacer merge, o trabajar en `develop` o `master`.

## 1. Lectura obligatoria, en este orden

1. `AGENTS.md`: ciclo de trabajo. Propones, esperas la aprobación del alcance, trabajas en tu worktree y rama, registras la entrega y el responsable hace el merge.
2. `CLAUDE.md`: capas `api/`, `application/`, `domain/`, `infrastructure/`. Claude implementa el backend y las migraciones autorizadas.
3. `codex.md` y `docs/agents/codex.md`: qué espera Codex (dobles de prueba, casos reproducibles, nada de `.env`).
4. `docs/agents/claude-login-implementacion.md`: instrucción general del módulo de Login (alcance, decisiones D-01…D-10, ciclo, Notion, reglas de construcción).
5. `docs/modules/login/01-reglas-de-negocio.md`: reglas LOG-01…LOG-16. Por decisión del responsable, **LOG-12, LOG-13 y CA-08 están retiradas**: no hay restablecimiento ni configuración de contraseña.
6. `docs/iterations/login-02-base/claude.md`: la base ya implementada. Fíjate en las decisiones aprobadas:
   - D-02: async con `asyncmy`.
   - D-11: `cryptography`.
   - La convención de nombres.
   - Los comandos AC-01…AC-07.
   - Q-01.
7. `app/core/db.py` (`Base`, `NAMING_CONVENTION`, `import_models()`, `create_migration_engine`), `alembic/env.py`, `alembic.ini`, `pyproject.toml`, `docker-compose.yml` y `.env.example`.
8. `docs/notion/README.md`: área de espera de las páginas de Notion cuando no hay conector.
9. Opcional, si tu sesión tiene acceso a Notion (solo lectura): "Sugerencias de Claude · Modelo de datos de Login (ER) · v2", aprobada el 2026-11-20 (https://app.notion.com/p/41e5bc4e7d0181bd8607e1e28630dfb4). La sección 5 la concreta para MySQL. Si no coinciden, manda la sección 5, y anota la diferencia en tu `claude.md`.

`docs/iterations/login-01/claude.md` tiene un esquema anterior (PostgreSQL, 4 tablas, uuid, citext) que **está reemplazado**. No lo uses como especificación.

## 2. Comprobaciones previas

Ejecuta lo siguiente y anota los resultados en tu `claude.md`:

```bash
git rev-parse --show-toplevel
git branch --show-current
git status -s
ls alembic/env.py app/core/db.py pyproject.toml uv.lock
```

- **Worktree:** `login-02-base` todavía **no tiene commit**. Solo existe como archivos sin seguimiento en `~/.herdr/worktrees/NEXUS_API_v2.0/worktree-claude-worktree` (rama `worktree/claude_worktree`).
  - Trabaja en ese worktree, o en uno creado después de que `login-02-base` tenga commit.
  - Si el `ls` anterior falla en tu worktree, **detente** y avisa al responsable. No recrees la base.
- **Rama:** si es `develop` o `master`, detente.
- **Cambios ajenos:** los archivos sin commit de `login-02-base` y de `docs/agents/` no son tuyos. Consérvalos sin modificarlos, salvo lo que autoriza la sección 4.
- **Entorno de Python:** `uv sync` instala lo que ya está en `uv.lock`. No agregues paquetes.
- **MySQL:**
  - `docker-compose.yml` usa `mysql:8.4`.
  - `app/core/db.py` exige MySQL 8.0.16 o superior y `STRICT_TRANS_TABLES`.
  - Todo lo de la sección 5 (CHECK, `DATETIME(3)`, `utf8mb4_0900_ai_ci`) es compatible.

## 3. Propuesta antes de implementar

Crea `docs/iterations/login-04-migracion/claude.md` con:

1. **Objetivo:** modelos de persistencia de las 7 tablas de Login y migración reversible `0001`.
2. **Comprobaciones de la sección 2**, con sus resultados.
3. **Rutas a crear o modificar** (sección 4).
4. **Especificación completa** (sección 5) con la regla que respalda cada restricción.
5. **Decisiones que necesitan aprobación** (sección 5.10), cada una con tu recomendación.
6. **Verificaciones previstas** (sección 6).
7. **Interfaces para Codex:** nombres de tablas, columnas, valores de ENUM y nombres de restricciones, para sus pruebas de integración. Esta tarea no crea puertos de aplicación.
8. **Fuera de alcance:** lo prohibido en la sección 0.

Documenta la propuesta como v1 (sección 7) y **detente**. Dile al responsable dónde está y espera su aprobación.

## 4. Archivos de la tarea

| Archivo | Acción | Contenido |
|---|---|---|
| `app/identity/login/infrastructure/persistence/__init__.py` | Crear | Vacío. |
| `app/identity/login/infrastructure/persistence/models.py` | Crear | Las 7 tablas como modelos de SQLAlchemy 2.0 (`Mapped`, `mapped_column`) sobre `app.core.db.Base`, con los tipos del dialecto MySQL (`sqlalchemy.dialects.mysql`: `BIGINT(unsigned=True)`, `BINARY`, `DATETIME(fsp=3)`, `ENUM`, `VARCHAR`), los `server_default`, los `__table_args__` (UK, FK compuestas, índices, CHECK) y `mysql_engine`, `mysql_charset`, `mysql_collate`. Sin relaciones ORM ni lógica: los modelos no salen de `infrastructure/`. |
| `app/core/db.py` | Modificar solo `import_models()` | Agregar `import app.identity.login.infrastructure.persistence.models  # noqa: F401` y actualizar su docstring. Es el punto de extensión que `login-02-base` dejó para esta tarea. |
| `alembic/versions/0001_login_base.py` | Crear | Se genera con `uv run alembic revision --autogenerate -m "login base" --rev-id 0001`, con `revision = "0001"` y `down_revision = None`. **Revísalo a mano** contra la sección 5: autogenerate no siempre detecta los CHECK ni los `server_default` con `ON UPDATE`, ni el orden correcto. `downgrade()` elimina en orden inverso. |
| `docs/iterations/login-04-migracion/claude.md` | Crear | Propuesta y registro de entrega. |
| `docs/notion/login-04-migracion-vN.md` y `docs/notion/README.md` | Crear o actualizar el índice | Solo si no puedes publicar en Notion (sección 7). |

`alembic/versions/` está excluido de ruff en `pyproject.toml`. Aun así, mantén la migración legible y con los nombres explícitos de la sección 5.

## 5. Especificación de las tablas

### 5.1 Convenciones comunes

- **Motor y juego de caracteres:** `InnoDB`, `utf8mb4`, `utf8mb4_0900_ai_ci`. Algunas columnas indicadas usan `utf8mb4_bin`.
- **Fechas:** `DATETIME(3)` en UTC. La conexión fija `time_zone = '+00:00'` (`app/core/db.py`).
  - `created_at`: `server_default=text("CURRENT_TIMESTAMP(3)")`.
  - `updated_at`: `server_default=text("CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3)")`.
- **Claves:**
  - Entidades de catálogo: `BIGINT UNSIGNED AUTO_INCREMENT`.
  - Sesiones y conexiones: `BINARY(16)` sin valor por defecto. La aplicación genera un UUIDv7 en una tarea posterior.
- **Nombres de restricciones:** los da la `NAMING_CONVENTION` de `app/core/db.py`. No la cambies.
  - `pk_%(table_name)s`
  - `fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s`
  - `uq_%(table_name)s_%(column_0_N_name)s`
  - `ix_%(table_name)s_%(column_0_N_name)s`
  - `ck_%(table_name)s_%(constraint_name)s`: en el modelo, el CHECK se declara con `name="<constraint_name>"`.
  - Los nombres de esta sección son los que debe producir la convención. **Ningún nombre puede superar 64 caracteres**, el límite de MySQL. Verifícalo (sección 6).
- **Borrados:**
  - `ondelete="RESTRICT"` en todas las FK, salvo `presence_connections.session_id`, que es `CASCADE`.
  - Usuarios, empresas y membresías nunca se borran: cambian de estado.
- **Sin FK a tablas que no existen.** `area_id`, `country_id`, `city_id`, `role_id` y `basic_role_id` apuntan a catálogos del ERP que todavía no existen. Van como `BIGINT UNSIGNED` con índice y **sin FK**. Sus FK se agregan en la migración que cree esos catálogos (decisión M-1).

### 5.2 `users`: identidad global (LOG-07, LOG-08, LOG-15)

| Columna | Tipo | Nulo | Default | Notas |
|---|---|---|---|---|
| `id` | BIGINT UNSIGNED AUTO_INCREMENT | NO | — | PK |
| `email` | VARCHAR(254) COLLATE utf8mb4_bin | NO | — | Normalizado en el dominio (trim, minúsculas) |
| `password_hash` | VARCHAR(255) | SÍ | NULL | argon2id. NULL en altas por SSO |
| `status` | ENUM('active','suspended') | NO | 'active' | Suspensión global (LOG-15) |
| `name` | VARCHAR(100) | NO | — | |
| `second_name` | VARCHAR(100) | SÍ | NULL | |
| `last_name` | VARCHAR(100) | NO | — | |
| `second_last_name` | VARCHAR(100) | SÍ | NULL | |
| `phone_wa` | VARCHAR(20) | SÍ | NULL | |
| `area_id` | BIGINT UNSIGNED | SÍ | NULL | Sin FK (M-1) |
| `created_at` | DATETIME(3) | NO | CURRENT_TIMESTAMP(3) | |
| `updated_at` | DATETIME(3) | NO | CURRENT_TIMESTAMP(3) ON UPDATE | |

- `pk_users`
- `uq_users_email` (`email`)
- `ck_users_email_normalized`: `email = LOWER(TRIM(email))`. Es una defensa en la base; la normalización principal está en el dominio.
- `ix_users_area_id` (`area_id`)
- Se retiran respecto al ER original: `id_sso`, `status_id`, `account_status` y `me` (M-2).

### 5.3 `enterprises`: empresa y estado operativo (LOG-01, LOG-06, LOG-16)

| Columna | Tipo | Nulo | Default |
|---|---|---|---|
| `id` | BIGINT UNSIGNED AUTO_INCREMENT | NO | — |
| `trade_name` | VARCHAR(150) | NO | — |
| `company_name` | VARCHAR(250) | NO | — |
| `rfc` | VARCHAR(13) | NO | — |
| `website` | VARCHAR(255) | SÍ | NULL |
| `contact_name` | VARCHAR(150) | NO | — |
| `email` | VARCHAR(254) | NO | — |
| `phone` | VARCHAR(20) | NO | — |
| `country_id` | BIGINT UNSIGNED | NO | — |
| `city_id` | BIGINT UNSIGNED | NO | — |
| `full_address` | VARCHAR(500) | NO | — |
| `postal_code` | VARCHAR(10) | NO | — |
| `status` | ENUM('active','inactive') | NO | 'active' |
| `sso_enabled` | BOOLEAN (TINYINT(1)) | NO | 0 |
| `created_at` | DATETIME(3) | NO | CURRENT_TIMESTAMP(3) |
| `updated_at` | DATETIME(3) | NO | CURRENT_TIMESTAMP(3) ON UPDATE |

- `pk_enterprises`
- `uq_enterprises_rfc` (`rfc`)
- `ix_enterprises_country_id` y `ix_enterprises_city_id`, sin FK (M-1).
- Usar `status` ENUM en lugar de `status_id` es la decisión M-2.

### 5.4 `enterprise_sso_config`: configuración SSO por empresa (LOG-06, LOG-07)

Depende de M-3. La propuesta recomienda **diferir esta tabla** a `login-07-sso` mientras el protocolo SSO (D-08) siga abierto. Si el responsable decide crearla ahora:

| Columna | Tipo | Nulo | Default |
|---|---|---|---|
| `enterprise_id` | BIGINT UNSIGNED | NO | — |
| `issuer` | VARCHAR(255) | NO | — |
| `audience` | VARCHAR(255) | NO | — |
| `jwks_url` | VARCHAR(500) | NO | — |
| `basic_role_id` | BIGINT UNSIGNED | NO | — |
| `updated_at` | DATETIME(3) | NO | CURRENT_TIMESTAMP(3) ON UPDATE |

- `pk_enterprise_sso_config` (`enterprise_id`)
- `fk_enterprise_sso_config_enterprise_id_enterprises`
- `ix_enterprise_sso_config_basic_role_id`, sin FK (M-1).
- No guardes secretos en esta tabla.

### 5.5 `users_enterprises`: membresías (LOG-02, LOG-05, LOG-07, LOG-09, LOG-15)

| Columna | Tipo | Nulo | Default |
|---|---|---|---|
| `id` | BIGINT UNSIGNED AUTO_INCREMENT | NO | — |
| `user_id` | BIGINT UNSIGNED | NO | — |
| `enterprise_id` | BIGINT UNSIGNED | NO | — |
| `role_id` | BIGINT UNSIGNED | NO | — |
| `status` | ENUM('active','suspended','revoked') | NO | 'active' |
| `joined_at` | DATETIME(3) | NO | CURRENT_TIMESTAMP(3) |
| `status_changed_at` | DATETIME(3) | NO | CURRENT_TIMESTAMP(3) |

- `pk_users_enterprises`
- `uq_users_enterprises_user_id_enterprise_id` (`user_id`, `enterprise_id`): una membresía por empresa. Un ticket SSO no recrea una membresía revocada (CA-05).
- `uq_users_enterprises_id_user_id` (`id`, `user_id`): destino de las FK compuestas.
- `fk_users_enterprises_user_id_users`
- `fk_users_enterprises_enterprise_id_enterprises`
- `ix_users_enterprises_user_id_status_joined_at` (`user_id`, `status`, `joined_at`): elegir la membresía vigente más antigua (LOG-05).
- `ix_users_enterprises_enterprise_id_status` (`enterprise_id`, `status`): directorio de presencia por empresa.
- `ix_users_enterprises_role_id` (`role_id`), sin FK (M-1).

### 5.6 `user_preferences`: empresa predeterminada (LOG-04, LOG-05)

| Columna | Tipo | Nulo | Default |
|---|---|---|---|
| `user_id` | BIGINT UNSIGNED | NO | — |
| `default_membership_id` | BIGINT UNSIGNED | SÍ | NULL |
| `updated_at` | DATETIME(3) | NO | CURRENT_TIMESTAMP(3) ON UPDATE |

- `pk_user_preferences` (`user_id`)
- `fk_user_preferences_user_id_users`
- `fk_user_preferences_default_membership_id_users_enterprises`: FK compuesta `(default_membership_id, user_id) → users_enterprises(id, user_id)`. Garantiza que la predeterminada sea del mismo usuario. Con `default_membership_id` NULL, MySQL no evalúa la FK, y eso es lo deseado.
- Que la membresía esté vigente lo garantiza el dominio, no la base.

### 5.7 `auth_sessions`: sesión y token Bearer (LOG-03, LOG-14, LOG-16, CU-06, CU-10, CU-11)

| Columna | Tipo | Nulo | Default |
|---|---|---|---|
| `id` | BINARY(16) | NO | — |
| `token_hash` | BINARY(32) | NO | — |
| `user_id` | BIGINT UNSIGNED | NO | — |
| `active_membership_id` | BIGINT UNSIGNED | NO | — |
| `auth_method` | ENUM('password','sso') | NO | — |
| `device_type` | ENUM('desktop','mobile','tablet','unknown') | NO | 'unknown' |
| `created_at` | DATETIME(3) | NO | CURRENT_TIMESTAMP(3) |
| `last_used_at` | DATETIME(3) | SÍ | NULL |
| `expires_at` | DATETIME(3) | NO | — |
| `revoked_at` | DATETIME(3) | SÍ | NULL |
| `revoked_reason` | ENUM('logout','switched','user_suspended','membership_revoked','enterprise_disabled','admin') | SÍ | NULL |

- `pk_auth_sessions`
- `uq_auth_sessions_token_hash` (`token_hash`): guarda el SHA-256 del token Bearer. El token en claro nunca se guarda.
- `fk_auth_sessions_user_id_users`
- `fk_auth_sessions_active_membership_id_users_enterprises`: FK compuesta `(active_membership_id, user_id) → users_enterprises(id, user_id)`.
- `ix_auth_sessions_active_membership_id_revoked_at_expires_at` (`active_membership_id`, `revoked_at`, `expires_at`)
- `ix_auth_sessions_user_id_revoked_at` (`user_id`, `revoked_at`)
- `ck_auth_sessions_revocation_consistent`: `(revoked_at IS NULL) = (revoked_reason IS NULL)`
- `ck_auth_sessions_expires_after_created`: `expires_at > created_at`

### 5.8 `presence_connections`: una fila por WebSocket (CU-07…CU-10)

| Columna | Tipo | Nulo | Default |
|---|---|---|---|
| `id` | BINARY(16) | NO | — |
| `session_id` | BINARY(16) | NO | — |
| `connected_at` | DATETIME(3) | NO | CURRENT_TIMESTAMP(3) |
| `last_seen_at` | DATETIME(3) | NO | CURRENT_TIMESTAMP(3) |
| `valid_until` | DATETIME(3) | NO | — |

- `pk_presence_connections`
- `fk_presence_connections_session_id_auth_sessions`, con `ondelete="CASCADE"`.
- `ix_presence_connections_session_id_valid_until` (`session_id`, `valid_until`)
- `ix_presence_connections_valid_until` (`valid_until`): limpieza por lotes.
- `ck_presence_connections_valid_after_connected`: `valid_until >= connected_at`

### 5.9 Orden en la migración

- **`upgrade()`:** `users` → `enterprises` → (`enterprise_sso_config`, si M-3 la incluye) → `users_enterprises` → `user_preferences` → `auth_sessions` → `presence_connections`.
- **`downgrade()`:** el inverso.

### 5.10 Decisiones que debes presentar para aprobación

| ID | Decisión | Recomendación |
|---|---|---|
| M-1 | Columnas que apuntan a catálogos inexistentes (`area_id`, `country_id`, `city_id`, `role_id`, `basic_role_id`) | Sin FK por ahora, con índice. FK en la migración del módulo de catálogos y roles. |
| M-2 | `status` ENUM en lugar de `status_id` o `account_status`, y retirar `me` e `id_sso` (D-07 de la instrucción general) | Aplicar el ENUM y retirarlos, salvo que el responsable aclare el significado de `me` o pida mapear al catálogo del ERP. |
| M-3 | Crear `enterprise_sso_config` antes de definir el protocolo SSO (D-08) | Diferirla a `login-07-sso`. |
| M-4 | Longitudes de VARCHAR (sección 5) | Aprobar o ajustar. |
| M-5 | `ck_users_email_normalized` | Mantenerla como defensa en profundidad. |

## 6. Verificaciones

Anota cada comando y su resultado real en tu `claude.md`, incluidos los fallos. Usa los comandos aprobados en `login-02-base`. Nunca abras ni muestres `.env`.

| # | Verificación | Comando o método |
|---|---|---|
| V-01 | Lint y formato | `uv run ruff check . && uv run ruff format --check .` |
| V-02 | Tipos | `uv run mypy app` |
| V-03 | Regla de importación entre capas | `uv run lint-imports`. Los 4 contratos en verde. |
| V-04 | SQL generado sin base de datos | `NEXUS_APP_ENV=test NEXUS_DATABASE_URL='mysql+asyncmy://ficticio:ficticio@127.0.0.1:3306/nexus' uv run alembic upgrade head --sql`, con la salida en un archivo temporal fuera del repositorio. Revisa que tenga todos los nombres, tipos, collations, CHECK, FK e índices de la sección 5. En `claude.md` va un resumen, no el archivo completo. |
| V-05 | Longitud de nombres | Ningún nombre de restricción o índice del SQL de V-04 supera 64 caracteres. |
| V-06 | Ida y vuelta | `docker compose up -d db && uv run alembic upgrade head && uv run alembic downgrade base && uv run alembic upgrade head` (AC-06 de `login-02-base`). |
| V-07 | Modelos y migración coinciden | Tras `upgrade head`, `uv run alembic check` no debe detectar diferencias. Si hay falsos positivos por `server_default` con `ON UPDATE`, documéntalos y explica por qué no son diferencias reales. |
| V-08 | Esquema real | `SHOW CREATE TABLE` de cada tabla, comparado con la sección 5. |
| V-09 | Integridad, con datos ficticios (Saga, Mega, Ana) | Con un script desechable fuera del repositorio o en una consola SQL, comprueba que se rechazan: <br>• Un correo duplicado (`uq_users_email`). <br>• Un correo con mayúsculas (`ck_users_email_normalized`). <br>• Una segunda membresía usuario-empresa. <br>• Una preferencia que apunta a la membresía de otro usuario (FK compuesta). <br>• Una sesión cuyo `user_id` no coincide con el de su membresía. <br>• `revoked_at` sin `revoked_reason`. <br>Comprueba también que al borrar una sesión se borran sus conexiones (CASCADE). |
| V-10 | Pruebas existentes | `uv run pytest`. Sin regresiones en lo que ya exista. |

Si la base local no está disponible, ejecuta V-01…V-05 y registra V-06…V-09 como pendientes. Entrégalos a Codex como escenarios de integración.

## 7. Documentación versionada en Notion (obligatoria)

**Títulos y versiones**
- `NEXUS ERP · Login · login-04-migracion · vN`.
- v1 es la propuesta. Siguen las versiones con ajustes tras la revisión, la entrega implementada y cada corrección.
- **Nunca edites una versión anterior.**

**Contenido mínimo de cada versión**
1. Encabezado: tarea, versión, fecha, estado, rama y PR, y versión que reemplaza.
2. Cambios respecto a la versión anterior.
3. Objetivo y alcance, incluido lo que queda fuera.
4. Diagrama ER en Mermaid (`erDiagram`) de las tablas tal como quedan en la migración.
5. Tablas con columnas, restricciones e índices, y la regla que respalda cada restricción.
6. Decisiones M-1…M-5 con su estado.
7. Verificaciones ejecutadas y sus resultados reales.
8. Pendientes y traspaso a Codex.

**Dónde publicar**
- **Si tu sesión tiene la herramienta `mcp__mcp_server_notion__save_note_in_notion`:**
  - Crea la página con ella.
  - La herramienta puede responder con el error `structured_content must be a dict or None` aunque la página sí se haya creado. La respuesta incluye la URL: ábrela y confirma que la página existe antes de reintentar, para no duplicarla.
  - Comprueba que quedó **dentro de NEXUS ERP**. Si no, avisa al responsable con la URL.
- **Si no tienes esa herramienta**, sigue la convención que `login-02-base` ya estableció:
  - Escribe `docs/notion/login-04-migracion-vN.md`.
  - Agrega una fila al índice de `docs/notion/README.md`. Del README solo se cambia el índice, nunca las notas ya escritas.
  - Avisa al responsable de que la nota está lista para publicarse en NEXUS ERP.

Usa solo datos ficticios. Nunca incluyas URLs de conexión reales, credenciales ni contenido de `.env`.

## 8. Entrega

Solo después de la aprobación y las verificaciones:

1. Actualiza `docs/iterations/login-04-migracion/claude.md` con:
   - La rama y el PR.
   - Los archivos modificados.
   - Lo acordado frente a lo entregado.
   - Las verificaciones y sus resultados.
   - Las decisiones aprobadas.
   - Los pendientes y el traspaso a Codex.
2. Documenta la versión de entrega (sección 7) con estado "Implementado, pendiente de revisión".
3. **Commit y PR, solo si el responsable lo indica.** `login-02-base` sigue sin commit por instrucción del responsable.
   - No mezcles en un mismo commit archivos de `login-02-base` y de esta tarea sin su autorización.
   - Excluye `__pycache__/`, `.DS_Store`, `venv/`, `.venv/` y `.env`.
   - Termina el mensaje con la línea de atribución que indique el sistema.
   - El merge lo decide el responsable.
4. Informa al responsable con:
   - La rama.
   - El estado del commit y del PR.
   - Dónde está la documentación (Notion o `docs/notion/`).
   - Las verificaciones pendientes.
   - Lo que Codex debe revisar.

## 9. Traspaso a Codex

Indica en tu `claude.md`:
- Los nombres exactos de tablas, columnas, valores de ENUM y restricciones.
- La ruta de los modelos (`app/identity/login/infrastructure/persistence/models.py`). Los repositorios llegarán en una tarea posterior.
- Los escenarios de V-09 que no pudiste ejecutar.
- Las reglas cubiertas por cada restricción: LOG-04, LOG-05, LOG-07, LOG-09, LOG-15, LOG-16, CA-05 y CU-06…CU-11.

Si Codex reporta un defecto:
1. Revisa el caso reproducible y la regla.
2. Corrige solo dentro del alcance aprobado. Una migración ya aplicada en un entorno compartido no se edita: se corrige con una migración nueva.
3. Documenta una versión nueva y devuelve la referencia del cambio.
