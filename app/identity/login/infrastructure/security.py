"""Adaptadores de seguridad: contraseñas con argon2id (L-02) y token Bearer opaco."""

import asyncio
import hashlib
import secrets

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

TOKEN_BYTES = 32  # 256 bits


class Argon2PasswordHasher:
    """Cumple ``PasswordHasher``. argon2 consume CPU: se ejecuta fuera del event loop."""

    def __init__(self, hasher: PasswordHasher | None = None) -> None:
        # Parámetros por defecto de argon2-cffi: argon2id.
        self._hasher = hasher or PasswordHasher()
        # Hash de una contraseña aleatoria: se verifica contra él cuando no hay usuario.
        self._dummy_hash = self._hasher.hash(secrets.token_urlsafe(16))

    async def hash(self, password: str) -> str:
        return await asyncio.to_thread(self._hasher.hash, password)

    async def verify(self, password_hash: str | None, password: str) -> bool:
        target = password_hash if password_hash is not None else self._dummy_hash
        try:
            await asyncio.to_thread(self._hasher.verify, target, password)
        except (VerifyMismatchError, VerificationError, InvalidHashError):
            return False
        return password_hash is not None


class Sha256TokenService:
    """Cumple ``TokenService``. El token en claro nunca se guarda ni se registra."""

    def new_token(self) -> str:
        return secrets.token_urlsafe(TOKEN_BYTES)

    def hash_token(self, token: str) -> bytes:
        return hashlib.sha256(token.encode("utf-8")).digest()
