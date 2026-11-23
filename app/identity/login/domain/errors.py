"""Errores de dominio de Login. El mensaje se muestra al usuario final (``app/core/errors.py``)."""


class LoginDomainError(Exception):
    """Base de los errores de Login."""


class InvalidEmail(LoginDomainError):
    """El correo no tiene la forma mínima esperada."""


class InvalidCredentials(LoginDomainError):
    """Correo inexistente, contraseña incorrecta o usuario sin contraseña (mismo error)."""

    def __init__(self) -> None:
        super().__init__("Correo o contraseña incorrectos.")


class AccountInactive(LoginDomainError):
    """El usuario está inactivo (LOG-15, CA-07). Solo tras verificar la contraseña."""

    def __init__(self) -> None:
        super().__init__("La cuenta está inactiva. Solicita la reactivación al administrador.")


class NoEnterpriseAccess(LoginDomainError):
    """El usuario no tiene ninguna empresa disponible (LOG-05)."""

    def __init__(self) -> None:
        super().__init__("No tienes acceso a ninguna empresa activa.")


class NotAuthenticated(LoginDomainError):
    """La petición no trae un token Bearer."""

    def __init__(self) -> None:
        super().__init__("Se requiere autenticación.")


class InvalidToken(LoginDomainError):
    """Token desconocido, sesión revocada o vencida, o se perdió el acceso (LOG-15, LOG-16)."""

    def __init__(self) -> None:
        super().__init__("La sesión no es válida o ha expirado. Inicia sesión de nuevo.")
