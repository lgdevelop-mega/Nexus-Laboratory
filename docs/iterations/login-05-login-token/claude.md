# login-05-login-token · Seeder de datos de prueba e inicio de sesión con token

**Autor:** Claude Code · **Fecha:** 2026-11-23 · **Estado:** propuesta **aprobada por el responsable el 2026-11-23** (L-01 a L-07). Codex no la revisó antes de la aprobación; revisa la entrega.
**Rama prevista:** `worktree/claude_worktree`.
**Depende de:** `login-04-migracion` R2, entregada en el commit `5cccb8c`.

## 1. Objetivo

Lograr el primer flujo completo de Login con lo que ya existe:

1. **Seeder:** registrar dos usuarios de prueba, con sus empresas y membresías, a partir de un archivo de entrada validado, y devolver un resultado estructurado. Reutilizable y modificable: otro archivo de entrada produce otros datos sin tocar código.
2. **Login convencional:** `POST /api/v1/auth/login` con correo y contraseña, que abre una sesión en la empresa correcta y devuelve un token Bearer.
3. **Autenticación reutilizable:** una dependencia que valida el token en cualquier endpoint protegido, y `GET /api/v1/auth/session` para comprobarla.

Reglas: LOG-02 (primera empresa predeterminada), LOG-03, LOG-05, LOG-09 (derivado), LOG-15, LOG-16 · CU-02 · CA-01, CA-07.

## 2. Agrupación de tareas (decisión L-01)

El plan original separa `login-03-dominio`, `login-05-login-token` y `login-06-sesion-logout`. Para tener un flujo completo propongo, en esta única tarea:

| Incluye | De la tarea | Qué |
|---|---|---|
| Sí | `login-03-dominio` | Solo lo que usa el login: `Email`, estados, entidades y la política de empresa de ingreso (LOG-03, LOG-05) y de acceso (LOG-15, LOG-16). Lo de SSO (LOG-07) queda en `login-03`. |
| Sí | `login-05-login-token` | Completa. |
| Sí | `login-06-sesion-logout` | Solo `GET /api/v1/auth/session`, para probar el token. El logout sigue en `login-06`. |
| Sí | Nueva | El seeder. |

## 3. Recorrido de una petición

```
POST /api/v1/auth/login
  api/routes.py          valida el JSON (LoginRequest), llama al caso de uso, arma LoginResponse
  application/login.py   LoginWithPassword: coordina pasos y transacción
    ├─ domain/email.py           normaliza el correo
    ├─ UserRepository            busca por correo
    ├─ PasswordHasher            verifica argon2id (también con usuario inexistente, para igualar tiempos)
    ├─ domain/access.py          usuario activo (LOG-15)
    ├─ MembershipRepository      membresías con el estado de su empresa
    ├─ domain/login_policy.py    elige la empresa de ingreso (LOG-03, LOG-05)
    ├─ PreferenceRepository      guarda la nueva predeterminada si cambió (LOG-05)
    └─ SessionOpener             genera token, guarda su SHA-256 y la sesión
  UnitOfWork.commit()
```

Se usa **caso de uso directo** más un servicio de aplicación compartido, `SessionOpener`, que reutilizarán el SSO (`login-07`) y el cambio de empresa (`login-08`). No hace falta pipeline ni orquestador: es una secuencia lineal en una sola transacción.

## 4. Contrato API

Todas las respuestas de error usan `application/problem+json` con `code` estable (`app/core/errors.py`). Las respuestas con token llevan `Cache-Control: no-store`.

### 4.1 `POST /api/v1/auth/login`

**Petición**

```json
{
  "email": "Ana@Saga.test ",
  "password": "<contraseña de prueba>",
  "device_type": "desktop"
}
```

| Campo | Regla |
|---|---|
| `email` | Obligatorio, texto de 3 a 255 caracteres. Se normaliza en el dominio (sin espacios, minúsculas). |
| `password` | Obligatorio, de 1 a 1024 caracteres. Nunca se registra en logs. |
| `device_type` | Opcional: `desktop`, `mobile`, `tablet` o `unknown` (por defecto `unknown`). Solo informativo, nunca autoriza. |

**200 OK**

