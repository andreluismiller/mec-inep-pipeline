"""Testes unitários para mec_inep_pipeline.config.loader."""

from __future__ import annotations

import pytest

from mec_inep_pipeline.config.loader import (
    get_source_config,
    load_api_mappings,
    load_pipelines,
    load_sources,
    load_yaml,
    resolve_mapping,
)

pytestmark = pytest.mark.unit


class TestLoadYaml:
    def test_loads_real_sources_yaml(self) -> None:
        data = load_yaml("sources.yaml")
        assert "sources" in data
        assert data["version"] == 1

    def test_raises_for_missing_file(self) -> None:
        with pytest.raises(FileNotFoundError):
            load_yaml("arquivo_que_nao_existe.yaml")


class TestLoadSourcesAndPipelines:
    def test_load_sources_returns_expected_keys(self) -> None:
        sources = load_sources()
        assert "censo_escolar_escolas" in sources
        assert "sinopse_educacao_basica_municipios" in sources
        assert "indicadores_educacionais_api" in sources

    def test_load_pipelines_returns_expected_keys(self) -> None:
        pipelines = load_pipelines()
        assert "censo_escolar" in pipelines
        assert "sinopses_estatisticas" in pipelines

    def test_pipeline_dataset_name_interpolates_env_var(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("POSTGRES_RAW_SCHEMA", "meu_schema_customizado")
        load_yaml.cache_clear()
        pipelines = load_pipelines()
        assert pipelines["censo_escolar"]["dataset_name"] == "meu_schema_customizado"

    def test_get_source_config_returns_the_right_block(self) -> None:
        config = get_source_config("censo_escolar_escolas")
        assert config["type"] == "csv"
        assert config["primary_key"] == ["CO_ENTIDADE"]

    def test_get_source_config_raises_for_unknown_source(self) -> None:
        with pytest.raises(KeyError, match="não definida"):
            get_source_config("fonte_inexistente")


class TestApiMappings:
    def test_load_api_mappings_excludes_version_key(self) -> None:
        mappings = load_api_mappings()
        assert "version" not in mappings
        assert "uf" in mappings
        assert "etapa_ensino" in mappings

    def test_all_27_ufs_present(self) -> None:
        mappings = load_api_mappings()
        assert len(mappings["uf"]) == 27

    def test_resolve_mapping_translates_known_value(self) -> None:
        assert resolve_mapping("uf", "São Paulo") == "35"
        assert resolve_mapping("uf", "Acre") == "12"

    def test_resolve_mapping_raises_for_unknown_mapping_name(self) -> None:
        with pytest.raises(KeyError, match="Mapeamento"):
            resolve_mapping("mapeamento_inexistente", "qualquer")

    def test_resolve_mapping_raises_for_unknown_value(self) -> None:
        with pytest.raises(KeyError, match="não encontrado"):
            resolve_mapping("uf", "Atlântida")
