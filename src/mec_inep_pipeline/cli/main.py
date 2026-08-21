"""CLI da aplicação: `uv run mec-inep --help`.

Comandos principais:
    mec-inep extract run <pipeline>   -> roda um pipeline dlt específico
    mec-inep extract run-all          -> roda todos os pipelines definidos
    mec-inep extract list             -> lista pipelines e fontes configuradas
    mec-inep db check                 -> testa a conexão com o Postgres
    mec-inep db init-schema           -> cria o schema "raw" (idempotente)
"""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from mec_inep_pipeline.config.loader import load_pipelines, load_sources
from mec_inep_pipeline.db.connection import check_connection, ensure_schema_exists
from mec_inep_pipeline.extract.pipelines.run import run_all_pipelines, run_pipeline
from mec_inep_pipeline.utils.logging import setup_logging

app = typer.Typer(help="Pipeline de dados de educação básica (MEC/INEP).", no_args_is_help=True)
extract_app = typer.Typer(help="Comandos de extração/carga (dlt).", no_args_is_help=True)
db_app = typer.Typer(help="Comandos utilitários de banco de dados.", no_args_is_help=True)
app.add_typer(extract_app, name="extract")
app.add_typer(db_app, name="db")

console = Console()


@app.callback()
def _main() -> None:
    setup_logging()


@extract_app.command("run")
def extract_run(
    pipeline: str = typer.Argument(..., help="Nome do pipeline (ver 'extract list')."),
) -> None:
    """Roda um único pipeline dlt (ex.: `mec-inep extract run censo_escolar`)."""
    run_pipeline(pipeline)


@extract_app.command("run-all")
def extract_run_all() -> None:
    """Roda todos os pipelines definidos em config/pipelines.yaml, em sequência."""
    run_all_pipelines()


@extract_app.command("list")
def extract_list() -> None:
    """Lista os pipelines e as fontes configuradas (config/pipelines.yaml e sources.yaml)."""
    sources = load_sources()
    pipelines = load_pipelines()

    table = Table(title="Pipelines configurados")
    table.add_column("Pipeline")
    table.add_column("Fontes")
    table.add_column("Dataset")
    for name, cfg in pipelines.items():
        table.add_row(name, ", ".join(cfg.get("sources", [])), str(cfg.get("dataset_name")))
    console.print(table)

    table = Table(title="Fontes configuradas")
    table.add_column("Fonte")
    table.add_column("Tipo")
    table.add_column("Habilitada")
    table.add_column("Tabela destino")
    for name, cfg in sources.items():
        table.add_row(
            name,
            cfg.get("type", "?"),
            "sim" if cfg.get("enabled", True) else "não",
            cfg.get("destination", {}).get("table", "?"),
        )
    console.print(table)


@db_app.command("check")
def db_check() -> None:
    """Testa a conexão com o Postgres configurado (.env)."""
    ok = check_connection()
    if ok:
        console.print("[bold green]OK[/] conexão com o Postgres bem-sucedida.")
    else:
        console.print("[bold red]FALHA[/] não foi possível conectar ao Postgres. Veja os logs.")
        raise typer.Exit(code=1)


@db_app.command("init-schema")
def db_init_schema() -> None:
    """Cria (se necessário) o schema de destino usado pelos pipelines dlt."""
    ensure_schema_exists()
    console.print("[bold green]OK[/] schema garantido no Postgres.")


if __name__ == "__main__":
    app()
