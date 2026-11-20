# Notas para Notion (área de espera)

Esta carpeta guarda, como Markdown, las páginas que la instrucción `docs/agents/claude-login-implementacion.md` (sección 7) pide publicar en Notion dentro de **NEXUS ERP**. Existe porque la sesión de Claude Code aún no tiene un conector de Notion.

## Reglas

- **Un archivo por versión:** `<tarea>-vN.md`. El título dentro del archivo es el de la página: `NEXUS ERP · Login · <tarea> · vN`.
- **Nunca se edita una versión anterior.** Cada cambio de contenido crea `vN+1`, que indica qué versión reemplaza y qué cambió.
- **Fuente de verdad:** el `docs/iterations/<tarea>/claude.md` de cada tarea. Si una nota y el `claude.md` no coinciden, manda el repositorio y se crea una versión nueva de la nota.
- Solo datos ficticios (Saga, Mega, Ana). Sin secretos, tokens ni contenido de `.env`.

## Publicación en Notion

Cuando haya conector, o si el responsable las sube a mano:

1. Crear cada página dentro de NEXUS ERP con el título del archivo, en orden de versión.
2. Comprobar que quedó dentro de NEXUS ERP.
3. Marcar la nota como publicada en el índice de abajo. Solo se cambia este README; las notas no se tocan.

## Índice

| Tarea | Versión | Estado de la versión | Fecha | Publicada en Notion |
|---|---|---|---|---|
| `login-02-base` | [v1](login-02-base-v1.md) | Propuesta para revisión (aprobada después) | 2026-11-20 | No |
| `login-02-base` | [v2](login-02-base-v2.md) | Implementado, pendiente de revisión | 2026-11-20 | No |
| `login-04-migracion` | [v1](login-04-migracion-v1.md) | Aprobada | 2026-11-20 | No |
| `login-04-migracion` | [v2](login-04-migracion-v2.md) | Implementado, pendiente de revisión | 2026-11-20 | No |

`login-01` fue anterior a esta instrucción y no tiene nota de Notion. La reemplaza en parte el ER v2 (ver `login-02-base` v1, sección 2).
