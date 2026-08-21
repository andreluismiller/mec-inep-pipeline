"""Fixtures compartilhadas entre os testes.

Principais responsabilidades:
  - Garantir que Settings/loaders tenham variáveis de ambiente mínimas mesmo
    sem um .env real presente (comum em CI).
  - Limpar os caches (`lru_cache`) de `get_settings()` e `load_yaml()` entre
    testes, já que um teste pode alterar env vars (via `monkeypatch.setenv`)
    e não queremos que esse estado vaze para o próximo teste.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"

_REQUIRED_ENV_DEFAULTS = {
    "APP_ENV": "test",
    "LOG_LEVEL": "WARNING",
    "POSTGRES_HOST": "localhost",
    "POSTGRES_PORT": "5432",
    "POSTGRES_DB": "mec_inep_test",
    "POSTGRES_USER": "test_user",
    "POSTGRES_PASSWORD": "test_password",
    "POSTGRES_RAW_SCHEMA": "raw",
    "INEP_API_BASE_URL": "https://api.inep.gov.br",
    "MEC_API_BASE_URL": "https://api.mec.gov.br",
}


@pytest.fixture(autouse=True)
def _clean_environment_and_caches() -> Iterator[None]:
    """Roda antes/depois de CADA teste: isola env vars e limpa caches de config."""
    from mec_inep_pipeline.config import loader, settings

    original_env = os.environ.copy()
    for key, value in _REQUIRED_ENV_DEFAULTS.items():
        os.environ.setdefault(key, value)

    settings.get_settings.cache_clear()
    loader.load_yaml.cache_clear()

    yield

    os.environ.clear()
    os.environ.update(original_env)
    settings.get_settings.cache_clear()
    loader.load_yaml.cache_clear()


@pytest.fixture
def fixtures_dir() -> Path:
    """Diretório com arquivos de exemplo usados pelos testes (CSV/XLSX pequenos)."""
    return FIXTURES_DIR
