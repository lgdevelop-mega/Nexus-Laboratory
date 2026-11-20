# NEXUS ERP · API

Backend modular de NEXUS ERP con Python 3.12, FastAPI, SQLAlchemy 2 (async con `asyncmy`), MySQL 8.4 y Alembic.

Antes de contribuir lee `AGENTS.md`, `CLAUDE.md` y las guías de `docs/agents/`. Las propuestas y entregas de cada tarea están en `docs/iterations/<tarea>/`.

## Requisitos

- [uv](https://docs.astral.sh/uv/). Descarga Python 3.12 automáticamente según `.python-version`.
- Docker, para MySQL local. También sirve un MySQL ≥ 8.0.16 propio con `sql_mode` que incluya `STRICT_TRANS_TABLES`.

## Puesta en marcha local

```bash
uv sync                                  # dependencias de ejecución y desarrollo
cp .env.example .env                     # edita las claves; .env nunca se sube
docker compose up -d db                  # MySQL 8.4 en 127.0.0.1:${NEXUS_DB_PORT:-3306}
uv run alembic upgrade head              # migraciones
uv run uvicorn app.main:create_app --factory --reload
```

- Salud: `GET http://127.0.0.1:8000/api/v1/health` y `GET /api/v1/health/ready` (comprueba la base).
- Documentación OpenAPI: `http://127.0.0.1:8000/docs`. Está deshabilitada en `production`.

`.env` solo se lee con `NEXUS_APP_ENV=local`. En los demás ambientes las variables `NEXUS_*` vienen del entorno del proceso. Las claves disponibles están en `.env.example`.

## Verificaciones

```bash
uv run ruff check . && uv run ruff format --check .   # lint y formato
uv run mypy app                                       # tipos
uv run lint-imports                                   # regla de importación entre capas
uv run pytest                                         # pruebas
uv run alembic upgrade head && uv run alembic downgrade base && uv run alembic upgrade head
```

## Estructura

```text
app/
├── main.py            # create_app(): fábrica de la app
├── bootstrap.py       # punto de composición: puertos → adaptadores
├── core/              # configuración, base de datos, errores problem+json, reloj UTC, logging, salud
└── identity/login/    # módulo de Login: api/ application/ domain/ infrastructure/
alembic/               # migraciones (identificadores explícitos: --rev-id 0001)
tests/                 # espejo de app/
```

La API depende de la aplicación, y la aplicación del dominio. Los adaptadores de `infrastructure/` implementan los puertos de `application/` y solo `app/bootstrap.py` los conecta. `uv run lint-imports` verifica esta regla.
