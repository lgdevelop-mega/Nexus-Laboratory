# login-01 · Infraestructura base del backend y primer contrato API de Login

**Autor:** Claude Code · **Fecha:** 2026-11-19 · **Estado:** borrador para revisión de Codex y del responsable.
**Rama:** `worktree/claude_worktree` · Sin código, dependencias, migraciones ni llamadas a SSO en esta tarea.

## 0. Estado y fuentes

| Fuente | Uso |
|---|---|
| `AGENTS.md`, `CLAUDE.md` | Ciclo de trabajo, capas `api/ application/ domain/ infrastructure/`, ubicación `app/<area>/<modulo>/`, pruebas espejo en `tests/`. |
| `docs/modules/login/01-reglas-de-negocio.md` (borrador funcional v0.1, 18-nov-2026) | Reglas LOG-01…LOG-16, tabla de decisión SSO y casos CA-01…CA-08. |
| `codex.md`, `docs/agents/codex.md` | Convenciones de pruebas que Codex aplicará (dobles para repositorios y servicios externos). |

- **No se encontró `NEXUS_Login_Agentes_v0.1.md`.** Tomo `docs/modules/login/01-reglas-de-negocio.md` como la versión incorporada (mismo contenido esperado: borrador v0.1 de Login). Si existe otra versión, hay que reconciliarla antes de aprobar el contrato.
- Las reglas de Login están **en validación por la PMO**. Todo el contrato se apoya en ese borrador.
- El repositorio no tiene código todavía. Todo lo descrito en las secciones 1 a 3 es **propuesta**.

Marcas usadas en este documento:

| Marca | Significado |
|---|---|
| `[APROBAR]` | Decisión técnica o de alcance que debe aprobar el responsable. |
| `[PMO]` | Comportamiento que depende de la validación de la regla por la PMO. |
| `[PROPUESTA]` | Decisión técnica que recomiendo. Sigue sujeta a revisión aunque no bloquea. |

---

## 1. Infraestructura base del backend

### 1.1 Tecnologías propuestas `[APROBAR]`

| Pieza | Propuesta | Motivo |
|---|---|---|
| Lenguaje | Python 3.12 | Versión estable con buen soporte de tipado. |
| Framework HTTP | FastAPI + Pydantic v2 | Requisito del proyecto. Pydantic valida la forma de la petición en `api/`. |
| Configuración | pydantic-settings | Configuración tipada por variables de entorno y por ambiente. |
| Base de datos | PostgreSQL 16 | Transacciones, restricciones únicas, `citext`/índices funcionales para el correo, y esquemas por tenant si se eligen (LOG-01). |
| ORM y acceso | SQLAlchemy 2.0 **async** + asyncpg | La validación del ticket SSO es una llamada de red; el modo async evita bloquear workers. Alternativa más sencilla: SQLAlchemy sync con rutas `def`. **Afecta a Codex**: con async, las pruebas usan `pytest-asyncio`. |
| Migraciones | Alembic | Estándar con SQLAlchemy. Solo Claude crea migraciones (`codex.md`). |
| Hash de contraseñas | argon2-cffi (Argon2id) | Algoritmo recomendado actualmente para contraseñas. |
| Cliente SSO | httpx (en el adaptador) | Cliente async, con transporte simulable en las pruebas de integración. |
| Pruebas | pytest + pytest-asyncio | Unitarias de dominio y aplicación con dobles; integración en tareas explícitas. |
| Calidad | ruff (lint y formato) + mypy (estricto en `domain/` y `application/`) | Mantiene el dominio puro y los puertos tipados. |
| Dependencias | uv + `pyproject.toml` + `uv.lock` | Instalación reproducible y rápida. |
| Entorno local | `docker-compose.yml` solo con PostgreSQL | La API se ejecuta con `uvicorn`, sin contenedor obligatorio. |

### 1.2 Árbol inicial propuesto

```text
NEXUS_API_v2.0/
├── pyproject.toml                 # dependencias, ruff, mypy, pytest
├── uv.lock
├── alembic.ini
├── alembic/
│   ├── env.py                     # lee DATABASE_URL de app.core.config
│   └── versions/
│       └── 0001_login_base.py     # enterprises, users, users_enterprises, sessions
├── docker-compose.yml             # PostgreSQL local
├── .env.example                   # variables NEXUS_* sin secretos
├── app/
│   ├── main.py                    # create_app(): FastAPI, routers, manejadores de error
│   ├── bootstrap.py               # punto de composición: puertos → adaptadores
│   ├── core/
│   │   ├── config.py              # Settings (pydantic-settings), APP_ENV
│   │   ├── db.py                  # engine async, sessionmaker
│   │   ├── errors.py              # formato problem+json común
│   │   └── clock.py               # SystemClock
│   └── identity/                  # área [APROBAR]
│       └── login/
│           ├── api/
│           │   ├── router.py      # rutas /api/v1/auth/*
│           │   ├── schemas.py     # entradas y respuestas Pydantic
│           │   ├── cookies.py     # emisión y borrado de la cookie de sesión
│           │   ├── dependencies.py# obtención de casos de uso y sesión actual
│           │   └── error_map.py   # error de dominio/aplicación → HTTP
│           ├── application/
│           │   ├── ports.py       # Protocols de repositorios y servicios
│           │   ├── dto.py         # comandos y resultados (dataclasses)
│           │   ├── errors.py      # errores de aplicación (ticket inválido, proveedor caído)
│           │   ├── session_opener.py
│           │   └── use_cases/
│           │       ├── login_with_password.py
│           │       ├── login_with_sso.py
│           │       ├── logout.py
│           │       └── get_current_session.py
│           ├── domain/
│           │   ├── entities.py    # User, Enterprise, Membership, Session
│           │   ├── values.py      # Email, UserStatus, MembershipStatus, AuthMethod
│           │   ├── policies.py    # reglas LOG-03/05/07/09/15/16
│           │   └── errors.py
│           └── infrastructure/
│               ├── persistence/
│               │   ├── models.py          # tablas SQLAlchemy
│               │   ├── repositories.py    # adaptadores de los repositorios
│               │   └── unit_of_work.py
│               ├── security/
│               │   ├── argon2_hasher.py
│               │   └── session_tokens.py  # token aleatorio + SHA-256
│               └── sso/
│                   └── ticket_validator.py# adaptador real (pendiente de proveedor)
└── tests/
    ├── conftest.py
    └── identity/login/
        ├── fakes.py               # dobles en memoria de cada puerto
        ├── domain/
        ├── application/
        ├── api/                   # integración HTTP (tarea posterior)
        └── infrastructure/        # integración BD/SSO (tarea posterior)
```

