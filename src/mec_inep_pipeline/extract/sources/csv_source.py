"""Extração de fontes CSV (ex.: microdados do Censo Escolar) como dlt resources.

Os microdados do INEP costumam vir em arquivos de 50-200MB. Para evitar picos
de memória, a leitura é feita linha a linha com `csv.DictReader` (streaming),
e cada linha é entregue ao dlt como um item de um generator — o dlt cuida do
buffering/chunking na hora de escrever no destino.
"""

from __future__ import annotations

import csv
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import dlt

from mec_inep_pipeline.config.settings import REPO_ROOT
from mec_inep_pipeline.load.normalizers import apply_minimal_transformations
from mec_inep_pipeline.utils.logging import get_logger

logger = get_logger(__name__)


def _resolve_local_path(source_config: dict[str, Any]) -> Path:
    """Resolve o caminho local do CSV a ser lido.

    Nesta etapa inicial do projeto, priorizamos o `local_fallback_path` (o
    download/descompactação da URL oficial do INEP fica para uma etapa
    posterior, de orquestração de ingestão). Isso mantém o módulo de extração
    testável sem depender de rede.
    """
    local_path = source_config["location"].get("local_fallback_path")
    if not local_path:
        raise ValueError(
            "source_config['location'] precisa definir 'local_fallback_path' "
            "para extração local (download automático via 'url' ainda não implementado)."
        )
    return REPO_ROOT / local_path


def _read_csv_rows(path: Path, *, delimiter: str, encoding: str) -> Iterator[dict[str, Any]]:
    """Gera dicts a partir de um arquivo CSV, linha a linha (streaming)."""
    with path.open("r", encoding=encoding, newline="") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        yield from reader


def build_csv_resource(source_name: str, source_config: dict[str, Any]) -> Any:
    """Constrói um dlt resource para uma fonte do tipo 'csv'.

    Args:
        source_name: chave da fonte em config/sources.yaml (usada como nome/tabela).
        source_config: bloco de configuração correspondente em config/sources.yaml.
    """
    fmt = source_config.get("format", {})
    delimiter = fmt.get("delimiter", ",")
    encoding = fmt.get("encoding", "utf-8")
    # Tipado explicitamente como Any: primary_key pode ser str, list[str] ou
    # None dependendo do YAML, e o decorator @dlt.resource aceita todas essas
    # formas — a anotação evita que o mypy infira "Any | None" (que não é
    # compatível com a assinatura do decorator) a partir de dict.get(...).
    primary_key: Any = source_config.get("primary_key")
    write_disposition = source_config.get("write_disposition", "append")
    table_name = source_config.get("destination", {}).get("table", source_name)

    @dlt.resource(
        name=source_name,
        table_name=table_name,
        write_disposition=write_disposition,
        primary_key=primary_key,
    )
    def resource() -> Iterator[dict[str, Any]]:
        path = _resolve_local_path(source_config)
        if not path.exists():
            logger.warning(
                "Arquivo CSV não encontrado em %s — pulando fonte '%s'. "
                "Baixe os dados oficiais do INEP antes de rodar o pipeline.",
                path,
                source_name,
            )
            return
        logger.info("Lendo CSV de %s (delimiter=%r, encoding=%r)", path, delimiter, encoding)
        for row in _read_csv_rows(path, delimiter=delimiter, encoding=encoding):
            yield apply_minimal_transformations(row)

    return resource
