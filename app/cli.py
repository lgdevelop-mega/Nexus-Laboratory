"""Comandos de línea de NEXUS. Como ``app/main.py``, es un punto de entrada que arma la app.

Uso:

    uv run python -m app.cli seed-login seeds/login/usuarios-prueba.json [--dry-run]

Salida: el reporte en JSON por stdout. Errores por stderr. Códigos de salida:
0 éxito · 2 archivo inválido · 3 ambiente no permitido · 1 error inesperado.
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

from pydantic import ValidationError

from app.bootstrap import build_seed_use_case
from app.core.config import load_settings
from app.core.db import create_engine, create_sessionmaker, verify_server
from app.identity.login.cli.seed import load_seed_file, report_to_json

# El seeder escribe contraseñas de prueba: nunca en ambientes compartidos (L-05).
SEED_ALLOWED_ENVS = frozenset({"local", "test"})

EXIT_INVALID_FILE = 2
EXIT_FORBIDDEN_ENV = 3


def _describe_invalid_file(exc: Exception) -> str:
    # Sin los valores de entrada: el archivo contiene contraseñas.
    if isinstance(exc, ValidationError):
        return "\n".join(
            f"- {'.'.join(str(part) for part in error['loc']) or 'archivo'}: {error['msg']}"
            for error in exc.errors(include_input=False, include_url=False)
        )
    return f"- {exc}"


async def _seed_login(path: Path, dry_run: bool) -> int:
    # Se revisa antes de cargar la configuración, que en producción tiene sus propias reglas.
    app_env = os.environ.get("NEXUS_APP_ENV", "local")
    if app_env not in SEED_ALLOWED_ENVS:
        print(f"El seeder no se ejecuta en el ambiente {app_env!r}.", file=sys.stderr)
        return EXIT_FORBIDDEN_ENV

    try:
        plan = load_seed_file(path)
    except (OSError, ValidationError, ValueError) as exc:
        detail = _describe_invalid_file(exc)
        print(f"Archivo de datos inválido ({path}):\n{detail}", file=sys.stderr)
        return EXIT_INVALID_FILE

    settings = load_settings()
    engine = create_engine(settings)
    try:
        await verify_server(engine)
        async with create_sessionmaker(engine)() as session:
            report = await build_seed_use_case(session).execute(plan, dry_run=dry_run)
    finally:
        await engine.dispose()

    print(report_to_json(report))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    commands = parser.add_subparsers(dest="command", required=True)
    seed = commands.add_parser("seed-login", help="Carga empresas, usuarios y membresías.")
    seed.add_argument("file", type=Path, help="Archivo JSON con el formato de SeedFile.")
    seed.add_argument("--dry-run", action="store_true", help="Valida y reporta sin escribir.")
    args = parser.parse_args(argv)

    if args.command == "seed-login":
        return asyncio.run(_seed_login(args.file, args.dry_run))
    return 1


if __name__ == "__main__":
    sys.exit(main())