- **Punto de entrada:** `app/main.py:create_app()`. Se ejecuta con `uvicorn app.main:create_app --factory`.
- **Composición de dependencias:** `app/bootstrap.py` construye los adaptadores concretos por petición (repositorios sobre la `AsyncSession`) y entrega a FastAPI funciones `get_login_with_password()`, etc. Las rutas solo conocen esas funciones. Las pruebas HTTP pueden sustituirlas con `app.dependency_overrides`.
- **Configuración por ambiente:** `APP_ENV = local | test | staging | production`. Variables con prefijo `NEXUS_`, por ejemplo `NEXUS_DATABASE_URL`, `NEXUS_SESSION_TTL_MINUTES`, `NEXUS_SESSION_COOKIE_SECURE` y `NEXUS_CORS_ORIGINS`. El `.env` se usa solo en local y no se versiona; `.env.example` documenta las claves sin valores. `production` rechaza arrancar con cookies no seguras o con el validador SSO falso.
- **Persistencia:** una `AsyncSession` por petición y un `UnitOfWork` que hace commit o rollback al terminar el caso de uso.
- **Migraciones:** Alembic con `env.py` leyendo la misma configuración. Cada cambio de esquema se hace en una migración revisable.
- **Pruebas:** reflejan `app/` (`tests/identity/login/domain/` y `tests/identity/login/application/`), según `docs/agents/codex.md`.

### 1.3 Recorrido de una solicitud

```text
POST /api/v1/auth/login  {email, password}
  │
  ▼ api/router.py
  │   · Pydantic valida forma (422 si falla)
  │   · arma PasswordLoginCommand(email, password, client=ClientInfo(ip, user_agent))
  │   · obtiene LoginWithPassword mediante Depends(get_login_with_password)   ← bootstrap.py
  ▼ application/use_cases/login_with_password.py
  │   · UserRepository.get_by_email → PasswordHasher.verify
  │   · domain.policies.ensure_user_can_log_in(user)                     (LOG-15)
  │   · SessionOpener.open(user, preferred=None, method=PASSWORD)
  │        · MembershipRepository.list_for_user
  │        · domain.policies.resolve_active_enterprise(...)              (LOG-03, LOG-05)
  │        · UserRepository.set_default_enterprise (si cambió)           (LOG-05)
  │        · SessionTokenGenerator + SessionRepository.add
  │   · UnitOfWork.commit
  ▼ LoginResult (token sin hash + SessionContext)
  │
  ▼ api/router.py
      · Set-Cookie nexus_session=<token>; HttpOnly; Secure; SameSite=Lax
      · 200 JSON SessionContextResponse
  (Error de dominio o aplicación → error_map.py → 4xx/5xx application/problem+json)
```

Los adaptadores (`SqlAlchemyUserRepository`, `Argon2PasswordHasher`, `HttpSsoTicketValidator`…) implementan los `Protocol` de `application/ports.py`. Solo `bootstrap.py` importa de `infrastructure/`; `domain/` no importa FastAPI, SQLAlchemy ni httpx.

### 1.4 Patrones `[PROPUESTA]`

- **Casos de uso directos.** Cada ingreso es una secuencia lineal dentro de una transacción: validar, decidir, persistir y abrir la sesión.
- **`SessionOpener` (servicio de aplicación compartido).** Ambos ingresos terminan igual: calculan la empresa activa y predeterminada, el permiso multitenant y la sesión. Extraerlo evita duplicar LOG-05, LOG-09 y la emisión de la sesión, y permite probarlo por separado. No es un pipeline.
- **Políticas de dominio como funciones puras** (`policies.py`). La tabla de decisión SSO (LOG-07) se expresa como `decide_sso_access(...)`, lo que permite probar cada fila de la tabla sin base de datos.
- **Sin pipeline ni orquestador.** No hay etapas que se recombinen ni coordinación entre servicios; añadirlos ocultaría el recorrido. Se revisará si el cambio de empresa o la recuperación introducen pasos asíncronos, como el envío de correo con outbox.

### 1.5 Qué necesita la primera entrega y qué puede esperar

| Primera entrega (login-01 implementación) | Puede esperar |
|---|---|
| Tablas `enterprises`, `users`, `users_enterprises`, `sessions` (migración 0001) | Modelo completo de roles y permisos (se guarda `role` como texto, `basic` por defecto) |
| Hash Argon2 y verificación sin filtrar la existencia del usuario | Notificador de correo y enlaces de contraseña (LOG-12, LOG-13) |
| Puerto `SsoTicketValidator` y un **doble falso** para pruebas; el adaptador real se crea cuando se defina el proveedor | Adaptador SSO real (protocolo pendiente, sección 3.4) |
| Sesión opaca en servidor, revalidada en cada petición (LOG-16) | Revocación de sesiones en otros dispositivos (pendiente según las reglas) |
| Formato de error problem+json | Auditoría de ingresos, rate limiting (429), bloqueo por intentos |
| Datos semilla de desarrollo (Saga, Mega, Ana) por script local | Estructura de tenant por empresa (LOG-01): esquema o columna `enterprise_id` en los módulos de negocio |

