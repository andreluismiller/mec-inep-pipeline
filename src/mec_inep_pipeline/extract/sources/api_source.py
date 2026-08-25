"""Extração de fontes de API (ex.: indicadores educacionais do INEP) como dlt resources.

Os parâmetros de chamada declarados em config/sources.yaml podem referenciar um
mapeamento de config/api_mappings.yaml (`from_mapping`) — nesse caso, o valor
"real"/legível é traduzido para o identificador que a API espera antes da
chamada, via `mec_inep_pipeline.config.loader.resolve_mapping`.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from typing import Any

import dlt
import requests

from mec_inep_pipeline.config.loader import resolve_mapping
from mec_inep_pipeline.load.normalizers import apply_minimal_transformations
from mec_inep_pipeline.utils.logging import get_logger

logger = get_logger(__name__)

DEFAULT_TIMEOUT_SECONDS = 30
DEFAULT_MAX_PAGES = 1000  # trava de segurança contra loops de paginação infinitos


def _normalize_dict_keys(record: dict[str, Any]) -> dict[str, Any]:
    """Normaliza as chaves de um dict: minúsculas e '-' trocado por '_'."""
    return {str(k).lower().replace("-", "_"): v for k, v in record.items()}


def _build_request_params(source_config: dict[str, Any]) -> dict[str, Any]:
    """Monta o dict de query params, resolvendo `from_mapping` quando presente."""
    params: dict[str, Any] = {}
    for param in source_config.get("request", {}).get("params", []):
        name = param["name"]
        if "static" in param:
            params[name] = param["static"]
        elif "from_mapping" in param:
            # `value` é o valor legível a ser traduzido; por padrão usamos o
            # primeiro valor do mapeamento apenas como placeholder de exemplo —
            # em uso real, isso deve vir de um parâmetro do CLI/config por execução.
            mapping_name = param["from_mapping"]
            real_value = param.get("value")
            if real_value is not None:
                params[name] = resolve_mapping(mapping_name, real_value)
        else:
            logger.warning("Parâmetro '%s' sem 'static' nem 'from_mapping' — ignorado.", name)
    return params


def _iter_pages(source_config: dict[str, Any]) -> Iterator[list[dict[str, Any]]]:
    """Itera as páginas da API, respeitando a estratégia de paginação configurada."""
    location = source_config["location"]
    base_url = os.environ.get(location["base_url_env"], "")
    token = os.environ.get(location.get("token_env", ""), "")
    endpoint = location["endpoint"]
    url = f"{base_url.rstrip('/')}{endpoint}"

    headers = {"Authorization": f"Bearer {token}"} if token else {}
    method = source_config.get("request", {}).get("method", "GET")
    base_params = _build_request_params(source_config)

    pagination = source_config.get("pagination")
    if not pagination:
        # Sem paginação: faz uma única requisição
        logger.debug("Chamando API %s (sem paginação)", url)
        response = requests.request(
            method, url, headers=headers, params=base_params, timeout=DEFAULT_TIMEOUT_SECONDS
        )
        response.raise_for_status()
        payload = response.json()
        items = payload if isinstance(payload, list) else payload.get("data", [])
        if items:
            yield items
        return

    page_param = pagination.get("page_param", "page")
    size_param = pagination.get("size_param", "size")
    page_size = pagination.get("page_size", 100)

    page = 1
    while page <= DEFAULT_MAX_PAGES:
        params = {**base_params, page_param: page, size_param: page_size}
        logger.debug("Chamando API %s (página %d)", url, page)
        response = requests.request(
            method, url, headers=headers, params=params, timeout=DEFAULT_TIMEOUT_SECONDS
        )
        response.raise_for_status()
        payload = response.json()

        items = payload if isinstance(payload, list) else payload.get("data", [])
        if not items:
            break

        yield items
        if len(items) < page_size:
            break
        page += 1


def build_api_resource(source_name: str, source_config: dict[str, Any]) -> Any:
    """Constrói um dlt resource para uma fonte do tipo 'api'.

    Args:
        source_name: chave da fonte em config/sources.yaml (usada como nome/tabela).
        source_config: bloco de configuração correspondente em config/sources.yaml.
    """
    # Ver comentário equivalente em csv_source.py sobre a anotação explícita Any.
    primary_key: Any = source_config.get("primary_key")
    write_disposition = source_config.get("write_disposition", "merge")
    table_name = source_config.get("destination", {}).get("table", source_name)

    # Normalização de chaves (para APIs como a do IBGE)
    normalize_keys = bool(source_config.get("normalize_keys", False))

    @dlt.resource(
        name=source_name,
        table_name=table_name,
        write_disposition=write_disposition,
        primary_key=primary_key,
    )
    def resource() -> Iterator[dict[str, Any]]:
        for page_items in _iter_pages(source_config):
            for item in page_items:
                if normalize_keys:
                    item = _normalize_dict_keys(item)
                yield apply_minimal_transformations(item)

    return resource
