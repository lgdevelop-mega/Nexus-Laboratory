# Claude Code · Instrucción para construir el módulo de Login

**Destinatario:** Claude Code (yo mismo, en sesiones futuras).
**Fecha:** 2026-11-20 · **Estado:** instrucción vigente para implementar Login.
**Origen:** el responsable aprobó la propuesta "Sugerencias de Claude · Modelo de datos de Login (ER) · v2" (Notion, NEXUS ERP) el 2026-11-20.

Esta instrucción no reemplaza `AGENTS.md` ni `CLAUDE.md`. Las aplica al módulo de Login. Si algo de aquí contradice esos archivos, mandan ellos: detente y reporta la contradicción.

---

## 1. Lectura obligatoria antes de cada sesión de trabajo

Lee en este orden y no empieces a editar sin haberlo hecho:

1. `AGENTS.md`: ciclo de trabajo, worktree y rama, estructura común, entrega.
2. `CLAUDE.md`: capas, dependencias entre capas, patrones, traspaso con Codex.
3. `codex.md` y `docs/agents/codex.md`: lo que Codex espera recibir (interfaces, dobles, casos reproducibles).
4. `docs/modules/login/01-reglas-de-negocio.md`: reglas LOG-01…LOG-16 y casos CA-01…CA-08.
5. La página de Notion "Sugerencias de Claude · Modelo de datos de Login (ER) · v2", con el modelo de datos aprobado.
6. La página de Notion "Modelo de datos de Login · Diagrama ER", con los casos CU-01…CU-11 y el comportamiento de presencia.
7. `docs/iterations/login-01/claude.md`: la propuesta anterior de infraestructura y contrato. Ver la sección 3 para lo que la v2 reemplaza.
8. El `docs/iterations/<tarea>/claude.md` y el `codex.md` de la tarea en curso, si existen.

## 2. Jerarquía de fuentes

Cuando dos fuentes no coinciden, decide con este orden:

1. Decisiones explícitas del responsable en el chat o registradas como aprobadas.
2. Modelo ER v2 aprobado (Notion), para el modelo de datos y el token de sesión.
3. Reglas de negocio del repositorio, salvo las que el responsable retiró (sección 3).
4. Propuesta `login-01`, solo en lo que la v2 no reemplaza y que esté aprobado.
5. El código y las pruebas existentes describen el comportamiento actual, no el esperado.

Si hay una contradicción que esta tabla no resuelve, documéntala con sus fuentes y la decisión que hace falta. Avanza solo con lo que no dependa de ella (AGENTS.md, "Lectura y autoridad").

## 3. Alcance aprobado del módulo

### 3.1 Dentro del alcance

- **Modelo de datos ER v2:**
  - `users`, `enterprises`, `enterprise_sso_config`, `users_enterprises`, `user_preferences`, `auth_sessions`, `presence_connections`.
  - Restricciones e índices tal como aparecen en la tabla "Restricciones e índices" de la v2.
- **Base de datos:** una sola base MySQL. Las tablas de Login son globales, compartidas entre empresas.
- **Token de sesión:**
  - Token opaco de 256 bits. Solo se guarda su SHA-256 en `auth_sessions.token_hash`.
  - En HTTP viaja en `Authorization: Bearer <token>`.
  - En WebSocket viaja en el primer mensaje. Nunca va en la query string.
  - Cada endpoint protegido valida que la sesión y el token sigan vigentes, igual que el usuario, la membresía y la empresa.
- **Login convencional (CU-02):** con la contraseña que el administrador definió en el registro inicial.
- **Login por SSO (CU-03, CU-04, CU-05):** se apoya en la tabla de decisión de LOG-07.
- **Sesión:**
  - Consultar la sesión actual.
  - Logout (LOG-14).
  - Revocar sesiones por pérdida de acceso (LOG-15, LOG-16, CU-11).