`users`, `enterprises` y `users_enterprises` son **globales** (fuera del tenant), porque el usuario y sus membresías cruzan empresas. Esto vale con cualquiera de las dos estrategias de tenant de LOG-01.

### 1.6 Esquema propuesto (migración 0001) `[PROPUESTA]`

| Tabla | Columnas principales | Restricciones |
|---|---|---|
| `enterprises` | `id uuid`, `code text`, `name text`, `is_active bool`, `sso_enabled bool`, `created_at` | `code` único |
| `users` | `id uuid`, `email citext`, `full_name text null`, `password_hash text null`, `status (active, suspended)`, `default_enterprise_id uuid null → enterprises`, `created_via (admin, sso)`, `created_at` | `email` único |
| `users_enterprises` | `id uuid`, `user_id`, `enterprise_id`, `status (active, suspended, revoked)`, `role text default 'basic'`, `created_at` | único (`user_id`, `enterprise_id`); índice (`user_id`, `created_at`) para LOG-05 |
| `sessions` | `id uuid`, `token_hash bytea`, `user_id`, `enterprise_id` (activa), `auth_method (password, sso)`, `created_at`, `expires_at`, `revoked_at null`, `revoked_reason null` | `token_hash` único |

La configuración del proveedor SSO por empresa (emisor, URL de servicio, secretos) queda pendiente hasta conocer el protocolo. Los secretos no se guardarán en texto plano.

---

## 2. Primer contrato API de Login

Prefijo `/api/v1`. JSON UTF-8. Todos los ejemplos usan datos ficticios.

### 2.1 Convenciones comunes

**Sesión `[APROBAR]`:** token opaco aleatorio de 256 bits enviado en la cookie `nexus_session` (`HttpOnly; Secure; SameSite=Lax; Path=/api`). En base de datos solo se guarda su SHA-256. Elijo un token en servidor en lugar de un JWT porque LOG-13, LOG-14 y LOG-16 exigen cerrar sesiones de inmediato, y un JWT seguiría siendo válido hasta vencer. Alternativa: `Authorization: Bearer`, si el frontend no comparte dominio o si hay clientes que no son navegador. Vigencia propuesta: 8 h absolutas, sin renovación deslizante en esta entrega.

**Errores:** `application/problem+json` (RFC 9457) con `code` estable para el frontend:

```json
{
  "type": "https://nexus.example.com/problems/invalid-credentials",
  "title": "Credenciales inválidas",
  "status": 401,
  "code": "INVALID_CREDENTIALS",
  "detail": "Correo o contraseña incorrectos."
}
```

| `code` | HTTP | Cuándo |
|---|---|---|
| `VALIDATION_ERROR` | 422 | Falta un campo o el correo tiene un formato inválido (incluye `errors[]`). |
| `INVALID_CREDENTIALS` | 401 | El correo no existe, el usuario no tiene contraseña o la contraseña es incorrecta. Se usa la misma respuesta en los tres casos. |
| `USER_SUSPENDED` | 403 | Usuario suspendido globalmente (LOG-15, CA-07). |
| `NO_ACTIVE_MEMBERSHIP` | 403 | Cero membresías vigentes en el ingreso convencional (LOG-05). |
| `SSO_NOT_AVAILABLE` | 403 | La empresa no existe, está inactiva o tiene SSO deshabilitado (LOG-07, fila 1). |
| `SSO_TICKET_INVALID` | 401 | El proveedor rechaza el ticket o el ticket no es para NEXUS o para esa empresa (LOG-07, fila 1). |
| `MEMBERSHIP_INACTIVE` | 403 | Membresía suspendida o revocada en la empresa de origen (LOG-07, LOG-15, CA-05). |
| `SSO_PROVIDER_UNAVAILABLE` | 503 | El proveedor no responde o falla de forma inesperada. |
| `SESSION_REVOKED` | 401 | No hay cookie, la sesión venció o fue cerrada, o falla la revalidación de LOG-16. |

**Contexto de sesión (respuesta común de los ingresos y de `GET /auth/session`):**

```json
{
  "session": {
    "auth_method": "password",
    "created_at": "2026-11-19T14:02:11Z",
    "expires_at": "2026-11-19T22:02:11Z"
  },
  "user": {
    "id": "a1a1a1a1-0000-4000-8000-000000000001",
    "email": "ana.perez@example.com",
    "full_name": "Ana Pérez",
    "has_password": true
  },
  "active_enterprise": { "id": "e5a9a000-0000-4000-8000-00000000000a", "code": "saga", "name": "Saga S.A." },
  "default_enterprise": { "id": "e5a9a000-0000-4000-8000-00000000000a", "code": "saga", "name": "Saga S.A." },
  "available_enterprises": [
    { "id": "e5a9a000-0000-4000-8000-00000000000a", "code": "saga", "name": "Saga S.A." },
    { "id": "e3e9a000-0000-4000-8000-00000000000b", "code": "mega", "name": "Mega Ltda." }
  ],
  "can_switch_enterprise": true
}
```

- `active_enterprise`: empresa de la sesión. Determina permisos, configuraciones y borradores, según el modelo funcional.
- `default_enterprise`: preferencia global (LOG-04). Puede diferir de la activa (CA-01).
- `available_enterprises`: empresas con membresía vigente. En esta entrega es informativo, porque el cambio de empresa queda para login-02.
- `can_switch_enterprise`: refleja `usuario_multitenant` (LOG-09, LOG-10); es `true` con dos o más membresías vigentes.
- `has_password`: permite al frontend indicar que el acceso convencional aún no está habilitado (LOG-08).
- El rol en la empresa activa queda fuera hasta que exista el modelo de permisos `[APROBAR]`.

**Membresía vigente `[PMO]`:** propongo definirla como `users_enterprises.status = active` **y** `enterprises.is_active = true`.

