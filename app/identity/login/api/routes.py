"""Rutas HTTP de Login (login-05): inicio de sesión y sesión actual."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Response

from app.identity.login.api.dependencies import (
    CurrentSession,
    get_describe_session_use_case,
    get_login_use_case,
)
from app.identity.login.api.schemas import LoginRequest, LoginResponse, SessionResponse
from app.identity.login.application.authenticate import DescribeSession
from app.identity.login.application.login import LoginCommand, LoginWithPassword

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

_PROBLEM: dict[str, Any] = {"content": {"application/problem+json": {}}}


def _no_store(response: Response) -> None:
    # La respuesta contiene datos de sesión (y en el login, el token): no se guarda en caché.
    response.headers["Cache-Control"] = "no-store"


@router.post(
    "/login",
    responses={
        401: {"description": "invalid_credentials", **_PROBLEM},
        403: {"description": "account_inactive | no_enterprise_access", **_PROBLEM},
    },
)
async def login(
    body: LoginRequest,
    response: Response,
    use_case: Annotated[LoginWithPassword, Depends(get_login_use_case)],
) -> LoginResponse:
    result = await use_case.execute(LoginCommand(body.email, body.password, body.device_type))
    _no_store(response)
    return LoginResponse.from_result(result)


@router.get(
    "/session",
    responses={401: {"description": "not_authenticated | invalid_token", **_PROBLEM}},
)
async def current(
    auth: CurrentSession,
    response: Response,
    use_case: Annotated[DescribeSession, Depends(get_describe_session_use_case)],
) -> SessionResponse:
    view = await use_case.execute(auth)
    _no_store(response)
    return SessionResponse.from_view(view)