```json
{
  "access_token": "Yp3...43 caracteres base64url...",
  "token_type": "Bearer",
  "expires_at": "2026-11-24T06:15:30.123Z",
  "session_id": "01935f2a-7c3e-7b1a-9f00-3c5d2e8a4b10",
  "user": { "id": 1, "email": "ana@saga.test", "name": "Ana", "last_name": "Prueba" },
  "active_enterprise": { "id": 1, "membership_id": 1, "trade_name": "Saga" },
  "enterprises": [
    { "id": 1, "membership_id": 1, "trade_name": "Saga", "is_default": true },
    { "id": 2, "membership_id": 2, "trade_name": "Mega", "is_default": false }
  ],
  "is_multitenant": true
}
```

- `enterprises` son las empresas disponibles: membresía `active` y empresa `active`.
- `is_multitenant` se deriva: dos o más empresas disponibles (LOG-09). No se guarda.

**Errores**

| HTTP | `code` | Cuándo | Regla |
|---|---|---|---|
| 400 | `bad_request` | El cuerpo no es JSON. | — |
| 422 | `validation_error` | Falta un campo, longitud fuera de rango o `device_type` no permitido. | — |
| 401 | `invalid_credentials` | Correo inexistente, contraseña incorrecta o `password_hash` NULL. **Mismo mensaje en los tres casos**: "Correo o contraseña incorrectos." | CU-02, seguridad |
| 403 | `account_inactive` | Contraseña correcta, usuario `inactive`. | LOG-15, CA-07 |
| 403 | `no_enterprise_access` | Contraseña correcta, sin ninguna empresa disponible. | LOG-05 |
| 503 | `service_unavailable` | MySQL no responde. | — |

`account_inactive` y `no_enterprise_access` solo se devuelven **después** de verificar la contraseña, así no revelan si un correo existe.

### 4.2 `GET /api/v1/auth/session`

**Petición:** cabecera `Authorization: Bearer <access_token>`.

**200 OK:** el mismo cuerpo que el login, **sin** `access_token` ni `token_type`.

**Errores**

| HTTP | `code` | Cuándo |
|---|---|---|
| 401 | `not_authenticated` | Falta la cabecera o no es `Bearer`. |
| 401 | `invalid_token` | Token desconocido, sesión revocada o vencida, usuario `inactive`, membresía `inactive` o empresa `inactive` (LOG-15, LOG-16). |

Los 401 llevan `WWW-Authenticate: Bearer`. Un solo `invalid_token` para todos los motivos evita filtrar el estado interno. En esta tarea la sesión **no** se revoca en la base al detectar la pérdida de acceso; eso es `login-10-perdida-acceso`.

### 4.3 Dependencia reutilizable

`app/identity/login/api/dependencies.py` expone `current_session` para `Depends(...)`. Devuelve un `AuthenticatedSession` (id de sesión, usuario, membresía y empresa activa). Cualquier módulo la usa para proteger sus rutas.

## 5. Dominio (Python puro)

| Archivo | Contenido |
|---|---|
| `domain/email.py` | `Email`: valor inmutable; `Email.parse(raw)` quita espacios, pasa a minúsculas y valida la forma `local@dominio`. Error `InvalidEmail`. |
| `domain/status.py` | Constantes `ACTIVE = "active"` e `INACTIVE = "inactive"`, y `DeviceType` (`unknown`, `desktop`, `mobile`, `tablet`). Son los `name` de los catálogos. |
| `domain/entities.py` | `User` (id, email, password_hash, status, nombres), `AvailableMembership` (membership_id, enterprise_id, trade_name, membership_status, enterprise_status, joined_at). |
| `domain/login_policy.py` | `choose_login_enterprise(memberships, default_membership_id) -> LoginChoice`. |
| `domain/access.py` | `ensure_user_active(user)` y `is_available(membership)`. |
| `domain/errors.py` | `InvalidCredentials`, `AccountInactive`, `NoEnterpriseAccess`, `InvalidToken`. |

**`choose_login_enterprise`** (LOG-03, LOG-05):
1. Disponibles = membresía `active` y empresa `active`.
2. Ninguna → `NoEnterpriseAccess`.
3. Si la predeterminada está entre las disponibles → esa.
4. Si no (no existe o perdió acceso) → la de `joined_at` más antiguo, y `LoginChoice.new_default` indica que hay que guardarla como predeterminada.