### 2.2 Ingreso convencional — `POST /api/v1/auth/login`

Reglas: LOG-03, LOG-05, LOG-15. Casos: CA-01, CA-06, CA-07.

**Entrada**

```json
{ "email": "ana.perez@example.com", "password": "Contraseña-Ficticia-1" }
```

**Algoritmo**

1. Normaliza el correo (trim y minúsculas `[PROPUESTA]`) y busca el usuario.
2. Si el usuario no existe o no tiene `password_hash`, ejecuta una verificación ficticia de igual costo y responde `401 INVALID_CREDENTIALS`. Si la contraseña es incorrecta, responde igual.
3. Si la contraseña es correcta y el usuario está suspendido, responde `403 USER_SUSPENDED` (LOG-15, CA-07) `[APROBAR]`.
4. **Empresa activa** (LOG-03, LOG-05):
   - Una sola membresía vigente: esa empresa.
   - Varias: la predeterminada si sigue vigente.
   - Si la predeterminada ya no es vigente, se guarda como predeterminada la empresa de la membresía vigente más antigua (`created_at` menor) y se abre en ella (CA-06) `[PMO]`.
   - Cero membresías vigentes: `403 NO_ACTIVE_MEMBERSHIP`.
5. Crea la sesión y responde `200` con `Set-Cookie` y el contexto.

**Ejemplos**

| Escenario | Resultado |
|---|---|
| CA-01: Ana (predeterminada Saga, Mega vigente) | `200`, `active_enterprise=saga`, `can_switch_enterprise=true` |
| CA-06: Saga se desactiva; Ana conserva Mega (2025-03-01) y Lumen (2026-02-10) | `200`, `active_enterprise=mega`, `default_enterprise=mega` (persistido) |
| Ana con contraseña errónea, o `nadie@example.com` | `401 INVALID_CREDENTIALS` |
| CA-07: `bruno.diaz@example.com` suspendido, contraseña correcta | `403 USER_SUSPENDED` |
| `carla.ruiz@example.com` con todas sus membresías revocadas | `403 NO_ACTIVE_MEMBERSHIP` |
| `{"email": "no-es-correo"}` | `422 VALIDATION_ERROR` |

```http
HTTP/1.1 403 Forbidden
Content-Type: application/problem+json

{"type":"https://nexus.example.com/problems/user-suspended","title":"Usuario suspendido","status":403,"code":"USER_SUSPENDED","detail":"Su acceso está suspendido. Solicite la reactivación al administrador."}
```

### 2.3 Ingreso por SSO — `POST /api/v1/auth/sso/login`

Reglas: LOG-06, LOG-07, LOG-08, LOG-09, LOG-15. Casos: CA-01 a CA-05 y CA-07.

**Flujo propuesto `[PMO]` / `[APROBAR]`:** el frontend redirige al proveedor y recibe el ticket en su callback. Después envía el ticket y el código de la empresa de origen al backend, que valida el ticket con el proveedor (servidor a servidor). La **empresa activa es siempre la de origen** (LOG-06).

**Entrada**

```json
{ "enterprise_code": "mega", "ticket": "ST-ficticio-7f3c9e" }
```

**Algoritmo (tabla de decisión LOG-07, en orden)**

| # | Condición | Resultado HTTP | Efecto |
|---|---|---|---|
| 1a | `enterprise_code` desconocido, empresa inactiva o `sso_enabled=false` | `403 SSO_NOT_AVAILABLE` | No se llama al proveedor ni se crea nada. |
| 1b | El proveedor rechaza el ticket, o el ticket no es para NEXUS o para esa empresa | `401 SSO_TICKET_INVALID` | No se crea nada. |
| 1c | El proveedor no responde | `503 SSO_PROVIDER_UNAVAILABLE` | No se crea nada. |
| 2 | Usuario con ese correo suspendido globalmente | `403 USER_SUSPENDED` | Se rechaza **antes** de crear membresías (CA-07). |
| 3 | Correo nuevo | `200`, `provisioning=user_created` | Crea un usuario sin contraseña, `created_via=sso`, y una membresía `basic` en origen. Origen pasa a ser predeterminada y activa (CA-02). |
| 4 | Usuario existente sin membresía en origen | `200`, `provisioning=membership_created` | Crea una membresía `basic` y abre en origen. **Conserva la predeterminada** (CA-03). Con dos membresías vigentes, `can_switch_enterprise=true` (LOG-09). |
| 5 | Membresía vigente en origen | `200`, `provisioning=none` | Abre en origen con el rol existente (CA-01, CA-04). |
| 6 | Membresía suspendida o revocada en origen | `403 MEMBERSHIP_INACTIVE` | No reactiva nada; solo el administrador puede hacerlo (CA-05, LOG-11). |

Se responde `200` en todos los casos de éxito, con el contexto de sesión y el campo adicional `"provisioning": "none" | "membership_created" | "user_created"`. No uso `201` porque el recurso devuelto es la sesión y no el usuario creado. El alta, la membresía y la sesión se hacen en **una sola transacción**. Si dos primeros ingresos simultáneos chocan con una restricción única, el adaptador reintenta una vez y vuelve a leer.

**Ejemplos**

CA-02 (correo nuevo `diego.mora@example.com` por SSO de Mega):

```json
{
  "provisioning": "user_created",
  "session": { "auth_method": "sso", "created_at": "2026-11-19T15:00:00Z", "expires_at": "2026-11-19T23:00:00Z" },
  "user": { "id": "d1d1d1d1-0000-4000-8000-000000000004", "email": "diego.mora@example.com", "full_name": "Diego Mora", "has_password": false },
  "active_enterprise": { "id": "e3e9a000-0000-4000-8000-00000000000b", "code": "mega", "name": "Mega Ltda." },
  "default_enterprise": { "id": "e3e9a000-0000-4000-8000-00000000000b", "code": "mega", "name": "Mega Ltda." },
  "available_enterprises": [ { "id": "e3e9a000-0000-4000-8000-00000000000b", "code": "mega", "name": "Mega Ltda." } ],
  "can_switch_enterprise": false
}
```

