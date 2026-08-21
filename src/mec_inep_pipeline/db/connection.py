"""Conexão direta ao Postgres, para operações fora do dlt (checagens, DDL pontual).

O dlt gerencia sua própria conexão internamente ao carregar dados — este módulo
NÃO é usado pelos pipelines de extração/carga. Ele existe para:
  - scripts de setup (ex.: `CREATE SCHEMA IF NOT EXISTS raw;`)
  - testes de integração que precisam validar o que foi carregado
  - comandos de CLI utilitários (ex.: `mec-inep db check`)
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import psycopg2
import psycopg2.extras

from mec_inep_pipeline.config.settings import get_settings
from mec_inep_pipeline.utils.logging import get_logger

logger = get_logger(__name__)


@contextmanager
def get_connection() -> Iterator[psycopg2.extensions.connection]:
    """Context manager que abre e fecha uma conexão Postgres a partir das Settings."""
    settings = get_settings()
    conn = psycopg2.connect(
        host=settings.postgres_host,
        port=settings.postgres_port,
        dbname=settings.postgres_db,
        user=settings.postgres_user,
        password=settings.postgres_password.get_secret_value(),
    )
    try:
        yield conn
    finally:
        conn.close()


def ensure_schema_exists(schema_name: str | None = None) -> None:
    """Cria o schema de destino (ex.: 'raw') caso ainda não exista."""
    settings = get_settings()
    schema = schema_name or settings.postgres_raw_schema
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema}";')
        conn.commit()
    logger.info("Schema '%s' garantido no Postgres.", schema)


def fetch_all(query: str, params: tuple[Any, ...] | None = None) -> list[dict[str, Any]]:
    """Executa uma query de leitura e retorna as linhas como lista de dicts."""
    with (
        get_connection() as conn,
        conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur,
    ):
        cur.execute(query, params)
        return [dict(row) for row in cur.fetchall()]


def check_connection() -> bool:
    """Testa se é possível conectar ao Postgres configurado. Não lança exceção."""
    try:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute("SELECT 1;")
            cur.fetchone()
        return True
    except Exception:
        logger.exception("Falha ao conectar ao Postgres.")
        return False
