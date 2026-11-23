"""Punto de composición (CLAUDE.md, login-02-base §4.7).

Es el único módulo que conecta implementaciones concretas con los puertos de cada caso
de uso.

- **HTTP:** la API declara puntos de inyección (``app/identity/login/api/dependencies.py``)
  y ``install_login`` los sustituye aquí con ``app.dependency_overrides``. La API no puede
  importar este módulo (import-linter), porque este módulo importa los adaptadores. Las
  pruebas pueden volver a sustituir los puntos de inyección con dobles.
- **CLI:** ``build_seed_use_case`` arma el seeder sobre una sesión de base de datos.
"""

from datetime import timedelta
from typing import Annotated

from fastapi import Depends, FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import SystemClock
from app.core.config import Settings, get_settings
from app.core.db import get_db_session
from app.identity.login.api import dependencies as login_api
from app.identity.login.api.error_map import install_login_errors
from app.identity.login.api.routes import router as login_router
from app.identity.login.application.authenticate import AuthenticateToken, DescribeSession
from app.identity.login.application.login import LoginWithPassword
from app.identity.login.application.ports import UnitOfWork, UnitOfWorkFactory
from app.identity.login.application.seed import SeedLoginData
from app.identity.login.application.session_opener import SessionOpener
from app.identity.login.infrastructure.ids import Uuid7Generator
from app.identity.login.infrastructure.persistence.unit_of_work import SqlUnitOfWork
from app.identity.login.infrastructure.security import Argon2PasswordHasher, Sha256TokenService

__all__ = [
    "build_seed_use_case",
    "get_clock",
    "get_db_session",
    "get_settings",
    "install_login",
]

_clock = SystemClock()
_tokens = Sha256TokenService()
_ids = Uuid7Generator()
_hasher: Argon2PasswordHasher | None = None


def get_clock() -> SystemClock:
    return _clock


def get_password_hasher() -> Argon2PasswordHasher:
    # Se crea al primer uso: calcula un hash de referencia para igualar tiempos.
    global _hasher
    if _hasher is None:
        _hasher = Argon2PasswordHasher()
    return _hasher


def _uow_factory(session: AsyncSession) -> UnitOfWorkFactory:
    def factory() -> UnitOfWork:
        return SqlUnitOfWork(session)

    return factory


DbSession = Annotated[AsyncSession, Depends(get_db_session)]
AppSettings = Annotated[Settings, Depends(get_settings)]


# --- Login (login-05) ----------------------------------------------------------------


def provide_login(session: DbSession, settings: AppSettings) -> LoginWithPassword:
    opener = SessionOpener(
        tokens=_tokens,
        ids=_ids,
        clock=_clock,
        session_ttl=timedelta(hours=settings.session_ttl_hours),
    )
    return LoginWithPassword(_uow_factory(session), get_password_hasher(), opener)


def provide_authenticate(session: DbSession) -> AuthenticateToken:
    return AuthenticateToken(_uow_factory(session), _tokens)


def provide_describe_session(session: DbSession) -> DescribeSession:
    return DescribeSession(_uow_factory(session))


def install_login(app: FastAPI) -> None:
    app.dependency_overrides[login_api.get_login_use_case] = provide_login
    app.dependency_overrides[login_api.get_authenticate_use_case] = provide_authenticate
    app.dependency_overrides[login_api.get_describe_session_use_case] = provide_describe_session
    install_login_errors(app)
    app.include_router(login_router)


def build_seed_use_case(session: AsyncSession) -> SeedLoginData:
    return SeedLoginData(_uow_factory(session), get_password_hasher())
