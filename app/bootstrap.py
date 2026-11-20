"""Punto de composición (CLAUDE.md, login-02-base §4.7).

Es el único módulo que conecta implementaciones concretas con los puertos de cada caso
de uso. Las rutas reciben sus dependencias con ``Depends(<función de este módulo>)`` y
las pruebas las sustituyen con ``app.dependency_overrides``.

A partir de login-04/login-05 se agregan aquí las funciones ``get_<caso_de_uso>()``
que arman repositorios MySQL, hasher y generadores sobre la sesión de la petición.
"""

from app.core.clock import SystemClock
from app.core.config import get_settings
from app.core.db import get_db_session

__all__ = ["get_clock", "get_db_session", "get_settings"]

_clock = SystemClock()


def get_clock() -> SystemClock:
    return _clock
