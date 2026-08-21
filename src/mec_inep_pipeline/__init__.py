"""mec_inep_pipeline: pipeline de dados de educação básica (MEC/INEP).

Estrutura de alto nível:
    config/     -> leitura de .env (pydantic-settings) e arquivos YAML (settings.py, loader.py)
    extract/    -> fontes (csv, xlsx, api) e orquestração dos pipelines dlt
    load/       -> transformações mínimas aplicadas antes da carga (normalizers.py)
    db/         -> helpers de conexão com o Postgres de destino
    utils/      -> utilidades transversais (logging etc.)
    cli/        -> interface de linha de comando (typer)
"""

__version__ = "0.1.0"
