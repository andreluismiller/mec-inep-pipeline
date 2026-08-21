"""Carregamento dos arquivos YAML em config/ (sources, api_mappings, pipelines, logging).

Os YAMLs podem referenciar variáveis de ambiente com a sintaxe ``${NOME_DA_VAR}``
(por exemplo, ``dataset_name: "${POSTGRES_RAW_SCHEMA}"`` em pipelines.yaml).
Essas referências são resolvidas em tempo de carregamento usando os valores
já validados em `mec_inep_pipeline.config.settings.Settings`.
"""

from __future__ import annotations

import os
import re
from functools import lru_cache
from typing import Any

import yaml

from mec_inep_pipeline.config.settings import CONFIG_DIR, get_settings

_ENV_VAR_PATTERN = re.compile(r"\$\{([A-Z0-9_]+)\}")


def _interpolate_env_vars(value: Any) -> Any:
    """Substitui recursivamente ``${VAR}`` pelo valor correspondente no ambiente."""
    if isinstance(value, str):

        def _replace(match: re.Match[str]) -> str:
            var_name = match.group(1)
            return os.environ.get(var_name, match.group(0))

        return _ENV_VAR_PATTERN.sub(_replace, value)
    if isinstance(value, dict):
        return {k: _interpolate_env_vars(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_interpolate_env_vars(v) for v in value]
    return value


def _ensure_env_populated() -> None:
    """Garante que os.environ tenha os valores lidos pelo Settings (para interpolação)."""
    settings = get_settings()
    os.environ.setdefault("POSTGRES_RAW_SCHEMA", settings.postgres_raw_schema)


@lru_cache
def load_yaml(relative_path: str) -> dict[str, Any]:
    """Carrega e faz o parse de um arquivo YAML dentro de config/.

    Args:
        relative_path: caminho relativo a config/, ex.: "sources.yaml".

    Returns:
        Dicionário com o conteúdo do YAML, já com variáveis de ambiente resolvidas.
    """
    _ensure_env_populated()
    path = CONFIG_DIR / relative_path
    if not path.exists():
        raise FileNotFoundError(f"Arquivo de configuração não encontrado: {path}")

    with path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    return _interpolate_env_vars(raw)


def load_sources() -> dict[str, Any]:
    """Atalho para config/sources.yaml -> retorna o dict em `sources`."""
    return load_yaml("sources.yaml").get("sources", {})


def load_pipelines() -> dict[str, Any]:
    """Atalho para config/pipelines.yaml -> retorna o dict em `pipelines`."""
    return load_yaml("pipelines.yaml").get("pipelines", {})


def load_api_mappings() -> dict[str, Any]:
    """Carrega config/api_mappings.yaml por completo (uma chave por tipo de mapeamento)."""
    data = load_yaml("api_mappings.yaml")
    data.pop("version", None)
    return data


def resolve_mapping(mapping_name: str, real_value: str) -> str:
    """Traduz um valor legível (ex.: "São Paulo") no identificador esperado pela API.

    Args:
        mapping_name: chave em config/api_mappings.yaml (ex.: "uf", "etapa_ensino").
        real_value: valor legível a ser traduzido.

    Raises:
        KeyError: se o mapeamento ou o valor não existirem.
    """
    mappings = load_api_mappings()
    if mapping_name not in mappings:
        raise KeyError(f"Mapeamento '{mapping_name}' não existe em config/api_mappings.yaml")
    table = mappings[mapping_name]
    if real_value not in table:
        raise KeyError(
            f"Valor '{real_value}' não encontrado no mapeamento '{mapping_name}'. "
            f"Valores disponíveis: {sorted(table.keys())}"
        )
    return str(table[real_value])


def get_source_config(source_name: str) -> dict[str, Any]:
    """Retorna a configuração de uma fonte específica de config/sources.yaml."""
    sources = load_sources()
    if source_name not in sources:
        raise KeyError(f"Fonte '{source_name}' não definida em config/sources.yaml")
    return sources[source_name]
