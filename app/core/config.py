"""Configuración por ambiente (login-02-base §4.4).

Las variables llevan el prefijo ``NEXUS_``. El archivo ``.env`` solo se carga en ``local``;
en el resto de ambientes la configuración viene del entorno del proceso.
"""

import os
from functools import lru_cache
from typing import Literal, Self

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

AppEnv = Literal["local", "test", "staging", "production"]
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR"]

DATABASE_URL_SCHEME = "mysql+asyncmy://"  # D-02: acceso async con asyncmy.


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="NEXUS_", extra="ignore")

    app_env: AppEnv = "local"
    log_level: LogLevel = "INFO"

    database_url: SecretStr
    db_pool_size: int = Field(default=5, ge=1)
    db_pool_recycle_seconds: int = Field(default=1500, ge=1)
    db_echo: bool = False

    cors_origins: list[str] = Field(default_factory=list)
    # Bearer es el transporte vigente; solo cambia si D-04 se resuelve por cookie.
    cors_allow_credentials: bool = False

    docs_enabled: bool = True

    # L-03 (login-05, D-03): vigencia absoluta del token de sesión.
    session_ttl_hours: int = Field(default=12, ge=1, le=168)

    @field_validator("database_url")
    @classmethod
    def _require_asyncmy(cls, value: SecretStr) -> SecretStr:
        if not value.get_secret_value().startswith(DATABASE_URL_SCHEME):
            raise ValueError(f"NEXUS_DATABASE_URL debe empezar por {DATABASE_URL_SCHEME}")
        return value

    @model_validator(mode="after")
    def _check_environment(self) -> Self:
        if self.cors_allow_credentials and "*" in self.cors_origins:
            raise ValueError("cors_allow_credentials no admite el origen '*'")
        if self.app_env == "production":
            problems = []
            if self.db_echo:
                problems.append("db_echo debe ser false")
            if self.docs_enabled:
                problems.append("docs_enabled debe ser false")
            if "*" in self.cors_origins:
                problems.append("cors_origins no admite '*'")
            if problems:
                raise ValueError("Configuración no válida en production: " + "; ".join(problems))
        return self


def load_settings() -> Settings:
    """Construye la configuración leyendo ``.env`` solo en el ambiente local."""
    if os.environ.get("NEXUS_APP_ENV", "local") == "local":
        return Settings(_env_file=".env")
    return Settings()


@lru_cache
def get_settings() -> Settings:
    return load_settings()
