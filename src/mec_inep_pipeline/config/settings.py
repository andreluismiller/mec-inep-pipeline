"""Configurações tipadas, carregadas a partir de variáveis de ambiente / .env.

Este módulo é a ÚNICA porta de entrada para credenciais e segredos no projeto.
Nada de senha, token ou string de conexão deve ser lido diretamente de
os.environ em outros módulos — sempre importe `get_settings()` daqui.

Uso:
    from mec_inep_pipeline.config.settings import get_settings

    settings = get_settings()
    settings.postgres_dsn()
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

# Raiz do repositório (dois níveis acima deste arquivo: src/mec_inep_pipeline/config/ -> raiz)
REPO_ROOT = Path(__file__).resolve().parents[3]
CONFIG_DIR = REPO_ROOT / "config"


class Settings(BaseSettings):
    """Variáveis de ambiente esperadas pela aplicação (ver .env.example)."""

    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ---- Ambiente ----
    app_env: str = Field(default="dev", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # ---- Postgres ----
    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_db: str = Field(default="mec_inep", alias="POSTGRES_DB")
    postgres_user: str = Field(default="mec_inep_user", alias="POSTGRES_USER")
    postgres_password: SecretStr = Field(default=SecretStr(""), alias="POSTGRES_PASSWORD")
    postgres_raw_schema: str = Field(default="raw", alias="POSTGRES_RAW_SCHEMA")

    # ---- APIs MEC/INEP ----
    inep_api_base_url: str = Field(default="https://api.inep.gov.br", alias="INEP_API_BASE_URL")
    inep_api_token: SecretStr = Field(default=SecretStr(""), alias="INEP_API_TOKEN")
    mec_api_base_url: str = Field(default="https://api.mec.gov.br", alias="MEC_API_BASE_URL")
    mec_api_token: SecretStr = Field(default=SecretStr(""), alias="MEC_API_TOKEN")

    # ---- dlt ----
    dlt_pipeline_name: str = Field(default="mec_inep_pipeline", alias="DLT_PIPELINE_NAME")
    dlt_data_dir: str = Field(default=".dlt_data", alias="DLT_DATA_DIR")

    # ---- SQLMesh ----
    sqlmesh_gateway: str = Field(default="postgres", alias="SQLMESH_GATEWAY")

    def postgres_dsn(self, *, hide_password: bool = False) -> str:
        """Monta a DSN de conexão com o Postgres.

        Args:
            hide_password: se True, mascara a senha (útil para logs).
        """
        password = "***" if hide_password else self.postgres_password.get_secret_value()
        return (
            f"postgresql://{self.postgres_user}:{password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    """Retorna uma instância cacheada de Settings (lida o .env uma única vez)."""
    return Settings()