| Escenario | Resultado |
|---|---|
| CA-01: Ana por SSO de Mega | `200`, `provisioning=none`, `active=mega`, `default=saga` |
| CA-03: `elena.soto@example.com` (solo Saga) entra por primera vez por SSO de Mega | `200`, `provisioning=membership_created`, `active=mega`, `default=saga`, `can_switch_enterprise=true` |
| CA-04: Ana vuelve a Mega, donde tiene rol `supervisor` | `200`, `provisioning=none`; el rol `supervisor` no cambia |
| CA-05: membresía de Ana en Mega revocada; presenta un ticket válido de Mega | `403 MEMBERSHIP_INACTIVE` |
| CA-07: Bruno suspendido con ticket válido | `403 USER_SUSPENDED` |
| `enterprise_code="lumen"` con SSO deshabilitado | `403 SSO_NOT_AVAILABLE` |
| Ticket vencido o reutilizado | `401 SSO_TICKET_INVALID` |

### 2.4 Sesión actual — `GET /api/v1/auth/session` (incluida)

Reglas: LOG-09, LOG-10, LOG-15, LOG-16. Casos: CA-05.

Devuelve `200` con el mismo contexto. Antes de responder, **revalida** que la sesión no esté vencida ni revocada, que el usuario no esté suspendido, que la empresa activa esté activa y que su membresía siga vigente. Si algo falla, marca la sesión como revocada (`revoked_reason`), borra la cookie y responde `401 SESSION_REVOKED` (LOG-16, CA-05). La misma revalidación será la dependencia `require_session` de todas las rutas protegidas futuras. Sirve al frontend para recuperar el contexto tras recargar la página.

```json
{"type":"https://nexus.example.com/problems/session-revoked","title":"Sesión cerrada","status":401,"code":"SESSION_REVOKED","detail":"Su acceso a Mega Ltda. ya no está vigente. Ingrese nuevamente."}
```

Nota CA-05: cuando el administrador revoca la membresía de Mega, la siguiente petición de Ana con esa sesión recibe `401`. Si vuelve a ingresar por contraseña abre en Saga con `can_switch_enterprise=false`; si usa un ticket de Mega recibe `403 MEMBERSHIP_INACTIVE`. El cierre **inmediato** desde la acción del administrador corresponde al módulo de administración, que llamará a `SessionRepository.revoke_for_membership(...)`.

### 2.5 Cierre de sesión — `POST /api/v1/auth/logout` (incluida)

Regla: LOG-14. Revoca solo la sesión actual de NEXUS (`revoked_reason=logout`), borra la cookie y responde `204`. No llama al proveedor SSO, cuya sesión se conserva. Es idempotente: sin sesión válida también responde `204` y borra la cookie.

### 2.6 Operaciones ubicadas y diferidas

| Operación | Ruta propuesta | Reglas / CA | Entrega | Motivo |
|---|---|---|---|---|
| Cambiar empresa activa | `POST /api/v1/auth/session/enterprise` `{enterprise_id}` → nuevo contexto | LOG-10, LOG-09 | login-02 | Requiere aplicar los permisos de la empresa destino; el modelo de permisos no existe aún. Esta entrega ya expone `can_switch_enterprise` y `available_enterprises`. |
| Elegir empresa predeterminada | `PUT /api/v1/me/default-enterprise` `{enterprise_id}` → `204` | LOG-04, LOG-10 | login-02 | Es independiente del ingreso y no bloquea el login. |
| Configurar o restablecer contraseña con enlace | `POST /api/v1/auth/password/setup` `{token, new_password}` | LOG-08, LOG-12, LOG-13, CA-08 | login-03 | Depende del notificador de correo y de las decisiones pendientes del borrador: invalidación del enlace anterior y vigencia de la contraseña actual. Al completarse cierra la sesión actual de NEXUS y conserva la del SSO. |
| Alta de usuario convencional con primera empresa | `POST /api/v1/admin/users` | LOG-01, LOG-02 | módulo de administración | Es una operación del administrador, no del Login. |
| Reenvío de enlace e inicio de recuperación | `POST /api/v1/admin/users/{id}/password-links` | LOG-12, LOG-13 | módulo de administración | La inicia el administrador. |
| Suspender o reactivar usuario o membresía; desactivar empresa | `PATCH /api/v1/admin/...` | LOG-05, LOG-11, LOG-15, LOG-16, CA-05, CA-06 | módulo de administración | Debe revocar sesiones y recalcular la predeterminada en el momento del evento. Esta entrega cubre ese recálculo al ingresar. |

---

## 3. Entrega para revisión

### 3.1 Trazabilidad operación ↔ reglas ↔ casos

| Operación | LOG | CA | Estado |
|---|---|---|---|
| `POST /auth/login` | 03, 05, 15 | 01, 06, 07 | Incluida |
| `POST /auth/sso/login` | 06, 07, 08, 09, 15 | 01, 02, 03, 04, 05, 07 | Incluida |
| `GET /auth/session` (revalidación) | 09, 10, 15, 16 | 05 | Incluida |
| `POST /auth/logout` | 14 | — | Incluida |
| `SessionOpener` (contexto común) | 03, 05, 06, 09 | 01, 03, 06 | Incluida (interna) |
| `POST /auth/session/enterprise` | 09, 10 | — | login-02 |
| `PUT /me/default-enterprise` | 04, 10 | 01 (preferencia) | login-02 |
| `POST /auth/password/setup` | 08, 12, 13 | 08 | login-03 |
| Operaciones de administrador | 01, 02, 05, 11, 12, 13, 15, 16 | 05, 06 | Otro módulo |

