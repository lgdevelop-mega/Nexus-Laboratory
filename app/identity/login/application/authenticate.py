"""Casos de uso: validar el token Bearer de cada petición y describir la sesión actual.

``AuthenticateToken`` es la base de la dependencia ``current_session`` que usa cualquier
endpoint protegido. Revalida en cada petición que el usuario, la membresía y la empresa
sigan activos (LOG-15, LOG-16). Revocar la sesión en la base al perder el acceso es de
``login-10-perdida-acceso``.
"""

from app.identity.login.application.ports import TokenService, UnitOfWorkFactory
from app.identity.login.application.views import AuthenticatedSession, SessionView
from app.identity.login.domain.errors import InvalidToken
from app.identity.login.domain.login_policy import available_memberships, can_keep_session


class AuthenticateToken:
    def __init__(self, uow_factory: UnitOfWorkFactory, tokens: TokenService) -> None:
        self._uow_factory = uow_factory
        self._tokens = tokens

    async def execute(self, token: str) -> AuthenticatedSession:
        async with self._uow_factory() as uow:
            active = await uow.sessions.find_active(self._tokens.hash_token(token))
            if active is None or not can_keep_session(active.user, active.membership):
                raise InvalidToken()
            await uow.sessions.touch(active.session_id)
            await uow.commit()
        return AuthenticatedSession(
            session_id=active.session_id,
            expires_at=active.expires_at,
            user=active.user,
            membership=active.membership,
        )


class DescribeSession:
    """Arma la vista de ``GET /api/v1/auth/session`` a partir de una sesión ya validada."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def execute(self, auth: AuthenticatedSession) -> SessionView:
        async with self._uow_factory() as uow:
            memberships = await uow.memberships.list_for_user(auth.user.id)
            default_id = await uow.preferences.get_default(auth.user.id)
        return SessionView(
            session_id=auth.session_id,
            expires_at=auth.expires_at,
            user=auth.user,
            active=auth.membership,
            enterprises=available_memberships(memberships),
            default_membership_id=default_id,
        )