- **Preferencia y empresa activa:**
  - Empresa predeterminada (LOG-04, LOG-05).
  - Cambio de empresa con sesión y token nuevos, y `expires_at` heredado (CU-06).
- **Multitenant:** `usuario_multitenant` es derivado y no se guarda (LOG-09).
- **Presencia por WebSocket (CU-07…CU-10):** el heartbeat revalida la sesión y el logout borra las conexiones.

### 3.2 Fuera del alcance (retirado por el responsable)

- Restablecimiento de contraseña por olvido: **LOG-13 y CA-08 retirados**.
- Configuración de contraseña por el usuario, enlace de un solo uso y reenvío: **LOG-12 retirado**. No se crean tablas ni endpoints para enlaces de contraseña. El usuario conserva la contraseña de su registro inicial.
- De LOG-08 solo se mantiene que ambas vías comparten la identidad (el correo). No se implementa la habilitación del acceso convencional por el propio usuario.

### 3.3 Lo que la v2 reemplaza de `login-01`

| Tema | `login-01` | Vigente (v2) |
|---|---|---|
| Motor de base de datos | PostgreSQL 16 + asyncpg | MySQL (driver pendiente, ver D-02) |
| Transporte del token | Cookie HttpOnly | `Authorization: Bearer`. La cookie sigue siendo una decisión abierta (D-04) |
| Esquema | 4 tablas, `default_enterprise_id` en `users` | 7 tablas del ER v2, con `user_preferences.default_membership_id` |
| Tipos de ID | `uuid` en todas | `BIGINT` en entidades de catálogo, `BINARY(16)` UUIDv7 en sesiones y conexiones |
| Correo | `citext` | Normalizado en el dominio y guardado con colación `utf8mb4_bin` |
| Contraseñas | Diferidas a login-03 | Fuera del alcance (sección 3.2) |

Antes de escribir código, registra este reemplazo en el `claude.md` de la primera tarea y pide al responsable que lo confirme.

## 4. Decisiones abiertas: no implementes lo que depende de ellas

| ID | Decisión | Qué bloquea |
|---|---|---|
| D-01 | Stack y herramientas (uv, SQLAlchemy 2.0, Alembic, ruff, mypy, pytest). Cualquier dependencia nueva requiere aprobación. | Toda la parte 1 |
| D-02 | Acceso a datos async o sync y driver MySQL (asyncmy, aiomysql o PyMySQL). Avisar a Codex, porque cambia sus pruebas. | Parte 1 y puertos |
| D-03 | Vigencia del token (propuesta: 12 h absolutas) y expiración por inactividad con `last_used_at`. | Parte 4 |
| D-04 | Transporte del token en el navegador: Bearer en memoria o cookie HttpOnly con CSRF. | Partes 4 y 8 |
| D-05 | Usuarios creados por SSO: solo SSO, o el administrador les asigna contraseña. | Parte 6 |
| D-06 | Acción del administrador ante una contraseña comprometida. | Fuera de Login base; se documenta |
| D-07 | `enterprises.status`: ENUM propio o el `status_id` del catálogo del ERP. Significado de `users.me`. | Parte 2 |
| D-08 | Protocolo SSO (OIDC, CAS, SAML) y el contenido de `enterprise_sso_config`. | Parte 6 (solo el adaptador real; el puerto y el doble se pueden hacer) |
| D-09 | Modelo del rol de administrador (LOG-02, LOG-11). | Parte 9 |
| D-10 | Reacción de las otras pestañas al cambiar de empresa (`session.revoked`, `switched`). | Parte 7 |

Si una parte depende de una decisión abierta, documenta las opciones y los escenarios en su `claude.md` y espera la aprobación (AGENTS.md, punto 4).

## 5. Partes del módulo y orden de construcción

Cada parte es una tarea con su propio identificador. Codex usa ese mismo identificador. Cada parte pasa completa por el ciclo de la sección 6 antes de empezar la siguiente, salvo que el responsable autorice trabajarlas en paralelo.

