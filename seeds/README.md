# Datos de prueba (seeders)

Archivos de entrada para `uv run python -m app.cli seed-login <archivo>`.

- Solo datos **ficticios**. Las contraseñas de estos archivos son de prueba (L-05 de `login-05-login-token`).
- El seeder se niega a ejecutarse fuera de `NEXUS_APP_ENV=local` o `test`.
- Es idempotente: lo que ya existe (empresa por `rfc`, usuario por correo, membresía por usuario y empresa) se reporta como `existing` y no se modifica.
- `--dry-run` valida el archivo y muestra qué haría, sin escribir.

El formato está definido por `SeedFile` en `app/identity/login/cli/seed.py`.

| Archivo | Contenido |
|---|---|
| `login/usuarios-prueba.json` | Empresas Saga y Mega. Ana: Saga (predeterminada) y Mega. Bruno: solo Saga. |