Las 16 reglas LOG y los 8 casos CA quedan asignados a alguna operación. CA-08 y LOG-01, 02, 11, 12 y 13 no se cubren en esta entrega.

### 3.2 Interfaces para las pruebas unitarias de Codex

**Dominio (Python puro, `app/identity/login/domain/`)**

```python
class UserStatus(StrEnum): ACTIVE = "active"; SUSPENDED = "suspended"
class MembershipStatus(StrEnum): ACTIVE = "active"; SUSPENDED = "suspended"; REVOKED = "revoked"
class AuthMethod(StrEnum): PASSWORD = "password"; SSO = "sso"

@dataclass(frozen=True)
class Email:
    value: str                       # normalizado: trim + minúsculas
    @classmethod
    def parse(cls, raw: str) -> "Email": ...   # InvalidEmail

@dataclass
class Enterprise:
    id: UUID; code: str; name: str; is_active: bool; sso_enabled: bool

@dataclass
class User:
    id: UUID; email: Email; full_name: str | None
    password_hash: str | None; status: UserStatus
    default_enterprise_id: UUID | None; created_at: datetime
    @property
    def has_password(self) -> bool: ...

@dataclass
class Membership:
    id: UUID; user_id: UUID; enterprise: Enterprise
    status: MembershipStatus; role: str; created_at: datetime
    def is_current(self) -> bool: ...     # status ACTIVE y enterprise.is_active  [PMO]

@dataclass
class Session:
    id: UUID; user_id: UUID; enterprise_id: UUID; auth_method: AuthMethod
    created_at: datetime; expires_at: datetime
    revoked_at: datetime | None; revoked_reason: str | None

# policies.py
def ensure_user_can_log_in(user: User) -> None: ...                       # UserSuspended (LOG-15)

@dataclass(frozen=True)
class EnterpriseResolution:
    active: Enterprise
    default: Enterprise
    default_changed: bool                                                  # persistir si True (LOG-05)

def resolve_active_enterprise(
    user: User, memberships: Sequence[Membership], origin: Enterprise | None
) -> EnterpriseResolution: ...
    # origin=None → ingreso convencional (LOG-03/05); origin → SSO (LOG-06)
    # NoActiveMembership si no hay vigentes y origin es None

class SsoDecision(StrEnum):
    CREATE_USER_AND_MEMBERSHIP = "user_created"
    CREATE_MEMBERSHIP = "membership_created"
    OPEN_EXISTING = "none"

def decide_sso_access(user: User | None, origin_membership: Membership | None) -> SsoDecision: ...
    # UserSuspended (fila 2), MembershipInactive (fila 6)

def has_multitenant_permission(memberships: Sequence[Membership]) -> bool: ...   # LOG-09

def session_revocation_reason(
    session: Session, user: User, membership: Membership | None, now: datetime
) -> str | None: ...       # None = válida; si no: "expired", "user_suspended", "membership_inactive", "enterprise_inactive" (LOG-15/16)

# errors.py
class LoginDomainError(Exception): ...
class InvalidEmail(LoginDomainError): ...
class UserSuspended(LoginDomainError): ...
class NoActiveMembership(LoginDomainError): ...
class MembershipInactive(LoginDomainError): ...
```

**Puertos (`application/ports.py`, `typing.Protocol`, async)**

```python
class UserRepository(Protocol):
    async def get_by_email(self, email: Email) -> User | None: ...
    async def get_by_id(self, user_id: UUID) -> User | None: ...
    async def add(self, user: User) -> None: ...
    async def set_default_enterprise(self, user_id: UUID, enterprise_id: UUID) -> None: ...

class EnterpriseRepository(Protocol):
    async def get_by_code(self, code: str) -> Enterprise | None: ...

class MembershipRepository(Protocol):
    async def list_for_user(self, user_id: UUID) -> list[Membership]: ...     # todas, con su empresa
    async def get(self, user_id: UUID, enterprise_id: UUID) -> Membership | None: ...
    async def add(self, membership: Membership) -> None: ...

class SessionRepository(Protocol):
    async def add(self, session: Session, token_hash: bytes) -> None: ...
    async def get_by_token_hash(self, token_hash: bytes) -> Session | None: ...
    async def revoke(self, session_id: UUID, reason: str, at: datetime) -> None: ...

class PasswordHasher(Protocol):
    def verify(self, password: str, password_hash: str) -> bool: ...
    def verify_dummy(self, password: str) -> None: ...                        # igual costo, sin usuario
    def hash(self, password: str) -> str: ...                                 # usado en login-03

@dataclass(frozen=True)
class SsoIdentity:
    email: Email; full_name: str | None; subject: str

class SsoTicketValidator(Protocol):
    async def validate(self, ticket: str, enterprise: Enterprise) -> SsoIdentity: ...
    # InvalidSsoTicket | SsoProviderUnavailable (application/errors.py)

class SessionTokenGenerator(Protocol):
    def new(self) -> tuple[str, bytes]: ...         # (token para la cookie, hash a guardar)
    def hash(self, token: str) -> bytes: ...

class Clock(Protocol):
    def now(self) -> datetime: ...                   # UTC

class IdGenerator(Protocol):
    def new(self) -> UUID: ...

class UnitOfWork(Protocol):
    async def __aenter__(self) -> "UnitOfWork": ...
    async def __aexit__(self, *exc: object) -> None: ...   # rollback si hubo excepción
    async def commit(self) -> None: ...
```

**Comandos, resultados y casos de uso (`application/`)**

