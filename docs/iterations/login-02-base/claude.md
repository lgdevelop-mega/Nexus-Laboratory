# login-02-base · Base del backend (parte 1 del módulo de Login)

**Autor:** Claude Code · **Fecha:** 2026-11-20 · **Estado:** implementado, pendiente de revisión de Codex y del responsable.
**Instrucción aplicada:** `docs/agents/claude-login-implementacion.md` (sección 5, parte 1; ciclo de la sección 6).
**Rama:** `worktree/claude_worktree` · Sin commits, por instrucción del responsable. Ver "Registro de entrega" al final.

**Aprobaciones del responsable (2026-11-20):** C-01 (reemplazo por el ER v2), C-02 (alcance y archivos de las secciones 3 y 4) y D-02 (acceso async con `asyncmy`). La aprobación de C-02 cubre la tabla de dependencias de la sección 4.1 (D-01 para esta parte) y las opciones propuestas en C-03 a C-08, que se implementaron tal como estaban descritas.

---

## 0. Comprobación del entorno (ciclo, paso 1)

| Comprobación | Resultado |
|---|---|
| Worktree y rama | Worktree propio, rama `worktree/claude_worktree`. No es el checkout principal ni `develop`. |
| `git status` antes de editar | Un archivo sin seguimiento ajeno: `docs/agents/claude-login-implementacion.md`. Lo conservo sin cambios. |
| Último commit | `1fb12f1 iteration-login-01` (propuesta `login-01`). |
| Iteraciones existentes | `docs/iterations/login-01/`. Esta tarea toma el siguiente identificador: `login-02-base`. |
| Archivos `.DS_Store` versionados | `.DS_Store` y `docs/.DS_Store` (ver sección 4.9). |

### 0.1 Lectura obligatoria (sección 1 de la instrucción)

| # | Fuente | Estado |
|---|---|---|
| 1–4 | `AGENTS.md`, `CLAUDE.md`, `codex.md`, `docs/agents/codex.md`, `docs/modules/login/01-reglas-de-negocio.md` | Leídas. |
| 5 | Notion: "Sugerencias de Claude · Modelo de datos de Login (ER) · v2" | **No leída.** Esta sesión no tiene un conector de Notion. |
| 6 | Notion: "Modelo de datos de Login · Diagrama ER" (CU-01…CU-11, presencia) | **No leída.** El motivo es el mismo. |
| 7 | `docs/iterations/login-01/claude.md` | Leída (es mi propuesta anterior). |
| 8 | `claude.md` y `codex.md` de esta tarea | No existían antes de este archivo. |

**Efecto:** esta parte no necesita el detalle del ER v2. Las convenciones que sí usa son MySQL, `DATETIME(3)` en UTC, `BINARY(16)` UUIDv7 y la colación `utf8mb4_bin` para el correo, y vienen escritas en la propia instrucción (secciones 3.3 y 8). Las partes `login-03-dominio` y `login-04-migracion` sí lo necesitan. Pido una de estas dos opciones (pregunta Q-01):
- (a) habilitar un conector de Notion en la sesión, o
- (b) exportar ambas páginas al repositorio, por ejemplo como `docs/modules/login/02-modelo-er-v2.md`.

---

## 1. Registro del reemplazo de `login-01` por el ER v2 (instrucción, sección 3.3)

La instrucción pide registrar este reemplazo antes de escribir código y que lo confirmes. **Necesito tu confirmación (C-01).**

| Tema | `login-01` (propuesta anterior) | Vigente (ER v2 aprobado el 2026-11-20) | Efecto en `login-02-base` |
|---|---|---|---|
| Motor de base de datos | PostgreSQL 16 + asyncpg | Una sola base MySQL; el driver depende de D-02 | Conexión, `docker-compose`, Alembic y URL de conexión para MySQL. |
| Transporte del token | Cookie HttpOnly | `Authorization: Bearer`; la cookie sigue abierta (D-04) | CORS sin credenciales por defecto (sección 4.4). |
| Esquema | 4 tablas; `default_enterprise_id` en `users` | 7 tablas del ER v2; `user_preferences.default_membership_id` | Ninguno: las tablas son de `login-04-migracion`. |
| Tipos de ID | `uuid` | `BIGINT` en catálogo; `BINARY(16)` UUIDv7 en sesiones y conexiones | Ninguno en esta parte. |
| Correo | `citext` | Normalizado en el dominio, guardado con colación `utf8mb4_bin` | Conexión con `charset=utf8mb4` (sección 4.3). |
| Contraseñas | Diferidas a login-03 | Fuera del alcance: LOG-12, LOG-13 y CA-08 retirados | No se agrega `argon2-cffi` aquí; se agrega en `login-05-login-token`. |
| Códigos de error | `INVALID_CREDENTIALS` (mayúsculas) | La instrucción usa `invalid_credentials` | El formato común usa `code` en `snake_case` (sección 4.5). |
| Numeración de tareas | `login-02` = cambio de empresa, `login-03` = contraseñas | Tabla de partes de la instrucción (sección 5) | La sección 2.6 de `login-01` queda obsoleta. |
| Vigencia de sesión | 8 h | Propuesta de 12 h absolutas (D-03, abierta) | Ninguno en esta parte. |

