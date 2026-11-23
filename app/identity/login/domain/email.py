"""Correo electrónico normalizado (LOG-07: el correo identifica al usuario entre vías)."""

import re
from dataclasses import dataclass

from app.identity.login.domain.errors import InvalidEmail

MAX_EMAIL_LENGTH = 255  # M-4

# Forma mínima: algo@algo.algo, sin espacios. La verificación real del buzón no es del dominio.
_EMAIL_SHAPE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass(frozen=True, slots=True)
class Email:
    value: str

    @classmethod
    def parse(cls, raw: str) -> "Email":
        """Quita espacios y pasa a minúsculas, igual que ``ck_users_email_normalized``."""
        normalized = raw.strip().lower()
        if len(normalized) > MAX_EMAIL_LENGTH or not _EMAIL_SHAPE.match(normalized):
            raise InvalidEmail("El correo no tiene un formato válido.")
        return cls(normalized)

    def __str__(self) -> str:
        return self.value