```python
@dataclass(frozen=True)
class ClientInfo: ip: str | None; user_agent: str | None

@dataclass(frozen=True)
class PasswordLoginCommand: email: str; password: str; client: ClientInfo

@dataclass(frozen=True)
class SsoLoginCommand: enterprise_code: str; ticket: str; client: ClientInfo

@dataclass(frozen=True)
class SessionContext:
    session: Session; user: User
    active_enterprise: Enterprise; default_enterprise: Enterprise
    available_enterprises: list[Enterprise]; can_switch_enterprise: bool

@dataclass(frozen=True)
class LoginResult:
    token: str                       # solo para Set-Cookie; nunca se registra en logs
    context: SessionContext
    provisioning: SsoDecision | None = None

class SessionOpener:
    def __init__(self, memberships: MembershipRepository, users: UserRepository,
                 sessions: SessionRepository, tokens: SessionTokenGenerator,
                 clock: Clock, ids: IdGenerator, session_ttl: timedelta): ...
    async def open(self, user: User, method: AuthMethod, origin: Enterprise | None) -> LoginResult: ...

class LoginWithPassword:
    def __init__(self, uow: UnitOfWork, users: UserRepository,
                 hasher: PasswordHasher, opener: SessionOpener): ...
    async def execute(self, cmd: PasswordLoginCommand) -> LoginResult: ...
    # InvalidCredentials | UserSuspended | NoActiveMembership

class LoginWithSso:
    def __init__(self, uow: UnitOfWork, enterprises: EnterpriseRepository, users: UserRepository,
                 memberships: MembershipRepository, validator: SsoTicketValidator,
                 opener: SessionOpener, clock: Clock, ids: IdGenerator): ...
    async def execute(self, cmd: SsoLoginCommand) -> LoginResult: ...
    # SsoNotAvailable | InvalidSsoTicket | SsoProviderUnavailable | UserSuspended | MembershipInactive

class GetCurrentSession:
    def __init__(self, uow: UnitOfWork, sessions: SessionRepository, users: UserRepository,
                 memberships: MembershipRepository, tokens: SessionTokenGenerator, clock: Clock): ...
    async def execute(self, token: str | None) -> SessionContext: ...
    # SessionRevoked (revoca y persiste el motivo antes de lanzar)

class Logout:
    def __init__(self, uow: UnitOfWork, sessions: SessionRepository,
                 tokens: SessionTokenGenerator, clock: Clock): ...
    async def execute(self, token: str | None) -> None: ...   # idempotente

# application/errors.py
class InvalidCredentials(Exception): ...
class SsoNotAvailable(Exception): ...
class InvalidSsoTicket(Exception): ...
class SsoProviderUnavailable(Exception): ...
class SessionRevoked(Exception): reason: str
```

**Estado de las interfaces**

| Interfaz | Estado |
|---|---|
| Entidades, `policies.py`, errores de dominio | Lista para pruebas tras la aprobación. `Membership.is_current` y `resolve_active_enterprise` dependen de las preguntas P1 y P2. |
| `LoginWithPassword`, `LoginWithSso`, `GetCurrentSession`, `Logout`, `SessionOpener` | Lista para pruebas con dobles en memoria. |
| `SsoTicketValidator` | La firma está lista. `SsoIdentity` puede crecer según el protocolo (P4). |
| `PasswordLinkNotifier` | **Pendiente** (login-03, P3). |
| `PermissionRepository` / rol en el contexto | **Pendiente** (modelo de permisos, D6). |
| `AuditLog` | **Pendiente** (D9). |
| `SessionRepository.revoke_for_membership / revoke_for_enterprise / revoke_for_user` | **Pendiente** (lo usará el módulo de administración para LOG-16). |

### 3.3 Decisiones que debe aprobar el responsable

| # | Decisión | Recomendación | Efecto si cambia |
|---|---|---|---|
| D1 | Stack (sección 1.1) y uso de uv | Como se propone | Cambia `pyproject`, CI y herramientas. |
| D2 | SQLAlchemy **async** frente a sync | Async | Con sync, los puertos y casos de uso pasan a ser `def` y Codex no necesita `pytest-asyncio`. Conviene decidirlo antes de que Codex escriba pruebas. |
| D3 | Área `app/identity/login/` | `identity` | Solo cambian las rutas de `app/` y `tests/`. |
| D4 | Sesión opaca en servidor y cookie HttpOnly, frente a Bearer o JWT | Opaca con cookie | Con Bearer, la sesión viaja en el cuerpo y en la cabecera `Authorization`. Con JWT, LOG-14 y LOG-16 no se cumplen de inmediato. Con cookie hay que definir el dominio del frontend, CORS con credenciales y la protección CSRF (SameSite=Lax y cabecera `X-Requested-With` en métodos que modifican). |
| D5 | Vigencia de sesión: 8 h absolutas, sin renovación deslizante | 8 h | Solo cambia la configuración. |
| D6 | `usuario_multitenant` **derivado** (≥ 2 vigentes) en lugar de almacenado | Derivado en esta entrega | Si debe almacenarse en una tabla de permisos, se agrega `PermissionRepository` y la sincronización al crear o revocar membresías (LOG-09, CA-03, CA-05). |
| D7 | Revelar `USER_SUSPENDED` solo tras una contraseña correcta, o un ticket válido en SSO | Sí | Si no se revela, CA-07 pasa a responder `401 INVALID_CREDENTIALS` y el usuario no sabe que debe contactar al administrador (LOG-11). |
| D8 | Errores problem+json con `code` estable | Sí | Define el contrato de errores de todos los módulos. |
| D9 | Diferir auditoría y rate limiting a otra entrega | Diferir, con prioridad alta | Si se requieren ya, se agregan el puerto `AuditLog` y un middleware, y la respuesta 429. |
| D10 | Alcance: incluir `login`, `sso/login`, `session` y `logout`; diferir el cambio de empresa, la predeterminada y las contraseñas | Como en la sección 2.6 | Incluir el cambio de empresa exige definir antes los permisos de la empresa destino. |
| D11 | Estrategia de tenant (LOG-01): esquema por empresa o columna `enterprise_id` | Decidir antes de Conciliación bancaria | No afecta a las tablas de Login, que son globales. |

