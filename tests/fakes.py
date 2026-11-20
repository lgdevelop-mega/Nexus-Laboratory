"""Dobles compartidos por todas las partes. Los de cada puerto de Login irán en
``tests/identity/login/fakes.py``."""

from datetime import datetime, timedelta


class FixedClock:
    """Reloj controlable que cumple el puerto ``Clock``. Solo acepta fechas con zona."""

    def __init__(self, at: datetime) -> None:
        if at.tzinfo is None:
            raise ValueError("FixedClock requiere una fecha consciente de zona (UTC)")
        self._now = at

    def now(self) -> datetime:
        return self._now

    def advance(self, delta: timedelta) -> None:
        self._now += delta