Lo que de `login-01` **sigue vigente**:
- La estructura en capas.
- `SessionOpener`.
- El formato problem+json.
- `usuario_multitenant` derivado.
- El token opaco de 256 bits del que solo se guarda el hash.

---

## 2. Objetivo y alcance

**Objetivo.** Dejar un esqueleto ejecutable sobre el que las partes 2 a 9 agreguen código sin rehacer la base. Lo forman la fábrica de la app, la configuración por ambiente, la conexión MySQL, el formato de errores, el reloj UTC, Alembic sin migraciones, el punto de composición, las reglas de calidad y la regla de importación entre capas.

**Fuera del alcance de esta parte:**
- Entidades, puertos y políticas (`login-03-dominio`).
- Tablas, modelos y repositorios (`login-04-migracion`).
- Endpoints de autenticación, hash de contraseñas y token (`login-05` en adelante).
- Cualquier dato de Login.
- Las pruebas unitarias: las escribe Codex. Aquí solo propongo sus escenarios (sección 6).

**Reglas de negocio:** esta parte no implementa ninguna regla LOG ni caso CA. Prepara las condiciones técnicas que las reglas exigen después:
- Fechas UTC para la vigencia (LOG-16).
- Errores con `code` estable (todas las reglas que rechazan).
- Pureza del dominio (CLAUDE.md).

---

## 3. Rutas a crear o modificar

Todas son nuevas, salvo que se indique otra cosa. Ninguna se toca hasta que se apruebe.

```text
.
├── .gitignore                     # nuevo
├── .python-version                # 3.12
├── .env.example                   # claves NEXUS_* sin valores secretos
├── README.md                      # nuevo
├── docker-compose.yml             # solo MySQL local [C-04]
├── pyproject.toml                 # dependencias y config de ruff, mypy, pytest, import-linter
├── uv.lock                        # generado por uv
├── alembic.ini
├── alembic/
│   ├── env.py                     # lee Settings; metadata con convención de nombres
│   ├── script.py.mako
│   └── versions/.gitkeep          # vacío; 0001 corresponde a login-04-migracion
├── app/
│   ├── __init__.py
│   ├── main.py                    # create_app(settings=None)
│   ├── bootstrap.py               # punto de composición
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py              # Settings (pydantic-settings)
│   │   ├── db.py                  # engine, sessionmaker, Base con convención de nombres
│   │   ├── errors.py              # problem+json y registro de traducciones
│   │   ├── clock.py               # SystemClock (UTC, precisión de ms)
│   │   ├── logging.py             # configuración de logging
│   │   └── health.py              # GET /api/v1/health y /health/ready [C-05]
│   └── identity/                  # área propuesta [C-03]
│       ├── __init__.py
│       └── login/
│           ├── __init__.py
│           ├── api/__init__.py            # paquetes vacíos: la regla de importación
│           ├── application/__init__.py    # entre capas ya rige desde esta parte
│           ├── domain/__init__.py
│           └── infrastructure/__init__.py
└── tests/
    ├── __init__.py
    ├── conftest.py                # fixtures: settings de prueba, app, cliente HTTP
    ├── core/                      # pruebas de Codex de esta parte (sección 6)
    └── identity/login/            # estructura espejo vacía
```

Cambio en Git que no es un archivo nuevo: quitar `.DS_Store` y `docs/.DS_Store` del índice (`git rm --cached`) **[C-06]**.

---

## 4. Cambios propuestos

### 4.1 Dependencias y herramientas (D-01 abierta)

Todas son nuevas y **requieren aprobación**. Las versiones mínimas se fijan en `pyproject.toml`; las exactas quedan en `uv.lock` al instalar. No fijo números aquí sin antes revisar el índice de paquetes en la instalación aprobada.

| Grupo | Paquete | Para qué |
|---|---|---|
| Ejecución | `fastapi` | Framework HTTP (requisito del proyecto). |
| Ejecución | `uvicorn[standard]` | Servidor ASGI; `standard` incluye soporte de WebSocket (parte 8). |
| Ejecución | `pydantic`, `pydantic-settings` | Esquemas y configuración tipada. |
| Ejecución | `sqlalchemy[asyncio]` (si D-02 = async) o `sqlalchemy` | Acceso a datos. |
| Ejecución | Driver MySQL según D-02: `asyncmy`, `aiomysql` o `PyMySQL` | Conexión. |
| Ejecución | `alembic` | Migraciones. |
| Desarrollo | `pytest`, `pytest-asyncio` (si async), `httpx` | Pruebas; `httpx` lo usa el `TestClient`. |
| Desarrollo | `ruff`, `mypy` | Lint, formato y tipos. |
| Desarrollo | `import-linter` | Regla automática de importación entre capas (instrucción, sección 8). |

