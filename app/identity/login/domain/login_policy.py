"""Políticas puras del inicio de sesión (LOG-03, LOG-05, LOG-09, LOG-15, LOG-16)."""

from collections.abc import Sequence
from dataclasses import dataclass

from app.identity.login.domain.entities import Membership, User
from app.identity.login.domain.errors import AccountInactive, NoEnterpriseAccess
from app.identity.login.domain.status import Status

MULTITENANT_THRESHOLD = 2


@dataclass(frozen=True, slots=True)
class LoginChoice:
    membership: Membership
    available: tuple[Membership, ...]
    # True cuando la predeterminada no existía o perdió acceso y hay que guardar esta (LOG-05).
    new_default: bool


def ensure_user_active(user: User) -> None:
    """LOG-15: un usuario inactivo no entra por ninguna vía."""
    if user.status is not Status.ACTIVE:
        raise AccountInactive()


def available_memberships(memberships: Sequence[Membership]) -> tuple[Membership, ...]:
    """Disponibles, de la más antigua a la más reciente."""
    eligible = (m for m in memberships if m.is_available)
    return tuple(sorted(eligible, key=lambda m: (m.joined_at, m.membership_id)))


def choose_login_enterprise(
    memberships: Sequence[Membership], default_membership_id: int | None
) -> LoginChoice:
    """Empresa de ingreso convencional.

    - LOG-03: la única disponible o, si hay varias, la predeterminada.
    - LOG-05: si la predeterminada no está disponible, la membresía vigente más antigua, que
      pasa a ser la nueva predeterminada. Sin disponibles, se deniega el ingreso.
    """
    available = available_memberships(memberships)
    if not available:
        raise NoEnterpriseAccess()
    for membership in available:
        if membership.membership_id == default_membership_id:
            return LoginChoice(membership, available, new_default=False)
    return LoginChoice(available[0], available, new_default=True)


def is_multitenant(available: Sequence[Membership]) -> bool:
    """LOG-09: derivado, nunca se guarda."""
    return len(available) >= MULTITENANT_THRESHOLD


def can_keep_session(user: User, membership: Membership) -> bool:
    """LOG-15, LOG-16: la sesión solo sigue válida con usuario, membresía y empresa activos."""
    return user.status is Status.ACTIVE and membership.is_available
