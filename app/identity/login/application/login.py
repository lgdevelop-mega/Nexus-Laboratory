"""Caso de uso: inicio de sesión convencional con correo y contraseña (CU-02).

Reglas: LOG-03 (empresa de ingreso), LOG-05 (predeterminada perdida), LOG-15 (usuario
inactivo). Es una secuencia lineal en una sola transacción: caso de uso directo.
"""

from dataclasses import dataclass

from app.identity.login.application.ports import PasswordHasher, UnitOfWorkFactory
from app.identity.login.application.session_opener import SessionOpener
from app.identity.login.application.views import LoginResult, SessionView
from app.identity.login.domain.email import Email
from app.identity.login.domain.errors import InvalidCredentials, InvalidEmail
from app.identity.login.domain.login_policy import choose_login_enterprise, ensure_user_active
from app.identity.login.domain.status import DeviceType


@dataclass(frozen=True, slots=True)
class LoginCommand:
    email: str
    password: str
    device_type: DeviceType = DeviceType.UNKNOWN


class LoginWithPassword:
    def __init__(
        self, uow_factory: UnitOfWorkFactory, hasher: PasswordHasher, opener: SessionOpener
    ) -> None:
        self._uow_factory = uow_factory
        self._hasher = hasher
        self._opener = opener

    async def execute(self, command: LoginCommand) -> LoginResult:
        try:
            email: Email | None = Email.parse(command.email)
        except InvalidEmail:
            email = None  # Se responde igual que un correo inexistente.

        async with self._uow_factory() as uow:
            user = await uow.users.get_by_email(email) if email else None
            # Siempre se verifica, también sin usuario, para no revelar qué correos existen.
            password_ok = await self._hasher.verify(
                user.password_hash if user else None, command.password
            )
            if user is None or not password_ok:
                raise InvalidCredentials()

            # A partir de aquí la contraseña es correcta: los errores pueden ser específicos (L-07).
            ensure_user_active(user)
            memberships = await uow.memberships.list_for_user(user.id)
            default_id = await uow.preferences.get_default(user.id)
            choice = choose_login_enterprise(memberships, default_id)
            if choice.new_default:
                await uow.preferences.set_default(user.id, choice.membership.membership_id)
                default_id = choice.membership.membership_id

            opened = await self._opener.open(uow, user, choice.membership, command.device_type)
            await uow.commit()

        return LoginResult(
            access_token=opened.access_token,
            session=SessionView(
                session_id=opened.session_id,
                expires_at=opened.expires_at,
                user=user,
                active=choice.membership,
                enterprises=choice.available,
                default_membership_id=default_id,
            ),
        )