| # | Tarea | Contenido | Reglas y casos |
|---|---|---|---|
| 1 | `login-02-base` | `pyproject.toml`, configuración (pydantic-settings), conexión MySQL, formato de errores problem+json, reloj UTC, Alembic, `.gitignore`, `.env.example` sin secretos, `README.md`, punto de composición (`app/bootstrap.py`). | — |
| 2 | `login-03-dominio` | Entidades y valores (`Email`, `UserStatus`, `MembershipStatus`, `AuthMethod`, `DeviceType`, `RevokedReason`) y políticas puras: predeterminada (LOG-05), decisión SSO (LOG-07), multitenant (LOG-09), acceso (LOG-15, LOG-16). Puertos en `application/ports.py`. | LOG-03, 05, 07, 09, 15, 16 |
| 3 | `login-04-migracion` | Migración `0001` con las 7 tablas, las FK compuestas, los UK y los índices de la v2. Reversible. Incluye los modelos de persistencia (sin repositorios). Instrucción detallada: `docs/agents/herdr-login-04-migraciones.md`. **Revisión R2 (aprobada 2026-11-23):** 9 tablas, catálogos `statuses`, `device_types` y `revoked_reasons` en lugar de ENUM; sin áreas, países, ciudades, roles ni SSO. Propuesta: `docs/iterations/login-04-migracion/claude-r2.md`; instrucción: `docs/agents/herdr-login-04-r2-migraciones.md`. | ER v3 |
| 4 | `login-05-login-token` | `POST /api/v1/auth/login`, emisión del token, hash argon2id, error genérico `invalid_credentials`, dependencia de autenticación reutilizable para todos los endpoints protegidos. | LOG-03, 05, 15 · CU-02 · CA-01, CA-07 |
| 5 | `login-06-sesion-logout` | `GET /api/v1/auth/session`, `POST /api/v1/auth/logout` con `revoked_reason=logout`. | LOG-14, 16 · CU-10 |
| 6 | `login-07-sso` | `POST /api/v1/auth/sso/login`, puerto `SsoTicketValidator` con un doble, altas concurrentes idempotentes (UK + reintento de lectura). | LOG-06, 07, 08 · CU-03, 04, 05 · CA-02, 03, 04, 05 |
| 7 | `login-08-empresa` | Cambio de predeterminada (LOG-04) y cambio de empresa activa con sesión y token nuevos, la sesión anterior `switched` y `expires_at` heredado. | LOG-04, 05, 09, 10 · CU-06 · CA-06 |
| 8 | `login-09-presencia` | WebSocket: autenticación por el primer mensaje, `presence_connections`, heartbeat que revalida, limpieza, directorio por empresa, `presence.changed`. | CU-07, 08, 09, 10, 11 |
| 9 | `login-10-perdida-acceso` | Revocación en la misma transacción al suspender un usuario, revocar una membresía o desactivar una empresa, y corrección de la predeterminada (LOG-05). Depende de D-09. | LOG-05, 09, 15, 16 · CU-11 · CA-05 |

Cada nueva tarea toma el siguiente número libre bajo `docs/iterations/`.

## 6. Ciclo obligatorio para cada parte

No te saltes ningún paso. Si un paso no aplica, escribe por qué en el `claude.md` de la tarea.

1. **Comprueba el entorno.**
   - Trabaja en tu propio worktree y rama (AGENTS.md, punto 2), no en el checkout principal ni en `develop`.
   - Revisa `git status` y la rama antes de editar.
   - Conserva los cambios ajenos que ya estén presentes.
2. **Propón antes de implementar** (CLAUDE.md, "Antes de implementar"). Escribe `docs/iterations/<tarea>/claude.md` con:
   - Objetivo, rutas a modificar y cambios propuestos.
   - Reglas de negocio que respaldan cada decisión (ID de la regla o del caso).
   - Contrato API con ejemplos de entrada, resultado y errores (código HTTP y `code` estable).
   - Interfaces internas que Codex necesita para sus pruebas: puertos, DTO, errores y dobles en memoria.
   - Patrón elegido (caso de uso directo, pipeline u orquestador) y qué problema resuelve.
   - Criterios de aceptación y verificaciones previstas.
   - Decisiones abiertas de la sección 4 que afectan esta parte.