Ejemplos con Ana: predeterminada Saga y Mega vigente → Saga (CA-01). Saga inactiva → Mega y `new_default = Mega` (CA-06 en su forma de ingreso).

## 6. Aplicación: puertos y casos de uso

Puertos en `application/ports.py` (`Protocol`):

| Puerto | Métodos |
|---|---|
| `UserRepository` | `get_by_email(email) -> User \| None`, `get_by_id(id)`, `add(new_user) -> int` |
| `EnterpriseRepository` | `get_by_rfc(rfc)`, `add(new_enterprise) -> int` |
| `MembershipRepository` | `list_for_user(user_id) -> list[AvailableMembership]`, `get(user_id, enterprise_id)`, `add(...) -> int` |
| `PreferenceRepository` | `get_default(user_id) -> int \| None`, `set_default(user_id, membership_id)` |
| `SessionRepository` | `add(new_session)`, `get_active_by_token_hash(token_hash) -> SessionView \| None`, `touch(session_id, now)` |
| `CatalogRepository` | `id_of(catalog, name) -> int` (`statuses`, `device_types`) |
| `PasswordHasher` | `hash(password) -> str`, `verify(password_hash, password) -> bool` |
| `TokenService` | `new_token() -> str`, `hash_token(token) -> bytes` |
| `IdGenerator` | `new_session_id() -> UUID` (UUIDv7) |
| `Clock` | `now() -> datetime` |
| `UnitOfWork` | contexto async con los repositorios, `commit()` y `rollback()` |

Casos de uso:

| Caso | Archivo | Entrada → salida |
|---|---|---|
| `LoginWithPassword` | `application/login.py` | `LoginCommand(email, password, device_type)` → `LoginResult` |
| `SessionOpener` | `application/session_opener.py` | `(user, membership, device_type)` → `OpenedSession(token, session_id, expires_at)` |
| `AuthenticateToken` | `application/authenticate.py` | `token` → `AuthenticatedSession` |
| `SeedLoginData` | `application/seed.py` | `SeedPlan` → `SeedReport` (sección 7) |

**Sesión:**
- Token: `secrets.token_urlsafe(32)` (256 bits). Se guarda `SHA-256(token)` en `token_hash`; el token en claro solo sale en la respuesta.
- `id`: UUIDv7 generado por la app. Python 3.12 no trae `uuid7`; se implementa en `infrastructure/ids.py` sin dependencias.
- `created_at = now`, `expires_at = now + session_ttl` (decisión L-03).
- `AuthenticateToken` compara la vigencia con `UTC_TIMESTAMP(3)` en MySQL y actualiza `last_used_at` como máximo una vez por minuto, para no escribir en cada petición.

## 7. Seeder

### 7.1 Uso

```bash
uv run python -m app.identity.login.cli.seed seeds/login/usuarios-prueba.json
```

Opciones: `--dry-run` valida y muestra qué haría sin escribir. La salida es el `SeedReport` en JSON por stdout; los errores van a stderr con código de salida distinto de 0.

**Se niega a ejecutarse** si `NEXUS_APP_ENV` es `staging` o `production`.

### 7.2 Contrato de entrada (`SeedPlan`, validado con Pydantic)

`seeds/login/usuarios-prueba.json`:

```json
{
  "version": 1,
  "enterprises": [
    {
      "key": "saga",
      "trade_name": "Saga",
      "company_name": "Saga Pruebas S.A. de C.V.",
      "rfc": "SPR010101AA1",
      "contact_name": "Contacto Saga",
      "email": "contacto@saga.test",
      "phone": "5500000001",
      "full_address": "Calle Ficticia 1, Ciudad de Prueba",
      "postal_code": "00001",
      "status": "active"
    },
    {
      "key": "mega",
      "trade_name": "Mega",
      "company_name": "Mega Pruebas S.A. de C.V.",
      "rfc": "MPR010101BB2",
      "contact_name": "Contacto Mega",
      "email": "contacto@mega.test",
      "phone": "5500000002",
      "full_address": "Calle Ficticia 2, Ciudad de Prueba",
      "postal_code": "00002",
      "status": "active"
    }
  ],
  "users": [
    {
      "email": "ana@saga.test",
      "password": "<contraseña de prueba>",
      "name": "Ana",
      "last_name": "Prueba",
      "status": "active",
      "memberships": [
        { "enterprise": "saga", "status": "active" },
        { "enterprise": "mega", "status": "active" }
      ],
      "default_enterprise": "saga"
    },
    {
      "email": "bruno@saga.test",
      "password": "<contraseña de prueba>",
      "name": "Bruno",
      "last_name": "Prueba",
      "status": "active",
      "memberships": [{ "enterprise": "saga", "status": "active" }],
      "default_enterprise": "saga"
    }
  ]
}
```