### 3.4 Preguntas para la PMO

| # | Pregunta | Reglas | Efecto en el diseño o contrato |
|---|---|---|---|
| P1 | ¿Una membresía es "vigente" solo si además su empresa está activa? | LOG-05, LOG-15, LOG-16 | Cambia `Membership.is_current` y, con ello, `available_enterprises`, `can_switch_enterprise` y CA-06. |
| P2 | ¿LOG-05 se aplica en el momento del evento (revocación o desactivación), al ingresar, o en ambos? | LOG-05, CA-06 | Esta propuesta lo aplica al ingresar. Si debe aplicarse en el evento, el módulo de administración también llama a la política. ¿Se aplica también en el ingreso por SSO? Propongo que sí, sin cambiar la empresa activa, que sigue siendo la de origen. |
| P3 | ¿El alta por SSO envía automáticamente el enlace para configurar la primera contraseña, o lo envía el administrador a demanda? | LOG-08, LOG-12 | Si es automático, `LoginWithSso` necesita `PasswordLinkNotifier` (o un outbox) en la primera entrega. |
| P4 | ¿Qué protocolo usa el proveedor SSO (CAS, OIDC, SAML) y qué valida "ticket válido para NEXUS"? ¿El ticket identifica la empresa o la envía el frontend? | LOG-06, LOG-07 | Define el adaptador, `SsoIdentity` y si `enterprise_code` se mantiene en la entrada. |
| P5 | ¿El perfil "básico" de una membresía nueva es un rol concreto? ¿Cuál es su nombre? | LOG-07, CA-02, CA-03 | Valor por defecto de `users_enterprises.role` y semilla del modelo de permisos. |
| P6 | ¿Puede el frontend mostrar el mensaje "usuario suspendido" o "membresía suspendida"? | LOG-15, CA-05, CA-07 | Relacionado con D7: cambia los códigos 403 por 401 genéricos. |
| P7 | ¿El correo se compara sin distinguir mayúsculas? | Modelo funcional, LOG-07 | Si se distinguen, se cambia `citext` por `text` y la normalización de `Email`. |
| P8 | ¿Qué nombre se usa para un usuario nuevo por SSO si el proveedor no lo entrega? | LOG-07 | Si es obligatorio, se rechaza el alta o se pide completarlo después. |
| P9 | Pendientes ya listados en el borrador: invalidación del enlace anterior al reenviar y vigencia de la contraseña actual durante el restablecimiento | LOG-12, LOG-13 | Bloquean login-03, no esta entrega. |

### 3.5 Cambios propuestos fuera del alcance autorizado

No se tocan en esta tarea; se piden para la implementación:

- `.gitignore` con `.env`, `.venv/`, `__pycache__/` y `.DS_Store`. Hoy hay archivos `.DS_Store` versionados; propongo eliminarlos del índice.
- `README.md` con los pasos para levantar Postgres, migrar, ejecutar y probar.
- Observación sobre documentación: `codex.md` (raíz) indica como ruta propuesta `docs/ai/codex.md`, pero existe `docs/agents/codex.md`. Conviene que el responsable fije una sola ubicación.
- Renombrar o enlazar `docs/modules/login/01-reglas-de-negocio.md` como la versión de referencia de `NEXUS_Login_Agentes_v0.1.md`.

### 3.6 Archivos de la futura implementación y verificaciones

**Archivos**

- Raíz: `pyproject.toml`, `uv.lock`, `alembic.ini`, `docker-compose.yml`, `.env.example`, `.gitignore`, `README.md`.
- `alembic/env.py`, `alembic/versions/0001_login_base.py`.
- `app/main.py`, `app/bootstrap.py`, `app/core/{config,db,errors,clock}.py`.
- `app/identity/login/{api,application,domain,infrastructure}/…` según el árbol de la sección 1.2.
- `tests/identity/login/fakes.py` (dobles en memoria compartidos con Codex) y `tests/conftest.py`. Las pruebas unitarias son de Codex; Claude solo agrega pruebas de integración si se autorizan.
- `scripts/seed_dev.py` (Saga, Mega, Lumen, Ana, Bruno con datos ficticios).

**Verificaciones**

| Verificación | Comando | Qué demuestra |
|---|---|---|
| Lint y formato | `uv run ruff check . && uv run ruff format --check .` | Estilo uniforme. |
| Tipos y pureza | `uv run mypy app` + regla de importación (por ejemplo, `import-linter`: `domain` no importa `fastapi`, `sqlalchemy` ni `httpx`) | Las capas respetan `CLAUDE.md`. |
| Unitarias | `uv run pytest tests/identity/login/domain tests/identity/login/application` | CA-01…CA-07 y cada fila de LOG-07 con dobles. |
| Migración | `docker compose up -d db && uv run alembic upgrade head && uv run alembic downgrade base` | Migración 0001 reversible. |
| Smoke HTTP | `uv run pytest tests/identity/login/api` con `TestClient` y un `SsoTicketValidator` falso (si se autoriza la integración) | Contrato: códigos, problem+json, `Set-Cookie`, `401` tras revocar (CA-05). |
| Arranque | `uv run uvicorn app.main:create_app --factory` + `GET /docs` | El OpenAPI generado coincide con este contrato. |

---

## Registro de entrega (login-01, propuesta)

- **Archivo creado:** `docs/iterations/login-01/claude.md` (único autorizado).
- **Acordado frente a entregado:** propuesta de infraestructura, contrato, trazabilidad, interfaces, decisiones y preguntas. Sin código.
- **Verificaciones:** revisión manual de la cobertura de LOG-01…16 y CA-01…08 (sección 3.1) y `git status` limpio salvo este archivo.
- **Traspaso a Codex:** revisar las secciones 2 y 3.2 contra las reglas. Las pruebas pueden prepararse cuando se resuelvan D2 (async o sync) y P1/P2 (vigencia y LOG-05).
