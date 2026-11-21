"""Fixtures comunes.

``client`` no ejecuta el ``lifespan`` de la app, así que no se conecta a MySQL. La URL de
prueba apunta a un puerto cerrado para que ninguna prueba unitaria use una base real por
accidente. Para probar errores 500 usa ``TestClient(app, raise_server_exceptions=False)``.
"""

from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.core.config import Settings
from app.main import create_app


@pytest.fixture
def settings_test() -> Settings:
    return Settings(
        _env_file=None,
        app_env="test",
        database_url=SecretStr("mysql+asyncmy://nexus:nexus@127.0.0.1:1/nexus_test"),
    )


@pytest.fixture
def app(settings_test: Settings) -> FastAPI:
    return create_app(settings_test)


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    yield TestClient(app)
