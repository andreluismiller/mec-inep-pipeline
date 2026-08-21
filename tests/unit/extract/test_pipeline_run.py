"""Testes unitários para mec_inep_pipeline.extract.pipelines.run."""

from __future__ import annotations

from typing import Any

import pytest

from mec_inep_pipeline.extract.pipelines import run as run_module
from mec_inep_pipeline.extract.pipelines.run import build_resource, run_pipeline

pytestmark = pytest.mark.unit


class TestBuildResource:
    def test_dispatches_to_csv_builder(self, monkeypatch: pytest.MonkeyPatch) -> None:
        called_with: dict[str, Any] = {}

        def fake_csv_builder(name: str, config: dict[str, Any]) -> str:
            called_with["name"] = name
            called_with["config"] = config
            return "fake-csv-resource"

        monkeypatch.setitem(run_module._SOURCE_BUILDERS, "csv", fake_csv_builder)
        result = build_resource("censo_escolar_escolas")

        assert result == "fake-csv-resource"
        assert called_with["name"] == "censo_escolar_escolas"

    def test_returns_none_for_disabled_source(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            run_module,
            "get_source_config",
            lambda name: {"type": "csv", "enabled": False},
        )
        assert build_resource("qualquer_fonte") is None

    def test_raises_for_unsupported_source_type(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            run_module,
            "get_source_config",
            lambda name: {"type": "ftp", "enabled": True},
        )
        with pytest.raises(ValueError, match="não suportado"):
            build_resource("fonte_com_tipo_invalido")

    def test_raises_for_unknown_source_name(self) -> None:
        with pytest.raises(KeyError):
            build_resource("fonte_que_nao_existe_no_yaml")


class TestRunPipeline:
    def test_raises_for_unknown_pipeline(self) -> None:
        with pytest.raises(KeyError, match="não definido"):
            run_pipeline("pipeline_que_nao_existe")

    def test_returns_none_when_no_resource_is_enabled(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            run_module,
            "load_pipelines",
            lambda: {"fake_pipeline": {"sources": ["fonte_desabilitada"], "dataset_name": "raw"}},
        )
        monkeypatch.setattr(
            run_module,
            "get_source_config",
            lambda name: {"type": "csv", "enabled": False},
        )
        assert run_pipeline("fake_pipeline") is None