Se agregan después, en su parte: `argon2-cffi` (`login-05`), cliente HTTP del SSO (`login-07`, depende de D-08) y la librería de UUIDv7 si la estándar de la versión de Python elegida no la trae (`login-04`).

### 4.2 Acceso a datos y driver (D-02 abierta, afecta a Codex)

| Opción | Driver | A favor | En contra | Efecto en Codex |
|---|---|---|---|---|
| **A. Async** (recomendada) | `asyncmy` (alternativa: `aiomysql`) | La presencia por WebSocket (parte 8) y la validación SSO (parte 6) son I/O concurrente. Async evita mandar cada heartbeat a un pool de hilos. Encaja con FastAPI. | Los drivers async de MySQL tienen menos uso y mantenimiento que PyMySQL; hay que verificar su estado al aprobar. Alembic necesita `run_sync`. | Puertos `async def`; pruebas con `pytest-asyncio` (`asyncio_mode = "auto"`). |
| B. Sync | `PyMySQL` | Driver más estable y simple. Alembic sin adaptaciones. | Los handlers WebSocket async tendrían que llamar a la base mediante `run_in_threadpool`. El SSO bloquea un hilo por petición. | Puertos `def`; pruebas sin asyncio. |

**Recomendación:** opción A con `asyncmy`, revisando antes su mantenimiento. Si no convence, opción A con `aiomysql`. La opción B solo si se prioriza la estabilidad del driver sobre la presencia en tiempo real. **Hay que decidirlo antes de `login-03-dominio`**, porque fija la firma de todos los puertos.

### 4.3 Conexión MySQL (`app/core/db.py`)

- URL desde `NEXUS_DATABASE_URL` (`SecretStr`), por ejemplo `mysql+asyncmy://nexus:***@localhost:3306/nexus?charset=utf8mb4`.
- Al abrir cada conexión se ejecuta `SET time_zone = '+00:00'`. Así `DATETIME(3)` y `UTC_TIMESTAMP(3)` trabajan en UTC (instrucción, sección 8).
- `sql_mode` estricto: se exige `STRICT_TRANS_TABLES` y se verifica al arrancar.
- `pool_pre_ping=True` y `pool_recycle` menor que el `wait_timeout` del servidor (por defecto 1800 s). El tamaño del pool es configurable.
- Al arrancar se comprueba la versión del servidor; se exige MySQL ≥ 8.0.16 porque las restricciones `CHECK` del ER v2 lo requieren. Propongo **MySQL 8.4 LTS** en todos los ambientes (Q-02).
- `Base = DeclarativeBase` con la convención de nombres de restricciones: `pk_%(table_name)s`, `fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s`, `uq_%(table_name)s_%(column_0_N_name)s`, `ix_%(table_name)s_%(column_0_N_name)s`, `ck_%(table_name)s_%(constraint_name)s`. Los nombres deterministas permiten migraciones reversibles en MySQL, que exige el nombre para hacer `DROP` de una FK o un índice. El límite de 64 caracteres se revisa en `login-04`.
- Una sesión de base de datos por petición, entregada por la dependencia `get_db_session`. El commit o rollback queda en el `UnitOfWork` de Login (`login-03`/`login-04`), no en `core`.
- Motor `InnoDB` y charset `utf8mb4` por defecto en las tablas (se aplica en `login-04`).

### 4.4 Configuración por ambiente (`app/core/config.py`)

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="NEXUS_", env_file=None)  # .env solo en local, ver abajo

    app_env: Literal["local", "test", "staging", "production"] = "local"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    database_url: SecretStr
    db_pool_size: int = 5
    db_pool_recycle_seconds: int = 1500
    db_echo: bool = False
    cors_origins: list[str] = []
    cors_allow_credentials: bool = False      # Bearer (vigente); solo cambia si D-04 = cookie
    docs_enabled: bool = True                  # /docs y /openapi.json
