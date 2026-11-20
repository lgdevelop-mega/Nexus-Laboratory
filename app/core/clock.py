"""Reloj del sistema en UTC (login-02-base §4.6).

Cumple por tipado estructural el puerto ``Clock`` que define cada módulo en su capa
``application``. La vigencia de sesiones se compara en MySQL con ``UTC_TIMESTAMP(3)``;
este reloj sirve para escribir marcas de tiempo.
"""

from datetime import UTC, datetime


class SystemClock:
    def now(self) -> datetime:
        """Fecha actual consciente de zona (UTC), truncada a ms para coincidir con DATETIME(3)."""
        current = datetime.now(UTC)
        return current.replace(microsecond=current.microsecond // 1000 * 1000)