- Ana cubre el caso multitenant (CA-01); Bruno, el de una sola empresa (LOG-03).
- Campos opcionales: `second_name`, `second_last_name`, `phone_wa`, `website`.
- Validaciones: `version` conocida; `key` y `rfc` únicos en el archivo; correo único y normalizado; cada `memberships[].enterprise` existe en `enterprises`; `default_enterprise` es una de sus membresías; `status` es `active` o `inactive`.
- Las contraseñas del archivo son de prueba y ficticias (decisión L-05).

### 7.3 Contrato de salida (`SeedReport`)

```json
{
  "dry_run": false,
  "enterprises": [
    { "key": "saga", "id": 1, "result": "created" },
    { "key": "mega", "id": 2, "result": "created" }
  ],
  "users": [
    {
      "email": "ana@saga.test",
      "id": 1,
      "result": "created",
      "memberships": [
        { "enterprise": "saga", "id": 1, "result": "created" },
        { "enterprise": "mega", "id": 2, "result": "created" }
      ],
      "default_enterprise": "saga"
    }
  ]
}
```

`result` es `created` o `existing`. Con `--dry-run`, `would_create` o `existing`, e `id` es `null` en lo que no existe.

### 7.4 Comportamiento

- **Idempotente:** empresas por `rfc`, usuarios por correo, membresías por `(user_id, enterprise_id)`. Lo que ya existe se reporta como `existing` y **no se modifica** (tampoco la contraseña). Ejecutarlo dos veces da el mismo estado.
- **Una transacción:** si algo falla, no queda nada a medias.
- **Contraseñas:** se guardan con el mismo `PasswordHasher` (argon2id) que usa el login.
- **Reutilizable:** el archivo de entrada es el único punto a cambiar para otros datos. `SeedLoginData` y sus puertos son los mismos que usará el alta por administrador (LOG-02).

## 8. Archivos

| Archivo | Acción |
|---|---|
| `app/identity/login/domain/{email,status,entities,login_policy,access,errors}.py` | Crear |
| `app/identity/login/application/{ports,login,session_opener,authenticate,seed}.py` | Crear |
| `app/identity/login/infrastructure/persistence/repositories.py` | Crear: repositorios MySQL con SQLAlchemy Core sobre los modelos existentes. |
| `app/identity/login/infrastructure/security.py` | Crear: hasher argon2id y `TokenService`. |
| `app/identity/login/infrastructure/ids.py` | Crear: UUIDv7. |
| `app/identity/login/infrastructure/unit_of_work.py` | Crear |
| `app/identity/login/api/{schemas,routes,dependencies,error_map}.py` | Crear |
| `app/identity/login/cli/{__init__,seed}.py` | Crear: entrada del seeder, esquema `SeedPlan` y `SeedReport`. |
| `seeds/login/usuarios-prueba.json` | Crear |
| `app/bootstrap.py` | Modificar: armar los casos de uso. |
| `app/main.py` | Modificar: incluir el router de Login y su `error_map`. |
| `app/core/config.py`, `.env.example` | Modificar: `session_ttl_hours` (L-03). |
| `pyproject.toml`, `uv.lock` | Modificar: dependencia L-02 y contrato de capas con `cli` (L-04). |
| `tests/identity/login/fakes.py` | Crear: dobles en memoria de cada puerto, para Codex. |
| `docs/iterations/login-05-login-token/claude.md` | Este archivo. |

## 9. Decisiones que necesitan aprobación

