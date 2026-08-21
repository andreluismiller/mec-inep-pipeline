"""Testes unitários para mec_inep_pipeline.extract.sources.csv_source."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from dlt.extract.exceptions import ResourceExtractionError

from mec_inep_pipeline.extract.sources.csv_source import build_csv_resource

pytestmark = pytest.mark.unit


def _source_config(fixtures_dir: Path, **overrides: Any) -> dict[str, Any]:
    config: dict[str, Any] = {
        "format": {"delimiter": ";", "encoding": "utf-8"},
        "location": {"local_fallback_path": str(fixtures_dir / "mini_escolas.csv")},
        "primary_key": ["CO_ENTIDADE"],
        "write_disposition": "merge",
        "destination": {"table": "censo_escolar_escolas"},
    }
    config.update(overrides)
    return config


class TestBuildCsvResource:
    def test_reads_all_rows_from_fixture(self, fixtures_dir: Path) -> None:
        resource = build_csv_resource("censo_escolar_escolas", _source_config(fixtures_dir))
        rows = list(resource())
        assert len(rows) == 3

    def test_applies_minimal_transformations(self, fixtures_dir: Path) -> None:
        resource = build_csv_resource("censo_escolar_escolas", _source_config(fixtures_dir))
        rows = list(resource())

        # Coluna normalizada para minúsculo (era 'CO_ENTIDADE')
        assert rows[0]["co_entidade"] == "123"
        # Espacos nas pontas removidos
        assert rows[2]["no_entidade"] == "Escola Estadual Exemplo"
        # Tokens nulos ('NA', '-') substituídos por None
        assert rows[1]["no_entidade"] is None
        assert rows[2]["uf"] is None

    def test_resource_name_and_metadata(self, fixtures_dir: Path) -> None:
        resource = build_csv_resource("censo_escolar_escolas", _source_config(fixtures_dir))
        assert resource.name == "censo_escolar_escolas"

    def test_missing_file_yields_no_rows_without_raising(self, fixtures_dir: Path) -> None:
        config = _source_config(fixtures_dir)
        config["location"]["local_fallback_path"] = str(fixtures_dir / "nao_existe.csv")
        resource = build_csv_resource("censo_escolar_escolas", config)
        assert list(resource()) == []

    def test_raises_when_local_fallback_path_missing(self, fixtures_dir: Path) -> None:
        config = _source_config(fixtures_dir)
        del config["location"]["local_fallback_path"]
        resource = build_csv_resource("censo_escolar_escolas", config)
        # O resource é decorado com @dlt.resource: iterá-lo passa pela máquina
        # de extração do dlt, que envolve a exceção original (ValueError) em
        # ResourceExtractionError. A causa original ainda fica acessível via
        # __cause__/__context__ e a mensagem original é preservada no texto.
        with pytest.raises(ResourceExtractionError, match="local_fallback_path"):
            list(resource())