3. **Documenta la propuesta en Notion** (sección 7) como versión `v1` con estado "Propuesta para revisión".
4. **Espera la aprobación.** Codex revisa la propuesta y el responsable aprueba el alcance. No edites código, pruebas, migraciones ni documentación de producto antes de eso. Si necesitas ampliar el alcance, pide aprobación para lo adicional.
5. **Implementa solo lo aprobado,** respetando las capas (sección 8).
6. **Verifica** con los comandos aprobados en `login-02-base` (lint, formato, tipos, regla de importación entre capas, pruebas, migración de ida y vuelta) y anota los resultados reales, incluidos los fallos.
7. **Actualiza el `claude.md` de la tarea** con:
   - La rama y el PR.
   - Los archivos modificados.
   - Lo acordado frente a lo entregado.
   - Las verificaciones y sus resultados.
   - Los pendientes y el traspaso a Codex.
8. **Publica una nueva versión en Notion** con lo entregado, con estado "Implementado, pendiente de revisión" (sección 7).
9. **Entrega.**
   - Con la tarea aprobada, haz commits locales en tu rama, publícala y abre la solicitud de PR (AGENTS.md, punto 5).
   - El merge lo decide el responsable.
   - Termina los commits con la línea de atribución que indique el sistema.
10. **Atiende los defectos de Codex.**
    - Revisa el caso reproducible y su regla, y corrige dentro del alcance autorizado.
    - Devuelve la referencia del cambio.
    - Publica una nueva versión en Notion con la corrección.

## 7. Documentación versionada en Notion (obligatoria por cada parte)

Cada parte del módulo se documenta en una página de Notion **dentro de NEXUS ERP**, para que el responsable la revise.

**Ubicación**
- La página va dentro del espacio o la página "NEXUS ERP".
- Después de crearla, abre la página y comprueba que quedó dentro de NEXUS ERP.
- Si la herramienta la creó en otro lugar y no puedes moverla, dile al responsable dónde quedó y pídele que la mueva. No la des por entregada hasta confirmarlo.

**Versionado**
- Título: `NEXUS ERP · Login · <tarea> · vN`. Ejemplo: `NEXUS ERP · Login · login-05-login-token · v1`.
- Cada cambio de contenido es una página nueva con `vN+1`. **Nunca edites una versión anterior** ni páginas que no creaste, salvo una instrucción expresa del responsable.
- Cada versión nueva indica qué versión reemplaza y resume los cambios frente a ella.
- Momentos que generan una versión: propuesta (v1), ajustes tras la revisión, entrega implementada y cada corrección por defectos de Codex.

**Contenido mínimo de cada versión**
1. Encabezado:
   - Tarea, versión, fecha y estado: Propuesta para revisión, Aprobada, Implementado pendiente de revisión, Corregido o Cerrada.
   - Rama y PR, si existen.
   - Versión que reemplaza.
2. Cambios respecto a la versión anterior.
3. Objetivo y alcance de la parte, incluido lo que queda fuera.
4. Reglas y casos cubiertos, con trazabilidad regla → componente → prueba.
5. Diseño:
   - Capas y archivos.
   - Patrón y su justificación.
   - Diagrama (Mermaid) cuando aclare el flujo o el modelo.
6. Contrato:
   - Endpoints con entradas, respuestas y errores de ejemplo.
   - Eventos WebSocket, si aplica.
7. Interfaces internas para Codex (puertos, DTO, errores, dobles).
8. Cambios de datos (migraciones, restricciones, índices), si aplica.
9. Verificaciones ejecutadas y sus resultados reales.
10. Decisiones abiertas y riesgos.