| ID | Decisión | Recomendación |
|---|---|---|
| L-01 | Agrupar en esta tarea el dominio mínimo, el login, `GET /auth/session` y el seeder (sección 2). | Aprobar. |
| L-02 | **Dependencia nueva** `argon2-cffi` para argon2id, que la instrucción del módulo ya exige. La alternativa sin dependencia es `hashlib.scrypt`. | `argon2-cffi`. |
| L-03 | Vigencia del token (D-03): 12 h absolutas, configurable con `NEXUS_SESSION_TTL_HOURS`. Sin expiración por inactividad por ahora. | Aprobar. |
| L-04 | Nueva carpeta `cli/` como capa de entrada al mismo nivel que `api/`, y ajuste del contrato de import-linter (`api \| cli` sobre `application`). | Aprobar. |
| L-05 | Contraseñas de prueba escritas en `seeds/login/usuarios-prueba.json`, con el seeder bloqueado en `staging` y `production`. Alternativa: el archivo nombra variables de entorno (`password_env`) y las contraseñas viven fuera del repositorio. | Contraseñas en el archivo; son ficticias. |
| L-06 | D-04 (transporte en el navegador) sigue abierta. Esta tarea solo usa `Authorization: Bearer`. | Aprobar así. |
| L-07 | `account_inactive` y `no_enterprise_access` distintos de `invalid_credentials`, solo tras verificar la contraseña. | Aprobar. |

## 10. Criterios de aceptación

| # | Escenario | Resultado |
|---|---|---|
| AC-01 | Seeder con el archivo de ejemplo en una base vacía. | 2 empresas, 2 usuarios, 3 membresías, 2 preferencias; todo `created`. |
| AC-02 | Seeder ejecutado otra vez. | Todo `existing`; la base no cambia. |
| AC-03 | Seeder con `default_enterprise` que no es membresía del usuario. | Error de validación, código de salida ≠ 0, nada escrito. |
| AC-04 | Seeder con `NEXUS_APP_ENV=production`. | Se niega a ejecutarse. |
| AC-05 | Ana inicia sesión. | 200, empresa activa Saga, `is_multitenant = true`, sesión guardada solo con el hash del token (CA-01). |
| AC-06 | Bruno inicia sesión. | 200, empresa activa Saga, `is_multitenant = false` (LOG-03). |
| AC-07 | Correo inexistente o contraseña incorrecta. | 401 `invalid_credentials`, mismo mensaje. |
| AC-08 | Ana `inactive` con contraseña correcta. | 403 `account_inactive` (CA-07). |
| AC-09 | Saga `inactive` y Ana inicia sesión. | Entra en Mega y Mega pasa a ser su predeterminada (LOG-05). |
| AC-10 | Bruno sin empresas disponibles. | 403 `no_enterprise_access`. |
| AC-11 | `GET /auth/session` con el token de AC-05. | 200 con Saga. |
| AC-12 | `GET /auth/session` con token inventado, vencido o tras desactivar a Ana. | 401 `invalid_token`. |

## 11. Verificaciones previstas

- ruff, mypy y lint-imports (con el contrato de L-04).
- Pruebas unitarias de dominio y aplicación con los dobles de `tests/identity/login/fakes.py` (Codex).
- AC-01 a AC-12 contra un MySQL desechable con `0001` R2 aplicada, por HTTP con `httpx` y `uv run python -m ...` para el seeder.
- Revisión de que ningún log contiene contraseñas ni tokens.

## 12. Interfaces para Codex

- Puertos y casos de uso de la sección 6, con sus tipos de entrada y salida.
- Excepciones de dominio y su `code` HTTP (sección 4).
- `SeedPlan` y `SeedReport` (sección 7) como contrato del seeder.
- Dobles en memoria en `tests/identity/login/fakes.py`.

## 13. Fuera de alcance

Logout (`login-06`), SSO (`login-07`), cambio de empresa y predeterminada desde el perfil (`login-08`), presencia (`login-09`), revocación por pérdida de acceso (`login-10`), límite de intentos de login, alta de usuarios por endpoint de administrador, restablecimiento de contraseña.

---

## 14. Registro de entrega (2026-11-23)

**Estado:** implementado y verificado contra MySQL 8.4, pendiente de revisión de Codex. **Sin commit ni PR** (no indicados por el responsable).
**Base:** rama `worktree/claude_worktree` en `5cccb8c` (R2 de `login-04-migracion` ya incluida). No se trajeron commits de `develop`.

