"""Orquestração dos pipelines dlt definidos em config/pipelines.yaml.

Este módulo é o ponto de entrada da camada de extração+carga: dado o nome de
um pipeline (ex.: "censo_escolar"), ele monta os dlt resources das fontes
associadas (config/sources.yaml) e executa `dlt.pipeline(...).run(...)`
contra o destino Postgres configurado em Settings.
"""

from __future__ import annotations

from typing import Any

import dlt

from mec_inep_pipeline.config.loader import get_source_config, load_pipelines
from mec_inep_pipeline.config.settings import get_settings
from mec_inep_pipeline.extract.sources.api_source import build_api_resource
from mec_inep_pipeline.extract.sources.csv_source import build_csv_resource
from mec_inep_pipeline.extract.sources.xlsx_source import build_xlsx_resource
from mec_inep_pipeline.utils.logging import get_logger

logger = get_logger(__name__)

# Registro: tipo declarado em sources.yaml -> função construtora do dlt resource
_SOURCE_BUILDERS = {
    "csv": build_csv_resource,
    "xlsx": build_xlsx_resource,
    "api": build_api_resource,
}


def build_resource(source_name: str) -> Any:
    """Constrói o dlt resource de UMA fonte, a partir do seu nome em sources.yaml."""
    source_config = get_source_config(source_name)
    if not source_config.get("enabled", True):
        logger.info("Fonte '%s' está desabilitada (enabled: false) — pulando.", source_name)
        return None

    source_type = source_config["type"]
    builder = _SOURCE_BUILDERS.get(source_type)
    if builder is None:
        raise ValueError(
            f"Tipo de fonte '{source_type}' não suportado (fonte '{source_name}'). "
            f"Tipos disponíveis: {sorted(_SOURCE_BUILDERS.keys())}"
        )
    return builder(source_name, source_config)


def run_pipeline(pipeline_name: str) -> Any:
    """Executa um pipeline dlt completo (todas as fontes associadas a ele).

    Args:
        pipeline_name: chave em config/pipelines.yaml (ex.: "censo_escolar").

    Returns:
        O `LoadInfo` retornado por `dlt.pipeline().run(...)`.
    """
    pipelines = load_pipelines()
    if pipeline_name not in pipelines:
        raise KeyError(
            f"Pipeline '{pipeline_name}' não definido em config/pipelines.yaml. "
            f"Disponíveis: {sorted(pipelines.keys())}"
        )
    pipeline_config = pipelines[pipeline_name]
    settings = get_settings()

    resources = [
        resource
        for source_name in pipeline_config["sources"]
        if (resource := build_resource(source_name)) is not None
    ]
    if not resources:
        logger.warning(
            "Pipeline '%s' não tem nenhuma fonte habilitada — nada a rodar.", pipeline_name
        )
        return None

    dataset_name = pipeline_config.get("dataset_name") or settings.postgres_raw_schema

    dlt_pipeline = dlt.pipeline(
        pipeline_name=f"{settings.dlt_pipeline_name}_{pipeline_name}",
        destination="postgres",
        dataset_name=dataset_name,
    )

    logger.info(
        "Rodando pipeline '%s' (%d fonte(s)) -> schema '%s'",
        pipeline_name,
        len(resources),
        dataset_name,
    )
    load_info = dlt_pipeline.run(resources)
    logger.info("Pipeline '%s' finalizado: %s", pipeline_name, load_info)
    return load_info


def run_all_pipelines() -> dict[str, Any]:
    """Executa todos os pipelines definidos em config/pipelines.yaml, em sequência."""
    results = {}
    for pipeline_name in load_pipelines():
        results[pipeline_name] = run_pipeline(pipeline_name)
    return results
