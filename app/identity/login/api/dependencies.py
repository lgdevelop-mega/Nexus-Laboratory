"""Dependencias HTTP de Login.

Las funciones ``get_*_use_case`` son puntos de inyección: la API no conoce los adaptadores
(regla de import-linter), así que ``app/bootstrap.py`` las sustituye con
``app.dependency_overrides``. Si no se sustituyen, fallan de forma explícita.

``current_session`` protege cualquier endpoint de cualquier módulo:

    @router.get("/algo")
    async def algo(auth: CurrentSession) -> ...:
        auth.user, auth.membership  # usuario y empresa activa de la sesión
"""

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.identity.login.application.authenticate import AuthenticateToken, DescribeSession
from app.identity.login.application.login import LoginWithPassword
from app.identity.login.application.views import AuthenticatedSession
from app.identity.login.domain.errors import NotAuthenticated

_NOT_WIRED = "Dependencia de Login sin conectar: revisa app.bootstrap.install_login"


def get_login_use_case() -> LoginWithPassword:
    raise NotImplementedError(_NOT_WIRED)


def get_authenticate_use_case() -> AuthenticateToken:
    raise NotImplementedError(_NOT_WIRED)


def get_describe_session_use_case() -> DescribeSession:
    raise NotImplementedError(_NOT_WIRED)


# auto_error=False: la ausencia de token se responde con el formato problem+json del proyecto.
_bearer = HTTPBearer(auto_error=False, description="Token devuelto por POST /api/v1/auth/login")


async def current_session(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    authenticate: Annotated[AuthenticateToken, Depends(get_authenticate_use_case)],
) -> AuthenticatedSession:
    if credentials is None or not credentials.credentials:
        raise NotAuthenticated()
    return await authenticate.execute(credentials.credentials)


CurrentSession = Annotated[AuthenticatedSession, Depends(current_session)]