```

- **`.env`:** solo se carga cuando `NEXUS_APP_ENV=local`. Nunca se versiona, y yo no lo leo ni lo comparto (instrucción, sección 8). `.env.example` contiene las mismas claves con valores ficticios o vacíos.
- **Validaciones al arrancar:**
  - En `production`: `db_echo=False`, `docs_enabled=False` y `cors_origins` sin `"*"` [C-07].
  - En todos los ambientes: no se permite `cors_allow_credentials=True` junto con `"*"`.
- Las claves de sesión (`session_ttl`, D-03) y de SSO (D-08) **no** se agregan aquí; entran en su parte.
- `get_settings()` está cacheada. Las pruebas la sustituyen con `create_app(settings=...)` o con `app.dependency_overrides`.

### 4.5 Formato de errores (`app/core/errors.py`)

Se usa `application/problem+json` (RFC 9457) con `code` estable en **`snake_case`**, alineado con `invalid_credentials` de la instrucción.

```json
{
  "type": "about:blank",
  "title": "Solicitud inválida",
  "status": 422,
  "code": "validation_error",
  "detail": "La solicitud contiene campos inválidos.",
  "errors": [ { "loc": ["body", "email"], "msg": "value is not a valid email address" } ]
}
```

| `code` | HTTP | Cuándo (en esta parte) |
|---|---|---|
| `validation_error` | 422 | `RequestValidationError` de FastAPI; incluye `errors[]` sin repetir los valores enviados. |
| `bad_request` | 400 | JSON mal formado. |
| `not_found` | 404 | Ruta inexistente. |
| `method_not_allowed` | 405 | Método no soportado. |
| `service_unavailable` | 503 | `/health/ready` sin base de datos. |
| `internal_error` | 500 | Excepción no controlada. Responde sin traza; la traza solo va al log. |

**Cómo agregan errores los módulos sin acoplar el dominio:**
- Los errores de dominio y aplicación son excepciones de Python puro.
- Cada módulo declara en su `api/error_map.py` una tabla `{TipoDeError: (status, code, title)}`.
- `create_app()` registra cada tabla con `register_error_mapping(...)`.
- Así el dominio no importa nada de `core` ni de FastAPI.

Ejemplo de uso futuro (`login-05`): `{InvalidCredentials: (401, "invalid_credentials", "Credenciales inválidas")}`.

### 4.6 Reloj UTC (`app/core/clock.py`)

`SystemClock.now() -> datetime` devuelve la fecha **consciente de zona en UTC** y truncada a milisegundos, para que coincida con `DATETIME(3)` sin diferencias al releer.
- El puerto `Clock` (`Protocol`) se define en `app/identity/login/application/ports.py` (`login-03`). `SystemClock` lo cumple por tipado estructural, sin importarlo.
- La vigencia de sesiones se compara en MySQL con `UTC_TIMESTAMP(3)` (instrucción, sección 8). El reloj de la app solo sirve para escribir marcas de tiempo y para las pruebas.
- Doble para Codex: `FixedClock(at: datetime)`, con método `advance(delta)`, en `tests/fakes.py`.

### 4.7 Punto de entrada y composición

- **`app/main.py`:** `create_app(settings: Settings | None = None) -> FastAPI`.
  - El `lifespan` crea el engine, verifica la versión y el `sql_mode` de MySQL, y libera el engine al cerrar.
  - Registra los manejadores de error, CORS y los routers (`/api/v1/health` en esta parte).
  - Se ejecuta con `uvicorn app.main:create_app --factory`.
- **`app/bootstrap.py`:** es el único lugar que conecta implementaciones concretas.
  - En esta parte expone `get_settings`, `get_db_session` y `get_clock`.
  - A partir de `login-04`/`login-05` agrega las funciones `get_<caso_de_uso>()`, que arman repositorios MySQL, el hasher y los generadores sobre la sesión de la petición.
- **Patrón:** fábrica de la app y raíz de composición. Resuelve dos necesidades concretas:
  - Pruebas: se puede crear una app con otra configuración o con dobles, sin variables globales.
  - Capas: solo `bootstrap.py` importa `infrastructure/`.
  - **No** propongo contenedor de inyección de dependencias, pipeline ni orquestador: `Depends` de FastAPI basta y mantiene legible el recorrido.

### 4.8 Salud del servicio (`app/core/health.py`) [C-05]

| Ruta | Respuesta | Uso |
|---|---|---|
| `GET /api/v1/health` | `200 {"status": "ok"}` sin tocar la base | Liveness. |
| `GET /api/v1/health/ready` | `200 {"status": "ready", "database": "ok"}` o `503 service_unavailable` | Readiness: ejecuta `SELECT 1`. |

No exponen la versión, la configuración ni datos del servidor. Son la verificación de humo de esta parte. Si no las quieres, la verificación pasa a ser solo el arranque y `/docs`.

### 4.9 Calidad, regla de importación y Git

**`pyproject.toml`:**
- `ruff`: reglas `E, F, I, UP, B, S, ASYNC`; longitud 100; formato con `ruff format`.
- `mypy`: `strict = true` en `app.core`, `app.identity.login.domain` y `app.identity.login.application`; `api` e `infrastructure` con chequeo estándar al inicio.
- `pytest`: `testpaths = ["tests"]` y `asyncio_mode = "auto"` si D-02 = async.

**`import-linter`, contratos desde esta parte:**
1. *Capas* `app.identity.login`: `api` → `application` → `domain`, con `infrastructure` a un lado.
2. *Prohibido:* `app.identity.login.domain` no importa `fastapi`, `starlette`, `sqlalchemy`, `pydantic`, `httpx`, `app.core` ni `app.identity.login.{application,api,infrastructure}`.
3. *Prohibido:* `app.identity.login.application` no importa `fastapi`, `sqlalchemy`, `httpx` ni `app.identity.login.{api,infrastructure}`.
4. *Prohibido:* `app.identity.login.api` no importa `app.identity.login.infrastructure`; solo `app.bootstrap` puede hacerlo.

Los contratos ya rigen aunque los paquetes estén vacíos, así que cualquier violación desde `login-03` en adelante hace fallar `lint-imports` en cuanto aparece.

**`.gitignore`:** `.env`, `.env.*` excepto `.env.example`, `.venv/`, `venv/`, `__pycache__/`, `*.pyc`, `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`, `.coverage`, `htmlcov/`, `.DS_Store`, `.idea/` y `.vscode/`. Además, quitar del índice los dos `.DS_Store` versionados [C-06].

**Logging (`app/core/logging.py`):** formato de texto en `local` y JSON en el resto [C-08]. Hay un filtro que elimina la cabecera `Authorization`, por regla: el token nunca va a los logs (instrucción, sección 8). El access log de uvicorn no registra cabeceras.

### 4.10 Alembic

- `alembic/env.py` toma la URL de `Settings` y no la duplica en `alembic.ini`.
- `target_metadata = Base.metadata`; los modelos de cada módulo se importan desde un único lugar (`app/core/db.py:import_models()`), que en esta parte no importa nada.
- Con D-02 = async: `connection.run_sync(do_run_migrations)`.
- `compare_type=True` y `compare_server_default=True` para detectar diferencias en la autogeneración.
- Identificadores de revisión explícitos (`--rev-id 0001`) para que coincidan con el nombre pedido en `login-04` (`0001`).
- `versions/` queda vacío en esta parte. `alembic upgrade head` solo crea `alembic_version` y `downgrade base` la deja sin revisiones.

### 4.11 Entorno local y README [C-04]

- **`docker-compose.yml`:** servicio `db` con MySQL 8.4, base `nexus` y una base `nexus_test` para la integración posterior; `utf8mb4` por defecto; puerto local 3306; volumen con nombre. Las credenciales salen de variables locales, no del archivo.
- **`README.md`:** requisitos, `uv sync`, `docker compose up -d db`, copiar `.env.example` a `.env`, `uv run alembic upgrade head`, arranque con uvicorn, comandos de verificación y enlaces a `AGENTS.md` y `docs/agents/`.

---

## 5. Contrato API de esta parte

Solo existen las rutas de salud (sección 4.8) y el formato de error común (sección 4.5). Los endpoints de Login empiezan en `login-05-login-token`.

```http
GET /api/v1/health/ready HTTP/1.1