### 14.1 Aprobaciones

| Fecha | Aprobación |
|---|---|
| 2026-11-23 | El responsable aprueba L-01 a L-07 tal como se recomendaron. |

### 14.2 Archivos

| Archivo | Cambio |
|---|---|
| `app/identity/login/domain/{email,errors,status,entities,login_policy}.py` | Nuevos. `Email`, `Status`, `DeviceType`, `User`, `Membership`, errores y políticas (`choose_login_enterprise`, `ensure_user_active`, `available_memberships`, `is_multitenant`, `can_keep_session`). |
| `app/identity/login/application/{ports,views,session_opener,login,authenticate,seed}.py` | Nuevos. Puertos, `LoginWithPassword`, `SessionOpener`, `AuthenticateToken`, `DescribeSession`, `SeedLoginData`. |
| `app/identity/login/infrastructure/security.py` | Nuevo. `Argon2PasswordHasher` (argon2id, fuera del event loop, hash de referencia para igualar tiempos) y `Sha256TokenService`. |
| `app/identity/login/infrastructure/ids.py` | Nuevo. UUIDv7 propio. |
| `app/identity/login/infrastructure/persistence/{repositories,unit_of_work}.py` | Nuevos. Repositorios con SQLAlchemy Core y `SqlUnitOfWork`. |
| `app/identity/login/api/{schemas,dependencies,routes,error_map}.py` | Nuevos. `POST /api/v1/auth/login`, `GET /api/v1/auth/session`, `CurrentSession` y traducción a problem+json. |
| `app/identity/login/cli/seed.py` | Nuevo. Contrato de entrada `SeedFile` y de salida `report_to_json`. |
| `app/cli.py` | Nuevo. Comando `seed-login`. |
| `app/bootstrap.py` | Conecta los adaptadores (`install_login`, `build_seed_use_case`). |
| `app/main.py` | Llama a `install_login(app)`. |
| `app/core/config.py`, `.env.example` | `session_ttl_hours` / `NEXUS_SESSION_TTL_HOURS` (L-03). |
| `pyproject.toml`, `uv.lock` | `argon2-cffi` 25.1.0 (L-02); contrato de capas `api \| cli` y prohibición de adaptadores en `cli` (L-04); mypy estricto también en `api`, `cli` y `app.cli`. |
| `seeds/login/usuarios-prueba.json`, `seeds/README.md` | Datos de prueba de Ana y Bruno con Saga y Mega. |
| `tests/identity/login/fakes.py` | Dobles en memoria de todos los puertos para Codex. |
| `docs/PENDIENTES.md` | Registro global de pendientes (pedido del responsable). |

### 14.3 Aprobado frente a entregado

| Tema | Propuesta | Entregado y motivo |
|---|---|---|
| Comando del seeder | `python -m app.identity.login.cli.seed <archivo>` | `uv run python -m app.cli seed-login <archivo> [--dry-run]`. El contrato de L-04 prohíbe que `cli/` importe `app.bootstrap` (que importa los adaptadores), así que el ejecutable vive en `app/cli.py`, igual que `app/main.py` para HTTP. `cli/seed.py` conserva el contrato de entrada y salida. |
| Conexión de la API | `Depends(<función de app.bootstrap>)` | La API declara puntos de inyección (`get_*_use_case`) y `app.bootstrap.install_login` los sustituye con `dependency_overrides`. Motivo: la regla "la API no importa adaptadores" también detecta la importación indirecta a través de `app.bootstrap`. |
| Puerto `CatalogRepository` | Puerto propio | No existe: los repositorios resuelven `statuses` y `device_types` por `name` dentro de la consulta. El dominio y la aplicación nunca ven un `id` de catálogo y hay una consulta menos. |
| `domain/access.py` | Archivo propio | Sus dos funciones están en `domain/login_policy.py`. |
| Contraseña en el archivo del seeder | Sin mínimo | Mínimo de 8 caracteres. |
| Errores del archivo del seeder | — | Se listan sin los valores de entrada, porque el archivo contiene contraseñas. |
| Campos extra en `POST /login` | — | Se rechazan con 422 (`extra="forbid"`). |
| Códigos de salida del seeder | ≠ 0 | 2 archivo inválido, 3 ambiente no permitido, 1 error inesperado. |

