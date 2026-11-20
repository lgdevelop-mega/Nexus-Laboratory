"""Formato de errores ``application/problem+json`` (RFC 9457) con ``code`` estable.

Los módulos no acoplan su dominio a HTTP: sus errores son excepciones de Python puro y
cada módulo declara en ``api/error_map.py`` cómo se traducen, registrándolas con
``register_error_mapping``. El mensaje de la excepción se expone como ``detail``, así que
debe estar redactado para el usuario final.
"""

import logging
from collections.abc import Mapping
from dataclasses import dataclass
from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

PROBLEM_JSON = "application/problem+json"

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ErrorSpec:
    status: int
    code: str
    title: str


_HTTP_ERRORS: dict[int, ErrorSpec] = {
    400: ErrorSpec(400, "bad_request", "Solicitud mal formada"),
    404: ErrorSpec(404, "not_found", "No encontrado"),
    405: ErrorSpec(405, "method_not_allowed", "Método no permitido"),
    503: ErrorSpec(503, "service_unavailable", "Servicio no disponible"),
}
_VALIDATION_ERROR = ErrorSpec(422, "validation_error", "Solicitud inválida")
_INTERNAL_ERROR = ErrorSpec(500, "internal_error", "Error interno")


class ServiceUnavailable(Exception):
    """Una dependencia necesaria (por ejemplo, la base de datos) no responde."""


def problem_response(
    spec: ErrorSpec,
    detail: str | None = None,
    *,
    errors: list[dict[str, Any]] | None = None,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    body: dict[str, Any] = {
        "type": "about:blank",
        "title": spec.title,
        "status": spec.status,
        "code": spec.code,
    }
    if detail:
        body["detail"] = detail
    if errors is not None:
        body["errors"] = errors
    return JSONResponse(
        body, status_code=spec.status, media_type=PROBLEM_JSON, headers=dict(headers or {})
    )


def _spec_for_status(status: int) -> ErrorSpec:
    if status in _HTTP_ERRORS:
        return _HTTP_ERRORS[status]
    phrase = HTTPStatus(status).phrase
    return ErrorSpec(status, phrase.lower().replace(" ", "_").replace("-", "_"), phrase)


async def _handle_validation(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)  # noqa: S101 - contrato de Starlette
    raw = exc.errors()
    if any(error.get("type") == "json_invalid" for error in raw):
        return problem_response(_HTTP_ERRORS[400], "El cuerpo de la solicitud no es JSON válido.")
    # No se repiten los valores enviados (``input``) para no reflejar datos sensibles.
    errors = [
        {"loc": list(error.get("loc", ())), "msg": error.get("msg", ""), "type": error.get("type")}
        for error in raw
    ]
    return problem_response(
        _VALIDATION_ERROR, "La solicitud contiene campos inválidos.", errors=errors
    )


async def _handle_http(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, StarletteHTTPException)  # noqa: S101 - contrato de Starlette
    spec = _spec_for_status(exc.status_code)
    detail = exc.detail if isinstance(exc.detail, str) else None
    if exc.status_code == 404 and detail == "Not Found":
        detail = "La ruta solicitada no existe."
    elif exc.status_code == 405 and detail == "Method Not Allowed":
        detail = "El método no está permitido en esta ruta."
    return problem_response(spec, detail, headers=exc.headers)


async def _handle_service_unavailable(request: Request, exc: Exception) -> JSONResponse:
    return problem_response(_HTTP_ERRORS[503], str(exc) or None)


async def _handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Error no controlado en %s %s", request.method, request.url.path)
    return problem_response(_INTERNAL_ERROR, "Ocurrió un error inesperado.")


def install_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(RequestValidationError, _handle_validation)
    app.add_exception_handler(StarletteHTTPException, _handle_http)
    app.add_exception_handler(ServiceUnavailable, _handle_service_unavailable)
    app.add_exception_handler(Exception, _handle_unexpected)


def register_error_mapping(app: FastAPI, mapping: Mapping[type[Exception], ErrorSpec]) -> None:
    """Traduce excepciones de un módulo a problem+json según su ``ErrorSpec``."""
    for exc_type, spec in mapping.items():
        app.add_exception_handler(exc_type, _mapped_handler(spec))


def _mapped_handler(spec: ErrorSpec) -> Any:
    async def handler(request: Request, exc: Exception) -> JSONResponse:
        return problem_response(spec, str(exc) or None)

    return handler