HTTP/1.1 503 Service Unavailable
Content-Type: application/problem+json

{"type":"about:blank","title":"Servicio no disponible","status":503,"code":"service_unavailable","detail":"La base de datos no responde."}
```

```http
GET /api/v1/no-existe HTTP/1.1

HTTP/1.1 404 Not Found
Content-Type: application/problem+json

{"type":"about:blank","title":"No encontrado","status":404,"code":"not_found","detail":"La ruta solicitada no existe."}
```

---

## 6. Interfaces internas para Codex

| Interfaz | Ubicación | Uso en pruebas |
|---|---|---|
| `create_app(settings: Settings \| None = None) -> FastAPI` | `app/main.py` | Construir la app con configuración de prueba. |
| `Settings`, `get_settings()` | `app/core/config.py` | Validaciones por ambiente; sustitución con `dependency_overrides`. |
| `register_error_mapping(app: FastAPI, mapping: Mapping[type[Exception], ErrorSpec]) -> None`, `ErrorSpec(status: int, code: str, title: str)`, `problem_response(spec, detail=None, *, errors=None, headers=None)` | `app/core/errors.py` | Verificar la traducción de errores sin módulos reales. Al implementar se agregó el parámetro `app` para no usar un registro global. |
| `SystemClock.now() -> datetime` | `app/core/clock.py` | UTC consciente de zona, truncado a ms. |
| `FixedClock(at)`, `.advance(delta)` | `tests/fakes.py` (lo entrego yo) | Doble del reloj para todas las partes. |
| Fixtures `settings_test`, `app`, `client` | `tests/conftest.py` (lo entrego yo) | `client` con `TestClient`/`httpx` sin base de datos. |

**Escenarios propuestos para las pruebas de Codex (`tests/core/`)**

| # | Escenario | Resultado esperado |
|---|---|---|
| T-01 | `Settings` en `production` con `docs_enabled=True`, `db_echo=True` o `cors_origins=["*"]` | Error de validación al construir. |
| T-02 | `cors_allow_credentials=True` con `cors_origins=["*"]` | Error de validación en cualquier ambiente. |
| T-03 | Cuerpo inválido en una ruta de prueba registrada en el fixture | `422`, `application/problem+json`, `code=validation_error`, `errors[]` sin los valores enviados. |
| T-04 | Ruta inexistente | `404`, `code=not_found`. |
| T-05 | Excepción no controlada en una ruta de prueba | `500`, `code=internal_error`, sin traza en el cuerpo. |
| T-06 | `register_error_mapping({ErrorFicticio: ErrorSpec(409, "conflicto_ficticio", ...)})` | `409`, `code=conflicto_ficticio`. |
| T-07 | `SystemClock.now()` | `tzinfo == UTC` y `microsecond % 1000 == 0`. |
| T-08 | `GET /api/v1/health` | `200 {"status":"ok"}`, sin acceso a la base. |
| T-09 | `/health/ready` con un `get_db_session` sustituido que falla | `503`, `code=service_unavailable`. |
| T-10 | El filtro de logging recibe un registro con `Authorization: Bearer abc` | El registro emitido no contiene `abc`. |

---

## 7. Criterios de aceptación y verificaciones previstas

| # | Criterio | Verificación |
|---|---|---|
| AC-01 | Instalación reproducible | `uv sync --frozen` sin errores. |
| AC-02 | Lint y formato en verde | `uv run ruff check . && uv run ruff format --check .` |
| AC-03 | Tipos en verde | `uv run mypy app` |
| AC-04 | Regla de importación en verde, con los 4 contratos | `uv run lint-imports` |
| AC-05 | Pruebas de Codex en verde | `uv run pytest tests/core` |
| AC-06 | Migración de ida y vuelta sin revisiones | `docker compose up -d db && uv run alembic upgrade head && uv run alembic downgrade base && uv run alembic upgrade head` |
| AC-07 | Arranque con base local | `uv run uvicorn app.main:create_app --factory` → `GET /api/v1/health/ready` = 200; `/docs` disponible en `local`. |
| AC-08 | Arranque rechazado ante MySQL < 8.0.16 o `sql_mode` no estricto | Mensaje claro en el log y la app no arranca (revisión manual). |
| AC-09 | Nada sensible en Git | `git status` y `git ls-files` sin `.env`, `__pycache__`, `.DS_Store` ni `venv/`. |

Registraré los resultados reales, incluidos los fallos, en la sección "Registro de entrega" al implementar.

---

## 8. Decisiones abiertas que afectan esta parte

| ID | Decisión | Efecto en `login-02-base` | Mi recomendación |
|---|---|---|---|
| D-01 | Stack y herramientas | Bloquea toda la parte (sección 4.1). | **Aprobada para esta parte** con C-02. Dos dependencias nuevas quedan pendientes: D-11 y D-12 (Registro de entrega). |
| D-02 | Async o sync y driver MySQL | Bloquea `db.py`, `env.py` de Alembic, `pytest-asyncio` y la firma de los puertos. Avisar a Codex. | **Aprobada: async con `asyncmy`.** `asyncmy` 0.2.18 se publicó el 2026-11-07 y tiene wheels para Python 3.12 en macOS ARM y Linux. Codex: puertos `async def`, `pytest-asyncio` con `asyncio_mode = "auto"`. |
| D-04 | Token en navegador: Bearer o cookie | Solo `cors_allow_credentials`, que por defecto es `False` (Bearer). | No bloquea: se deja configurable. |

## 9. Confirmaciones y preguntas para el responsable

| ID | Pregunta | Efecto |
|---|---|---|
| C-01 | ¿Confirmas el reemplazo de `login-01` por el ER v2 registrado en la sección 1? | Es requisito previo de la instrucción (sección 3.3) para escribir código. |
| C-02 | ¿Apruebas el alcance y los archivos de las secciones 3 y 4? | Sin esta aprobación no edito nada (ciclo, paso 4). |
| C-03 | ¿El área es `identity` (`app/identity/login/`)? | Cambia rutas de `app/`, `tests/` y los contratos de `import-linter`. |
| C-04 | ¿Se incluye `docker-compose.yml` con MySQL 8.4 para el entorno local? | Sin él, el README describe una instalación local de MySQL y AC-06 se ejecuta contra esa base. |
| C-05 | ¿Se incluyen `/api/v1/health` y `/health/ready`? | Sin ellas, AC-07 se reduce al arranque y `/docs`. |
| C-06 | ¿Quito del índice los `.DS_Store` versionados? | Es un cambio en Git fuera de los archivos nuevos. |
| C-07 | ¿`/docs` deshabilitado en `production`? | Validación de `Settings` (T-01). |
| C-08 | ¿Logs JSON fuera de `local`? | Formato de logs y su prueba T-10. |
| Q-01 | ¿Cómo accedo a las páginas de Notion del ER v2 y del diagrama ER (conector o exportación al repositorio)? | Bloquea `login-03-dominio` y `login-04-migracion`. También bloquea el paso 3 del ciclo (ver sección 10). |
| Q-02 | ¿Qué versión de MySQL hay en staging y producción? | Requisito mínimo de 8.0.16 (CHECK) y elección de 8.4 LTS en local. |

## 10. Documentación en Notion (ciclo, paso 3) · pendiente

La instrucción pide publicar esta propuesta como `NEXUS ERP · Login · login-02-base · v1`, con estado "Propuesta para revisión", dentro de NEXUS ERP. **No la publiqué:** esta sesión no tiene un conector de Notion. Este Markdown ya tiene el contenido mínimo de la sección 7 de la instrucción, salvo las verificaciones ejecutadas, porque aún no hay implementación. Puede usarse tal cual para la página. Según la instrucción, la tarea **no se considera entregada** hasta que la página exista y esté dentro de NEXUS ERP.

## 11. Inconsistencias detectadas entre fuentes

| # | Inconsistencia | Fuentes | Decisión necesaria |
|---|---|---|---|
| I-01 | El documento de reglas aún contiene LOG-12, LOG-13 y CA-08, que el responsable retiró. | `docs/modules/login/01-reglas-de-negocio.md` frente a la instrucción, sección 3.2 | Actualizar el documento de reglas (le corresponde a Codex mantener la documentación) o anotar el retiro en él. |
| I-02 | `codex.md` propone `docs/ai/codex.md`, pero la guía está en `docs/agents/codex.md`, igual que la nueva instrucción de Claude. | `codex.md`, `docs/agents/` | Fijar `docs/agents/` como ubicación única. |
| I-03 | La instrucción `docs/agents/claude-login-implementacion.md` no está versionada. | `git status` | Que el responsable la incorpore al repositorio. Es un archivo ajeno: no lo toco. |
| I-04 | `login-01` usaba `code` en mayúsculas; la instrucción usa `invalid_credentials`. | `login-01` §2.1, instrucción §5 parte 4 | Ya resuelto en favor de la instrucción (sección 1). Solo pido que lo confirmes con C-01. |

No encontré contradicciones entre la instrucción y `AGENTS.md` o `CLAUDE.md`. La instrucción agrega pasos (Notion), pero no se opone a ellos.

---

## Registro de entrega (2026-11-20)

### Rama y PR

- Rama: `worktree/claude_worktree`. **Sin commits ni PR**, por instrucción expresa del responsable. Todos los cambios están en el árbol de trabajo.

### Archivos

| Tipo | Archivos |
|---|---|
| Nuevos (raíz) | `pyproject.toml`, `uv.lock`, `.python-version`, `.gitignore`, `.env.example`, `README.md`, `docker-compose.yml`, `alembic.ini` |
| Nuevos (Alembic) | `alembic/env.py`, `alembic/script.py.mako`, `alembic/versions/.gitkeep` |
| Nuevos (`app/`) | `main.py`, `bootstrap.py`, `core/{__init__,config,db,errors,clock,logging,health}.py`, `identity/login/{api,application,domain,infrastructure}/__init__.py` (paquetes vacíos) |
| Nuevos (`tests/`) | `conftest.py`, `fakes.py` (`FixedClock`), `__init__.py` de `tests/`, `tests/core/`, `tests/identity/` y `tests/identity/login/` |
| Índice de Git | `git rm --cached .DS_Store docs/.DS_Store` (C-06). El borrado está preparado en el índice, sin commit. |
| Documentación | Este archivo; `docs/notion/{README,login-02-base-v1,login-02-base-v2}.md`. |
| D-11 | `pyproject.toml` y `uv.lock`: `cryptography` 50.0.2 (con `cffi` y `pycparser`). |

No toqué `docs/agents/claude-login-implementacion.md`, que es ajeno y está sin seguimiento.

### Acordado frente a entregado

| Tema | Acordado | Entregado |
|---|---|---|
| Secciones 3 y 4 | Árbol y cambios propuestos | Implementados según lo propuesto, con las diferencias de esta tabla. |
| `register_error_mapping` | `register_error_mapping(mapping)` | `register_error_mapping(app, mapping)`: recibe la app y evita un registro global (sección 6 actualizada). |
| `docker-compose.yml` | Bases `nexus` y `nexus_test` | Solo `nexus`. Crear `nexus_test` exige un script de inicialización que no estaba en la lista de archivos; queda para la tarea de integración. |
| Config de ruff | Reglas E, F, I, UP, B, S, ASYNC | Igual, más `extend-exclude = ["docs"]`: ruff 0.17 también formatea los bloques de código de los Markdown y reformateaba las firmas ilustrativas de `login-01`. |
| Revisión de humo | Pruebas de Codex (T-01…T-10) | Las pruebas son de Codex y aún no existen. Verifiqué T-01…T-10 con un script temporal fuera del repositorio (ver verificaciones). |
| Notion (ciclo, pasos 3 y 8) | Páginas v1 y v2 en NEXUS ERP | **No publicadas** en Notion: la sesión no tiene conector (Q-01). Por indicación del responsable, quedan como notas en `docs/notion/` (`login-02-base-v1.md` y `login-02-base-v2.md`, con índice en `docs/notion/README.md`), listas para subirse. |

### Verificaciones y resultados reales

Entorno: Python 3.12.14 (gestionado por uv) y las versiones fijadas en `uv.lock`: fastapi 0.165.0, starlette 1.10.0, pydantic 2.14.4, pydantic-settings 2.16.3, sqlalchemy 2.1.9, asyncmy 0.2.18, alembic 1.20.1, uvicorn 0.54.0, pytest 9.2.0, pytest-asyncio 1.5.0, ruff 0.17.6, mypy 2.4.1 e import-linter 2.17.

| # | Verificación | Resultado |
|---|---|---|
| AC-01 | `uv sync` | OK: genera `uv.lock` e instala todo. |
| AC-02 | `uv run ruff check .` y `uv run ruff format --check .` | OK: `All checks passed!` y `27 files already formatted`. El primer intento falló por un import largo en `db.py`, ya corregido. |
| AC-03 | `uv run mypy app` | OK: `Success: no issues found in 16 source files`. |
| AC-04 | `uv run lint-imports` | OK: `4 kept, 0 broken`. Control negativo: agregué temporalmente `import sqlalchemy` en `domain/__init__.py` y el resultado fue `Login: el dominio es Python puro BROKEN`. Lo revertí. |
| AC-05 | `uv run pytest` | `collected 0 items`: aún no hay pruebas de Codex. pytest termina con código 5 (sin pruebas) y un aviso de deprecación (D-12). |
| AC-05 (humo) | Script temporal con T-01…T-10, más 400, 405, URL sin `asyncmy`, MariaDB y `/docs` apagado en producción | **24/24 OK.** |
| AC-06 | `alembic upgrade head` → `downgrade base` → `upgrade head` en MySQL 8.4.13 (contenedor desechable en el puerto 3307) | OK tras resolver el hallazgo H-01. Solo existe `alembic_version`, con 0 revisiones. |
| AC-07 | `uvicorn app.main:create_app --factory` contra la misma base | OK: `/api/v1/health` 200, `/health/ready` 200 `{"status":"ready","database":"ok"}`, `/docs` 200 y una ruta inexistente responde 404 problem+json. |
| AC-07 (UTC) | `SELECT @@SESSION.time_zone` desde el engine de la app | `+00:00`. |
| AC-08 | `check_server` con 8.0.15, `sql_mode` sin `STRICT_TRANS_TABLES` y MariaDB | Los tres se rechazan; 8.4.3 con modo estricto se acepta. Se verificó con el script, no arrancando contra servidores reales. |
| AC-09 | `git status --ignored` | `.env` no existe; `.venv/`, `.DS_Store` y `__pycache__` quedan ignorados. |

El contenedor y el volumen de verificación se eliminaron (`docker compose -p nexus-login02-verify down -v`). El MySQL local en el puerto 3306 no se tocó.

### Hallazgos y decisiones nuevas

| ID | Hallazgo | Efecto | Recomendación |
|---|---|---|---|
| H-01 / D-11 | MySQL 8.4 autentica con `caching_sha2_password`. Sin TLS, la primera autenticación completa de `asyncmy` exige el paquete `cryptography`; sin él falla con `RuntimeError: 'cryptography' package is required…`. Para verificar, precargué la caché de autenticación del servidor con un login del cliente `mysql` dentro del contenedor. | **Resuelto.** D-11 fue aprobado el 2026-11-20 y se agregó `cryptography>=50.0` (bloqueado en 50.0.2). Verificado en un contenedor nuevo **sin precargar la caché**: Alembic sube, baja y vuelve a subir, y la app reconecta tras `docker restart` del servidor con `time_zone +00:00`. | Sigue recomendado conectar por TLS en staging y producción (tarea aparte). |
| D-12 | Starlette 1.10 avisa: `Using httpx with starlette.testclient is deprecated; install httpx2 instead`. `httpx2` lo publica la organización `pydantic` en GitHub (versión 2.16.2). | Solo un aviso en las pruebas; por ahora no falla. | Decidir antes de que Codex escriba muchas pruebas: mantener `httpx` y silenciar el aviso, o cambiar a `httpx2` (dependencia nueva, requiere aprobación). |

### Pendientes y traspaso a Codex

- **Codex:** escribir `tests/core/` con los escenarios T-01…T-10 de la sección 6 usando las fixtures `settings_test`, `app` y `client` y el doble `FixedClock`. Para T-05 usar `TestClient(app, raise_server_exceptions=False)`. Para T-09, sustituir `app.core.db.get_db_session` con una sesión cuyo `execute` lance `SQLAlchemyError`.
- **Responsable:**
  - D-12 (`httpx` o `httpx2`). D-11 ya está aprobado y aplicado.
  - Q-01 (acceso a Notion), necesario para `login-03-dominio` y `login-04-migracion` y para subir las notas de `docs/notion/` a NEXUS ERP.
  - Q-02 (versión de MySQL por ambiente).
  - Incorporar `docs/agents/claude-login-implementacion.md` al repositorio (I-03).
- **Git:** cuando lo autorices, commit en la rama, publicación y solicitud de PR (AGENTS.md, punto 5).
