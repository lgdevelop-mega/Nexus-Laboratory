"""Traducción de los errores de dominio de Login a ``application/problem+json``."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.errors import ErrorSpec, problem_response, register_error_mapping
from app.identity.login.domain.errors import (
    AccountInactive,
    InvalidCredentials,
    InvalidToken,
    NoEnterpriseAccess,
    NotAuthenticated,
)

LOGIN_ERRORS: dict[type[Exception], ErrorSpec] = {
    InvalidCredentials: ErrorSpec(401, "invalid_credentials", "Credenciales inválidas"),
    AccountInactive: ErrorSpec(403, "account_inactive", "Cuenta inactiva"),
    NoEnterpriseAccess: ErrorSpec(403, "no_enterprise_access", "Sin empresas disponibles"),
}

# RFC 6750: los 401 de un recurso protegido anuncian el esquema Bearer.
BEARER_ERRORS: dict[type[Exception], ErrorSpec] = {
    NotAuthenticated: ErrorSpec(401, "not_authenticated", "No autenticado"),
    InvalidToken: ErrorSpec(401, "invalid_token", "Sesión inválida"),
}


def install_login_errors(app: FastAPI) -> None:
    register_error_mapping(app, LOGIN_ERRORS)
    for exc_type, spec in BEARER_ERRORS.items():
        app.add_exception_handler(exc_type, _bearer_handler(spec))


def _bearer_handler(spec: ErrorSpec):  # type: ignore[no-untyped-def]
    async def handler(request: Request, exc: Exception) -> JSONResponse:
        return problem_response(spec, str(exc) or None, headers={"WWW-Authenticate": "Bearer"})

    return handler
