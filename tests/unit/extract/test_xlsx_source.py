"""Testes unitários para mec_inep_pipeline.extract.sources.xlsx_source."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from mec_inep_pipeline.extract.sources.xlsx_source import build_xlsx_resource

pytestmark = pytest.mark.unit


def _source_config(fixtures_dir: Path, **overrides: Any) -> dict[str, Any]:
    config: dict[str, Any] = {
        "format": {"sheet_name": "Município", "header_row": 3, "skip_footer_rows": 1},
        "location": {"local_fallback_path": str(fixtures_dir / "mini_sinopse.xlsx")},
        "primary_key": ["CO_MUNICIPIO"],
        "write_disposition": "replace",
        "destination": {"table": "sinopse_educacao_basica_municipios"},
    }
    config.update(overrides)
    return config


class TestBuildXlsxResource:
    def test_reads_only_data_rows_ignoring_header_notes_and_footer(
        self, fixtures_dir: Path
    ) -> None:
        resource = build_xlsx_resource(
            "sinopse_educacao_basica_municipios", _source_config(fixtures_dir)
        )
        rows = list(resource())
        # 2 linhas de dado (Bauru, São Paulo); notas de topo e rodapé descartadas.
        assert len(rows) == 2

    def test_columns_match_header_row(self, fixtures_dir: Path) -> None:
        resource = build_xlsx_resource(
            "sinopse_educacao_basica_municipios", _source_config(fixtures_dir)
        )
        rows = list(resource())
        assert rows[0]["co_municipio"] == "3506003"
        assert rows[0]["no_municipio"] == "Bauru"
        assert rows[0]["qt_escolas"] == 250

    def test_missing_file_yields_no_rows_without_raising(self, fixtures_dir: Path) -> None:
        config = _source_config(fixtures_dir)
        config["location"]["local_fallback_path"] = str(fixtures_dir / "nao_existe.xlsx")
        resource = build_xlsx_resource("sinopse_educacao_basica_municipios", config)
        assert list(resource()) == []
