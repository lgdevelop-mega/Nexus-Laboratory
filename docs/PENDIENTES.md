# NEXUS ERP · Puntos pendientes

Registro global de lo que queda abierto en el proyecto. Se actualiza al cerrar o abrir un punto; los cerrados pasan a la sección final con su fecha y su referencia (commit, BIT o documento) para no perder la trazabilidad.

**Última actualización:** 2026-11-23 (entrega de `login-05`) · Claude Code.

Estados: **Abierto** (nadie lo atiende), **En curso** (hay una tarea o un agente trabajando), **Bloqueado** (espera una decisión o a otra tarea).

## 1. Login: trabajo en curso

| ID | Pendiente | Estado | Responsable | Referencia |
|---|---|---|---|---|
| P-02 | Registrar en la bitácora de Notion la entrega de R2 (commit `5cccb8c`) y la de `login-05`. La migración R2 ya se aplicó sin errores en un MySQL desechable durante `login-05`. | Abierto | Claude | `docs/iterations/login-04-migracion/claude-r2.md` |
| P-03 | Revisión de Codex de `login-02-base`, `login-04-migracion` (R1 y R2) y `login-05-login-token`. Codex no ha revisado ninguna entrega todavía. | Abierto | Codex | BIT-0001, BIT-0002 |
| P-04 | `login-05-login-token`: seeder y login con token. Implementado y verificado (AC-01 a AC-12); sin commit, pendiente de revisión de Codex y de las pruebas unitarias. | En curso | Codex y responsable | `docs/iterations/login-05-login-token/claude.md` · Notion "NEXUS ERP · Login · login-05-login-token · v1" (falta moverla dentro de NEXUS ERP) |
| P-05 | `0001` R2 ya está lista. Una vez aplicada en una base compartida o duradera, cualquier cambio exige una migración nueva. | Abierto | Responsable | R2-08 |
| P-06 | Pruebas unitarias de `login-05` con los dobles de `tests/identity/login/fakes.py`. | Abierto | Codex | `docs/iterations/login-05-login-token/claude.md` §14.5 |
| P-07 | El docstring de `import_models()` en `app/core/db.py` sigue diciendo "6 tablas" (R1). Solo es un comentario. | Abierto | Claude | `app/core/db.py` |
| P-08 | Límite de intentos de inicio de sesión (fuerza bruta). No está en ninguna tarea. | Abierto | Responsable | `login-05` §13 |

## 2. Decisiones abiertas del módulo de Login

Vienen de `docs/agents/claude-login-implementacion.md`, sección 4. D-01, D-02 y D-07 están resueltas.

| ID | Decisión | Afecta a |
|---|---|---|
| D-03 | Expiración por inactividad con `last_used_at`. La vigencia absoluta quedó en 12 h configurables (L-03). | `login-05`, `login-06` |
| D-04 | Transporte del token en el navegador: Bearer en memoria o cookie HttpOnly con CSRF. Por ahora solo Bearer (L-06). | `login-08` |
| D-05 | Usuarios creados por SSO: solo SSO, o el administrador les asigna contraseña. | `login-07-sso` |
| D-06 | Acción del administrador ante una contraseña comprometida. | Fuera de Login base |
| D-08 | Protocolo SSO (OIDC, CAS, SAML) y contenido de `enterprise_sso_config`. | `login-07-sso` |
| D-09 | Modelo del rol de administrador (LOG-02, LOG-11). | `login-10-perdida-acceso` |
| D-10 | Reacción de las otras pestañas al cambiar de empresa. | `login-08-empresa` |

## 3. Alcance diferido por decisión del responsable

| ID | Pendiente | Cuándo vuelve |
|---|---|---|
| P-10 | Áreas (`users.area_id`): se quitó de las tablas y la migración (R2-01). | Cuando exista el catálogo de áreas. |
| P-11 | Países y ciudades (`enterprises.country_id`, `city_id`) (R2-01). | Cuando exista el catálogo geográfico y su fuente de datos. |
| P-12 | Roles por empresa (`users_enterprises.role_id`) (R2-02). | Con el modelo de roles (D-09). |
| P-13 | SSO completo: `enterprise_sso_config`, `enterprises.sso_enabled`, `auth_sessions.auth_method` (R2-03, M-3). | `login-07-sso`. |
| P-14 | Distinguir suspensión temporal de revocación definitiva de una membresía. Hoy ambas son `inactive` (R2-04). | Si el negocio lo pide: se agrega un valor al catálogo `statuses`. |
| P-15 | `password_hash` obligatorio. Sigue opcional pensando en el SSO (R2-07). | Al definir D-05. |

## 4. Documentación y reglas

| ID | Pendiente | Responsable |
|---|---|---|
| P-20 | `docs/modules/login/01-reglas-de-negocio.md` sigue en v0.1: no marca LOG-12, LOG-13 y CA-08 como retiradas ni usa los estados de R2 (`active` / `inactive`). | Codex (mantiene la documentación) |
| P-21 | `login-03-dominio` debe reflejar R2: "suspendido" y "revocado" pasan a "inactivo" en LOG-05, LOG-15, LOG-16 y CA-05. | Claude |
| P-22 | Las notas de `docs/notion/` (login-02-base v1, login-04-migracion v1 y v2) no se publicaron en Notion (hallazgo H-05). | Claude, con conector de Notion |
| P-23 | Los registros de entrega de `login-02-base` y `login-04-migracion` (R1) dicen "sin commits" aunque ya están en `develop` (H-02). | Claude, cuando el responsable lo indique |

## 5. Proceso y repositorio

| ID | Pendiente | Responsable |
|---|---|---|
| P-30 | El commit `e1563c8` mezcla `login-02-base`, `login-04` y documentos de agentes, con un mensaje poco descriptivo y sin atribución (H-01, H-08). Solo se documenta; no se reescribe la historia. | — |
| P-31 | R1 se fusionó en `develop` antes de la revisión de Codex (H-03). | Responsable |
| P-32 | La rama `worktree/claude_worktree` está atrasada respecto a `develop` (le falta, por ejemplo, `0d22731 fix main.py`). Decidir si se sincroniza antes de seguir. | Responsable |
| P-33 | No hay pruebas automatizadas ni base `nexus_test` (H-07). | Codex y responsable |
| P-34 | Base de pruebas fuera de Docker: se configura con `NEXUS_DATABASE_URL`. Falta crear la base dedicada y su usuario con permisos limitados. | Responsable |
| P-35 | La carpeta `venv/` del repositorio local es antigua y no la maneja `uv`; activarla provoca `ModuleNotFoundError: asyncmy`. Usar `uv run` o `.venv/`. Valorar borrarla. | Responsable |
| P-36 | `users_enterprises.status_changed_at` no tiene `ON UPDATE`: lo debe actualizar el código al cambiar el estado (H-06). | Claude, en la tarea que cambie estados |

## 6. Cerrados

| ID | Pendiente | Cerrado | Referencia |
|---|---|---|---|
| — | D-07: `enterprises.status` con catálogo `statuses` en lugar de ENUM. | 2026-11-23 | R2-04, BIT-0002 |
| P-01 | Rehacer `0001` según R2. | 2026-11-23 | Commit `5cccb8c` |