**Restricciones**
- Usa solo datos ficticios en los ejemplos (Saga, Mega, Ana).
- No incluyas secretos, tokens reales, contenido de `.env` ni datos personales.
- La página de Notion acompaña al `claude.md` de la tarea; no lo reemplaza. Si no coinciden, el repositorio es la fuente y la página se corrige con una versión nueva.

## 8. Reglas de construcción

**Capas** (CLAUDE.md), en `app/<area>/login/`. El área la aprueba el responsable; la propuesta es `identity`.
- `api/`:
  - Rutas y esquemas Pydantic.
  - Valida la forma de la petición, invoca el caso de uso y traduce el resultado a HTTP.
  - Cualquier lógica excepcional en una ruta va justificada en un comentario.
- `application/`:
  - Casos de uso y puertos (`Protocol`).
  - Coordina los pasos y la transacción.
- `domain/`:
  - Python puro.
  - No importa FastAPI, SQLAlchemy, httpx ni ningún proveedor.
- `infrastructure/`:
  - Adaptadores de los puertos: repositorios MySQL, hasher argon2id, generador y hash de tokens, validador SSO.
- Las implementaciones concretas se conectan solo en el punto de composición (`app/bootstrap.py`).

**Dependencias:** `api → application → domain`. `infrastructure` implementa los puertos de `application`. Verifícalo con una regla de importación automática.

**Patrones:**
- Por defecto, caso de uso directo.
- `SessionOpener` como servicio de aplicación compartido entre el login convencional y el SSO.
- Un pipeline o un orquestador solo si la parte lo justifica, explicando qué problema resuelve.

**Seguridad:**
- Token aleatorio de 256 bits. Solo se guarda su SHA-256 y nunca se registra en logs.
- Contraseñas con argon2id. Correo inexistente, contraseña incorrecta o `password_hash` NULL responden con el mismo `invalid_credentials`.
- Las fechas van en UTC con `DATETIME(3)`. La vigencia se compara con `UTC_TIMESTAMP(3)` de MySQL.
- `device_type` nunca se usa para autorizar.
- Validación de acceso en cada petición, además de la revocación inmediata en la misma transacción.

**Concurrencia:** las altas SSO se apoyan en los UK. El flujo es `INSERT`, capturar la clave duplicada, volver a leer y continuar. `user_preferences` se crea con `INSERT IGNORE`.

**Pruebas:**
- Codex escribe las pruebas unitarias.
- Yo entrego los dobles en memoria de cada puerto en `tests/<area>/login/fakes.py`.
- Agrego pruebas de integración (HTTP, MySQL, SSO) solo si la tarea las autoriza.
- Las pruebas reflejan la estructura de `app/` bajo `tests/`.

**Límites de edición:**
- Implemento `app/` y `alembic/`.
- No edito instrucciones globales, dependencias, configuración compartida ni otros módulos sin aprobación.
- No leo ni comparto archivos `.env`; si hace falta, pido permiso explícito.

**Git:**
- Commits, publicación de la rama y PR solo cuando la tarea está aprobada (AGENTS.md, punto 5).
- Nada de merge.
- No subo `__pycache__`, `.DS_Store` ni `venv/`.

## 9. Definición de terminado de una parte

- [ ] `docs/iterations/<tarea>/claude.md` con la propuesta aprobada y el registro de entrega completo.
- [ ] Implementación limitada al alcance aprobado, con las capas respetadas y la regla de importación en verde.
- [ ] Verificaciones ejecutadas, con sus resultados reales registrados.
- [ ] Interfaces y dobles entregados a Codex. Defectos reportados por Codex resueltos o registrados como pendientes.
- [ ] Página de Notion `NEXUS ERP · Login · <tarea> · vN` dentro de NEXUS ERP, con el estado actualizado y sin editar versiones anteriores.
- [ ] Rama publicada y PR solicitado para revisión. El merge lo decide el responsable.
