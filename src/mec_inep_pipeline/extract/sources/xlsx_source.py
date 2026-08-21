"""Extração de fontes XLSX (ex.: Sinopses Estatísticas do INEP) como dlt resources.

Usa `openpyxl` em modo `read_only=True`, que faz streaming das linhas da
planilha em vez de carregar o workbook inteiro em memória — importante para
os arquivos de 50-200MB citados nos requisitos do projeto.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any

import dlt
from openpyxl import load_workbook

from mec_inep_pipeline.config.settings import REPO_ROOT
from mec_inep_pipeline.load.normalizers import apply_minimal_transformations
from mec_inep_pipeline.utils.logging import get_logger

logger = get_logger(__name__)


def _resolve_local_path(source_config: dict[str, Any]) -> Path:
    """Resolve o caminho local do XLSX a ser lido (mesma lógica do csv_source)."""
    local_path = source_config["location"].get("local_fallback_path")
    if not local_path:
        raise ValueError(
            "source_config['location'] precisa definir 'local_fallback_path' "
            "para extração local (download automático via 'url' ainda não implementado)."
        )
    return REPO_ROOT / local_path


def _read_xlsx_rows(
    path: Path,
    *,
    sheet_name: str | None,
    header_row: int,
    skip_footer_rows: int,
) -> Iterator[dict[str, Any]]:
    """Gera dicts a partir de uma planilha XLSX, usando `header_row` como cabeçalho."""
    workbook = load_workbook(filename=path, read_only=True, data_only=True)
    try:
        sheet = workbook[sheet_name] if sheet_name else workbook.active
        if sheet is None:
            raise ValueError(f"Planilha '{sheet_name}' não encontrada em {path}")

        total_rows = sheet.max_row
        last_data_row = total_rows - skip_footer_rows

        headers: list[str] | None = None
        for row_idx, row in enumerate(sheet.iter_rows(values_only=True), start=1):
            if row_idx < header_row:
                continue
            if row_idx == header_row:
                headers = [
                    str(cell).strip() if cell is not None else f"col_{i}"
                    for i, cell in enumerate(row)
                ]
                continue
            if row_idx > last_data_row:
                break
            if headers is None:
                continue
            yield dict(zip(headers, row, strict=False))
    finally:
        workbook.close()


def build_xlsx_resource(source_name: str, source_config: dict[str, Any]) -> Any:
    """Constrói um dlt resource para uma fonte do tipo 'xlsx'.

    Args:
        source_name: chave da fonte em config/sources.yaml (usada como nome/tabela).
        source_config: bloco de configuração correspondente em config/sources.yaml.
    """
    fmt = source_config.get("format", {})
    sheet_name = fmt.get("sheet_name")
    header_row = int(fmt.get("header_row", 1))
    skip_footer_rows = int(fmt.get("skip_footer_rows", 0))
    # Ver comentário equivalente em csv_source.py sobre a anotação explícita Any.
    primary_key: Any = source_config.get("primary_key")
    write_disposition = source_config.get("write_disposition", "replace")
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
                "Arquivo XLSX não encontrado em %s — pulando fonte '%s'. "
                "Baixe os dados oficiais do INEP antes de rodar o pipeline.",
                path,
                source_name,
            )
            return
        logger.info("Lendo XLSX de %s (sheet=%r, header_row=%d)", path, sheet_name, header_row)
        for row in _read_xlsx_rows(
            path,
            sheet_name=sheet_name,
            header_row=header_row,
            skip_footer_rows=skip_footer_rows,
        ):
            yield apply_minimal_transformations(row)

    return resource