### 14.4 Verificaciones y resultados reales

| Verificación | Resultado |
|---|---|
| `uv run ruff check .` / `ruff format --check .` | "All checks passed!" / "53 files already formatted". |
| `uv run mypy app` | "Success: no issues found in 40 source files". |
| `uv run lint-imports` | 4 contratos KEPT, 0 rotos. |
| `uv run pytest` | 0 pruebas: todavía no hay pruebas automatizadas (las escribe Codex). |
| MySQL desechable | `mysql:8.4` (8.4.13) en un contenedor en el puerto 3318, con clave aleatoria temporal fuera del repo, `alembic upgrade head` (0001 R2). Contenedor eliminado al terminar. `.env` no se leyó. |
| AC-01 | Primer `seed-login`: 2 empresas, 2 usuarios, 3 membresías, 2 preferencias, todo `created`; `password_hash` empieza por `$argon2id$`. `--dry-run` previo: todo `would_create` y la base vacía. |
| AC-02 | Segunda ejecución: todo `existing`; conteos sin cambio. |
| AC-03 | `default_enterprise` fuera de sus membresías: salida 2, mensaje `users.1: ... no está entre sus membresías`, nada escrito. |
| AC-04 | `NEXUS_APP_ENV=production`: salida 3, "El seeder no se ejecuta en el ambiente 'production'." |
| AC-05 | Ana con el correo con mayúsculas y espacios: 200, Saga, `is_multitenant: true`, 2 empresas, `Cache-Control: no-store`, token de 43 caracteres; en la base solo su SHA-256 y `device_type = desktop`. |
| AC-06 | Bruno: 200, Saga, `is_multitenant: false`. |
| AC-07 | Correo inexistente y contraseña incorrecta: ambos 401 `invalid_credentials` con el mismo `detail`. |
| AC-08 | Ana `inactive` con contraseña correcta: 403 `account_inactive`. |
| AC-09 | Saga `inactive`: Ana entra en Mega y su predeterminada pasa a Mega (verificado en `user_preferences`). |
| AC-10 | Bruno con Saga inactiva: 403 `no_enterprise_access`. |
| AC-11 | `GET /auth/session` con el token de AC-05: 200, Saga, mismo `session_id`, sin `access_token`; `last_used_at` actualizado. |
| AC-12 | Token inventado: 401 `invalid_token` con `WWW-Authenticate: Bearer`. Sin cabecera: 401 `not_authenticated`. Token tras desactivar a Ana: 401 `invalid_token`. Token vencido: 401 `invalid_token`. |
| Extra | `device_type: "watch"`: 422 `validation_error`, sin repetir el valor enviado. |
| Logs | Ninguna línea de log contiene contraseñas, `access_token` ni tokens Bearer. |

Las verificaciones HTTP se hicieron con `httpx.ASGITransport` sobre `create_app()` contra el MySQL real, con un script desechable fuera del repositorio (11 de 11 escenarios). Una segunda corrida sobre la misma base dio 9 de 11, como se esperaba: AC-09 de la primera corrida dejó a Mega como predeterminada de Ana (LOG-05 es persistente), así que AC-05 y AC-11 la ven en Mega.

### 14.5 Pendientes y traspaso a Codex

- **Pruebas unitarias** de dominio y aplicación con `tests/identity/login/fakes.py` (`InMemoryStore`, `FakePasswordHasher`, `FakeTokenService`, `FakeIdGenerator`). Escenarios sugeridos: los AC-05 a AC-12 en memoria, más `choose_login_enterprise` con empates de `joined_at` y `SeedLoginData` idempotente y en `dry_run`.
- **Pruebas de integración** (HTTP + MySQL): no hay base `nexus_test` (P-33). Los AC de la sección 14.4 son el guion.
- **Contratos para las pruebas:** sección 4 (API), sección 6 (puertos) y `SeedFile` / `report_to_json` (seeder).
- **Revisar:** que la API no exponga detalles internos; que `AuthenticateToken` revalide usuario, membresía y empresa; que el seeder no modifique datos existentes.
- La revocación en base al perder el acceso sigue en `login-10`; el logout, en `login-06`.
